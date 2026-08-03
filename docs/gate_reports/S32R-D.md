# Gate report — Session 32R, Amendment D (fully public, fully named)

Date: 2026-08-03. Amendment D is the baseline; where C and D conflicted, D governed.

## Placement rule lifted

| change | state |
|---|---|
| `docs/client_research/` gitignore carve-out | **removed** |
| `docs/client_research/` contents | migrated to `docs/appendix/`, directory deleted |
| name-grep blocking class | **retired** |
| key material + internal firm names in the leak audit | **untouched, still blocking** |

## What replaced the restriction

`tests/test_named_screen_discipline.py` — five tests, all passing:

1. **Citation-or-silence.** Every line naming a manager carries a document reference on that
   same line. It caught three real violations while this appendix was being written, including a
   negative claim about five named firms with no source for the negative.
2. **No inside knowledge.** No language implying awareness of any manager's interest,
   discussions, or relationship with any desk.
3. **Proxy labelling.** Korea-ADR appetite and discount-structure DNA are labelled as proxies in
   the files that rely on them.
4. **Visibility boundary stated.** The Q3-13F date must appear.
5. **The rules bite.** A meta-test asserting the regexes match what they must and not what they
   must not — because a regex that matches nothing passes every file silently.

**One rule is mine rather than the amendment's, and it is the load-bearing one.** Amendment C
withheld names partly to avoid triangulating a confidence the author holds. D lifts placement
and adds a wording grep — but a grep polices sentences, not selection, and *which names appear
at all* can leak independently of how carefully each is phrased. So the row set is
rule-determined: every manager named in the specification, plus every manager surfaced by a
pull, with no discretionary inclusion or exclusion. Membership therefore carries no information.
This is recorded in the method note as a reason, not merely as a rule.

## The pulls

**13F screen** — 19 managers, 4 quarters each, `data/raw/d9_13f/2026-08-03/`. All 19 resolved.

**Cross-reference, which is the headline.** Amendment B answered this question with zero against
a one-row table. Against the full roster the answer is **six**, and the division is the finding:

| population | count | |
|---|---|---|
| both US Korea longs and KRX 5% filings | 6 | BlackRock, Wellington, Norges Bank, Nomura, Macquarie, T. Rowe Price |
| US Korea appetite only | 6 | Citadel, Millennium, Point72, D. E. Shaw, Balyasny, Dalton |
| Korean local leg only | 2 | Capital Research, Silchester |
| neither | 5 | Davidson Kempner, Mason, Pentwater, Elliott, Weiss |

**The populations sort by manager type, in the direction that argues against the pitch.** Every
manager holding the local leg is long-only or sovereign. Every multi-strategy and event-driven
manager has ADR exposure and no local leg.

**Strongest single piece of filing evidence:** the six DART filings by Wellington Management
Company LLP dated 2025-12-02 to 2026-07-30 — the only filings in either pull that report
movement between local shares and depositary receipts, including one (2026-05-13) reporting a
local sale on-exchange and a DR purchase off-exchange in the same document. It is also the most
easily over-read, and the appendix states in the same paragraph that Korea aggregates DRs with
the underlying into one stake, so this is a dual-format long and not a hedged pair.

**The one-sentence answer about the famous names:** they have the capacity and no demonstrated
local leg, while the names with the local leg are long-only institutions whose filings declare
passive intent — so public paper splits the capability across two populations that do not
overlap the way this trade requires, and evidences appetite for it in neither.

## Table counts

19 rows · **57 cells carry a filing citation** · **38 cells `MANUAL-PENDING`** (RAUM and
prime-broker roster, awaiting hand transcription from IAPD) · mandate fit left as prose because
the evidence for it is in the pending cells, and scoring it first would invent the column.

## Four bugs found, three of which produced false findings

Recorded because in a document naming real firms, a resolution failure and a real zero render
identically — and that is the worst failure mode available here.

1. `find_cik` used a regex with nested lazy quantifiers; on a 56KB Atom feed it backtracked
   catastrophically. The symptom was a live process issuing no requests, which reads as a
   network stall and is not one.
2. `browse-edgar`'s company search returned **empty feeds** for three of nineteen managers who
   file every quarter. Replaced with the SEC's complete CIK index.
3. Resolution accepted any CIK with any 13F and selected a **dormant registrant last filing in
   2005 with zero holdings**; the screen reported that manager as holding no Korean names. Now
   requires a recent, non-empty filing. After the fix that manager shows 31 Korean positions.
4. A fund family's pooled vehicles crowded the adviser past the candidate cap, returning "no 13F
   filer" for a manager that files quarterly. Management companies now sort ahead of vehicles.

Also: `HANMI FINL CORP` is a Los Angeles bank, not a Korean ADR. It matched the first draft of
the Korea list and would have scored Korea appetite for anyone holding a US small-cap bank.

## Access

`SEC_USER_AGENT` is now required and must contain a real email address — measured: a UA naming
the project with a repository URL is refused 403 by `company_tickers.json`, the Archives index
and `efts.sec.gov` alike. There is deliberately no default, because a placeholder address would
satisfy the server and defeat the header's purpose. It is set in `.env` (gitignored) and is
personal data: **it must not be committed.** Verified absent from the staged diff.

## Gates

| gate | state |
|---|---|
| suite | **675 passed, 5 skipped** |
| discipline tests | 5/5 pass |
| leak audit | **0 blocking** across 306 files |
| key material or email in staged diff | **none** |
| push | **awaiting the author's go-word** |
| re-fetch verification | to run at push |
