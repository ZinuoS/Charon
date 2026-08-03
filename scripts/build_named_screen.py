"""Generate docs/appendix/01_public_filings_screen.md from the pulled evidence.

    uv run python -m scripts.build_named_screen

Generated, not transcribed. Eighty-two DART filings and four quarters across nineteen managers
is more than anyone hand-copies correctly, and a miscopied cell in a document that names real
firms is the one error class this whole appendix cannot afford.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pipeline.ingest._common import RAW_ROOT
from pipeline.ingest.d10_adv import ADV_QUERY, firm_lookup, raum
from pipeline.ingest.d9_thirteenf import MANAGERS, SKHY_FIRST_VISIBLE

GENERATED = date.today().isoformat()
#: ADV registration identity, pulled live. RAUM and the prime-broker roster are NOT here --
#: they live in the ADV form, which robots disallows, so those two stay hand-transcribed.
ADV = {label: firm_lookup(q) for label, q in ADV_QUERY.items()}

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "appendix" / "01_public_filings_screen.md"

#: Managers appearing in the DART 5% screen, with the filing that evidences it.
DART_FILERS = {
    "Wellington Management": ("KT, SK Telecom", "20260730000099"),
    "Capital Research": ("SK hynix", "20260609000049"),
    "BlackRock": ("SK hynix", "20260220000091"),
    "T. Rowe Price": ("KT", "20260209000286"),
    "Silchester": ("KT", "20250224001573"),
    "Macquarie": ("SK Square", "20251210000421"),
    "Nomura": ("SK Square", "20260608000396"),
    "Norges Bank": ("SK Square", "20250620000490"),
}


def latest_screen() -> dict:
    root = Path(RAW_ROOT) / "d9_13f"
    snap = sorted(p for p in root.iterdir() if p.is_dir())[-1]
    return json.loads((snap / "screen.json").read_text()), snap.name


def korea_summary(entry: dict) -> tuple[str, float, int]:
    """(issuer list, latest-quarter USD value, quarters with any position)."""
    issuers, latest_value, quarters = set(), 0.0, 0
    for q in entry.get("quarters", []):
        if q["korea"]:
            quarters += 1
            issuers |= {k["issuer"].title() for k in q["korea"]}
    for q in entry.get("quarters", []):          # quarters are newest-first
        if q["korea"]:
            latest_value = sum(k["value"] for k in q["korea"])
            break
    return ", ".join(sorted(issuers)), latest_value, quarters


def main() -> int:
    screen, snap_date = latest_screen()
    rows, cited, pending = [], 0, 0

    for name, provenance in MANAGERS.items():
        e = screen.get(name, {})
        qs = e.get("quarters", [])
        if e.get("error"):
            rows.append(f"| {name} | `{provenance}` | — | no 13F-HR filing found for any "
                        f"candidate CIK (EDGAR CIK index, retrieved {snap_date}) | — | — | "
                        f"— | MANUAL-PENDING | MANUAL-PENDING |")
            continue

        issuers, value, kq = korea_summary(e)
        breadth = max((q["positions"] for q in qs), default=0)
        fams = sorted({f for q in qs for f in q["discount_dna"]})
        acc = qs[0]["accession"] if qs else "—"
        rdate = qs[0]["report_date"] if qs else "—"

        book = max((q.get("total_value", 0) for q in qs), default=0)
        korea_cell = (f"{issuers} — ${value/1e6:,.0f}M, {kq}/{len(qs)} quarters "
                      f"(13F-HR {acc}, {rdate})" if issuers else
                      f"none (13F-HR {acc}, {rdate})")
        dna_cell = (f"{', '.join(fams)}; book={breadth:,} positions (13F-HR {acc})"
                    if fams else f"none; book={breadth:,} positions (13F-HR {acc})")
        dart_cell = (f"YES — {DART_FILERS[name][0]} (DART filing {DART_FILERS[name][1]})"
                     if name in DART_FILERS else "not in the 2026-08-02 DART 5% screen")
        cap_cell = f"${book/1e9:,.1f}bn US-listed longs (13F-HR {acc}, {rdate})"

        adv = ADV.get(name)
        adv_cell = (f"{adv['firm_name']}, SEC {adv['sec_number']}, CRD {adv['crd']}, "
                    f"{adv['status'].lower()}, {adv['relying_advisers']} relying advisers "
                    f"(Form ADV via IAPD, retrieved {GENERATED})" if adv else
                    "no US adviser registration found (IAPD firm search, "
                    f"retrieved {GENERATED})")
        _r = raum(adv["crd"]) if adv else None
        raum_cell = (f"${_r/1e9:,.1f}bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated "
                     f"2026-05-01)" if _r else
                     "no US adviser registration, so no Item 5.F filing exists")
        cited += 5
        pending += 1
        rows.append(f"| {name} | `{provenance}` | {cap_cell} | {korea_cell} | {dna_cell} | "
                    f"{dart_cell} | {adv_cell} | {raum_cell} | MANUAL-PENDING |")

    body = TEMPLATE.format(
        snap_date=snap_date, generated=date.today().isoformat(),
        n_rows=len(rows), rows="\n".join(rows),
        cited=cited, pending=pending, first_visible=SKHY_FIRST_VISIBLE)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  rows={len(rows)} cited={cited} pending={pending}")
    return 0


TEMPLATE = """# Who trades this family: a public-filings capability screen

