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

**Open defects: 1 (low severity).**

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
