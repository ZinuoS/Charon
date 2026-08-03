"""Generate notebooks/09_tsmc_lab.ipynb — the comparator lab, with its boundary drawn first."""
from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from scripts._nb import notebook  # noqa: E402
from pipeline.viz import figures  # noqa: E402

OUT = ROOT / "notebooks" / "09_tsmc_lab.ipynb"
md, code, write = notebook()

md(r"""
# The TSMC lab — 21.6 years of the nearest regime

SK Hynix's ADR programme is fourteen sessions old. Every question the trade sheet has to
answer is a question about a **distribution** — how long an elevated premium takes to
resolve, which leg closes it, how far it goes against you first, whether hedging the
currency matters — and fourteen observations cannot describe one.

So this notebook measures the deepest pair in the same family and reports what actually
happened. **It is a characterisation, not a forecast**, and §1 exists to bound how far its
numbers may be carried.

**What this session changed about the data.** The comparator's ADR leg was sitting at a
2016 start on disk, not because the history did not exist but because the leg's provider
chain resolved to the listing venue first and that venue's API serves a rolling ten-year
window. The chain now prefers a provider that serves from 1997 — admitted only because it
agrees with the listing venue **bit-for-bit** over the whole 2,513-day overlap. After
excluding the stock-dividend era (§1.0a), the usable sample went from 2,328 sessions to
**5,064**.
""")

code(r'''
%matplotlib inline
import sys, pathlib, numpy as np, pandas as pd
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
pd.set_option("display.width", 190); pd.set_option("display.max_columns", 40)
from pipeline.viz import theme, figures
from pipeline.lab import tsmc as LAB
from pipeline.hedging.ratios import HedgeLegs
theme.apply()

FRAME = LAB.legs()
PI = FRAME["pi"]
SAMPLE = {"first": str(PI.index[0].date()), "last": str(PI.index[-1].date()), "n_obs": len(PI)}
print(f"{SAMPLE['n_obs']:,} sessions, {SAMPLE['first']} to {SAMPLE['last']}")
print(LAB.rule_grid_note())
''')

md(r"""
## 1. The structural audit — similarities justify the lab, differences bound it

Read the **"which way it cuts"** column before reading any number in this notebook. It is
the reason none of these figures is a prediction.
""")

code(r'''
from IPython.display import Markdown
COLS = ["dimension", "TSMC", "SKHY", "which way it cuts", "source"]
# Hand-rendered rather than DataFrame.to_markdown(), which needs `tabulate`. One table is not
# worth a dependency, and the cells contain prose that a DataFrame repr would truncate.
rows = ["| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
rows += ["| " + " | ".join(c.replace("|", "/") for c in r) + " |" for r in LAB.STRUCTURAL_ROWS]
Markdown("\n".join(rows))
''')

md("### The asymmetry paragraph\n\nThis is the boundary. Every figure below inherits it.")
code('print(LAB.ASYMMETRY)')

md(r"""
### 1.0a Why the sample starts in 2005, and what happens if it does not

TSMC paid annual stock dividends into the early 2000s. Both legs are **raw** closes and the
depositary ratio is a constant 5.0, so a stock dividend the two providers adjust
inconsistently accumulates into the *level*: the constructed premium averages −55% in 1997
and walks to roughly zero by 2005. That is a compounded share-count artefact, not a discount
anyone left on the table.

Eleven one-leg-only price jumps above 5σ are detectable, **all** of them between 1997-10-09
and 2002-07-25 and clustered in the June–August ex-dividend season; none occur in the
following 24 years. Using *adjusted* closes on both legs is worse, because the two legs'
cash-dividend adjustments differ.

The cause-based cut is therefore 2002-07-26. The registry uses the **more conservative**
2005-01-03, which additionally requires the level to be economically possible. A screen that
looks at the level deserves suspicion, so here is the headline number under both:
""")
code('LAB.curation_sensitivity()')
md(r"""
The wider sample is **worse**, not better. The exclusion is not flattering the result — which
is the only form of answer a curation objection can actually be given.
""")

