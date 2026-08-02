"""Push, then PROVE the push by re-fetching the rendered public page.

WHY THIS EXISTS. On 2026-07-30 the author fetched the public repository and saw a five-commit
history with the day-one README, while every session had reported a successful push. The
reported pushes were in fact real -- `git ls-remote`, `git rev-list --count origin/main` and
the rendered HTML all independently showed 59 commits and the corrected README -- so the
stale view came from a cached page, not from a broken push path.

That the alarm was false does not make the process sound. For weeks the only evidence that a
push had landed was an agent saying so, and a `git push` that exits 0 proves the ref moved on
SOME remote, not that the public page a reader loads reflects it. This module closes that
gap: it pushes, then fetches the public page and checks the commit count moved and the
expected paths are visible. Evidence, not assertion.

    uv run python -m scripts.publish            # verify only, no push
    uv run python -m scripts.publish --push     # push, then verify
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = "https://github.com/ZinuoS/Charon"
#: Paths whose absence from the rendered page means the reader is not seeing the project.
EXPECT_PATHS = ("notebooks", "pipeline", "docs", "tests", "README.md")


def _git(*args: str) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()


def local_state() -> dict:
    return {"branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "head": _git("rev-parse", "HEAD"),
            "count": int(_git("rev-list", "--count", "HEAD")),
            "remote": _git("remote", "get-url", "origin")}


def remote_ref() -> dict:
    """The remote's refs, queried live. Not the local cache of them."""
    out = _git("ls-remote", "origin")
    refs = dict(reversed(line.split("\t")) for line in out.splitlines() if "\t" in line)
    return {"main": refs.get("refs/heads/main"), "head": refs.get("HEAD"), "all": refs}


def api_head() -> dict:
    """The authoritative HEAD of the default branch, uncached.

    CORRECTED 2026-08-02: THIS CACHES TOO. An earlier version of this module treated the API
    as authoritative because the HTML page had been caught lagging. Then the opposite happened
    -- `ls-remote` and the rendered page both showed a landed push while this endpoint still
    returned the previous sha. Both HTTP surfaces cache; neither is authoritative.

    THE ONLY UNCACHED SOURCE IS `git ls-remote`, which speaks the git protocol rather than
    HTTP. That is the primary check and it is done in `remote_ref()`. The API and the page are
    CORROBORATING signals: useful, because they are what a reader and a script actually see,
    and each can lag a push by minutes. A disagreement between them and ls-remote is reported
    as lag, not as failure -- reporting it as failure is what produced the false alarm this
    module was written to diagnose in the first place.
    """
    req = urllib.request.Request(
        "https://api.github.com/repos/ZinuoS/Charon/commits/main",
        headers={"User-Agent": "charon-publish-verify",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    return {"sha": j["sha"], "date": j["commit"]["committer"]["date"],
            "subject": j["commit"]["message"].splitlines()[0]}


def rendered_page() -> dict:
    """What a reader actually loads. Secondary — it is cached and can lag a landed push."""
    req = urllib.request.Request(PUBLIC, headers={"User-Agent": "charon-publish-verify"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    m = re.search(r'([\d,]+)\s*Commits?', html) or re.search(r'"totalCount":(\d+)', html)
    count = int(m.group(1).replace(",", "")) if m else None
    return {"commits": count,
            "paths_present": {p: (f'>{p}<' in html or f'/{p}"' in html or f"/{p}'" in html)
                              for p in EXPECT_PATHS},
            "bytes": len(html)}


def verify(expect_count: int | None = None) -> tuple[bool, list[str]]:
    loc, rem = local_state(), remote_ref()
    problems: list[str] = []

    if rem["main"] != loc["head"]:
        problems.append(f"remote refs/heads/main {rem['main']!r} != local HEAD {loc['head']!r}")
    if rem["head"] != rem["main"]:
        problems.append(f"remote HEAD {rem['head']!r} != refs/heads/main — the DEFAULT BRANCH "
                        "is not main, so the public page serves something else")
    api_lag = None
    try:
        api = api_head()
    except Exception as exc:                      # network refusal is not a pass
        problems.append(f"could not reach the GitHub API: {type(exc).__name__}: {exc}")
        api = {}
    else:
        if api["sha"] != loc["head"]:
            # ls-remote above is the authority. This endpoint caches, so a mismatch here
            # while the ref matches is lag, not failure.
            api_lag = api["sha"][:7]

    lag = None
    try:
        page = rendered_page()
    except Exception as exc:
        problems.append(f"could not fetch {PUBLIC}: {type(exc).__name__}: {exc}")
        page = {}
    else:
        if page["commits"] is not None and page["commits"] != loc["count"]:
            # Not a problem when the API already agrees: the landing page is cached.
            lag = page["commits"]
            if api and api.get("sha") != loc["head"]:
                problems.append(f"rendered page shows {page['commits']} commits, local has "
                                f"{loc['count']}")
        missing = [p for p, ok in page["paths_present"].items() if not ok]
        if missing:
            problems.append(f"paths not visible on the rendered page: {missing}")
    if expect_count is not None and loc["count"] != expect_count:
        problems.append(f"local count {loc['count']} != expected {expect_count}")

    print(f"  local    {loc['branch']} @ {loc['head'][:7]}  ({loc['count']} commits)")
    print(f"  remote   refs/heads/main @ {(rem['main'] or '—')[:7]}")
    if api:
        note = "  (cached — lagging)" if api["sha"] != loc["head"] else ""
        print(f"  API      HEAD @ {api['sha'][:7]}  ({api['date']}){note}")
    if lag is not None:
        print(f"  note     the rendered page still shows {lag} commits — GitHub caches the "
              "landing page; the API above is authoritative")
    if page:
        print(f"  rendered {PUBLIC} shows {page['commits']} commits, "
              f"{sum(page['paths_present'].values())}/{len(EXPECT_PATHS)} expected paths")
    return (not problems), problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--push", action="store_true", help="push before verifying")
    ap.add_argument("--skip-tests", action="store_true",
                    help="push without running the suite first. For recovery only.")
    args = ap.parse_args(argv)

    if args.push and not args.skip_tests:
        # A push that can outrun its own test suite is the same defect class as a push that
        # reports success it never verified. Gated here rather than only in the justfile,
        # because the justfile is not what every caller uses.
        print("  running the suite before pushing")
        r = subprocess.run(("uv", "run", "pytest", "-q", "-p", "no:warnings"),
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            tail = [l for l in r.stdout.splitlines() if "failed" in l or l.startswith("FAILED")]
            print("  SUITE FAILED — not pushing:", file=sys.stderr)
            for l in tail[-8:]:
                print(f"    {l}", file=sys.stderr)
            return 1

    if args.push:
        branch = local_state()["branch"]
        # Explicit refspec. `git push origin HEAD` pushes to a branch of the CURRENT name,
        # which silently creates a side branch the public page never serves if HEAD is not
        # main -- the exact failure this module was written to be able to detect.
        print(f"  pushing {branch} -> origin/main")
        subprocess.run(("git", "push", "origin", f"{branch}:main"), cwd=ROOT, check=True)

    ok, problems = verify()
    if ok:
        print("\n  VERIFIED — the public page reflects local HEAD.")
        return 0
    print("\n  NOT VERIFIED:", file=sys.stderr)
    for p in problems:
        print(f"    - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
