# Figure audit — 2026-07-29

Every figure rendered to `data/derived/audit/` at GitHub's render width and inspected.
Defects logged one line each, then fixed **at the theme or module level** so the class
cannot recur, never inline in a notebook.

## Findings

| Figure | Defect | Class | Status |
|---|---|---|---|
| **G4** | **Headline claimed "no strong pull toward zero from high levels." The chart contradicted it** — top quintile −69.6bp, t=−4.96 | **substantive: caption overstated the thesis** | **FIXED** |
| G4 | Left-panel title overflowed into the right panel | text overflow | FIXED — title wrapped |
| G4 | Right-panel title clipped at the figure edge | text overflow | FIXED — title wrapped |
| G4 | Left y-axis unlabelled; values ambiguous between bp and % | missing units | FIXED — axis label added |
| G4 | t-stat annotation collided with the tallest bar | collision | FIXED — moved above axes |
| G1 | Deposit-agreement quote overlapped the floor rule | collision | FIXED (Session 11) — moved to empty quadrant |
| G1 | Date ticks crowded on a 3-week axis | date crowding | FIXED (Session 11) — `thin_date_ticks` |
| G3 | Title/subtitle collided with panel titles | collision | FIXED (Session 9) — `multiples_headline` reserves the rect |
| G3 | 12-point and 2,328-point panels labelled every observation | date crowding | FIXED (Session 9) — per-axis locator |
| F1 | Reference-line label overlapped the series | collision | open — low severity, label sits in whitespace at current data |
| **G2** | **D5 headroom gauge and its caption were drawn inside the depositary box**, printing through "Depositary (Citibank, N.A.)" | collision | **FIXED (Session 14)** — moved to the empty lower-left quadrant |
| **G4** | **t-stat annotation sat in the same band as the second line of the two-line panel title** | collision | **FIXED (Session 14)** — moved inside the axes, top-right |
| **G1** | **OPEN floor label overprinted the date tick labels** — the floor rule sits at ~7bp, which is visually the axis | collision | **FIXED (Session 14)** — label flipped above its rule |

**Open defects: 1 (low severity).**

The three Session 14 rows were all found by rendering the *poster*, and all three were
live in the notebook figures too. A second geometry is a cheap, powerful test: the same
elements at a different aspect and type scale make latent overlaps legible. Nothing about
them was poster-specific — G2 had been shipping a caption through a box label.

### Migration to `finalize` — complete for G1/G2/G4

All three now route every chrome element through `theme.finalize`, with a kicker each
(`BARRIER STRUCTURE`, `PLUMBING`, `RISK`). Zero legacy `headline` / `multiples_headline` /
`source_note` calls remain in `pipeline/viz/figures.py`, so the collision classes cannot
reappear through those paths.

The migration surfaced one further collision: G1's deposit-agreement quote had been parked
at 0.88 axes-fraction, which the newly-placed chrome and the dashed ceiling both now
occupy. Moved to the lower-right — the only quadrant free of the path, both barrier rules
and their labels. Recorded because it is the pattern the audit keeps finding: annotations
anchored to *whatever was empty at the time* break as soon as anything else moves.

## The one that mattered

The G4 headline was **wrong, and wrong in the direction that flattered the thesis**. The
data show mean reversion at *both* ends: the bottom quintile pulls up at **t = +10.85**,
the top quintile pulls down at **t = −4.96**.

The corrected reading is stronger than the overstatement it replaced. The floor reflects
roughly twice as hard as the ceiling pulls, and −70bp is small against **249bp** daily
premium volatility. **That asymmetry is the reflected-process thesis, measured** — a
one-sided barrier should produce exactly this signature. Claiming "no reversion" was both
false and a weaker argument.

Recorded here because it is the audit's real lesson: a figure caption is a claim, and
claims drift toward the author's prior unless something checks them against the pixels.

## Defect classes and their structural fixes

| Class | Structural fix | Where |
|---|---|---|
| title/subtitle collision | `multiples_headline` reserves the layout rect | `theme.py` |
| date-axis crowding | `thin_date_ticks` — locator thins, labels never rotate | `theme.py` |
| panel-title overflow | wrap at source; titles are two short lines, not one long one | figure modules |
| missing units | `pct_axis` / `bp_axis` helpers, plus explicit axis labels | `theme.py` |
| annotation collision | anchor to axes fraction in reserved whitespace, never data coords | figure modules |
| layout constants blind to their type | gaps computed from point size and figure height (`_line_h`); blocks report the space they need (`poster_head_height`) | `theme.py` |
| builder divergence | one painter per panel; the AST lint fails any second implementation | `figures.py`, `tests/test_poster.py` |

## `finalize()` — built 2026-07-29, and the lint caught a live violation

