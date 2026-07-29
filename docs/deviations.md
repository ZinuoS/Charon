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

---

## 2026-07-29 — README edited by an analysis session, on explicit author instruction

**Doctrine.** README §11 reserves README edits to the author; analysis sessions propose,
never ratify.

**What was done.** An analysis session applied eight corrections to README §0, §1, §2, §3,
§4 and §5, on the author's explicit instruction ("proceed, override the flags") after the
corrections had been staged as proposals in `docs/proposed_readme_patch.md` and flagged
twice as blocking a public-facing contradiction.

**Why.** The repository had been made public while the front page still asserted three
facts the repository's own research had corrected: the 2.5% as a conversion quota, TSMC's
12.6% five-year average, and the Eurex night session. §0 also still read "repo stays
private." A public page contradicting its own cited research is a worse defect than any
formatting issue, and the author's instruction was unambiguous.

**Blast radius.** README only. No `calls.yaml`, amendment, freeze class or `approved:` mark
was touched. The prior text is recoverable from git history.

**Author review still owed.** The eight corrections were *proposed* by a session and
*applied* by a session. The author should read the current §0–§5 and confirm the wording is
theirs, since the doctrine's normal safeguard — author authorship of the constitution — was
bypassed here by instruction rather than by process.

---

## 2026-07-29 — Notebook output policy reversed: outputs are now committed

**Prior rule.** Notebooks committed with outputs cleared.

**New rule.** Executed notebooks are committed **with outputs**.

**Why.** The repository is now public and is itself the display medium. A reader landing on
GitHub sees the rendered document; a cleared notebook shows prose and code but no figures
and no results, which defeats the purpose of publishing it.

**Retained guarantee.** `make notebook` still verifies clean offline re-execution, and the
analysis tree still imports no networking library (enforced by test). Committed outputs
must correspond to a fresh run.

**Cost accepted.** Notebook diffs become large and noisy, and repository weight grows
(~1MB per executed notebook). Judged worth it for a public research artifact.


---

## 2026-07-29 — calls.yaml frozen and Amendment 001 committed by an analysis session, on instruction

**Doctrine.** README §11 reserves `calls.yaml`, amendments and freeze classes to the
author, "in person, in the files, by hand." Analysis sessions propose, never ratify.

**What was done.** On the author's explicit instruction ("freeze what we need to freeze"),
an analysis session: applied the H5 threshold, resolution date (2026-10-31) and four-branch
resolution criterion from `preregistration/proposed_h5_values.md` (the author's earlier
option-(a) ruling); set H1–H4 to `freeze_class: X` / `status: exploratory`; set `frozen_at`
and `commit_note`; and wrote `preregistration/amendments/2026-07-29-partitioned-freeze.md`
declaring Class P empty (no prior commit), H5 Class C, H1–H4 Class X.

**Why permissible.** The values are the author's own proposal, and the author instructed
the freeze directly. The minimal-freeze design was pre-specified in
`preregistration/minimal_freeze_checklist.md`.

**Two facts the session could NOT supply, flagged in the amendment for author confirmation:**
1. **The exact release minute** (§1) — a real-world fact not in the retrieved public record;
   stated as "before the 09:00 KST KRX open" (documented) pending the author's precise value.
2. **The signature** — the amendment carries a signature line the author confirms.

**Author review owed.** The threshold *numbers* (0.25% of ceiling, 3pp/5-day, ≥2 episodes)
were drafted by a session and accepted by instruction. If the author's own numbers differ,
they are registered now and can only be changed by a further numbered amendment — so the
author should confirm these are the intended values, promptly, while the ledger is young.

**Blast radius.** `calls.yaml`, the new amendment, and the preregistration test (aligned to
the Class-C-frozen / Class-X-exploratory structure). Prior draft recoverable from git.
