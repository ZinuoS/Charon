"""The hard boundary: archetypes only, never a named client.

Historical episodes and publicly listed vehicles may be named AS HISTORY — that is what a
citation is. What may never appear is a live fund presented as a counterparty, or any
inference about a specific current relationship. The distinction is the whole reason the
clientele analysis can exist in a public repository at all, so it is a test rather than a
convention.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "pipeline" / "package" / "clientele.py",
           ROOT / "scripts" / "build_notebook_11.py",
           ROOT / "pipeline" / "viz" / "figures.py"]

#: Language that turns a citation into a client claim.
CLIENT_CLAIM = re.compile(
    r"\bour client\b|\bthe client is\b|\bcurrent(ly)? (a )?client\b"
    r"|\bprospect(ive)? client\b|\bis (our|the) counterparty\b"
    r"|\bwe are pitching \w+ to\b", re.IGNORECASE)


#: A line that PROHIBITS the language is not a line that uses it. Without this the guard
#: trips on its own definition -- the docstring saying "no live fund appears as a current
#: client" matched, which is the rule, not a breach of it.
_NEGATED = re.compile(r"\b(no|not|never|nothing|cannot|may not|is not|avoid|prohibit\w*"
                      r"|prevent\w*|omit\w*)\b", re.IGNORECASE)


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: p.name)
def test_no_named_client(path):
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    hits = []
    for i, ln in enumerate(path.read_text().splitlines(), 1):
        m = CLIENT_CLAIM.search(ln)
        # The negation may sit either side of the phrase -- `"our client" is not` puts it
        # after -- so the whole line is the window, not just the prefix.
        if m and not _NEGATED.search(ln):
            hits.append((i, ln.strip()))
    assert not hits, (
        f"{path.name} presents someone as a client:\n"
        + "\n".join(f"  line {i}: {ln[:110]}" for i, ln in hits)
        + "\nHistory may be named; a counterparty may not."
    )


def test_every_clientele_row_states_its_confidence_and_verification():
    """A row that cannot say how well-sourced it is has no business being cited."""
    from pipeline.package import clientele as CLI

    for row in CLI.CLIENTELE:
        assert row["confidence"] in ("canonical", "documented", "thin"), row["archetype"]
        assert row.get("verified_this_session"), (
            f"{row['archetype']}: must state whether the source was opened while writing — "
            "'I know this' and 'I checked this' are different claims"
        )


def test_every_gate_declares_measured_or_convention():
    from pipeline.package import clientele as CLI

    for g in CLI.FUNNEL_GATES:
        assert g["basis"].startswith(("measured", "convention")), (
            f"{g['gate']}: a gate must say whether it rests on a measurement or a convention; "
            "a filter that looks empirical but is not borrows credibility it did not earn"
        )


def test_no_researched_fund_name_appears_in_any_committed_file():
    """Named funds live in the gitignored research layer and nowhere else.

    The names are read FROM that layer rather than hardcoded here, so the guard cannot drift
    out of sync with what has actually been researched — and this test file is itself
    committed, so it must not contain them either. Anything matching is checked only against
    files git actually tracks.
    """
    import re
    import subprocess

    research = ROOT / "docs" / "client_research"
    if not research.exists():
        pytest.skip("no client research on this machine")

    # Proper-noun-ish entity names from the research pages: capitalised runs of 2+ words.
    names = set()
    for f in research.glob("*.md"):
        for m in re.finditer(r"\b([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+){1,4}(?: Inc| Ltd| LP| LLC)?)\b",
                             f.read_text()):
            cand = m.group(1)
            if len(cand.split()) >= 2 and not cand.startswith(("The ", "This ", "Not ", "Every ")):
                names.add(cand)
    # Only entity-shaped names carrying a corporate suffix are treated as blocking.
    blocking = {n for n in names if re.search(r"\b(Inc|Ltd|LP|LLC|Fund|Capital|Partners)\b", n)}
    assert blocking, "no entity-shaped names found — the guard would be vacuous"

    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.split()
    hits = []
    for rel in tracked:
        f = ROOT / rel
        if not f.is_file() or f.suffix in (".png", ".ipynb", ".lock", ".json", ".csv"):
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for n in blocking:
            if n in text:
                hits.append((rel, n))
    assert not hits, (
        "researched fund names leaked into committed files:\n"
        + "\n".join(f"  {rel}: {n}" for rel, n in sorted(set(hits))[:12])
        + "\nNamed research belongs in docs/client_research/ only."
    )
