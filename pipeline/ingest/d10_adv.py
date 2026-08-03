"""D10 — Form ADV registration identity, from the IAPD search API.

WHAT THIS CORRECTS. An earlier session recorded that "every automated route to ADV data refuses
a correctly-identified client". That was wrong, and the error was mine rather than the host's:
the client was sending a repository URL as its User-Agent, and the SEC requires an email
address. With a compliant header `api.adviserinfo.sec.gov/search/firm` answers normally. The
conclusion had been drawn from a 403 produced by my own non-compliance, which is exactly the
shape of mistake this repository keeps finding — a local fault wearing a remote refusal's face.

WHAT IS STILL OUT OF REACH, and why it is a rule rather than an obstacle. Regulatory AUM
(Part 1A Item 5.F) and the prime-broker roster (Schedule D Section 7.B.(1) Q24) live in the ADV
FORM, not in the search index. The form viewer is disallowed by
`adviserinfo.sec.gov/robots.txt` (`/IAPD/content/viewform/adv*.aspx`) and the PDF host answers
403 to everything. Those two columns are therefore transcribed by hand from a browser, which is
a person reading a public page and a different act from a crawler.

So this module fills the identity half of the ADV column — registration status, SEC file
number, CRD, the date the adviser last filed, and the relying-adviser roster — and leaves the
two form-only fields to the manual checklist.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ._http import DEFAULT_CLIENT

SEARCH = "https://api.adviserinfo.sec.gov/search/firm"

#: The registered legal name to search for, per manager label. Short labels are ambiguous and
#: the search returns its nearest neighbour rather than nothing, so a two-word label reaches an
#: unrelated same-sector firm. These are the names as registered, not as colloquially used.
ADV_QUERY: dict[str, str] = {
    "Citadel Advisors": "Citadel Advisors LLC",
    "Millennium Management": "Millennium Management LLC",
    "Point72 Asset Management": "Point72 Asset Management",
    "Balyasny Asset Management": "Balyasny Asset Management",
    "D. E. Shaw": "D. E. Shaw & Co",
    "Davidson Kempner": "Davidson Kempner Capital Management",
    "Mason Capital": "Mason Capital Management",
    "Pentwater Capital": "Pentwater Capital Management",
    "Elliott Investment Management": "Elliott Investment Management",
    "Weiss Asset Management": "Weiss Asset Management",
    "Dalton Investments": "Dalton Investments",
    "Wellington Management": "Wellington Management Company",
    "Capital Research": "Capital Research and Management",
    "BlackRock": "BlackRock Advisors",
    "T. Rowe Price": "T. Rowe Price Associates",
    "Silchester": "Silchester International Investors",
    "Macquarie": "Macquarie Investment Management",
    "Nomura": "Nomura Asset Management",
    # Norges Bank is a central bank, not a US-registered investment adviser. It files 13F as an
    # institutional manager and has no ADV. The empty cell is the correct answer, not a gap.
    "Norges Bank": "Norges Bank",
}


@lru_cache(maxsize=256)
def firm_lookup(name: str) -> dict | None:
    """Registration identity for the best-matching ACTIVE adviser named ``name``.

    Prefers an active registration whose name starts with the query, because a search for one
    manager returns its relying advisers and foreign affiliates alongside the principal entity.
    """
    raw = DEFAULT_CLIENT.get(SEARCH, params={"query": name, "start": "0", "hits": "10"})
    hits = json.loads(raw).get("hits", {}).get("hits", [])
    rows = [h.get("_source", {}) for h in hits]
    if not rows:
        return None

    needle = name.upper().replace(".", "").replace(",", "")

    def rank(r: dict) -> tuple:
        nm = (r.get("firm_name") or "").upper().replace(".", "").replace(",", "")
        return (r.get("firm_ia_scope") != "ACTIVE", not nm.startswith(needle), len(nm))

    best = sorted(rows, key=rank)[0]

    # REFUSE A NEAR-MISS. The search returns the closest thing it has, which for an adviser that
    # is not registered is some other firm entirely — a query for one manager returned a
    # same-sector firm with a different name, and publishing its SEC file number against the
    # wrong manager would be a false statement about two real firms at once. Requiring the first
    # two tokens to agree turns that into an empty cell, and empty is this table's honest value.
    best_name = (best.get("firm_name") or "").upper().replace(".", "").replace(",", "")
    lead = " ".join(needle.split()[:2])
    if lead and not best_name.startswith(lead):
        return None
    return {
        "firm_name": best.get("firm_name"),
        "crd": best.get("firm_source_id"),
        "sec_number": best.get("firm_ia_full_sec_number"),
        "status": best.get("firm_ia_scope"),
        "has_disclosure": best.get("firm_ia_disclosure_fl"),
        "relying_advisers": len(best.get("firm_relying_advisors") or []),
        "other_names": len(best.get("firm_other_names") or []),
    }


def iapd_url(crd: str | int) -> str:
    """The public firm page a person would open to transcribe RAUM and the PB roster."""
    return f"https://adviserinfo.sec.gov/firm/summary/{crd}"


if __name__ == "__main__":
    got = firm_lookup("Citadel Advisors")
    assert got and got["crd"], got
    assert got["sec_number"].startswith("801-"), got
    assert got["status"] == "ACTIVE", got
    # The ranking must prefer the principal entity over its relying advisers.
    assert "CITADEL ADVISORS" in got["firm_name"].upper(), got
    assert iapd_url(148826).endswith("/148826")
    print("ok:", got)
