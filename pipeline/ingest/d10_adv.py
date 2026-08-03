"""D10 — Form ADV registration identity, from the IAPD search API.

WHAT THIS CORRECTS. An earlier session recorded that "every automated route to ADV data refuses
a correctly-identified client". That was wrong, and the error was mine rather than the host's:
the client was sending a repository URL as its User-Agent, and the SEC requires an email
address. With a compliant header `api.adviserinfo.sec.gov/search/firm` answers normally. The
conclusion had been drawn from a 403 produced by my own non-compliance, which is exactly the
shape of mistake this repository keeps finding — a local fault wearing a remote refusal's face.

REGULATORY AUM COMES FROM THE SANCTIONED BULK ROUTE, not from the interface. The SEC publishes
a monthly FOIA extract of Form ADV Part 1A on its data-research pages — 448 columns, one row
per registered adviser, keyed by CRD — and Item 5.F(2)(c) in it IS regulatory AUM. That file
exists precisely so this data does not have to be scraped out of IAPD, so it is the route used.
See :func:`adv_bulk`.

WHAT REMAINS OUT OF REACH is one field, and the reason is now specific rather than general. The
prime-broker roster is Schedule D Section 7.B.(1) Question 24, which is per-private-fund and
appears in no published bulk file — the extract is firm-level Part 1A only. It exists in the
per-firm ADV form, whose viewer `adviserinfo.sec.gov/robots.txt` disallows
(`/IAPD/content/viewform/adv*.aspx`). So that one column is transcribed by hand from a browser,
which is a person reading a public page and a different act from a crawler.
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


#: SEC's own FOIA bulk extract of Form ADV Part 1A, one row per registered adviser, keyed by
#: CRD. This is the SANCTIONED machine route — published by the SEC on its data-research pages
#: precisely so that this data does not have to be scraped out of the IAPD interface.
ADV_BULK = ("https://www.sec.gov/files/investment/data/other/"
            "information-about-registered-investment-advisers-exempt-reporting-advisers/"
            "ia050126.zip")

#: Item 5.F(2)(c) IS regulatory assets under management. The other 5.F columns are the account
#: counts and the discretionary/non-discretionary split; (2)(c) is the total.
RAUM_COLUMN = "5F(2)(c)"


@lru_cache(maxsize=1)
def adv_bulk() -> dict[str, dict]:
    """CRD -> the adviser's Part 1A row from the SEC bulk extract.

    Note what is NOT here: Schedule D Section 7.B.(1), the per-private-fund page carrying the
    prime-broker roster. The bulk extract is firm-level Part 1A only, and no Schedule D file is
    published alongside it. So RAUM fills from this and the prime-broker column does not.
    """
    import csv
    import io
    import zipfile

    raw = DEFAULT_CLIENT.get(ADV_BULK)
    archive = zipfile.ZipFile(io.BytesIO(raw))
    with archive.open(archive.namelist()[0]) as handle:
        reader = csv.DictReader(io.TextIOWrapper(handle, encoding="latin-1"))
        return {(row.get("Organization CRD#") or "").strip(): row for row in reader}


def raum(crd: str | int) -> float | None:
    """Regulatory AUM in USD for one CRD, or None if the adviser is not in the extract."""
    row = adv_bulk().get(str(crd).strip())
    if not row:
        return None
    value = (row.get(RAUM_COLUMN) or "").replace(",", "").replace("$", "").strip()
    try:
        return float(value)
    except ValueError:
        return None
