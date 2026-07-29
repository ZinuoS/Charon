# Figure audit — S17

Every figure rendered to `data/derived/audit/` at 200 DPI with `bbox_inches='tight'`, then
**viewed**, one at a time. Defects logged per figure. This is not a lint pass; a lint test
cannot see a label sitting on a line.

## Method

`uv run python -m scripts.render_audit` writes all seven G-figures to `data/derived/audit/`.
Fixes are applied at **theme or figure-module level only** — never in a notebook — so a
correction cannot land in one rendering and miss another.

## Before → after

| Figure | Defect found | Class | Fix | Status |
|---|---|---|---|---|
| G1 | floor annotation collides with x-axis date ticks | collision | `theme.annotate_barrier()` — measures the rendered label and expands the limit to make room | ✅ fixed |
| G2 | schematic box fill was raw hex `#eceae5` | palette | given the meaning `inert_fill` | ✅ fixed |
| G2 | both channels drawn in *series* hues, so barrier state was colour-coded twice | semantics | one `barrier` hue; linestyle carries binding vs discretionary | ✅ fixed |
| G4 | left-panel title overprinted the t-stat annotation | collision | t-stats moved inside the axes, upper area | ✅ fixed |
| G4 | bars coloured black for **any** positive value, so the +15bp 12% quintile (noise) read with the same emphasis as the floor reflection | **misleading encoding** | single hue; sign already encoded by direction from zero | ✅ fixed |
| G4 | "GAIN BOUNDED" sat on top of the barrier line, then (after first fix) on the realized-excursion label | collision ×2 | relocated into the empty gain region | ✅ fixed |
| G4 | t-stats, after being moved below the axes, landed on `finalize()`'s source line | collision **I introduced** | moved back inside the axes | ✅ fixed |
| G9 | loss/drawdown marks used the constrained-regime hue | semantics | `warning`, which is reserved | ✅ fixed |
| G10 | "landed"/"missing" used the fungible/constrained regime hues — a third meaning for each | semantics | `emphasis` / `barrier` / `warning` by availability state | ✅ fixed |
| G11 | first draft plotted **ρ₁ on the y-axis, which does not separate the classes at all** (ggb 0.934 vs cht 0.936) | **wrong variable** | redrawn on half-life; separates completely, 161–398d vs 1–24d | ✅ fixed |
| G11 | docstring and caption claimed the classes *overlap* on premium level. They do not (1.96% vs 0.91%) | **overstated claim** | restated as the gap comparison: 2.2× level vs 6.7× dynamics | ✅ fixed |
| G_convergence | caption asserted ρ never crosses ½ — false after S17 extended the window | **stale claim** | redrawn with bands, crossing and floor annotated | ✅ fixed |
| G_convergence | "floor 143d" label overprinted the fungible series | collision | re-anchored into the empty band below | ✅ fixed |

**Count: 13 found, 13 fixed, 0 open.**

## The last defect, and why the first two attempts at it failed

**G1 — floor annotation vs date ticks.** Measured: the `OPEN` block spanned figure-y
[0.087, 0.128] while the tick labels sat at [0.071, 0.093], with the axes floor at 0.110. The
label was hanging *outside* the axes.

**The fix named in the first draft of this document was wrong.** It proposed a `finalize()`
bottom-padding contract. `finalize()` owns the chrome *outside* the axes, but tick labels are
the axes' own furniture — padding the chrome moves the annotation and the ticks together and
the overlap survives. The room has to be made in **data space**.

`theme.annotate_barrier(ax, y, text, side)` now does that, and it took three passes to get
right:

1. Reserve `text_height + pad` in data units → still 0.002 below the axis line. The 6pt
   offset that pushes the label off the barrier line was not counted.
2. Add the offset → still 0.004 below. **Expanding the limit changes how many data units a
   point is worth**, so a requirement measured on the old scale is too small for the new one.
3. Measure the *rendered* box, adjust, re-measure, up to six passes. Converges in two or
   three and cannot be fooled by the scale change.

Any figure drawing a near-boundary barrier now gets this for free, instead of hand-tuned
offsets that break at the next figure size. Pinned by
`TestAnnotationsStayInsideTheAxes`, which asserts the geometric property — no annotation
outside its axes — rather than pixel values, so it survives font and size changes.

## Three of these were not cosmetic

Worth separating, because they are the reason a viewing pass exists at all:

1. **G11 on the wrong variable.** ρ₁ shows *no* class separation. Had that shipped, the
   ratified taxonomy would have looked worthless in its own headline figure — and the real
   finding (classes are indistinguishable at daily frequency, diverge over weeks) would have
   been invisible.
2. **G4's bar encoding.** Colouring every positive bar as emphasis made a noise bar look like
   evidence. Sign was already encoded by direction; the colour added only error.
3. **G_convergence's stale caption.** A correct chart under a caption asserting the opposite
   is worse than no chart, because the caption is what gets quoted.

## Ten-second test

Each figure must let a cold reader get the point from **headline + one drawn annotation
alone**, with plain-English bullets underneath. Bullets live in `figures.LAYMAN` — one source
of truth, rendered into notebooks and deck exports alike, so the two cannot drift.

| Figure | Headline is a declarative sentence | One takeaway annotation | Layman bullets | Verdict |
|---|---|---|---|---|
| G1 barrier anatomy | ✅ "a floor that works and a ceiling that is somebody's decision" | ✅ the two barrier rules, labelled OPEN / DISCRETIONARY | ✅ 3 | **pass** |
| G2 plumbing map | ✅ "One direction is a right; the other is a permission" | ✅ the gate bar across the narrow channel | ✅ 3 | **pass** |
| G4 asymmetry | ✅ "relative value against a one-sided barrier — not arbitrage" | ✅ "LOSS UNBOUNDED — no ceiling on file" | ✅ 3 | **pass** |
| G9 cost & skew | ✅ documented cost is the obol; hatched legs are quoted live | ✅ the hatching itself + the drawdown callout | ✅ 3 | **pass** |
| G_convergence | ✅ "The premium half-life has a floor, and no ceiling" | ✅ "upper band never crosses ½ → no finite upper bound" | ✅ 3 | **pass** |
| G10 readiness | ✅ "One expression is constructible today; four wait on named inputs" | ✅ the holes themselves, with the marker legend | ✅ 3 | **pass** |
| G11 taxonomy | ✅ "predicts how a premium behaves, not how big it is" | ✅ "no pair lands here — 24d to 161d" | ✅ 3 | **pass** |

**7/7 pass.** `figures.ten_second_test()` reports this programmatically.