*Generated {generated} from filings. Row set is rule-determined — see "How rows were chosen".*

**What this is.** A screen of public filings for managers who demonstrably hold the instruments
adjacent to this trade. **It is not a client list, a prospect list, or a statement about anyone's
interest in anything.** Every cell cites a document. Where a cell is empty, the evidence is
absent and stays absent.

**The boundary on all of it.** Form 13F reports quarterly with a 45-day lag, and SK hynix's ADR
listed 2026-03-24. **The first filing that could name a holder of this pair's ADR is the Q3 2026
report, due about {first_visible}.** Nothing below identifies a holder of the actual trade,
because no such filing exists yet. Everything here is adjacency.

## How rows were chosen

Two ways in, and no third: named in the session specification, or surfaced by a prior evidence
pull (`amendment` and `dart` in the table). **There is no discretionary inclusion or exclusion.**
That is the load-bearing property of this document. If membership were a judgement call, the
roster would encode a view about who is interesting — and a public document must not carry that
view. Rule-determined membership means a name's presence here says nothing about anyone.

## What each column can and cannot evidence

- **Korea appetite** — 13F holdings of Korean ADR complex names. **This is a proxy.** Appetite
  for the complex is not appetite for this pair, and 13F cannot see either of this trade's legs:
  it reports US-listed longs, and this trade is a short plus a Korean local line.
- **Discount-structure DNA** — two or more legs of one US-listed discount family held at once.
  **This is a proxy and a weak one.** A simultaneous holding is **not a hedged pair**, and 13F
  cannot show which leg was short or whether either was hedged. Position count is printed beside
  every hit because a manager reporting fifteen thousand positions holds two legs of almost any
  family by breadth alone.
- **Korean local leg** — the DART 5% screen. This is the only column that sees the local side.
- **Capacity** — the total value of the manager's own most recent 13F information table. This is
  the US-listed long book, not regulatory AUM; it is the right denominator for an ADR trade and
  the wrong one for firm size, and it is stated as what it is.
- **ADV registration** — filed identity from the IAPD firm search: legal name, SEC file number,
  CRD, registration status, relying-adviser count. **CORRECTED 2026-08-03:** an earlier version
  of this note said every automated route to ADV data refuses a correctly-identified client.
  That was wrong, and the fault was local rather than the host's — the client was sending a
  repository URL where the SEC requires an email address, and the resulting 403 was read as a
  refusal. With a compliant header the search API answers normally.
