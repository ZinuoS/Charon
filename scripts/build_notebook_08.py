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
theme.apply()
PANELS = dict(panels())
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
---
**Informational only.** Not advice, not a recommendation, not a solicitation. Four of five cost
components are bracketed assumptions; margining is illustrative; the desk quotes real levels.
H5 is a registered call resolving 2026-10-31 and is not resolved here.
""")

n = write(OUT)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells)")
