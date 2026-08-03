"""The tests that replace the gitignore exclusion on named client research.

Session 32R Amendment D lifted the placement rule: named managers may be discussed in the
public repository because the analysis rests on public filings. The exclusion was a blunt
instrument — it made the question unaskable rather than answerable. What replaces it is craft,
and craft that is not enforced is a preference. So it is enforced here.

Three rules, each a real failure mode rather than a style preference:

1.  CITATION-OR-SILENCE. A named claim without a document behind it is an assertion about a
    real firm made by someone with no standing to make it.
2.  NO INSIDE KNOWLEDGE. The text must not imply awareness of any manager's current interest,
    discussions, or relationship with any desk. The author holds non-public knowledge; the
    danger is not deliberate disclosure but a sentence that reads as though informed by it.
3.  PROXY LABELLING. Korea-ADR appetite is not this trade, and a simultaneous holding of two
    listed lines is not a hedged pair. Where a proxy stands in for the thing, the substitution
    is stated where the claim is made, not in a footnote a reader may not reach.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPENDIX = ROOT / "docs" / "appendix"

#: Managers nameable in the screen. Kept here so the tests fail loudly if prose starts naming
#: firms the rule-determined row set never admitted.
NAMED = ("Citadel", "Millennium", "Point72", "Balyasny", "D. E. Shaw", "D.E. Shaw",
         "Davidson Kempner", "Mason Capital", "Pentwater", "Elliott", "Weiss",
         "Dalton", "Wellington", "Capital Research", "Capital Group", "BlackRock",
         "T. Rowe Price", "Silchester", "Macquarie", "Nomura", "Norges")

#: Language that would imply private knowledge of a commercial relationship.
INSIDE = re.compile(
    r"(?i)\b(our client|the client|a client of|prospective client|interested in|"
    r"has expressed|in discussions|in conversation|we understand|we know|"
    r"has approached|approached us|is engaged|currently engaged|has asked us|"
    r"we are told|reportedly wants|is looking to)\b")

#: A citation is a specific, checkable document reference.
CITATION = re.compile(
    r"(?i)(accession|000\d{7}-\d\d-\d{6}|13F-HR|13[DG]|N-PORT|N-CSR|Form ADV|Schedule D|"
    r"Item 5\.?F|rcpNo|rcept|DART filing|prospectus|CIK\s*\d|IAPD|dated \d{4}|"
    r"\b(19|20)\d{2}-\d\d-\d\d\b|Q[1-4]\s*20\d\d)")


def appendix_files() -> list[Path]:
    return sorted(APPENDIX.glob("*.md")) if APPENDIX.is_dir() else []


def named_lines(path: Path) -> list[tuple[int, str]]:
    """Lines mentioning a manager, excluding this file's own rule statements."""
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(n.lower() in line.lower() for n in NAMED):
            out.append((i, line))
    return out


@pytest.mark.skipif(not APPENDIX.is_dir(), reason="named appendix not built yet")
class TestNamedScreenDiscipline:

    def test_no_language_implying_a_commercial_relationship(self):
        """Rule 2. The strictest of the three, and the one worth failing a build over.

        A single sentence reading as though it were informed by non-public knowledge does more
        damage than a hundred uncited numbers: the numbers are checkable and wrong, the
        sentence is unfalsifiable and compromising.
        """
        hits = []
        for f in appendix_files():
            for i, line in named_lines(f):
                if INSIDE.search(line):
                    hits.append(f"{f.name}:{i}  {line.strip()[:120]}")
        assert not hits, ("language implying private knowledge of a relationship, adjacent to "
                          "a manager name:\n  " + "\n  ".join(hits))

    def test_every_named_claim_carries_a_citation(self):
        """Rule 1. Every line that names a manager cites a document, on that same line."""
        uncited = []
        for f in appendix_files():
            for i, line in named_lines(f):
                stripped = line.strip()
                if stripped.startswith(("#", ">", "|---")) or len(stripped) < 40:
                    continue            # headings and table rules make no claims
                if not CITATION.search(line):
                    uncited.append(f"{f.name}:{i}  {stripped[:120]}")
        assert not uncited, ("named claims with no document reference on the line:\n  "
                             + "\n  ".join(uncited))

    def test_proxy_evidence_is_labelled_where_it_is_used(self):
        """Rule 3. The two proxies must be disclosed in the files that rely on them."""
        for f in appendix_files():
            text = f.read_text(encoding="utf-8").lower()
            if "korea-adr" in text or "korea adr" in text:
                assert "proxy" in text, (
                    f"{f.name} uses Korea-ADR appetite as evidence without labelling it a "
                    f"proxy — appetite for the complex is not this trade")
            if "discount-pair" in text or "discount dna" in text or "discount-dna" in text:
                assert "proxy" in text or "not a hedged pair" in text, (
                    f"{f.name} uses discount-pair DNA without stating that a simultaneous "
                    f"holding is not a hedged pair")

    def test_the_visibility_boundary_is_stated(self):
        """The Q3-13F date is the honest limit of everything nameable, so it must appear."""
        joined = " ".join(f.read_text(encoding="utf-8") for f in appendix_files())
        assert "2026-11-14" in joined, (
            "the appendix must state when SKHY ADR holders first become visible in filings; "
            "without it, a reader may take the screen for a register of this pair's holders")


def test_rules_actually_bite():
    """The guards must reject the things they exist to reject.

    A test of the tests, because rules 1 and 2 are regex-shaped and a regex that matches
    nothing passes every file silently — which is the failure mode that would matter most.
    """
    assert INSIDE.search("Citadel is interested in the structure")
    assert INSIDE.search("we understand Millennium would want the standby form")
    assert not INSIDE.search("filings show Citadel Advisors held KB Financial in Q1 2026")
    assert CITATION.search("13F-HR for Q1 2026 shows the position")
    assert CITATION.search("DART filing 20260730000099")
    assert not CITATION.search("Wellington is a large and capable manager")
