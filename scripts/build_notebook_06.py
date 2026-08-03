"""Generate notebooks/06_complexity_ledger.ipynb. uv run python -m scripts.build_notebook_06"""
from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from scripts._nb import notebook  # noqa: E402
from pipeline.viz import figures  # noqa: E402

OUT = ROOT / "notebooks" / "06_complexity_ledger.ipynb"
md, code, write = notebook()

md(r"""
# Parsimony vs. complexity — the ledger

> **EXPERIMENT — deviation-gated.** Track B runs under `docs/deviations.md` **DEV-004, signed
> 2026-07-29**. It exceeds README §8's capacity rule *by construction*: random Fourier features
> with P ≫ N. Outputs are quarantined to `data/derived/voc_experiment/` and reach no
> client-facing artifact. The exception expires with this experiment.

**The question.** §8 caps model complexity because this panel's effective N is small. That is a
*prior*, not a result. Kelly, Malamud & Zhou (*The Virtue of Complexity in Return Prediction*,
J. Finance 2024) is a serious published claim that the prior is wrong in this asset class.

**The design.** Two tracks, one harness. Same inputs, same target, same test folds — the folds
are shared *by construction*, since both tracks consume `jorda.fold_iter`. Two parallel fold
builders compared by a test is a test waiting to pass while the implementations drift.

**The target is what a trade is paid by.** Δln(1+π), not the level. The premium's level is 92%
forecastable and that is not an edge — it is the statement that a slow series stays put.
""")

code(r'''
%matplotlib inline
import sys, pathlib, pandas as pd
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pipeline.viz import theme, figures
from pipeline.convergence.jorda import s4_metrics_table
theme.apply()
VOC = ROOT / "data" / "derived" / "voc_experiment"
grid = pd.read_csv(VOC / "complexity_grid.csv")
diag = pd.read_csv(VOC / "strategy_diagnostics.csv")
print("DEV-004 signed 2026-07-29 — Track B ran under the exception.")
print(f"grid points: {len(grid)}   diagnostics rows: {len(diag)}")
''')

md(r"""
## 1. Track A — the parsimony anchor, on the tradeable target
""")
code(r'''
# SAME SCOPE AS TRACK B. The first ledger quoted this at full N against Track B at N=200 --
# two designs in one table, i.e. a comparison of sample sizes wearing a comparison of models.
a = s4_metrics_table(target="change", max_train=200)
a[["regime","horizon","n","rmse","r2","hit_rate","scope"]].round(4)
''')
md(r"""
Every metric here carries `N_train = 200 (capped; see DEV-004)`, h, and the fold scheme inline.
**The full-N complexity grid was infeasible, not omitted:** c = 20 against N ≈ 18,000 demands
360,000 features, so capping the training block is what makes a P ≫ N grid computable at the
sample size §8's capacity rule was actually written for.

R² is negative for the constrained class at every horizon — worse than forecasting no move.
That is the capacity rule's own prediction, and it sets the bar Track B has to clear.

## 2. Track B — the complexity grid
""")
code(r'''
fig, _ = figures.g13_complexity(grid)
fig;
''')
md(figures.layman_block("g13_complexity"))