md(r"""
## 2. Episode census (G25) — how often, how big, how long, and which leg closes it

An episode is a peak-to-trough swing exceeding a threshold, found by a **forward-only
reversal walk**: a running extreme is carried until the premium retraces the threshold, which
confirms it. Nothing is smoothed and no window is centred, so an episode's endpoints are
knowable when they are dated.

Every cell of the rule grid is reported. `dropped_short` is the number of swings the
`min_days` filter removed — carried so the filter is visible rather than silent.

One thing the full grid exposes that a single cell would hide: **the episode count is not
monotone in the threshold.** At `min_days=5`, the 3pp rule reports *more* episodes (355) than
the 2pp rule (346). That is the two-part rule behaving correctly — a larger reversal threshold
produces fewer but longer swings, so a smaller share of them is dropped by the duration
filter. The raw swing count *is* monotone, and the test suite pins that instead.
""")
code('LAB.census(frame=FRAME)')

code(r'''
EP = LAB.episodes(PI, 5.0, 10)
CH = LAB.resolution_channel(FRAME, EP)
fig, meta = figures.g25_episode_census(LAB.census(frame=FRAME), EP, CH, SAMPLE)
fig;
''')
md(figures.layman_block("g25_episode_census"))

md(r"""
**Why the channel split is a trade decision, not trivia.** The decomposition is an identity —
`log(1+π) = log ADR + log FX − log local`, so the three contributions sum to the move exactly
(the notebook asserts the residual is zero). Compressions closed via the **ADR leg 56% of the
time** and via the local leg 44%; widenings ran through the ADR leg **74%** of the time.

The ADR is where both the convergence and the risk live. That promotes the short-ADR
expression on the sheet and demotes any framing in which the local leg does the work.
""")
code('CH.groupby(["direction", "channel"]).agg(n=("move_pp","size"), median_move=("move_pp","median"), median_days=("days","median"))')

md(r"""
## 3. Entry outcomes against the breakeven (G26) — the lab's headline

The rule: enter short-premium whenever the premium sits above a given percentile **of its own
past** (expanding, 504-session warmup — the rule never sees its own future), hold for a fixed
horizon, subtract the bracketed carry.

Every (percentile × horizon × bracket) cell is reported.
""")
code('EO = LAB.entry_outcomes(PI); EO[EO.horizon_d == 252]')
code('fig, meta = figures.g26_entry_outcomes(EO)\nfig;')
md(figures.layman_block("g26_entry_outcomes"))

md(r"""
**The number the financing decision turns on.** At the 90th-percentile entry held one year:
**55.5%** of historical entries beat the *low* carry bracket, **41.8%** beat the *mid*, and
**16.4%** beat the *high*.

Two readings, and the second is the important one.

1. The signal is real and monotone in extremity — the 99th percentile beats mid carry 60.4%
   of the time against 34.8% at the 80th. Entering further out is better.
2. **The cost bracket, not the signal, decides the trade.** The same rule wins or loses
   depending only on which carry it pays, and four of the five carry components are still
   bracketed assumptions. That is a quantitative argument for having the desk conversation
   before having the view — and it is the empirical form of what the pitch already sells:
   access and financing, not timing.

And the boundary: this pair's facility **revolves**. These rates describe the mean-reverting,
*favourable* variant of the family.
""")

md(r"""
## 4. What it costs you en route (G26b) — the case for sizing over stopping

Same entries, but now the *path*: the maximum adverse excursion before resolution. For a
short-premium position, adverse means the gap **widening**.
""")
code(r'''
EX = LAB.excursions(PI)
SK = LAB.skhy_week_one_excursion()
print(f"excursion: median {EX.attrs['median_mae_pp']:.1f}pp   95th {EX.attrs['p95_mae_pp']:.1f}pp   "
      f"worst in 21.6 years {EX.attrs['max_mae_pp']:.1f}pp")
print(f"SKHY realised, first {SK['sessions']} sessions: {SK['excursion_pp']:.1f}pp")
EX
''')
code('fig, meta = figures.g26b_stop_survival(EX, SK)\nfig;')
md(figures.layman_block("g26b_stop_survival"))

md(r"""
**The finding that hardens the risk budget.** The worst 252-day adverse excursion in 21.6
years of the comparator is **25.3 points**. SKHY moved **35.6 points** against an early
seller in **three sessions** — larger than the worst case in the whole comparator history,
in a pair whose barrier is *harder* than the comparator's.

And the stop table shows why a stop is not the answer. A 10-point stop fires on **54%** of
historical entries, and on 22% of entries that would have ended profitable. Tighten it to 4
points and it fires on 86%. There is no distance at which it bounds loss without also
cutting the winners: this is the empirical case for **sizing** as the risk control, with
stops expressing intent. It is the same conclusion G24 reaches from the exit tree, reached
independently from the path distribution.
""")

