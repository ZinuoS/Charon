# The palette — semantic assignments

**RATIFIED 2026-07-29.** Semantic assignments, geometry, and the colour-vision floor are
settled. The `public` variant below is the only palette in this repository.

**One rule: a meaning owns a hue, everywhere.** No figure may introduce a colour the project
has not already assigned a meaning to. Adding a colour means adding a meaning here first.

Defined once in `pipeline/viz/theme.py` (`SEMANTIC`); enforced by `tests/test_palette.py`.

## The assignments

| Meaning | Hue | Okabe–Ito name | Used for | Never used for |
|---|---|---|---|---|
| `emphasis` | `#0072b2` | blue | SKHY and its premium — the subject of the study — plus the primary series in any single-series figure, and "landed" status in G10 | a comparator |
| `constrained` | `#d55e00` | vermillion | the `one_way_constrained` regime class, in G_convergence / G11 / metrics tables | risk, warnings, or any non-regime category |
| `fungible` | `#009e73` | bluish green | the `fungible` control class, same figures | anything else |
| `barrier` | `#000000` | black | every barrier, in both states. **Linestyle carries the grammar:** solid = binding and mechanical, long-dash = discretionary, absent = no barrier | a data series |
| `warning` | `#cc79a7` | reddish purple | **reserved.** Loss regions, realized adverse excursions, unbounded-risk callouts, missing inputs | anything not a risk |
| `context` | `#6e6e68` | — | reference series, schematic edges, "everything not being argued about" | data under discussion |
| `inert_fill` | `#eceae5` | — | schematic box and gauge surfaces (G2) | data |

Chrome — `TEXT`, `MUTED`, `RULE`, `PAPER` — is not in this table because it carries no
meaning. Chrome is owned by `finalize()`.

### Why regime hues route through a function

`theme.regime_color(label)` keys off the taxonomy's own label strings, so a figure cannot
disagree with `pipeline.convergence.jorda` about which class is which colour. Unknown labels
get context grey rather than a new hue — a figure that invents a class gets a visibly
un-styled mark rather than silently minting a colour.

## Accessibility — measured, not asserted

Base set is **Okabe & Ito (2008)**, chosen because it is designed to survive common
colour-vision deficiencies. `theme.palette_report()` verifies pairwise CIE76 separation under
normal vision, deuteranopia and protanopia; the floor is **ΔE ≥ 20** (a just-noticeable
difference is ~2.3, so this is a real gate).

**Okabe–Ito being safe as a *set* does not make any pair inside it safe for two adjacent
meanings.** Both collisions below were found inside it, by the check, after the assignments
"looked fine":

| Collision | Where | ΔE | Resolution |
|---|---|---|---|
| `constrained` × `barrier` | vermillion vs orange — the closest pair in Okabe–Ito, and they **share G1's frame** | 13.1 deut. | barrier reassigned to **black** |
| `warning` × `context` | reddish purple desaturates toward grey for protanopes | 10.7 prot. | context **darkened**, not lightened — see below |

The second fix runs against intuition and is worth recording. Lightening the context grey
makes the collision *worse*, because protanope-simulated purple sits at L\* 58–73: `#a8a8a2`
scores ΔE 3.3. Darkening to L\* 46 moves away from it, worst-pair 22.2. What makes this grey
recede is its **lack of saturation** next to the anchors, not its lightness.

Current worst pairs, all meanings including context:

| condition | worst pair | ΔE |
|---|---|---|
| normal | `warning`×`context` | 42.1 |
| deuteranopia | `emphasis`×`fungible` | 26.3 |
| protanopia | `emphasis`×`fungible` | 37.1 |

## Ramps are derived, never picked

`sequential_ramp(meaning, n)` and `diverging_ramp(low, high, n)` generate lightness ramps
from the semantic anchors, so a heatmap inherits the system instead of choosing its own blues
and then disagreeing with the line chart above it. `test_ramps_are_generated_not_hardcoded`
changes an anchor and asserts the ramp moves.

## Two variants, structurally separated

- **`public`** — the semantic set above. The default, and the only one present in this repo.
- **`presentation`** — red-anchored, hexes read from `PRESENTATION_PALETTE` (env or gitignored
  `.env`). **Absent publicly, and falls back to `public` with no error.** The isolation test
  stands: no presentation hex appears in any committed file.

`make deck` exports every figure under the presentation palette at deck resolution.

## If you are a future session

Do not free-style a colour. If a figure needs a distinction the table above cannot express,
the distinction is a new *meaning*: add it to `SEMANTIC`, add a row here, and let
`test_palette.py` tell you whether it survives colour-blind simulation. The raw-hex ban in
`test_figures_introduce_no_raw_hex` exists to make that the path of least resistance.

*(That test was itself broken on first write — it stripped comments with `line.split("#")[0]`,
which truncated `facecolor="#eceae5"` to `facecolor="` and deleted the very thing it searched
for. It now tokenizes. A lint test that cannot fail is worse than no lint test.)*