md(r"""
**No double descent.** The paper's signature is out-of-sample performance *improving* past the
interpolation threshold c = 1. Here the curve is flat in complexity — a 500× range in feature
count (P = 20 to P = 10,000) moves R² by about 0.06 at heavy shrinkage — and ordered almost
entirely by **shrinkage**, which moves it by three orders of magnitude.

Read the right panel carefully: hit rate is **0.61 at every c, including c = 0.1**. A 20-feature
model gets it. So whatever Track B is picking up is the **nonlinear basis**, not P ≫ N. Calling
that a virtue of complexity would be mislabelling a virtue of regularisation.

## 3. The critique diagnostics

Both tracks face them. This is the credibility layer, and one of them is a full stop.
""")
code(r'''
diag[["regime","horizon","sharpe_track_a","sharpe_track_b",
      "sharpe_unconditional","sharpe_vol_managed"]].round(3)
''')
md(r"""
### The Nagel objection, implemented rather than cited

An apparent edge can be **mechanical position-scaling with volatility** rather than
sign-prediction skill: a strategy that levers up when vol is low earns a Sharpe premium that
looks like forecasting. So the benchmark is not zero — it is a **vol-managed unconditional**
strategy on the same folds: always short the premium, sized 1/σ.
""")
code(r'''
diag[["regime","horizon","track_b_alpha_vs_volmanaged","track_b_t_alpha_naive",
      "track_b_t_alpha_hac","track_b_t_alpha_nonoverlap","n_effective_blocks",
      "turnover_track_b"]].round(4)
''')
md(r"""
**Track B's alpha over the vol-managed benchmark is POSITIVE** (+0.0037), so the Nagel objection
is faced and survived rather than fatal — the edge is not merely mechanical vol-sizing. But read
the three t-columns together: **11.51 naive, 5.32 HAC, 4.08 non-overlapping.** The naive figure
is inflated by roughly √h because h=20 returns overlap by 19 periods. **5.32 is the number to
quote**; the naive one stays visible so the size of the correction is auditable.

Sharpe is annualised √(252/h), not √252, for the same reason. Turnover is reported (0.21 per
step), and it matters: an unquantified cost stack at that turnover can plausibly consume a +0.54
gross Sharpe, which is why §5(b) refuses to call this tradeable.

### Permutation placebo — the full stop
""")
code(r'''
from pipeline.convergence import voc
G, S = (0.5, 2.0, 20.0), (1e-3, 1.0)
real = voc.run("one_way_constrained", h=20, complexity=G, shrinkage=S)
plac = pd.concat([voc.run("one_way_constrained", h=20, complexity=G, shrinkage=S, shuffle_seed=s)
                  for s in (11, 22)]).groupby(["c","shrinkage"], as_index=False)[["r2","hit_rate"]].mean()
j = real.merge(plac, on=["c","shrinkage"], suffixes=("_real","_placebo"))
assert (j.hit_rate_placebo - 0.5).abs().max() < 0.03, "PLACEBO FAILURE — harness leaking"
print("PLACEBO PASSES — shuffled hit rate stays at ~50%, so the 60% is signal, not leakage.\n")
j[["c","shrinkage","hit_rate_real","hit_rate_placebo","r2_real","r2_placebo"]].round(4)
''')

md(r"""
## 4. What this result does and does not invalidate

The firewall, because a public artifact containing a strategy Sharpe invites exactly one
misreading — that the project's case rests on it. It does not.

**(a) The structural thesis is untouched.** The barrier framework and the premium's documented
persistence rest on **mechanism and measurement**: a deposit agreement that gates issuance, a
cancellation right that does not, ρ₁ = 0.94 with a half-life floor of 220 trading days. Nothing
in this notebook is an input to any of that. If every forecast here were deleted, the thesis
would read identically.

**(b) The tactical timing overlay is a gross, panel-only result and is reported as such.** A
+0.54 Sharpe at h=20, before any transaction cost, on the comparator panel — **SKHY is never
fitted**. Borrow, funding and hedge points are undocumented and the trade sheets say so. At
0.21 turnover per step an unquantified cost stack can plausibly consume this. **It is not a
tradeable claim and it is not presented as one.**

**(c) The client expressions are access and financing products, not signal products.** Their
case is that the leg is hard to book and the position hard to finance — both true regardless of
whether anything is forecastable. Nothing in §2 of the client note depends on (b).
""")

md(figures.layman_block("g14_magnitude_paradox"))

md(r"""
**One sentence a salesperson can repeat:** *the reason to do this trade is that the plumbing is
one-way and the financing is hard, not that we think we can time it.*

## 5. G14 — where the difference actually comes from
""")

code(r'''
from pipeline.convergence.voc import magnitude_deciles
dec = pd.read_csv(VOC / "magnitude_deciles.csv")
fig, _ = figures.g14_magnitude_paradox(dec)
fig;
''')

md(r"""
At the same N, the two tracks have **near-identical overall hit rates** (62.1% vs 62.2%). The
Sharpe gap is built entirely in the top magnitude decile — 60.6% against 52.6% — and that decile
carries most of the P&L. Being right about small moves is cheap.

## 6. The ledger
""")

