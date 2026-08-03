# IAPD manual checklist — the ADV column, filled by hand

**Why this is a checklist and not a puller.** Every automated route to Form ADV data refuses a
correctly-identified client: `reports.adviserinfo.sec.gov` and `api.adviserinfo.sec.gov` return
403 on every path including their own `robots.txt`, and the one adviserinfo host that answers
disallows `/IAPD/content/viewform/adv*` in robots. That refusal is the host's and it stands. A
person reading a public page in a browser is a different act, and the permitted one.

**Three fields per adviser**, 15–20 minutes for the whole list:

1. **RAUM** — Form ADV Part 1A, **Item 5.F(2)(c)**, regulatory assets under management.
2. **Prime broker roster** — **Schedule D, Section 7.B.(1), Question 24**, per private fund.
   Question 25 is the custodian and 26 the administrator; 24 is the booking chain.
3. **Fund structure / redemption terms** — Schedule D 7.B.(1) Questions 11–15 where visible.

Cite transcribed cells as `Form ADV via IAPD, retrieved by hand YYYY-MM-DD`.

Search at <https://adviserinfo.sec.gov/> → Firm → the name below. Some managers file under
several registered entities; transcribe the one whose RAUM matches the advisory business, and
note the entity name you used.

| adviser | on this list because | IAPD | RAUM (5.F) | PB roster (7.B.1 Q24) | structure/redemption |
|---|---|---|---|---|---|
| Citadel Advisors | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Citadel Advisors` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Millennium Management | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Millennium Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Point72 Asset Management | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Point72 Asset Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Balyasny Asset Management | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Balyasny Asset Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| D. E. Shaw | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `D. E. Shaw` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Davidson Kempner | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Davidson Kempner` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Mason Capital | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Mason Capital` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Pentwater Capital | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Pentwater Capital` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Elliott Investment Management | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Elliott Investment Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Weiss Asset Management | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Weiss Asset Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Dalton Investments | amendment | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Dalton Investments` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Wellington Management | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Wellington Management` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Capital Research | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Capital Research` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| BlackRock | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `BlackRock` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| T. Rowe Price | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `T. Rowe Price` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Silchester | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Silchester` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Macquarie | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Macquarie` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Nomura | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Nomura` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |
| Norges Bank | dart | [IAPD search](https://adviserinfo.sec.gov/compilation) → search `Norges Bank` | MANUAL-PENDING | MANUAL-PENDING | MANUAL-PENDING |

**`amendment`** = named explicitly in the session specification. **`dart`** = surfaced by the
2026-08-02 DART 5% pull. There is no third category: no adviser is on this list because
someone thought they looked promising, which is what keeps the membership of the list from
carrying information of its own.