md(r"""
## 5. The FX case (G27)

The analytic sensitivity is `d(π)/d(FX) = (1+π)/FX`, a ceteris-paribus derivative. The
empirical one absorbs both equity legs' own FX betas, and is what a hedge actually faces.
""")
code('FX = LAB.fx_sensitivity_deep(FRAME); FX')
code(r'''
RS = LAB.premium_notional_structure(FRAME)
p = HedgeLegs.live("skhy").premium
fig, meta = figures.g27_fx_case(FX, RS, p / (1 + p))
fig;
''')
md(figures.layman_block("g27_fx_case"))

md(r"""
**Three things the shallow sample could not show.**

The coefficient is **0.856 (95% CI 0.653–1.058)** on 5,063 days, and FX explains **1.34%** of
daily premium variance. On 2,327 days the interval was 0.507–1.103 and comfortably contained
1.0; on the deep sample the pair's own analytic coefficient (1.062) sits just outside it. So
the mechanical link is real and partially offset — not "theory, unrejected".

It is **not stable across eras**. 2016–2020 gives 0.31 with an interval containing zero;
2021–2026 gives 1.26. No single hedge ratio is correct for all regimes, which is a caveat the
hedge menu's FX row now carries.

The **premium-as-currency-notional** structure is identical, because it is arithmetic:
hedging the local leg leaves `π/(1+π)` of the ADR leg exposed in any pair. What is not
arithmetic is the magnitude — TSMC's median residual is 4.0% and its 21-year maximum is
24.7%, while SKHY today sits at **18.4%**, above this pair's 95th percentile. The same hedge
is materially less complete on the traded pair than on the lab's.

**A circularity worth disclosing.** The FX coefficient shipped on the SKHY hedge menu was
estimated on *this* pair. It is a Taiwanese estimate applied to a Korean pair, and because
the TWD is a managed float, it is a lower bound on the won's sensitivity rather than a
like-for-like.
""")

md(r"""
## 6. What the lab changes

| Sheet element | Direction | Why, by figure |
|---|---|---|
| **Risk-budget framing** | **HARDENED** | G26b. SKHY's realised week-one excursion exceeds the worst 252-day excursion in 21.6 years of a pair with a *softer* barrier. Sizing carries the risk; stops express intent. |
| **Short-ADR as the primary expression** | **PROMOTED** | G25. 56% of compressions and 74% of widenings ran through the ADR leg. The ADR is where both the convergence and the risk live. |
| **Financing conversation before the view** | **HARDENED, and now quantified** | G26. 55.5% / 41.8% / 16.4% by bracket. The bracket decides the trade; the signal only ranks entries within it. |
| **FX hedge row on the hedge menu** | **WEAKENED** | G27. Era-unstable (0.31 to 1.26), and its coefficient is borrowed from this comparator. Still worth doing; no longer quotable as one ratio. |
| **The ~80bp/month breakeven** | **UNTOUCHED** | The lab measures outcomes against the bracketed carry directly, so it neither confirms nor moves the breakeven arithmetic. |
| **The reflected-process claim itself** | **UNTOUCHED** | By construction. This pair's facility revolves; it cannot be evidence about a barrier it does not have. |
| **Half-life estimates** | **MOVED, mechanically** | The comparator's usable history went from 2,328 to 5,064 sessions, so the pooled constrained-class estimate is re-fitted on 2.2× the data. See notebook 04. |

---
**Informational only.** Not advice, not a recommendation, not a solicitation. Every number
here is a characterisation of a regime family measured on its *favourable* variant. Quoting a
fraction-beats-carry from a revolving facility as the probability an SKHY entry beats carry
substitutes the easier trade for the real one.
""")

REQUIRED_SECTIONS = (
    '## 1. The structural audit — similarities justify the lab, differences bound it',
    '## 2. Episode census (G25) — how often, how big, how long, and which leg closes it',
    "## 3. Entry outcomes against the breakeven (G26) — the lab's headline",
    '## 4. What it costs you en route (G26b) — the case for sizing over stopping',
    '## 5. The FX case (G27)',
    '## 6. What the lab changes',
)

n = write(OUT, require=REQUIRED_SECTIONS)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells, "
      f"{len(REQUIRED_SECTIONS)} sections verified)")
