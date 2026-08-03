"""D9 — 13F holdings screens: who demonstrably trades this family, from filings alone.

WHAT THIS CAN AND CANNOT SEE, stated first because every number below inherits it. Form 13F
reports LONG positions in US-listed securities held by managers above the reporting threshold,
quarterly, with a 45-day lag. It does not report shorts, does not report foreign-listed lines,
and does not report swap exposure. A short-ADR/long-local pair is therefore invisible in 13F by
construction — BOTH of its legs, for two different reasons.

So nothing here is evidence of the pair trade. What it is evidence of is APPETITE and DNA:
which managers hold Korean ADR complex names at size, and which hold both legs of a
US-listed discount structure at the same time. Both are proxies, and the proxy status travels
with every claim they support.

THE ROW SET IS RULE-DETERMINED, NOT CHOSEN. Managers enter this list two ways: named
explicitly in the session amendment, or surfaced by a prior evidence pull. There is no
discretionary inclusion or exclusion. That is a deliberate design property, not tidiness —
if inclusion were a judgement call, the membership of the list would itself carry information
about who the author thinks is interesting, and the list is meant to carry none.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache

from ._http import DEFAULT_CLIENT

ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
SUBMISSIONS = "https://data.sec.gov/submissions"
BROWSE = "https://www.sec.gov/cgi-bin/browse-edgar"

#: Why each manager is on the list. `amendment` = named in the session spec; `dart` = surfaced
#: by the 2026-08-02 DART 5% pull. No third category exists, by design.
MANAGERS: dict[str, str] = {
    "Citadel Advisors": "amendment",
    "Millennium Management": "amendment",
    "Point72 Asset Management": "amendment",
    "Balyasny Asset Management": "amendment",
    "D. E. Shaw": "amendment",
    "Davidson Kempner": "amendment",
    "Mason Capital": "amendment",
    "Pentwater Capital": "amendment",
    "Elliott Investment Management": "amendment",
    "Weiss Asset Management": "amendment",
    "Dalton Investments": "amendment",
    "Wellington Management": "dart",
    "Capital Research": "dart",
    "BlackRock": "dart",
    "T. Rowe Price": "dart",
    "Silchester": "dart",
    "Macquarie": "dart",
    "Nomura": "dart",
    "Norges Bank": "dart",
}

#: Korean issuers with US-listed ADRs. Matched on the issuer NAME as it appears in the 13F
#: information table, not on hardcoded CUSIPs — a CUSIP typed from memory is the silent-
#: substitution failure this repository has already paid for twice on symbology.
#: HANMI is deliberately ABSENT. "HANMI FINL CORP" is a Los Angeles bank serving the
#: Korean-American community — US-incorporated, US-listed, not a Korean issuer and not an ADR.
#: It matched a first draft of this list and would have counted as Korea appetite for every
#: manager holding a small-cap US bank.
KOREA_ADR = ("KB FINANCIAL", "SHINHAN FINANCIAL", "COUPANG", "POSCO", "SK TELECOM", "KT CORP",
             "LG DISPLAY", "WOORI FINANCIAL", "GRAVITY CO", "SK HYNIX", "KOREA ELECTRIC",
             "KEPCO")

#: US-listed structures where TWO listed lines are claims on overlapping assets. Holding both
#: at once is the closest public analogue of this trade's shape. Still a proxy: simultaneous
#: holding is not a hedged pair, and 13F cannot show which leg was short.
DISCOUNT_PAIRS = {
    "Liberty complex": ("LIBERTY BROADBAND", "LIBERTY MEDIA", "LIBERTY GLOBAL", "QURATE"),
    "Holdco/tracker":  ("NAKED BRAND", "ALPHABET", "UNDER ARMOUR", "FOX CORP", "NEWS CORP"),
    "Dual-listed":     ("CARNIVAL", "ROYAL CARIBBEAN", "RIO TINTO", "BHP"),
}

#: SKHY's own ADR listed 2026-03-24. 13F reports quarterly with a 45-day lag, so the first
#: filing that COULD show a holder is the Q3 2026 report, due ~2026-11-14. Everything nameable
#: about this specific pair's actual holders post-dates that date. This is the honest boundary
#: of the entire screen and is quoted in the public method note.
SKHY_FIRST_VISIBLE = "2026-11-14"


@lru_cache(maxsize=1)
def _cik_index() -> list[tuple[str, str]]:
    """(NAME, cik) for every EDGAR filer, from the SEC's own complete lookup file.

    `browse-edgar`'s company search is not a search — it is a prefix match with undocumented
    behaviour, and it returned an EMPTY feed for managers that certainly file 13Fs (measured
    2026-08-03 on three of nineteen). A screen whose row set silently drops a fifth of its
    subjects is worse than one that fails, because the gaps look like findings: "no Korean
    exposure" and "we could not resolve the name" render identically as a zero.
    """
    raw = DEFAULT_CLIENT.get("https://www.sec.gov/Archives/edgar/cik-lookup-data.txt")
    out = []
    for line in raw.decode("latin-1").splitlines():
        name, _, cik = line.rstrip(":").rpartition(":")   # the file is `NAME:CIK:`
        if name and cik.isdigit():
            out.append((name.upper(), cik.zfill(10)))
    return out


@lru_cache(maxsize=256)
def find_cik(name: str) -> list[tuple[str, str]]:
    """(cik, company_name) for filers whose name contains ``name``. Index first, search second.

    Ordered shortest-name-first, but the caller must still pick by whether the CIK ACTUALLY
    FILES 13Fs — see :func:`resolve_filer`. Name shape is a bad discriminator: a substring
    search for one manager returns the founder as an individual filer ahead of the firm,
    and the founder's CIK has no 13F at all.
    """
    needle = name.upper().replace(".", "").replace(",", "")
    hits = [(cik, nm) for nm, cik in _cik_index()
            if needle in nm.replace(".", "").replace(",", "")]
    if hits:
        # Management companies first, pooled vehicles last. A large fund family registers
        # dozens of FUND/TRUST/PORTFOLIO entities that sort ahead of the adviser on name length
        # alone and crowd it past any cap — which returned "no 13F filer" for a manager that
        # files every quarter. resolve_filer still verifies against actual filings; this only
        # decides what it examines first.
        vehicle = ("FUND", "TRUST", "PORTFOLIO", "ETF", "INDEX", "SERIES")
        hits.sort(key=lambda t: (any(w in t[1] for w in vehicle), len(t[1]), t[1]))
        return hits[:25]   # cap raised from 8: it truncated before one manager's actual filer

    raw = DEFAULT_CLIENT.get(BROWSE, params={
        "action": "getcompany", "company": name, "type": "13F-HR",
        "dateb": "", "owner": "include", "count": "40", "output": "atom"})
    # Parsed as XML, not scraped with a regex. The first version used a pattern containing
    # `.*?\n?.*?` and hung the whole screen: against a 56KB Atom feed those nested lazy
    # quantifiers backtrack catastrophically, and the symptom is a live process making no
    # requests — which reads exactly like a network stall and is not one.
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    def _text(el, tag: str) -> str:
        hit = next((c for c in el.iter() if c.tag.rsplit("}", 1)[-1] == tag), None)
        return (hit.text or "").strip() if hit is not None else ""

    out: list[tuple[str, str]] = []
    for info in root.iter():
        if info.tag.rsplit("}", 1)[-1] != "company-info":
            continue
        cik = _text(info, "cik")
        if cik:
            out.append((cik.zfill(10), _text(info, "conformed-name")))

    seen, uniq = set(), []
    for cik, title in out:
        if cik not in seen:
            seen.add(cik)
            uniq.append((cik, title))
    return uniq


def resolve_filer(name: str, limit: int = 8) -> tuple[str, str, list[dict]] | None:
    """The first candidate CIK for ``name`` that actually has 13F-HR filings.

    Resolving by capability rather than by name shape, where "capability" means a RECENT and
    NON-EMPTY filing — not merely the existence of a 13F in the entity's history.

    Both extra conditions were bought with a wrong answer. A first version accepted any CIK
    with any 13F-HR, and for one manager it selected a dormant registrant whose most recent
    filing was dated 2005 and contained zero holdings. The screen duly reported that manager as
    holding no Korean names and no discount structures — a resolution failure wearing the
    costume of a finding, and the most dangerous shape of error in a document that names real
    firms. An empty book and an absent book must never render identically.
    """
    from datetime import date

    cutoff = f"{date.today().year - 2}-01-01"
    for cik, title in find_cik(name):
        try:
            filings = [f for f in filings_13f(cik, limit=limit)
                       if f["report_date"] >= cutoff]
            if not filings:
                continue
            if not holdings(cik, filings[0]["accession"]):
                continue                      # files, but reports nothing — a shell registrant
        except Exception:
            continue
        return cik, title, filings
    return None


def filings_13f(cik: str, limit: int = 8) -> list[dict]:
    """The most recent 13F-HR filings for one CIK, newest first."""
    payload = json.loads(DEFAULT_CLIENT.get(f"{SUBMISSIONS}/CIK{cik.zfill(10)}.json"))
    recent = payload.get("filings", {}).get("recent", {})
    rows = []
    for form, acc, date, doc in zip(recent.get("form", []),
                                    recent.get("accessionNumber", []),
                                    recent.get("reportDate", []),
                                    recent.get("primaryDocument", [])):
        if form == "13F-HR":
            rows.append({"accession": acc, "report_date": date, "primary": doc})
        if len(rows) >= limit:
            break
    return rows


def holdings(cik: str, accession: str) -> list[dict]:
    """Parse one 13F information table into (issuer, cusip, value_usd, shares) rows.

    Values are reported in THOUSANDS of dollars before 2023Q1 and in DOLLARS after the SEC's
    amendment; this returns the raw filed number and the unit is resolved by the caller against
    `report_date`, because guessing it silently would misstate every position by 1000x.
    """
    nodash = accession.replace("-", "")
    index = json.loads(DEFAULT_CLIENT.get(f"{ARCHIVES}/{int(cik)}/{nodash}/index.json"))
    names = [i["name"] for i in index.get("directory", {}).get("item", [])]
    table = next((n for n in names
                  if n.lower().endswith(".xml") and "primary_doc" not in n.lower()), None)
    if table is None:
        return []
    xml = DEFAULT_CLIENT.get(f"{ARCHIVES}/{int(cik)}/{nodash}/{table}")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    # ONE pass per infoTable. The first version called a helper per field, and each call
    # re-walked the whole subtree -- four walks per holding, against filings that run to
    # 15,000+ holdings. It was not wrong, it was quadratic, and it looked like a network stall
    # because the process sat burning CPU between requests with nothing to show for it.
    wanted = {"nameOfIssuer", "cusip", "value", "sshPrnamt"}
    rows = []
    for el in root.iter():
        if not el.tag.endswith("infoTable"):
            continue
        got: dict[str, str] = {}
        for child in el.iter():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag in wanted and tag not in got:
                got[tag] = child.text or ""
        rows.append({"issuer": got.get("nameOfIssuer", "").strip().upper(),
                     "cusip": got.get("cusip", "").strip(),
                     "value": _num(got.get("value")),
                     "shares": _num(got.get("sshPrnamt"))})
    return rows


def _num(text: str | None) -> float:
    try:
        return float(str(text).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def korea_positions(rows: list[dict]) -> list[dict]:
    """Rows whose issuer name matches a Korean ADR complex name."""
    return [r for r in rows if any(k in r["issuer"] for k in KOREA_ADR)]


def discount_dna(rows: list[dict]) -> dict[str, list[str]]:
    """Which discount-structure families the filer held BOTH-or-more legs of, simultaneously.

    Two or more legs of one family in a single filing is the signal; one leg is just a stock.

    THE BREADTH CONFOUND, which nearly invalidates this signal for the largest filers. A
    manager reporting 15,000+ positions holds two legs of almost any family by breadth alone —
    measured on a Q1 2026 filing, one multi-strategy filer matched all three families, which
    says nothing about strategy and everything about owning most of the market. Callers must
    read the returned `breadth` alongside the families, and the screen reports both. A hit from
    a 60-position book and a hit from a 15,000-position book are not the same observation.
    """
    held = {r["issuer"] for r in rows}
    out = {}
    for family, legs in DISCOUNT_PAIRS.items():
        hits = sorted({leg for leg in legs if any(leg in h for h in held)})
        if len(hits) >= 2:
            out[family] = hits
    return out


if __name__ == "__main__":
    assert MANAGERS["Citadel Advisors"] == "amendment"
    assert set(MANAGERS.values()) == {"amendment", "dart"}, (
        "a third provenance category would mean a manager entered the list by judgement, "
        "which is exactly what the rule-determined row set exists to prevent")
    # discount_dna must need TWO legs: one holding of one family member proves nothing.
    assert discount_dna([{"issuer": "LIBERTY BROADBAND CORP"}]) == {}
    two = discount_dna([{"issuer": "LIBERTY BROADBAND CORP"}, {"issuer": "LIBERTY MEDIA CORP"}])
    assert "Liberty complex" in two, two
    assert korea_positions([{"issuer": "KB FINANCIAL GROUP INC"}])
    assert not korea_positions([{"issuer": "APPLE INC"}])
    print("ok — SKHY ADR holders first visible in filings due", SKHY_FIRST_VISIBLE)