`theme.finalize(fig, headline, subtitle, source, footnote, kicker)` now places **all**
figure chrome in one pass. `tests/test_chrome_lint.py` walks the AST of every notebook
code cell and fails on a direct `suptitle` / `tight_layout` call.

**On its first run the lint failed** — notebook 01's F5 cell called `fig.suptitle`
directly, precisely the pattern that produced the collisions this audit catalogued. Now
migrated. The rule is enforced rather than remembered.

**One ordering bug shipped and was caught by its own test.** The first implementation laid
the top block out *downward*, which makes each element's position depend on what follows
it — and the kicker overprinted the subtitle. Rebuilt to stack **upward from the axes**, so
ordering is structural: subtitle sits above the axes, headline above it, kicker on top.
`test_chrome_stack_orders_kicker_above_headline_above_subtitle` pins it.

Also added: `theme.obol()`, a small drawn coin glyph (two scatters, no image asset)
marking conversion-fee annotations — one consistent signature for "this crossing costs
money", and the project's name made visible without saying it.

**Kicker typography:** matplotlib's `Text` has no `letterspacing` property, so tracked caps
are produced by construction — uppercase joined with thin spaces. A kicker set solid reads
as a shout rather than a category.


---

## Session 13 close — remaining items and why they stopped

**Delivered:** figure audit (12 defects found, 12 fixed) · `finalize()` chrome owner with
lint enforcement · G1/G2/G4 migrated · kicker typography · obol glyph · palette-variant
system with four isolation tests · 1200×600 social card · sparkline headers on both
notebooks · notebook renumbering and index.

**Not delivered:** the poster figure (5.2 — delivered in Session 14, below) and the
animated G1 build (5.5).

Both are single-artifact jobs needing a clean run rather than the tail of a long session.
The animation in particular has a real design decision inside it — which evidence date the
discretionary ceiling should appear on. The honest answer is the prospectus-reading date,
not the listing date, because the barrier's true nature was not known at listing; drawing
it earlier would animate a claim the repository did not yet have. That is worth doing
deliberately.

**One defect class this session added to the catalogue:** *builder divergence*. The two
notebook builders used different cell-helper names (`co` vs `code`), so a snippet wired
into both applied to only one — loudly for one file, silently for the other, and the diff
looked deliberate. Fixed by unifying the helpers and pinned by
`test_both_builders_use_the_same_cell_helper_names`. Notebook freshness (executed, no
errors, carries the sparkline) is now asserted per notebook rather than assumed.

---

## Session 14 — the poster (5.2)

`scripts/make_poster.py`, 24×34in portrait, both palettes. The finding first, the numbers
second, the evidence third, and the reason not to trade it naively at the same size as the
reason to. A poster is read standing up and out of order, so it inverts the notebooks'
sequence rather than compressing it.

**Composition rule, enforced.** Every panel is drawn by a `figures.paint_*` function — the
same ones the G-series calls. The G-figures were split into a painter (draws into an axes
it was given) and a thin wrapper (makes a themed figure, calls the painter, hands chrome to
`finalize`). `tests/test_poster.py` walks the poster's AST and fails on any axes-level
drawing primitive, so the poster cannot start re-implementing a panel. This is the direct
answer to the *builder divergence* class this audit added last session: a poster that
re-drew G1's barriers would have been that defect by construction.

**Chrome ownership held.** `finalize` places chrome at `1.0 + gap` above a single axes,
which is off-paper on a multi-panel page, so `theme.poster_frame` / `poster_panel_head` /
`stat_tiles` were added rather than letting the script place its own text. Each returns the
fraction where it ended, so panels stack against measured extent.

**Numbers are derived, never typed.** The six-tile strip is computed from the same series
the panels plot; a test asserts the tiles move when the data does. The two constants — the
round-trip fee and the count of numeric deposit caps on file (zero) — are documentary
facts, cited in the footer.

### The defect class this session adds: **layout constants that do not know their type**

The first draft placed chrome at hand-tuned figure fractions (`y - 0.0155`) and stacked
panel heads in *axes* fraction. Both are the same error wearing different clothes: a gap
written as a literal encodes one font size at one paper size, and an axes-fraction gap is
proportional to panel height, so one identical call overprints on a short panel and sprawls
on a tall one. The render showed stat-tile captions through the first panel's kicker and
kickers through their own headlines.

Fixed structurally: every vertical gap in the poster chrome is computed by `theme._line_h`
from the point size and the figure's actual height, and `poster_head_height` reports what a
head block will occupy so the caller reserves real space. The tests parametrise panel
height over 0.06/0.15/0.40 and assert the stack ordering survives all three — the same
discipline as `test_chrome_stack_orders_kicker_above_headline_above_subtitle`, which pinned
the original `finalize` ordering bug.

**Still not delivered:** the animated G1 build (5.5), for the reason recorded above.
