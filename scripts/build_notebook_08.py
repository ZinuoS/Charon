"""Generate notebooks/08_pitch_logic.ipynb — the argument, in sentences.

The reading layer over P7/P8/P8b/P9. Renders the same panel builders as the pack.
"""
from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from scripts._nb import notebook  # noqa: E402
from pipeline.viz import figures  # noqa: E402

OUT = ROOT / "notebooks" / "08_pitch_logic.ipynb"
md, code, write = notebook()

md(r"""
# The pitch logic — why this package, step by step

## Where the assignment is answered

| Original ask | Answered in |
|---|---|
| Part 1 — the mechanism: what the barrier is, and why the premium persists | [00 pitch](00_executive_pitch.ipynb), [02 anatomy](02_premium_anatomy.ipynb); panels P1, P2 |
| Part 2 — the trade: convergence RV, its dynamics and its economics | [04 regimes](04_regimes_convergence.ipynb), [06 ledger](06_complexity_ledger.ipynb); panels P3, P7, P8, P8b |
| Part 3 — execution: access, financing, capital, capacity, exits | panels P2, P4a, P4b, P5, P9; trade sheets in `pipeline/hedging/sheets.py` |
| Macro and FX risk | [07 environment](07_macro_environment.ipynb); panels P0a, P0b |

**What the pitch sells is a package, not a view** — and that is a conclusion the repo earned
rather than assumed. Directional timing was tested against an overparameterised alternative
(notebook 06) and the shallow model won, but only gross, pre-cost, on the comparator panel with
SKHY never fitted. So the honest product is access, financing and capital efficiency.
""")

code(r'''
%matplotlib inline
import sys, pathlib
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pipeline.viz import theme
from scripts.export_client_pack import panels
from scripts.build_deck_v2 import extra_panels
theme.apply()
PANELS = dict(panels()) | dict(extra_panels())
''')

md("## 1. The chain\n\nSix steps. Each answers the objection the previous one raises.")
code('fig, _ = PANELS["P7_the_chain"]()\nfig;')
md(figures.layman_block("g21_chain"))

md(r"""
## 2. Scenario P&L — in return-on-margin, because that is how a book is run

Three paths: compression to the cost floor at the estimated base-rate half-life; static, where
the carry simply bleeds; and the realised widening, applied **additively** from today's level.

The shaded band is the **cost bracket, not a confidence interval.** Four of five carry components
are undocumented, so no path here has a single number.
""")
code('fig, _ = PANELS["P8_scenario_pnl"]()\nfig;')
md(figures.layman_block("g22_scenario_pnl"))

md(r"""
## 3. The hedge menu

**This panel was wrongly deferred once**, on the reasoning that one of its three rows — the
convexity overlay — cannot be priced without a listed-option surface. That dropped two rows that
are presentable, including the FX row, which carries the project's most substantive hedge result:
**a premium position is not FX-neutral even with the local leg fully hedged**, because the premium
is itself a currency-exposed notional.
""")
code('fig, _ = PANELS["P8b_hedge_menu"]()\nfig;')
md(figures.layman_block("g23_hedge_menu"))

md(r"""
## 4. Exit discipline

Since no timing is sold, exits are **rules**, and rules are a tree. Five observables, three
routes, and each monitor points at the route that answers it — recall points at cancellation
because the borrow problem lives on the very leg cancellation extinguishes.

A stop on a gapping spread limits **intent, not loss**: this spread moved 36 points in five
sessions. Sizing bounds loss here; stops express preference.
""")
code('fig, _ = PANELS["P9_exit_discipline"]()\nfig;')
md(figures.layman_block("g24_exit_tree"))


md(r"""
## 5. The P&L identity — the premium-decay question, settled

A practitioner reading this deck will ask the right question early: *where does the return
come from?* The answer is an identity, and it has exactly two terms.

$$\mathbb{E}[\text{P\&L}] \;=\; \underbrace{-\,\text{financing differential}}_{\text{deterministic}} \;+\; \underbrace{\mathbb{E}[\Delta\pi]}_{\text{zero drift under the structural null}}$$

**Financing is the only deterministic component.** It accrues every day, it is what the desk
prices and earns on, and it is the one number known in advance — subject to four of its five
components still being bracketed assumptions.

**Δπ has no assumed drift, and this repository is the argument for why.** There is no
mechanical convergence force. A premium held open by a consent gate has nothing pulling it
down: cancellation removes ADRs and pushes the premium *up*, and issuance — the only force
that would push it down — requires the Company's consent. That is the barrier framework, and
it cuts against the trade as often as for it. So Δπ is high-variance, catalyst-driven, and
argued for by the **entry level** and the **identifiable channels**, never by decay.

This agrees with the desk's formulation, and it locates the pitch precisely: **financing is
the leg the desk prices; Δπ is the opportunity leg.** Two people who thought they disagreed
were describing the two terms of the same identity.
""")
code('fig, _ = PANELS["S04a_identity"]()\nfig;')
md(figures.layman_block("g28_pnl_identity"))

md(r"""
### And the second term has a boundary, not a threshold

The identity says financing is deterministic and Δπ is not. It does not say how much financing
the trade can absorb — that depends on how fast the gap closes, and **convergence is an
interval rather than a point.** The upper tail was open until 2026-08-02, when KT Corporation
joined the constrained class and bounded it; the estimate is now 211 to 391 sessions at 95%.

A breakeven computed from an interval is a **boundary**. The trade bears roughly 105bp/mo at
the fast end, 82 at the point, and 67 at the slow end — against an all-in carry of 7–70bp/mo.

**It clears at every borrow level except one corner: slow convergence and expensive borrow
together.** That is a better object than a single number, because a single number invites the
question *"and what if you are wrong about the half-life?"* — which this answers on its face,
and answers by naming the one combination that fails rather than by widening a band.
""")
code('fig, _ = PANELS["S07a_breakeven"]()\nfig;')

md(r"""
## 6. Two registers, one analysis

This repository presents the **research register**: full distributions, the risk analysis,
the nulls, and the results that went against the thesis. The pitch deck derived from it
presents the **opportunity register** appropriate to an internal sales document — which panel
leads, which of three honest paths is featured, and where the qualifier sits.

**Both draw on identical numbers.** Every deck figure is rendered by a builder in this
repository; there is no second set of numbers, and no figure exists in one and not the other
except by ordering. Advocacy is allowed to select and to emphasise. It is not allowed to
invent a number, to quote a cost without its range, or to claim a convergence force the
research disproved — and in `scripts/build_deck_v2.py` those three are assertions that fail
the build, not conventions someone has to remember.

The separation is the point. A sales document that reads like a research paper convinces
nobody, and a research paper that reads like a sales document is worth nothing. The reason
both can exist here is that only the emphasis differs.
""")

md(r"""
---
**Informational only.** Not advice, not a recommendation, not a solicitation. Four of five cost
components are bracketed assumptions; margining is illustrative; the desk quotes real levels.
H5 is a registered call resolving 2026-10-31 and is not resolved here.
""")

REQUIRED_SECTIONS = (
    '## Where the assignment is answered',
    '## 2. Scenario P&L — in return-on-margin, because that is how a book is run',
    '## 3. The hedge menu',
    '## 4. Exit discipline',
    '## 5. The P&L identity — the premium-decay question, settled',
    '## 6. Two registers, one analysis',
)

n = write(OUT, require=REQUIRED_SECTIONS)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells, "
      f"{len(REQUIRED_SECTIONS)} sections verified)")