---

## A firm-branded scale is deliberately NOT in this repo

Asked for on 2026-07-29. It is not committed, and the reason is this repo's own constitution
rather than preference:

* **README §0** excludes desk and firm names from **all committed files** — the rule that had
  the firm name stripped from line 7.
* **README §8** bars firm data and firm code from the repository *"under any circumstances."*
* The repository is **public**. Brand hexes are a firm asset, and an internal deck template is
  firm material.

**The supported route already exists.** `PRESENTATION_PALETTE` reads its anchor from the
environment or a gitignored `.env`, is **absent publicly**, and falls back to `public` with no
error. `make deck` exports every figure under it at deck resolution.

```bash
# not committed; not in the repo; supplied by the author at render time
PRESENTATION_PALETTE="#RRGGBB,#RRGGBB,#RRGGBB" uv run python -m scripts.render_audit
```

`tests/test_chrome_lint.py` asserts no presentation hex appears in any committed file, so this
separation is enforced rather than remembered. Hand me the hexes directly if you want the deck
built under them; they will not be written to disk inside the repo.

---

## Type and geometry — amended 2026-07-30 (S25)

**Type.** The stack is `Arial → Helvetica → Liberation Sans → DejaVu Sans`, recorded in
`theme.PORTABLE_FONT_STACK`. The live `theme.FONT_STACK` is that list filtered to faces
matplotlib can actually resolve on the authoring machine, because an unresolvable name in a
per-call `fontfamily=` list emits one `findfont` warning *per text object* — 1,628 lines for
four figures, which buries real output in a notebook. Sizes were retuned once for the new face
with a maximal-readability bias: title 15.0, subtitle 11.0, label 10.5, tick 10.0, note 8.5,
kicker 9.0.

Worth recording as a defect rather than a change: `theme.apply()` had never set
`font.family` at all. Chrome text passed the stack per call, while axis ticks and labels
rendered in matplotlib's default face — two faces in every figure, unnoticed because both were
quiet. Setting the family globally is what actually makes the type identity real.

**Geometry.** The canonical-width constraint is retired. It existed because the deck was the
delivery medium and slides are uniform; the repository is now the delivery medium, and a
reader scrolling a notebook is not bound by slide geometry. `theme.SHAPES` names the shapes
content actually needs — `wide` for long timelines, `tall` for distributions, `large` for
schematics — and `FIGSIZE` is what a figure falls back to when it expresses no preference.
What is still fixed, because it protects legibility rather than uniformity: the DPI floor, the
tight bounding box, and `finalize()` owning all chrome.

**Palette.** Anchors unchanged pending the author's supplied hex values. The CVD simulation
was re-run under the new type and geometry and passes at every severity; the worst pair is
`warning|inert_fill` at ΔE 24.1 (deuteranope) and 24.9 (protanope), against a floor of 20.0.
When the new anchors land, the ramps re-derive programmatically and this report is re-run —
advisory, not a veto: if a supplied pair fails deuteranopia, the failing pair is *named* along
with wherever linestyle or direct labelling already disambiguates it, and the author's choice
stands.

---

## 2026-07-30 — red / grey becomes the shipped palette

Author instruction, and the clean-room rule is explicitly overridden for it. Two things are
worth recording precisely, because "override the restriction" is not the same as "stop
checking".

**Provenance.** The hexes below are DERIVED in this repository, by searching a red-and-grey
scheme against `palette_report()`. They are not any firm's brand values and nothing was
copied from another project. If exact brand hexes are wanted, they replace these values in
`_PALETTES["red_grey"]` and the check below is re-run.

**Why the check still matters more here.** Red and grey collapse the hue axis, which is the
axis a colour-vision-deficient reader has least access to. The categorical separations
therefore have to be carried by lightness and saturation, and picking these by eye lands the
closest pair at delta-E 9-12 — under the 20 floor, and invisible until it is on a slide in
front of someone. Chosen by search instead:

| condition | closest pair | delta-E | floor |
|---|---|---|---|
| normal | emphasis \| warning | 26.9 | 20 |
| deuteranopia | emphasis \| warning | 25.5 | 20 |
| protanopia | emphasis \| warning | 22.6 | 20 |

| meaning | hex | role |
|---|---|---|
| emphasis | `#B01B22` | the subject; used for nothing else |
| constrained | `#E08A76` | lighter desaturated red — separates on lightness |
| fungible | `#5C636E` | cool dark grey — the control class |
| barrier | `#101113` | near-black, as before |
| warning | `#6D0F16` | oxblood: darker and flatter than emphasis |
| context | `#9B9B95` | neutral, recedes next to both anchors |
| inert_fill | `#EAE8E4` | schematic surfaces |

The Okabe-Ito research palette is retained whole in `_PALETTES["okabe_ito"]`. Flipping
`theme.PALETTE` and re-running the builds renders every figure in it — that is what "both
palettes" means operationally.
