"""Pre-push audit: what must never leave this machine.

Run before the first push. Scans everything git WOULD track (not the working tree —
gitignored payloads are irrelevant) for five classes of leak.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "key material": [
        re.compile(r"\b[0-9a-f]{32}\b"),                    # FRED-style
        re.compile(r"\b[0-9a-f]{40}\b"),                    # OpenDART-style
        re.compile(r"\b[0-9a-f]{14}\.[0-9]{8}\b"),          # EODHD-style
        # Any `<something>key=<value>` parameter, not only the ones spelled "api_key". DART's
        # is `crtfc_key`, which the previous alternation could not reach: it required a literal
        # "api" before "key", so a keyed request URL in a pull log or a notebook output would
        # have passed the audit clean. Widened 2026-08-03, before the pull that produces such
        # URLs.
        #
        # The VALUE side is deliberately strict: >=16 chars and at least one digit. A looser
        # version of this pattern flagged `key = os.environ.get(...)` in all three adapters --
        # the variable name, never a value. Three false blocking hits on a first run is worse
        # than the gap it closed, because an audit that cries wolf is one the operator learns
        # to wave through, and this file already carries that lesson about a stale reminder.
        re.compile(r"(?i)[a-z_-]*(?:key|token|secret|password)\s*[=:]\s*"
                   r"['\"]?(?=[A-Za-z0-9._-]*\d)[A-Za-z0-9._-]{16,}"),
    ],
    "absolute local path": [re.compile(r"/Users/[a-z0-9]+/", re.I)],
    "withheld-source data": [re.compile(r"(?i)(smbs|investing\.com)[-_/]?(scrape|fx_swap_xml)")],
}
# Desk/firm names are deliberately NOT hardcoded here — writing them into a committed
# audit script would itself be the leak. The check is structural: flag any capitalised
# multi-word token adjacent to desk vocabulary for human review.
DESK_HINT = re.compile(r"(?i)\b(desk|colleague|internal (?:memo|email|call)|our team)\b")

SKIP_SUFFIX = {".png", ".lock", ".pyc"}

#: Notebooks are NOT skipped, but their base64 image payloads are stripped before scanning.
#: They used to be skipped wholesale -- and they are tracked, they carry EXECUTED OUTPUT, and
#: this project's whole publishing model is that the notebooks show real results. A key printed
#: into an output cell would have shipped past a clean audit. The skip existed because a base64
#: PNG trips the bare-hex patterns; stripping the payload keeps that protection without
#: exempting the text, which is where a leak would actually be legible.
def notebook_text(path: Path) -> str:
    import json

    try:
        nb = json.loads(path.read_text(errors="replace"))
    except Exception:
        return path.read_text(errors="replace")      # unparseable: scan it raw rather than skip

    parts: list[str] = []
    for cell in nb.get("cells", []):
        parts.extend(cell.get("source", []))
        for output in cell.get("outputs", []):
            parts.extend(output.get("text", []))
            for mime, payload in (output.get("data") or {}).items():
                if mime.startswith(("image/", "application/pdf")):
                    continue                          # the base64 blob, not readable text
                parts.extend(payload if isinstance(payload, list) else [str(payload)])
    return "\n".join(parts)


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    files = [ROOT / f for f in out.splitlines() if f.strip()]
    if not files:  # no commits yet — audit what WOULD be tracked
        out = subprocess.run(["git", "add", "-An", "--dry-run", "."], cwd=ROOT,
                             capture_output=True, text=True).stdout
        files = [ROOT / m.group(1) for line in out.splitlines()
                 if (m := re.match(r"add '(.+)'", line))]
    return [f for f in files if f.is_file() and f.suffix not in SKIP_SUFFIX]


def main() -> int:
    files = tracked_files()
    print(f"auditing {len(files)} files git would track\n")
    findings: list[tuple[str, str, int, str]] = []
    for f in files:
        try:
            text = notebook_text(f) if f.suffix == ".ipynb" else f.read_text(errors="replace")
        except Exception:
            continue
        rel = f.relative_to(ROOT).as_posix()
        for i, line in enumerate(text.splitlines(), 1):
            for label, pats in PATTERNS.items():
                for p in pats:
                    if p.search(line):
                        findings.append((label, rel, i, line.strip()[:110]))
            if DESK_HINT.search(line):
                findings.append(("desk-vocabulary (review)", rel, i, line.strip()[:110]))

    if not findings:
        print("  CLEAN — no key material, local paths, withheld-source data or desk vocabulary.")
    for label, rel, i, snippet in findings:
        print(f"  [{label}] {rel}:{i}\n      {snippet}")

    blocking = [f for f in findings if not f[0].startswith("desk-vocabulary")]
    print(f"\n  blocking: {len(blocking)}   review-only: {len(findings) - len(blocking)}")
    # README §0 was AMENDED 2026-07-28: the repository is public by the author's decision,
    # and the firm name was removed at the same time under §0's own rule. The old reminder
    # told the operator to confirm a setting the constitution no longer asks for, which is a
    # worse failure than no reminder -- a checklist that is wrong trains you to skip it.
    print("\n  README §0 (amended 2026-07-28): repository is PUBLIC by author decision.")
    print("  What still matters on every push: no key material, no internal names, no")
    print("  withheld-source data. All three are checked above, not remembered.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