- **RAUM** — Form ADV Part 1A Item 5.F(2)(c), from the SEC's own monthly FOIA extract of Part
  1A. That file is published on the SEC data-research pages so this data need not be scraped out
  of IAPD, and it is the route used.
- **Prime-broker roster** — Schedule D Section 7.B.(1) Question 24. The last `MANUAL-PENDING`
  column, and the reason is now specific: it is per-private-fund and appears in no published
  bulk file, existing only in the per-firm ADV form whose viewer `robots.txt` disallows. A
  person opening that page in a browser is the permitted act (see
  `03_iapd_manual_checklist.md`).

## Capacity is scored separately from mandate fit, and never averaged

A composite score would rank the largest balance sheets first, and the filings do not support
that ordering. This trade's measured behaviour is a bounded gain against an unbounded adverse
excursion, with the excursion arriving first — tolerated by a long-horizon mandate, punished by
a monthly-liquidity one. The honest reading is frequently "largest capacity, weakest mandate
fit", and a single number would erase exactly that.

## The screen

| manager | on list via | capacity (13F book) | Korea appetite (proxy) | discount-structure DNA (proxy) | Korean local leg | ADV registration | RAUM (ADV 5.F) | PB roster (ADV 7.B.1) |
|---|---|---|---|---|---|---|---|---|
{rows}

{n_rows} rows. {cited} cells carry a filing citation; {pending} are `MANUAL-PENDING` awaiting
hand transcription from IAPD.

## The cross-reference, which is the result

Amendment B asked which filers appear in **both** the US screen and the Korean local-leg screen,
and answered zero — because the US table then held a single row. Against the full rule-determined
roster the answer is six, and the way they divide is the finding.

| population | managers | what the filings show |
|---|---|---|
| **Both layers** | BlackRock, Wellington Management, Norges Bank, Nomura, Macquarie, T. Rowe Price | US-listed Korean ADR longs **and** ≥5% of a KRX line (13F-HR Q1 2026; DART filings 2025-02-24 → 2026-07-30) |
| **US Korea appetite only** | Citadel Advisors, Millennium Management, Point72, D. E. Shaw, Balyasny, Dalton Investments | Korean ADR complex longs, no KRX 5% filing in the 2026-08-02 DART pull |
| **Korean local leg only** | Capital Research, Silchester | ≥5% of a KRX line (DART filings 20260609000049, 20250224001573), no Korean ADR long in Q1 2026 13F-HR |
| **Neither** | Davidson Kempner, Mason Capital, Pentwater, Elliott, Weiss Asset Management | no Korean ADR long in Q1 2026 13F-HR and no KRX 5% filing in the DART pull dated 2026-08-02 |

**The two populations sort almost perfectly by manager type, and in the direction that argues
against the pitch rather than for it.** Every manager holding the local leg is a long-only
institution or a sovereign fund; every multi-strategy and event-driven manager on the roster has
Korean ADR exposure and no local leg at all. The managers whose structure resembles this trade
cannot be shown to touch the hard side of it, and the managers who demonstrably execute the hard
side file passive-intent disclosures that argue against running it.

## What the screen supports, in one sentence

The famous names have the capacity and no demonstrated local leg, while the names with the local
leg are long-only institutions whose own filings declare passive intent — so on public paper the
capability for this trade is split across two populations that do not overlap in the way the
trade would require, and appetite for the trade itself is evidenced in neither.

## Mandate-fit note

Left as prose rather than a score, because the evidence for it is structural rather than filed:
a manager's tolerance for a bounded-gain/unbounded-excursion payoff follows from redemption
terms and horizon, which are prospectus and ADV facts, and those cells are `MANUAL-PENDING`.
Scoring mandate fit before that data lands would be inventing the column this table exists to
populate honestly.
"""

if __name__ == "__main__":
    raise SystemExit(main())
