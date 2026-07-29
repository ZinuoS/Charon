"""Generate notebooks/05_hypothesis_engines.ipynb. uv run python -m scripts.build_notebook_05"""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "05_hypothesis_engines.ipynb"
cells=[]
md=lambda s: cells.append({"cell_type":"markdown","metadata":{},"source":s.strip().splitlines(True)})
code=lambda s: cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.strip().splitlines(True)})

md(r"""
# Hypothesis engines — status, results, and what each can honestly claim

**Notebook 05.** The five research channels (H1–H5), each with its freeze class and what it
has actually produced. **The pre-registration ledger is now frozen** — this notebook reads
its real state below and labels every claim accordingly.
""")
code(r'''
%matplotlib inline
import sys, subprocess, yaml, pathlib
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
calls = yaml.safe_load((ROOT/"preregistration"/"calls.yaml").read_text())
print("LEDGER FROZEN at", calls.get("frozen_at"))
for h in ("h1_term_structure","h2_index_access","h3_letf_loop","h4_vol_decomposition","h5_quota_ledger"):
    print(f"  {h:22s} freeze_class={calls[h].get('freeze_class')}  status={calls[h]['status']}")
print("\\nClass C = registered (H5). Class X = exploratory (H1-H4). Class P = empty (no prior commit).")
from pipeline.viz import theme; theme.apply()
_pi = __import__("pipeline.measurement.premium", fromlist=["build_all_variants"]).build_all_variants("skhy")[0].series
theme.sparkline_header(_pi, highlight=("2026-07-15","2026-07-28"), label="SKHY premium  ·  this notebook: the engines that watch it");
''')

md(r"""
## H5 — barrier-state monitor (Class C, **registered**)

The one pre-registered call. Its observable, live, with the scope limit on every output.
""")
code(r'''
from hypotheses.h5_quota_ledger.monitor import status_report
print(status_report())
''')

