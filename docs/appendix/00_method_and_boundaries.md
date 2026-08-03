# The three-layer screen: method, and what each layer cannot see

## Why a named screen publishes in a public research repository

This analysis rests entirely on public filings, so it publishes as research. Until 2026-08-03 it
was excluded from version control instead. The exclusion was a blunt instrument: it made the
question unaskable rather than answerable, and an unaskable question produces no discipline at
all. What replaces it is craft, enforced by tests in `tests/test_named_screen_discipline.py`
that fail the build rather than by an intention to be careful.

**Citation or silence.** Every named claim cites a specific document. Claims are filing-shaped —
"filings show X held Y over period Z" — never assertions about what a firm thinks or wants.

**The row set is rule-determined.** A manager enters one of two ways: named in the session
specification, or surfaced by an evidence pull. There is no discretionary inclusion. This is the
least obvious of the three rules and the most load-bearing. If membership were a judgement call,
the roster itself would encode a view about who is interesting — and that view is precisely what
a public document must not carry, independent of how carefully each sentence is worded. A
rule-determined roster means a name's presence says nothing about anyone's interest in anything.

**Proxies are labelled where they are used.** Appetite for the Korean ADR complex is not this
trade. Holding two legs of a US-listed discount structure is not a hedged pair. Both are the
nearest public analogue of a shape that leaves no public trace, and the substitution is stated
at the point of claim, not in a footnote.

## The honest boundary on everything nameable

Form 13F reports quarterly with a 45-day lag. SK hynix's ADR listed 2026-03-24, so **the first
filing that could name a holder of this pair's ADR is the Q3 2026 report, due about
2026-11-14.** No document in this appendix identifies a holder of the actual trade, because no
such document exists yet. Everything here is adjacency, and the date is the follow-up.

## Three regimes, three populations, three products

| layer | sees | identifies | product implied |
|---|---|---|---|
| **US filings** (13F, 13D/G) | US-listed longs above threshold | balance sheet and appetite for a synthetic pair | the full package — synthetic local leg, ADR borrow, financing |
| **Korean 5% filings** (DART) | the KRX leg, including foreign managers | managers who already carry the local side | thinner: ADR borrow, short-leg financing, margin and monitoring |
| **N-CSR / N-PORT** | the audited book of a registered fund | long-local holders of the discount instrument | not the pair — hedging or financing against a held position |

**The inversion in the middle row is the part that gets read backwards by default.** A capability
screen normally reads as a buyer list: the more capable the manager, the better the prospect.
Here it runs the other way. Evidence that a manager already executes the Korean local leg is
evidence they do not need the largest component of what is being sold. That does not make them
uninteresting; it makes them a different and smaller sale. Read the usual way, this layer would
put the wrong pitch in front of the most sophisticated name on the list.

## Capacity and mandate are scored separately, and never averaged

A composite would rank the largest balance sheets first, and the filings do not support that
ordering. The measured behaviour of this trade is a bounded gain against an unbounded adverse
excursion, with the excursion arriving before the convergence — tolerated by a long-horizon
mandate, punished by a monthly-liquidity one. The honest cell is frequently "largest capacity,
weakest mandate fit", and one number would erase exactly that finding.

**The breadth confound belongs in the same paragraph.** A manager reporting fifteen thousand
positions holds two legs of almost any structure by breadth alone. A discount-structure hit from
such a book carries far less information than the same hit from a sixty-position book, so
position count is printed beside every hit and no hit is read without it.

## What each source refused

- **KRX short balances** — Article 10(2) prohibits automated collection and the sanctioned Open
  API has no short-selling endpoint. Closed, not pending.
- **Form ADV data** — every automated route refuses a correctly-identified client:
  `reports.adviserinfo.sec.gov` and `api.adviserinfo.sec.gov` return 403 on every path including
  their own `robots.txt`, and the adviserinfo host that does answer disallows
  `/IAPD/content/viewform/adv*`. That refusal is the host's and it stands, so those columns are
  transcribed by hand from a browser instead (`03_iapd_manual_checklist.md`).
