# Deviations register

README §8 requires that any departure from doctrine carry a dated justification. One
entry per deviation, newest last. An undocumented deviation is a defect.

Each entry states: **what** the doctrine says, **what was done instead**, **why**, the
**blast radius**, and the **reversal path**.

---

## 2026-07-28 — D1/D6 transport: Yahoo chart API instead of the `yfinance` wrapper

**Doctrine / instruction.** Session 1 was authorised to use `yfinance` as the session-1
provider for daily bars, recording the provider in the pull log so it could be swapped
later.

**What was done instead.** `pipeline/ingest/_yahoo.py` calls Yahoo Finance's public
chart endpoint (`query1.finance.yahoo.com/v8/finance/chart/{symbol}`) directly via
`requests`, rather than through `yfinance`.

**Why.** `yfinance==0.2.51` fails on *every* symbol in this environment, including
control symbols like `AAPL`, with `Expecting value: line 1 column 1 (char 0)` — its
cookie/crumb handshake receives a non-JSON response and it then reports each ticker as
"possibly delisted; no price data found". The same symbols return complete, correct
data over plain `requests` against the endpoint `yfinance` itself wraps. The failure is
in the wrapper's auth preamble, not in data availability.

**Why this is not a silent substitution.** Task 3 forbids substituting a source rather
than reporting it. This is not a change of source: the bytes originate from the same
Yahoo Finance service, and `provider` in the pull log remains `yahoo_finance`, with
`transport: chart_api_v8` recording the distinction. Access is unauthenticated, uses
the same public endpoint the finance website calls, and involves no credential, paywall
or scraping of a page whose terms forbid it. The endpoint is nonetheless an
undocumented internal API and could change without notice — see the open question in
`docs/gate_reports/S1.md`.

**Blast radius.** All D1 and D6 daily bars. `yfinance` remains a pinned dependency and
is currently unused by pipeline code.

**Reversal path.** `fetch_daily()` in `pipeline/ingest/_yahoo.py` is the entire
migration surface — one function, called only by `pipeline/ingest/_puller.py`. Swapping
back to `yfinance` (or forward to a paid vendor) means reimplementing that one function
to return the same `(frame, url, params)` triple.

**Author decision required.** Whether to keep this transport, revert to `yfinance` on a
different pin, or move D1/D6 to a contractual data source before S3.

---

## 2026-07-28 — Provider throttle added to ingestion

**Doctrine.** Ingestion is a separate, logged, network-permitted stage; determinism is
required of *analysis*, not of the provider's availability.

**What was done.** `_yahoo.py` enforces a minimum 2.5s spacing between requests and
treats HTTP 429 as a hard backoff (20s, 40s, …) distinct from an ordinary retry.

**Why.** Yahoo rate-limits an unauthenticated client that fans out across ~14 symbols
in quick succession, and the limit persists for several minutes once tripped. Without
pacing, a full D6 panel pull fails partway and leaves the raw tree half-populated.

**Blast radius.** Wall-clock duration of ingestion only. No effect on stored bytes,
checksums, or any analysis result.

**Note.** Being rate-limited is recorded in the pull log with `status: "failed"` rather
than being retried into silence, so a partial panel is always visible as a partial
panel.
