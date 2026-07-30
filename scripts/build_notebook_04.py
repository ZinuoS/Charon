"""Generate notebooks/04_regimes_convergence.ipynb. uv run python -m scripts.build_notebook_04"""
from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from pipeline.viz import figures  # noqa: E402  (layman blocks: one source of truth)

OUT = ROOT / "notebooks" / "04_regimes_convergence.ipynb"
from scripts._nb import notebook  # nbformat does the JSON; see scripts/_nb.py

md, code, write = notebook()

md(r"""
# Regimes and convergence — the per-regime metrics table

> **PROVISIONAL.** The regime *taxonomy* is ratified (2026-07-29, `docs/regime_taxonomy.md`):
> membership is assigned from a documented issuance rule, before any price is read. The
> **panel** is not ratified — the constrained class is four issuers under one regulator, and
> five of the six controls are Brazilian. Every number below inherits that.

**What this notebook is.** The S4 deliverable: out-of-fold RMSE, R² and sign hit rate for the
premium, per regime class and per horizon. It is the artifact that every trade sheet, hedge
ratio and convergence number in the project has been waiting on.

**What it is not.** There is no M2 regime classifier, and there does not need to be. The
regime label is read off a filing, so it is an **input** here. A model trained to predict a
label already fixed by a deposit agreement is fitted to its own answer key.
""")

code(r'''
%matplotlib inline
import sys, pathlib
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import pandas as pd
from pipeline.viz import theme, figures
from pipeline.convergence.jorda import (PANEL_CAVEATS, TAXONOMY_RATIFIED, TABLE_HORIZONS,
                                        run_panel, s4_metrics_table)
theme.apply()
print(f"taxonomy RATIFIED {TAXONOMY_RATIFIED}   horizons {TABLE_HORIZONS}")
for c in PANEL_CAVEATS: print("  PROVISIONAL:", c)
''')

md(r"""
## The table

Out-of-fold. Expanding walk-forward, 5 splits, **embargo = h** — training labels overlap the
test block by h periods, and without the embargo the fit sees its own test window through the
label. Centring fitted train-only. SKHY excluded from every fit.

The predictor is the Jordà local projection M3 already uses: π_{t+h} ~ π_t. **Sign hit rate
scores the change from today's level, not the level** — a premium that is almost always
positive would score ~100% on the level and tell you nothing.
""")

code(r'''
tbl = s4_metrics_table()
tbl.drop(columns=["PROVISIONAL"])
''')

md(r"""
**The classes separate out of sample, in the direction the mechanism predicts.** The
barrier-constrained premium is forecastable — R² 0.92 at h=1, still 0.68 at h=60. The fungible
control's R² is **negative beyond one day**: worse than predicting its own mean. There is no
persistence left in it, which is exactly what a working two-way arbitrage should leave behind.

**The hit rates run the other way, and that is worth saying out loud.** The control's sign hit
rate (57–60%) beats the constrained class's (53%). Level and direction are different
questions: the constrained premium's *level* is highly predictable while its next *move* is
close to a coin flip — the profile of a slow-moving series sitting near a barrier. A trade
sheet that quoted the R² and skipped the hit rate would be quoting the flattering half.

The pooled row is last and labelled. It is not a regime.
""")

code(r'''
fig, ax = figures.g_convergence(run_panel())
fig;
''')
md(figures.layman_block("g_convergence"))

md(r"""
## Ablations — both feature families are cut

**M5** is each pair's own local-leg context (20-day realized vol, 60-day drawdown). **M6** is
each pair's own FX 20-day trend. In and out under identical folds — asserted, not assumed: the
first version of the M6 ablation dropped rows when the feature was added, so the two arms
scored different samples and RMSE appeared to improve while R² fell. That is only possible
when the sample moves underneath you.

*M5 is specified as "000660 deep history" and cannot be: 000660 is SKHY's local leg and SKHY
is never fitted. It is built per-pair on each pair's own local leg instead — the only form in
which the feature is both testable and inside the quarantine.*
""")

code(r'''
def ablate(fams, label):
    b = s4_metrics_table(families=fams, use_features=False)
    x = s4_metrics_table(families=fams, use_features=True)
    j = b.merge(x, on=["regime", "horizon"], suffixes=("_b", "_x"))
    assert (j.n_b == j.n_x).all(), f"{label}: arms scored different samples"
    j["d_rmse"] = j.rmse_x - j.rmse_b
    j["d_r2"] = j.r2_x - j.r2_b
    j.insert(0, "family", label)
    return j[["family", "regime", "horizon", "n_b", "d_rmse", "d_r2"]]

abl = pd.concat([ablate(("m5",), "M5"), ablate(("m6",), "M6"),
                 ablate(("m5", "m6"), "M5+M6")], ignore_index=True)
print("identical folds CONFIRMED in every arm\n")
abl.round(5)
''')

md(r"""
**Verdict: cut.** RMSE worsens and R² falls at every horizon in every class. Hit rate moves up
marginally, not enough to offset either. A near-zero-to-negative delta cuts the family, and
**that is a finding, not a failure** — it says the premium's dynamics are its own rather than
an FX overlay, consistent with FX explaining ~1.2% of daily premium variance.

**Verdict: cut both.** M5 is the worse of the two — it costs the control 0.41 of R² at h=60.
Together they are no better than either alone, so no interaction is being missed.

### The degenerate-regime case, which M5 actually produced

At h=60 M5 **helps the minority class and hurts the dominant one**: constrained (n≈13,210)
gains Δr² +0.0039 while fungible (n≈23,207) loses 0.41, and the pooled row nets **−0.053**.

Reading only the improved cell — *"M5 helps the constrained regime at the horizon we care
about"* — would justify keeping a family that makes the panel measurably worse. That is why the
pooled row exists, why it is labelled, and why the detector that finds this pattern is computed
in `scripts/s4_table.py` rather than left to a reader comparing columns.

## Variance shares — and why they do not separate the classes
""")

code(r'''
from hypotheses.h4_vol_decomposition.realized import compare_pairs
fig, ax = figures.g12_variance_shares(compare_pairs().to_dict("records"))
fig;
''')
md(figures.layman_block("g12_variance_shares"))

md(r"""
**No regime-timeline figure, deliberately.** The session spec paired the variance figure with
one. There is nothing to plot: regime is a per-pair label read off a filing, so a timeline of
it is a horizontal line. The time-varying quantity is *binding-ness* — headroom — which the H5
monitor already reports as text, and which has a single observation on the capped programme.

## What this unlocks, and what it does not

The table's half-lives are what the trade sheets accrue financing against, and they are quoted
as a **floor with an open tail**: at least 220 trading days at 95%, no finite upper bound,
because ρ's upper confidence edge never crosses one half at any estimable horizon.

It does not unlock a point cost. Cost is linear in holding horizon and the horizon's upper
tail is open, so a point estimate would understate in the direction that flatters the trade.

Regenerate everything here with `just s4`. Research programme:
**[00 pitch](00_executive_pitch.ipynb)** · **[01 client note](01_client_note.ipynb)** ·
**[02 anatomy](02_premium_anatomy.ipynb)** · **[05 engines](05_hypothesis_engines.ipynb)**.
""")

n = write(OUT)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells)")
