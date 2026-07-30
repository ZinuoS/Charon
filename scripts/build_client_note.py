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

from scripts.export_client_pack import ORDER  # noqa: E402  (pack order + one-liners)

md("# SK Hynix ADR premium — the package\n\n"
   f"**{len(ORDER)} panels.** Environment, access, capital, economics, risk, size, exit, service. "
   "Research and sources: [00 — executive pitch](00_executive_pitch.ipynb).")

code(r'''
%matplotlib inline
import sys, pathlib
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pipeline.viz import theme
from scripts.export_client_pack import ORDER, panels
theme.apply()
PANELS = dict(panels())
missing = [s for s, _ in ORDER if s not in PANELS]
assert not missing, f"pack order references panels with no builder: {missing}"
print(f"{len(ORDER)} panels, all with builders")
''')

for stem, note in ORDER:
    md(f"## {stem.split('_', 1)[0]} · {stem.split('_', 1)[1].replace('_', ' ')}\n\n{note}")
    code(f'fig, _ = PANELS["{stem}"]()\nfig;')

md(r"""
---
**Informational only — not advice, not a recommendation, not a solicitation.** Levels marked
*desk quotes live* are not published. Four of five cost components are **bracketed assumptions**,
not quotes: local borrow, ADR borrow, FX forward points, funding differential. Margining shown is
an **illustrative** parametric sketch; the desk quotes actual schedules. Base-rate half-life is
measured on a comparator panel of four barrier-constrained pairs under one regulator — SKHY is
**never fitted**. Directional model timing was tested (notebook 06) and the shallow model's edge
is gross, pre-cost and panel-only; triggers are therefore mechanism-observables, not forecasts.
Foreign-investor flows are a **named gap** — no sanctioned route. H5 is a registered call with a
2026-10-31 resolution and is **not resolved here**. Public data throughout.
""")

n = write(OUT)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells)")