md(r"""
The publication check is the substantive line: the capped programme's silence since
2026-07-15 is disambiguated by the control printing through 07-28 — so the barrier is
**sealed by observation, not by a dead feed.** The registered criterion carries an
INDETERMINATE branch for the case where headroom moves but no deposit clears, because
measured headroom is not the operative consent gate.

## H4 — realized variance decomposition (Class X, exploratory)

Exact log identity; the covariance terms reported, not folded away. The contrast between
pairs is the finding, not the SKHY level.
""")
code(r'''
from hypotheses.h4_vol_decomposition.realized import compare_pairs
vd = compare_pairs()
vd[["pair","n","ann_vol_adr_pct","share_local","share_fx","share_pi","share_cov_local_pi","residual"]]
''')
md(r"""
Premium variance is comparable to — for TSM slightly exceeds — total ADR variance, offset
by a strongly negative local-premium covariance: the premium **absorbs** local moves. BABA,
the fungible control, shows near-total cancellation (local 0.999, cov −0.946).

## M3 — convergence dynamics per regime class (PROVISIONAL)

Jordà local projections, HAC errors, SKHY forward-scored never fitted. **The deliverable
that gates the trade-sheet work.**
""")
code(r'''

from pipeline.convergence.jorda import run_panel, metrics_table, score_skhy
res = run_panel()
metrics_table(res)
''')
code(r'''
from pipeline.viz import figures
fig, ax = figures.g_convergence(res)
fig;
''')
md(r"""
**Read as the reflected-process thesis in a convergence estimate.** `one_way_constrained`
(TSM): ρ ≈ 0.94 one day out, still 0.88 at twenty days, t-HAC 129 — persistence on a scale
of **months**. `fungible` (BABA): ρ ≈ 0.04, statistically insignificant — same-week noise
around parity. The identical estimator produces both.

**The half-life is an interval with an open end, and that is the S17 result.** Through S15
the window stopped at h=20, ρ never approached ½ inside it, and the reported ~227d came from
extrapolating an exponential fit. Extending to h=400 was meant to make the crossing
observable. It did — and the observation contradicted the extrapolation in the direction that
matters:

- First passage of ρ below ½ is at **h ≈ 331**, roughly **46% slower** than the extrapolation
  claimed. The extrapolation was optimistic.
- The 95% band's **upper edge never crosses ½ at any estimable horizon**, so there is **no
  finite upper bound** — these data do not reject a premium that never halves.
- The band's lower edge crosses at **h ≈ 143**, where coefficients are still identified. That
  floor is the defensible number.

So extending the horizon did not turn an extrapolation into an estimate. It turned a false
point into a **floor with an open tail** — which is what any quantity linear in holding
horizon, financing cost above all, has to be quoted against.

**S18 then took the constrained class from one pair to four.** S17 named single-pair
dependence as the binding constraint, and it was: with only TSMC, "barrier regimes are
persistent" and "TSMC is persistent" were the same statement.

Membership is assigned from the **documented re-issuance rule, before any persistence is
estimated.** All four Taiwanese pairs run on one ROC rule — a *revolving* facility, where
re-issuance is permitted only within the scope of previously cancelled shares — which TSMC's
FY2024 20-F states directly and which Chunghwa Telecom's FY2025 20-F goes further on, drawing
the price conclusion itself. AU Optronics carries the same rule but is **excluded**: it
delisted its ADSs from the NYSE in 2019, and a premium built on the thin OTC successor
measures quote staleness as much as mispricing.

Three things changed, and one did not:

- The crossing became **identified** rather than underpowered — enough independent spans now
  sit under it.
- The 95% floor **rose from 143 to 220 trading days** (~7 months to ~10½). More evidence made
  the constraint tighter *and* more demanding, not looser.
- Per-pair ρ₁ runs 0.82–0.99 across the four, so the persistence **replicates** rather than
  resting on one issuer.
- **The open upper tail survived.** Roughly four times the data did not produce a finite upper
  bound. That is now a robust result rather than a small-sample artefact.

⚠️ **The limitation, stated where the estimate is:** these four share a regulator. Four pairs
reduce *issuer*-idiosyncratic noise; they do not give independent variation in the *rule*. A
second jurisdiction is the remaining gap — and India, the obvious candidate, turns out to be
the wrong one: its headroom regime was repealed effective 15 December 2014.
""")
code(r'''
from pipeline.convergence.jorda import REGIME_OF_PAIR
from pipeline.measurement.premium import build_all_variants
print("PER-PAIR, constrained class (pooled membership assigned from the rule, not the data)")
print(f"{'pair':6s} {'n':>6s} {'mean pi':>9s} {'min':>8s} {'max':>8s}")
for pid, rg in REGIME_OF_PAIR.items():
    if rg != "one_way_constrained": continue
    s_ = build_all_variants(pid)[0].series
    print(f"{pid:6s} {len(s_):6d} {s_.mean():+8.2%} {s_.min():+8.2%} {s_.max():+8.2%}")
print()
for regime, r in res.items():
    print(f"{regime:22s} half-life {r.hl.describe()}")
    print(f"{'':22s} {r.hl.method}")
    for n in r.notes: print("   !", n)
sk = score_skhy()
print(f"\\nSKHY: {sk['n_obs']} obs — {sk['out_of_support']}")
print(f"  {sk['note']}")
print(f"  resolution: {sk['resolution']}")
''')

md(r"""
## H1, H2, H3 — status (all Class X, exploratory; data-blocked)

| | channel | blocker |
|---|---|---|
| **H1** | term-structure RV | no sanctioned listed-derivatives source landed |
| **H2** | synthetic index access | venue reframed (Eurex terminated); KRX night-session separability unverified |
| **H3** | LETF close-imbalance | **no landed AUM** — issuer pages are JS SPAs, the data-bearing Naver route is terms-withheld |

H3's rebalance-notional estimator has no AUM input, so its power analysis is moot until an
AUM series lands. This is data-blocked, not a null result — the distinction matters.

## What this notebook does not claim

Nothing here is a blind pre-event forward test — **Class P is empty** (no call predates the
2026-07-29 release on the record). H5 is registered post-earnings, pre-flow, with earnings
acknowledged as known context. The convergence table is a **two-regime contrast**, not a
four-regime sweep — the `two_way_headroom` middle is empty (India unavailable). All of this
is stated rather than smoothed.
""")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}, indent=1)+"\n")
print(f"wrote {OUT.relative_to(ROOT)} ({len(cells)} cells)")
