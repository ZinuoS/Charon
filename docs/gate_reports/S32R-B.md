# Gate report — Session 32R, Amendment B (DART as a third layer)

Date: 2026-08-03. **Counts only. No filer is named in this file, by rule.**

## Block 0 — key handling and audit coverage

| check | result |
|---|---|
| `probe()` before any request | `key_present: true, usable: true, status: 000` |
| key written/echoed/modified by agent this session | **no** — installed by hand by the author |
| DART key present anywhere in scratchpad | **no** |
| DART key present in any tracked or staged file | **no** |
| leak audit blocking findings | **0** |

**Three audit gaps were found and closed BEFORE the pull ran**, which was the point of
checking first:

1. **Notebooks were skipped wholesale** (`.ipynb` in `SKIP_SUFFIX`). They are tracked, they
   carry executed output, and this project's publishing model is that they show real results —
   so a key printed into an output cell would have shipped past a clean audit. Now scanned,
   with base64 image payloads stripped so the original false-positive problem stays solved.
2. **`crtfc_key=` was not matched.** The key-material pattern required a literal `api` before
   `key`. DART's parameter is `crtfc_key`, so a keyed request URL in a pull log or notebook
   output would have passed clean. Widened to any `*key=`/`*token=`/`*secret=` parameter.
3. **No bare-40-hex pattern.** Only 32-hex (FRED) and the EODHD shape were covered; a bare
   OpenDART key matched nothing.

A first attempt at (2) was too loose and produced **three false blocking hits** on
`key = os.environ.get(...)` — the variable name, never a value. Tightened to require ≥16 chars
and at least one digit in the value. This mattered enough to redo: an audit that cries wolf is
one the operator learns to wave through, and this repository already carries that lesson about
a stale checklist item.

**Scratchpad coverage — the honest answer is that the audit does not and structurally cannot
cover it.** The audit enumerates through `git ls-files`; the scratchpad lives outside the repo
tree and is therefore unreachable by it. The real guarantee is different in kind: scratchpad
contents cannot be committed *because* they are outside the repository. That protects the repo
and not the disk — which is exactly how **a backup of `.env` containing live FRED and EODHD
keys** came to be sitting there, created by an agent two turns earlier. Found and securely
destroyed this session. The DART key was never in it.

## Terms

| source | verdict | basis |
|---|---|---|
| **OpenDART `majorstock`** | **PERMITTED** | Automated collection nowhere prohibited; Art. 10(6) restricts only excessive access. Art. 16(1) reserves copyright, so **redistribution is not granted** — raw payloads stay uncommitted, already enforced by `.gitignore:8` and verified with `git check-ignore` on the actual files |
| **KRX short balances** | **REFUSAL** | Art. 10(2) prohibits automated collection outright; Art. 12(2) bars copying without permission. The sanctioned Open API **has no short-selling endpoint** — verified against the full service list in a prior session. Both already recorded at `docs/data_sources.md` §0 |

The KRX refusal is on terms, not on difficulty, and it was already settled — it was not
re-litigated or re-probed this session.

## The pull

| issuer | filings | window |
|---|---|---|
| 000660 | 10 | 2024-08-05 → 2026-06-09 |
| 402340 | 11 | 2024-08-05 → 2026-06-08 |
| 030200 | 16 | 2024-08-27 → 2026-07-30 |
| 017670 | 5 | 2025-01-03 → 2026-05-13 |
| 005930 | 40 | 2024-10-25 → 2026-07-31 |
| **total** | **82** | |

- Distinct reporters: **10**. Foreign managers after excluding the domestic pension and the
  strategic affiliate: **9**.
- Foreign managers appearing on more than one issuer: **1**.
- Filings whose stated reason cites depositary receipts: **6**, from **1** reporter, falling
  entirely on the two consent-constrained pairs.
- Reporters populating the contract (derivative-exposure) column: **1** — a strategic
  affiliate, in 40 consecutive filings. **Foreign managers doing so: 0.**

**Cross-reference against the US fit table: 0 hits.** A real zero, not a pending lookup. The
two layers are disjoint by regime construction — a filer visible in both would need a
13F-scale US-listed long *and* ≥5% of a KRX line. The capability inference the cross-reference
was meant to support is therefore unavailable from the sources pulled, and the booking-chain
column stays empty pending Form ADV Schedule D.

**Request budget.** ~20 DART requests total (one corpCode index, cached thereafter, plus one
`majorstock` call per issuer across three runs during development). Well inside the daily cap;
no `020` throttle response was seen at any point.

## Repo-side changes

- `all_series()` omitted two collections, so three pairs' legs were unreachable via
  `series_by_id` and exempt from every ingest-contract and FX-convention invariant. Fixed, with
  a test that asserts reachability **from PAIRS** rather than from the same incomplete sum the
  old tests iterated.
- `usdphp_spot_daily` had no declared FX convention — no direction guard had ever run on that
  pair's FX leg. Declared, and its units string normalised to the canonical form.
- G34R gains two criterion rows reachable only through the Korean regime, and its footnote now
  carries the contract-column result.
- `THREE_LAYER_METHOD` states the segmentation as method, with no names.

## Standing gates

| gate | state |
|---|---|
| gitignore verified **before** the first named row | yes — `git check-ignore` on the sheet path |
| named rows in any tracked file | **none** — grep clean |
| suite | pass |
| push | **awaiting the author's go-word** |
| re-fetch verification | to run at push |
