"""Generate notebooks/01_client_note.ipynb — the VISUAL PACK, not a document.

Six panels a PM scans in ninety seconds. Composition rule: headline + figure + stat callouts +
at most one plain-English line. **No body paragraphs.** Anything that was prose became a label,
a callout, a caption line, or moved to notebook 00 where the verbal research belongs.

Disclaimers are a footer band, once, not paragraphs throughout.
"""

from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from scripts._nb import notebook  # noqa: E402
from pipeline.viz import figures  # noqa: E402

OUT = ROOT / "notebooks" / "01_client_note.ipynb"
md, code, write = notebook()

#: One line per panel, in the register the desk approved. Any longer and it is a paragraph.
LINE = {
    1: "The gap is 22.6% and the trade that would normally close it runs one way only.",
    2: "You hold one position; the registration, borrow, FX and booking chain sit on our side.",
    3: "At today's level the carry has to stay under about 79bp a month for the base rate to pay.",
    4: "A move that already happened would have called for 44 cents of margin per dollar.",
    5: "Getting out is not the problem. Borrowing the US shares to sell is.",
    6: "You receive a state report, because we tested model timing and it came back a draw.",
}

md("# SK Hynix ADR premium — the package\n\n"
   "**Six panels.** Access, capital, economics, risk, size, service. "
   "Research and sources: [00 — executive pitch](00_executive_pitch.ipynb).")

code(r'''
%matplotlib inline
import sys, pathlib
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pipeline.viz import theme
from scripts.export_client_pack import panels
theme.apply()
PANELS = dict(panels())
list(PANELS)
''')

TITLES = {
    1: "P1 · The situation", 2: "P2 · The structure", 3: "P3 · The economics",
    4: "P4 · How it hurts", 5: "P5 · Size and exit", 6: "P6 · What you receive",
}
KEYS = {1: ["P1_situation"], 2: ["P2_structure"], 3: ["P3_economics"],
        4: ["P4a_payoff", "P4b_margin_path"], 5: ["P5_size_and_exit"],
        6: ["P6_what_you_receive"]}

for n in range(1, 7):
    md(f"## {TITLES[n]}\n\n{LINE[n]}")
    for k in KEYS[n]:
        code(f'fig, _ = PANELS["{k}"]()\nfig;')

md(r"""
---
**Informational only — not advice, not a recommendation, not a solicitation.** Levels marked
*desk quotes live* are not published. Four of five cost components are **bracketed assumptions**,
not quotes: local borrow, ADR borrow, FX forward points, funding differential. Margining shown is
an **illustrative** parametric sketch; the desk quotes actual schedules. Base-rate half-life is
measured on a comparator panel of four barrier-constrained pairs under one regulator — SKHY is
**never fitted**. Directional model timing was tested (notebook 06) and the shallow model's edge
is gross, pre-cost and panel-only; triggers are therefore mechanism-observables, not forecasts.
H5 is a registered call with a 2026-10-31 resolution and is **not resolved here**. Public data
throughout; every figure reproducible from this repository.
""")

n = write(OUT)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells)")