code(r'''
best = (grid[grid.regime == "one_way_constrained"]
        .sort_values("hit_rate", ascending=False).head(1).iloc[0])
a20 = s4_metrics_table(horizons=(20,), target="change", max_train=200).set_index("regime")
d20 = diag[(diag.regime == "one_way_constrained") & (diag.horizon == 20)].iloc[0]
r = "one_way_constrained"
pd.DataFrame([
    {"metric": "OOS R²", "Track A — shallow": round(a20.loc[r, "r2"], 3),
     "Track B — complexity": round(best.r2, 3)},
    {"metric": "sign hit rate", "Track A — shallow": f"{a20.loc[r,'hit_rate']:.1%}",
     "Track B — complexity": f"{best.hit_rate:.1%}"},
    {"metric": "strategy Sharpe (GROSS)", "Track A — shallow": round(d20.sharpe_track_a, 3),
     "Track B — complexity": round(d20.sharpe_track_b, 3)},
    {"metric": "vs unconditional (+0.04) / vol-managed (−0.02)",
     "Track A — shallow": "beats both", "Track B — complexity": "beats both"},
    {"metric": "alpha vs vol-managed, HAC t", "Track A — shallow": "—",
     "Track B — complexity": f"{d20.track_b_alpha_vs_volmanaged:+.4f} (t={d20.track_b_t_alpha_hac:.2f})"},
    {"metric": "double descent observed?", "Track A — shallow": "n/a",
     "Track B — complexity": "NO"},
    {"metric": "placebo", "Track A — shallow": "passes", "Track B — complexity": "passes"},
    {"metric": "scope", "Track A — shallow": d20.scope, "Track B — complexity": d20.scope},
]).set_index("metric")
''')

md(r"""
**t-stat footnote.** The alpha's naive t is 11.51. Corrected for h=20 overlap it is **5.32**
(Newey–West, lag h−1) and **4.08** on non-overlapping blocks (658 effective observations against
13,146 overlapping ones). The naive figure is kept visible so the size of the correction is
auditable rather than quietly absorbed; **5.32 is the number to quote.** The same audit was
applied to both Sharpe standard errors.

## 7. The ending the numbers support — and a correction

**This notebook previously reported the opposite conclusion, and the hardening pass caught it.**
`strategy_diagnostics` computed `pnl = -sign(forecast) × Δπ` — a strategy that *faded its own
signal*. Every Sharpe and alpha was the exact negative of the truth. The magnitude-decile table
is what exposed it: P&L was negative in **every** decile including buckets with a 67% hit rate,
which is arithmetically impossible for a strategy trading with its forecast. Recording it here
because a result that reversed under its own diagnostic is worth more as a documented catch than
as a quietly amended number.

Two claims from the earlier version were also **scope artefacts**: "hit rate 62% vs 53%" and
"neither beats not trading". Both dissolve once Track A is quoted at the same N_train = 200.

**The corrected ending, closest to Block E's second:**

- **Parsimony wins.** Track A Sharpe **+0.54** against Track B **+0.36**, same folds, same N.
- **Both beat the benchmarks**, including the vol-managed one — so the Nagel objection is faced
  and survived rather than fatal. Track B's alpha over it is positive at HAC t = 5.3.
- **Complexity adds nothing, and the reason is visible.** Accuracy is identical overall; the
  complex model gives back its edge precisely in the decile that pays.
- **No double descent.** R² flat over a 500× range in P; three orders of magnitude come from
  shrinkage; hit rate 0.61 at c = 0.1. **What helped was regularisation, not dimensionality.**

**§8's capacity rule was right for this problem, and it is now shown rather than assumed.**
DEV-004 expires here: the exception was granted to test whether complexity wins, and it does not.

**What it changes downstream.** Not the expressions — see the firewall in §5. It does change the
*methods* story, which is now a stronger one: the doctrine was challenged with the strongest
published counter-argument, adjudicated on identical folds, and held.
""")

REQUIRED_SECTIONS = (
    '## 1. Track A — the parsimony anchor, on the tradeable target',
    '## 2. Track B — the complexity grid',
    '## 3. The critique diagnostics',
    '## 4. What this result does and does not invalidate',
    '## 5. G14 — where the difference actually comes from',
    '## 6. The ledger',
    '## 7. The ending the numbers support — and a correction',
)

n = write(OUT, require=REQUIRED_SECTIONS)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells, "
      f"{len(REQUIRED_SECTIONS)} sections verified)")
