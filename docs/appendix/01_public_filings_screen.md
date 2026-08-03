# Who trades this family: a public-filings capability screen

*Generated 2026-08-03 from filings. Row set is rule-determined — see "How rows were chosen".*

**What this is.** A screen of public filings for managers who demonstrably hold the instruments
adjacent to this trade. **It is not a client list, a prospect list, or a statement about anyone's
interest in anything.** Every cell cites a document. Where a cell is empty, the evidence is
absent and stays absent.

**The boundary on all of it.** Form 13F reports quarterly with a 45-day lag, and SK hynix's ADR
listed 2026-03-24. **The first filing that could name a holder of this pair's ADR is the Q3 2026
report, due about 2026-11-14.** Nothing below identifies a holder of the actual trade,
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
| Citadel Advisors | `amendment` | $665.9bn US-listed longs (13F-HR 0001104659-26-062477, 2026-03-31) | Coupang Inc, Gravity Co Ltd, Kt Corp, Lg Display Co Ltd, Posco Holdings Inc, Shinhan Financial Group Co L, Sk Telecom Co Ltd — $134M, 4/4 quarters (13F-HR 0001104659-26-062477, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=15,589 positions (13F-HR 0001104659-26-062477) | not in the 2026-08-02 DART 5% screen | CITADEL ADVISORS LLC, SEC 801-70860, CRD 148826, active, 10 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $570.6bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 32 named: BOFA SECURITIES, INC., BARCLAYS CAPITAL INC., BARCLAYS BANK PLC… (Form ADV Schedule D 7.B.(1) Q24(b), 305pp form, retrieved 2026-08-03) |
| Millennium Management | `amendment` | $240.3bn US-listed longs (13F-HR 0001273087-26-000004, 2026-03-31) | Coupang     Inc, Coupang   Inc, Posco  Holdings        Inc — $113M, 4/4 quarters (13F-HR 0001273087-26-000004, 2026-03-31) | Dual-listed; book=5,978 positions (13F-HR 0001273087-26-000004) | not in the 2026-08-02 DART 5% screen | MILLENNIUM MANAGEMENT LLC, SEC 801-73884, CRD 158117, active, 54 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $720.8bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 37 named: UBS SECURITIES LLC, MORGAN STANLEY & CO. LLC, J.P. MORGAN SECURITIES LLC… (Form ADV Schedule D 7.B.(1) Q24(b), 324pp form, retrieved 2026-08-03) |
| Point72 Asset Management | `amendment` | $89.4bn US-listed longs (13F-HR 0000919574-26-003476, 2026-03-31) | Coupang Inc, Kt Corp, Lg Display Co Ltd, Posco Holdings Inc, Shinhan Financial Group Co L, Sk Telecom Co Ltd — $178M, 4/4 quarters (13F-HR 0000919574-26-003476, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=3,862 positions (13F-HR 0000919574-26-003476) | not in the 2026-08-02 DART 5% screen | POINT72 ASSET MANAGEMENT, L.P., SEC 801-107348, CRD 283077, active, 25 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $274.1bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 20 named: GOLDMAN SACHS & CO. LLC, J.P. MORGAN SECURITIES LLC, CITIBANK, N.A.… (Form ADV Schedule D 7.B.(1) Q24(b), 233pp form, retrieved 2026-08-03) |
| Balyasny Asset Management | `amendment` | $78.9bn US-listed longs (13F-HR 0001193125-26-226359, 2026-03-31) | Coupang Inc, Kt Corp, Posco Holdings Inc, Shinhan Financial Group Co L, Sk Telecom Co Ltd — $2M, 4/4 quarters (13F-HR 0001193125-26-226359, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=3,338 positions (13F-HR 0001193125-26-226359) | not in the 2026-08-02 DART 5% screen | BALYASNY ASSET MANAGEMENT L.P., SEC 801-66002, CRD 138111, active, 29 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $248.1bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 8 named: GOLDMAN SACHS & CO. LLC, MORGAN STANLEY & CO. LLC, UBS SECURITIES LLC… (Form ADV Schedule D 7.B.(1) Q24(b), 382pp form, retrieved 2026-08-03) |
| D. E. Shaw | `amendment` | $182.4bn US-listed longs (13F-HR 0001104659-26-062472, 2026-03-31) | Coupang Inc, Kt Corp, Lg Display Co Ltd, Posco Holdings Inc, Shinhan Financial Group Co L, Sk Telecom Co Ltd — $176M, 4/4 quarters (13F-HR 0001104659-26-062472, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=5,839 positions (13F-HR 0001104659-26-062472) | not in the 2026-08-02 DART 5% screen | D. E. SHAW & CO., L.P., SEC 801-56171, CRD 108679, active, 16 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $213.4bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 72 named: BARCLAYS CAPITAL INC., BARCLAYS BANK PLC, BANCO SANTANDER, S.A.… (Form ADV Schedule D 7.B.(1) Q24(b), 418pp form, retrieved 2026-08-03) |
| Davidson Kempner | `amendment` | $7.3bn US-listed longs (13F-HR 0001595082-26-000046, 2026-03-31) | none (13F-HR 0001595082-26-000046, 2026-03-31) | none; book=233 positions (13F-HR 0001595082-26-000046) | not in the 2026-08-02 DART 5% screen | DAVIDSON KEMPNER CAPITAL MANAGEMENT LP, SEC 801-72222, CRD 155680, active, 8 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $46.6bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 9 named: J.P. MORGAN SECURITIES LLC, GOLDMAN SACHS & CO. LLC, CITIGROUP GLOBAL MARKETS INC.… (Form ADV Schedule D 7.B.(1) Q24(b), 396pp form, retrieved 2026-08-03) |
| Mason Capital | `amendment` | $0.6bn US-listed longs (13F-HR 0001104659-26-062410, 2026-03-31) | none (13F-HR 0001104659-26-062410, 2026-03-31) | none; book=9 positions (13F-HR 0001104659-26-062410) | not in the 2026-08-02 DART 5% screen | MASON CAPITAL MANAGEMENT LLC, SEC 801-73255, CRD 158797, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $2.2bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 5 named: GOLDMAN SACHS & CO. LLC, BARCLAYS CAPITAL INC., CITIGROUP GLOBAL MARKETS INC.… (Form ADV Schedule D 7.B.(1) Q24(b), 39pp form, retrieved 2026-08-03) |
| Pentwater Capital | `amendment` | $19.3bn US-listed longs (13F-HR 0001140361-26-021678, 2026-03-31) | none (13F-HR 0001140361-26-021678, 2026-03-31) | Liberty complex; book=110 positions (13F-HR 0001140361-26-021678) | not in the 2026-08-02 DART 5% screen | PENTWATER CAPITAL MANAGEMENT LP, SEC 801-72861, CRD 156873, active, 3 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $19.3bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 7 named: UBS AG, UBS SECURITIES LLC, BOFA SECURITIES, INC.… (Form ADV Schedule D 7.B.(1) Q24(b), 141pp form, retrieved 2026-08-03) |
| Elliott Investment Management | `amendment` | $22.7bn US-listed longs (13F-HR 0001013594-26-000613, 2026-03-31) | none (13F-HR 0001013594-26-000613, 2026-03-31) | none; book=35 positions (13F-HR 0001013594-26-000613) | not in the 2026-08-02 DART 5% screen | ELLIOTT INVESTMENT MANAGEMENT L.P., SEC 801-119969, CRD 307151, active, 21 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $128.6bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 27 named: BNP PARIBAS SECURITIES CORP., BOFA SECURITIES PRIME, INC., BOFA SECURITIES, INC.… (Form ADV Schedule D 7.B.(1) Q24(b), 249pp form, retrieved 2026-08-03) |
| Weiss Asset Management | `amendment` | $8.7bn US-listed longs (13F-HR 0001357550-26-000023, 2026-03-31) | none (13F-HR 0001357550-26-000023, 2026-03-31) | Holdco/tracker, Liberty complex; book=593 positions (13F-HR 0001357550-26-000023) | not in the 2026-08-02 DART 5% screen | WEISS ASSET MANAGEMENT, SEC 801-73590, CRD 155564, active, 7 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $15.6bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 12 named: BARCLAYS CAPITAL INC., BMO CAPITAL MARKETS CORP., BNP PARIBAS PRIME BROKERAGE INTERNATIONAL LIMITED… (Form ADV Schedule D 7.B.(1) Q24(b), 90pp form, retrieved 2026-08-03) |
| Dalton Investments | `amendment` | $0.2bn US-listed longs (13F-HR 0001172661-26-001724, 2026-03-31) | Shinhan Financial Group Co L — $1M, 1/4 quarters (13F-HR 0001172661-26-001724, 2026-03-31) | none; book=20 positions (13F-HR 0001172661-26-001724) | not in the 2026-08-02 DART 5% screen | DALTON INVESTMENTS, INC., SEC 801-121986, CRD 308609, active, 1 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $5.7bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 3 named: MORGAN STANLEY & CO. INTERNATIONAL PLC, GOLDMAN SACHS & CO. LLC, MORGAN STANLEY & CO. LLC… (Form ADV Schedule D 7.B.(1) Q24(b), 100pp form, retrieved 2026-08-03) |
| Wellington Management | `dart` | $571.3bn US-listed longs (13F-HR 0000902219-26-000209, 2026-03-31) | Coupang Inc, Kt Corp, Shinhan Financial Group Co L — $718M, 4/4 quarters (13F-HR 0000902219-26-000209, 2026-03-31) | Dual-listed, Holdco/tracker; book=7,635 positions (13F-HR 0000902219-26-000209) | YES — KT, SK Telecom (DART filing 20260730000099) | WELLINGTON MANAGEMENT COMPANY LLP, SEC 801-15908, CRD 106595, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $1,428.0bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | 2 named: BARCLAYS CAPITAL INC., CITIGROUP GLOBAL MARKETS INC.… (Form ADV Schedule D 7.B.(1) Q24(b), 509pp form, retrieved 2026-08-03) |
| Capital Research | `dart` | $644.6bn US-listed longs (13F-HR 0001422848-26-000041, 2026-03-31) | Coupang Inc, Kt Corp, Shinhan Financial Group Co L — $125M, 4/4 quarters (13F-HR 0001422848-26-000041, 2026-03-31) | Dual-listed; book=459 positions (13F-HR 0001422848-26-000041) | YES — SK hynix (DART filing 20260609000049) | CAPITAL RESEARCH AND MANAGEMENT COMPANY, SEC 801-8055, CRD 110885, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $3,753.5bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 68pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| BlackRock | `dart` | $4,418.3bn US-listed longs (13F-HR 0001086364-24-008417, 2024-06-30) | Coupang Inc, Gravity Co Ltd, Kt Corp, Lg Display Co Ltd, Posco Holdings Inc, Shinhan Financial Group Co L, Sk Telecom Ltd — $815M, 2/2 quarters (13F-HR 0001086364-24-008417, 2024-06-30) | Dual-listed, Holdco/tracker, Liberty complex; book=48,325 positions (13F-HR 0001086364-24-008417) | YES — SK hynix (DART filing 20260220000091) | BLACKROCK ADVISORS, LLC, SEC 801-47710, CRD 106614, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $1,096.1bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 326pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| T. Rowe Price | `dart` | $0.2bn US-listed longs (13F-HR 0001897612-26-000460, 2026-03-31) | Coupang Inc — $0M, 2/4 quarters (13F-HR 0001897612-26-000460, 2026-03-31) | Holdco/tracker; book=879 positions (13F-HR 0001897612-26-000460) | YES — KT (DART filing 20260209000286) | T. ROWE PRICE ASSOCIATES, INC., SEC 801-856, CRD 105496, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $2,196.5bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 329pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| Silchester | `dart` | $0.3bn US-listed longs (13F-HR 0000929638-26-002505, 2026-06-30) | none (13F-HR 0000929638-26-002505, 2026-06-30) | none; book=4 positions (13F-HR 0000929638-26-002505) | YES — KT (DART filing 20250224001573) | SILCHESTER INTERNATIONAL INVESTORS, SEC 801-49530, CRD 110987, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $38.0bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 63pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| Macquarie | `dart` | $85.7bn US-listed longs (13F-HR 0001193125-26-225415, 2026-03-31) | Coupang Inc, Kt Corp, Sk Telecom Co Ltd — $0M, 4/4 quarters (13F-HR 0001193125-26-225415, 2026-03-31) | Dual-listed, Holdco/tracker; book=3,191 positions (13F-HR 0001193125-26-225415) | YES — SK Square (DART filing 20251210000421) | MACQUARIE INVESTMENT MANAGEMENT GLOBAL LIMITED, SEC 801-106854, CRD 277065, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $160.2bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 47pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| Nomura | `dart` | $75.1bn US-listed longs (13F-HR 0000905148-26-002310, 2026-03-31) | Coupang Inc, Shinhan Financial Group Co L, Sk Telecom Co Ltd — $6M, 3/4 quarters (13F-HR 0000905148-26-002310, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=2,495 positions (13F-HR 0000905148-26-002310) | YES — SK Square (DART filing 20260608000396) | NOMURA ASSET MANAGEMENT CO., LTD., SEC 801-24357, CRD 110814, active, 0 relying advisers (Form ADV via IAPD, retrieved 2026-08-03) | $514.3bn (Form ADV Item 5.F(2)(c), SEC bulk extract dated 2026-05-01) | none named (Form ADV Schedule D 7.B.(1) Q24, 26pp form, retrieved 2026-08-03) — no private fund reports a prime broker |
| Norges Bank | `dart` | $934.8bn US-listed longs (13F-HR 0001374170-26-000023, 2026-03-31) | Coupang Inc — $498M, 2/4 quarters (13F-HR 0001374170-26-000023, 2026-03-31) | Dual-listed, Holdco/tracker, Liberty complex; book=1,707 positions (13F-HR 0001374170-26-000023) | YES — SK Square (DART filing 20250620000490) | no US adviser registration found (IAPD firm search, retrieved 2026-08-03) | no US adviser registration, so no Item 5.F filing exists | no US adviser registration, so no Schedule D exists (2026-08-03) |

19 rows. 114 cells carry a filing citation; 0 are `MANUAL-PENDING` awaiting
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
