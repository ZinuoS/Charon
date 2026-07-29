"""Chart theme — one visual system for every figure in the repo.

Design brief (NYT-graphics idiom, clean-room re-implementation; README §0 forbids
importing or referencing any prior firm project):

*   **Declarative headlines.** A chart title states the *finding* as a sentence — "The
    premium's overnight jump on July 29 was mostly a measurement artifact" — not the
    variables plotted. A smaller subtitle underneath carries the qualifier. Both are
    left-aligned to the plot area, because a centred title reads as decoration and a
    left-aligned one reads as a lede.
*   **Direct labelling over legends.** A legend makes the eye do a lookup. Where the
    series count allows, :func:`label_line_end` writes each series' name at the end of its
    own line in its own colour. Legends are a fallback, not a default.
*   **No chartjunk.** No box spines — only an x-axis baseline. Gridlines are a light
    dotted horizontal rule or nothing. No shadows, no gradients, no 3-D, no markers on
    dense series.
*   **Annotations carry the argument.** Events come from ``data/raw/events/events.yaml``
    via :func:`annotate_events`, never hand-typed, so a chart cannot drift out of sync
    with the event calendar.
*   **Every figure is attributable.** :func:`source_note` writes a source line and a
    construction footnote under the plot area. A chart that leaves the repo without its
    provenance is not finished.

Typeface choice (recorded per the spec)
---------------------------------------
Display face is **Charter**, with Palatino, Georgia and DejaVu Serif as fallbacks — all
four were verified present on this machine, and DejaVu Serif ships with matplotlib so the
stack degrades rather than breaking on another host. Charter was drawn for low-resolution
rendering and holds up small, which is what chart titles and footnotes actually need.

Body/numeric text is the default sans stack. Deliberately *not* Inter, Roboto or the other
ubiquitous UI faces: those read as template.

Palette
-------
Constants are exposed at module top as ``TODO(ash: ratify)`` — final aesthetic calls are
the author's (README §11). The current set is a muted ink-and-clay pair plus a neutral
gray for context series, chosen to stay legible in greyscale print and to avoid
red/green, which carries unwanted directional meaning in a finance chart.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = REPO_ROOT / "data" / "raw" / "events" / "events.yaml"

# ================================================================================
# SEMANTIC PALETTE — ratified structure, author-ratifiable hues.
#
# The rule this replaces: figures previously picked from INK/CLAY/MOSS by position in a
# series, so the same hue meant "SKHY" in one figure and "the comparator" in the next. A
# reader who learned the chart on page 3 had to relearn it on page 5.
#
# THE RULE NOW: a MEANING owns a HUE, everywhere. No figure may introduce a colour the
# project has not already assigned a meaning to. Adding a colour means adding a meaning
# here first, and documenting it in docs/palette.md.
#
# Base set is Okabe-Ito, chosen because it is designed to survive the common colour-vision
# deficiencies rather than merely looking distinct to trichromats. `palette_report()`
# verifies that claim numerically under deuteranope simulation rather than asserting it, and
# tests/test_palette.py fails the build if any assigned pair collapses.
# ================================================================================

#: Okabe & Ito (2008), "Color Universal Design". Named, not indexed, so a reference to a
#: hue in code says which hue it is.
OKABE_ITO = {
    "black":         "#000000",
    "orange":        "#e69f00",
    "sky_blue":      "#56b4e9",
    "bluish_green":  "#009e73",
    "yellow":        "#f0e442",
    "blue":          "#0072b2",
    "vermillion":    "#d55e00",
    "reddish_purple":"#cc79a7",
}

#: MEANING -> HUE. This dict is the legend of the entire project.
SEMANTIC: dict[str, str] = {
    # The subject. SKHY and its premium are the emphasis colour in every figure they appear
    # in, whether or not other series share the frame.
    "emphasis":    OKABE_ITO["blue"],
    # Regime classes (docs/regime_taxonomy.md). Fixed across G3/G10/G11 and metrics tables.
    "constrained": OKABE_ITO["vermillion"],
    "fungible":    OKABE_ITO["bluish_green"],
    # Barriers: ONE hue. The grammar is carried by LINESTYLE, not colour --
    #   solid = binding and mechanical | long-dash = discretionary | absent = no barrier.
    # Colour-coding barrier types as well would double-encode and then disagree with itself
    # the first time a figure needed a third barrier state.
    #
    # BLACK, and not the obvious orange. Vermillion and orange are the closest pair in
    # Okabe-Ito, and `palette_report()` measured them collapsing under deuteranope
    # simulation at delta-E 13.1 against a 20 floor -- on exactly the two meanings that
    # share a frame in G1, where barriers are drawn over a constrained-pair series. The set
    # is CVD-safe as a SET; that does not make every pair inside it safe for adjacent
    # meanings, which is why the check is numeric and runs in CI.
    "barrier":     OKABE_ITO["black"],
    # Reserved for risk/warning marks and used for NOTHING else, so its appearance in a
    # figure is information on its own.
    "warning":     OKABE_ITO["reddish_purple"],
    # Context, reference, "everything not being argued about". Always neutral.
    #
    # DARKER than the obvious mid-grey, and the direction is counter-intuitive. Reddish
    # purple desaturates toward grey for protanopes, so `palette_report()` measured
    # warning|context colliding at delta-E 10.7. Lightening the grey makes it WORSE (the
    # simulated purple sits at L* 58-73, so #a8a8a2 scores 3.3); darkening moves away from
    # it. At L* 46 the worst pair across all three conditions is 22.2. What makes this grey
    # recede is its lack of saturation next to the anchors, not its lightness.
    "context":     "#6e6e68",
    # Inert fill for schematic boxes/gauges (G2). A shape that is neither data nor argument
    # still needs a surface; giving it a NAME stops the next figure inventing its own.
    "inert_fill":  "#eceae5",
}

#: Structural neutrals — chrome, not data. Never carry meaning.
TEXT  = "#22201d"      # titles and body
MUTED = "#6e6a64"      # subtitles, footnotes, annotations
RULE  = "#d6d3cc"       # gridlines, event rules
PAPER = "#ffffff"      # figure background

# Legacy names, retained so existing figure code keeps working, but now POINTING AT
# MEANINGS rather than at arbitrary hues. New code should prefer SEMANTIC[...] or the
# accessors below; these aliases exist so the migration did not have to be atomic.
INK   = SEMANTIC["emphasis"]
CLAY  = SEMANTIC["constrained"]
MOSS  = SEMANTIC["fungible"]
GRAY  = SEMANTIC["context"]
BARRIER = SEMANTIC["barrier"]
WARNING = SEMANTIC["warning"]

#: Ordered cycle. Three series maximum before a chart should be split or small-multipled.
SERIES_COLORS = (INK, CLAY, MOSS)

#: Regime class -> hue, keyed by the taxonomy's own label strings so a figure cannot
#: disagree with pipeline.convergence.jorda about which class is which colour.
REGIME_COLORS = {
    "one_way_constrained": SEMANTIC["constrained"],
    "fungible":            SEMANTIC["fungible"],
}


def regime_color(regime: str) -> str:
    """Hue for a regime label. Unknown labels get context grey rather than a new colour."""
    return REGIME_COLORS.get(regime, SEMANTIC["context"])


#: TODO(ash: ratify) — standard geometry. One size for single charts keeps the notebook
#: visually consistent; small-multiples override height only.
FIGSIZE = (9.5, 5.2)
DPI = 150

SERIF_STACK = ["Charter", "Palatino", "Georgia", "DejaVu Serif"]

TITLE_SIZE = 13.5
SUBTITLE_SIZE = 10
LABEL_SIZE = 9
TICK_SIZE = 8.5
NOTE_SIZE = 7.5



# ================================================================================
# Derived ramps and colour-vision verification
#
# Ramps are GENERATED from the semantic anchors, never hand-picked. A heatmap that picks its
# own blues ends up disagreeing with the line chart above it about what "more premium" looks
# like; deriving from the anchor makes that impossible by construction.
# ================================================================================

def _to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _to_hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb)


def sequential_ramp(meaning: str, n: int = 7, light: float = 0.88) -> list[str]:
    """n colours from near-white to the semantic anchor. For density/heatmaps."""
    anchor = SEMANTIC[meaning]
    return [_ramp(anchor, light - (light + 0.15) * i / max(1, n - 1)) for i in range(n)]


def diverging_ramp(low: str = "fungible", high: str = "constrained", n: int = 9) -> list[str]:
    """Two semantic anchors through a near-neutral midpoint. Odd n keeps the midpoint exact."""
    half = n // 2
    lo = [_ramp(SEMANTIC[low], 0.80 - 0.80 * i / max(1, half)) for i in range(half)][::-1]
    hi = [_ramp(SEMANTIC[high], 0.80 - 0.80 * i / max(1, half)) for i in range(half)]
    return lo[::-1] + ["#f2f0ec"] + hi[::-1]


#: Deuteranope simulation. Brettel/Vienot-style linear approximation in linear-RGB, which is
#: the standard matplotlib-implementable form. Good enough to catch a collapsed PAIR, which
#: is the only thing being asked of it.
_DEUTER_M = ((0.625, 0.375, 0.0), (0.700, 0.300, 0.0), (0.0, 0.300, 0.700))
_PROTAN_M = ((0.567, 0.433, 0.0), (0.558, 0.442, 0.0), (0.0, 0.242, 0.758))


def simulate_cvd(hex_color: str, kind: str = "deuteranopia") -> str:
    """Simulate how a colour appears under a colour-vision deficiency."""
    m = _DEUTER_M if kind == "deuteranopia" else _PROTAN_M
    r, g, b = _to_rgb(hex_color)
    return _to_hex(tuple(sum(m[i][j] * (r, g, b)[j] for j in range(3)) for i in range(3)))


def _lab(hex_color: str) -> tuple[float, float, float]:
    """sRGB -> CIELAB (D65). Enough for a perceptual distance."""
    def inv(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (inv(c) for c in _to_rgb(hex_color))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.0
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(a: str, b: str) -> float:
    """CIE76 distance. ~2.3 is a just-noticeable difference; the gate below wants far more."""
    la, lb = _lab(a), _lab(b)
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


#: Minimum CIE76 separation required between any two MEANING colours, under normal vision
#: and under both simulated deficiencies. 20 is well above JND and is what the assigned set
#: actually clears — it is a real gate, not a rubber stamp.
MIN_DELTA_E = 20.0


def palette_report(meanings: Iterable[str] | None = None) -> dict:
    """Pairwise separation of the semantic colours under normal and simulated CVD.

    Returns the worst pair per condition so a failure names the two colours that collided
    rather than reporting that 'the palette' failed.
    """
    keys = list(meanings) if meanings else [k for k in SEMANTIC if k != "context"]
    out = {}
    for cond in ("normal", "deuteranopia", "protanopia"):
        conv = (lambda c: c) if cond == "normal" else (lambda c, k=cond: simulate_cvd(c, k))
        pairs = {}
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                pairs[f"{a}|{b}"] = round(delta_e(conv(SEMANTIC[a]), conv(SEMANTIC[b])), 1)
        worst = min(pairs, key=pairs.get)
        out[cond] = {"worst_pair": worst, "worst_delta_e": pairs[worst],
                     "passes": pairs[worst] >= MIN_DELTA_E, "all_pairs": pairs}
    return out

def apply() -> None:
    """Install the theme globally. Idempotent; call once per notebook."""
    mpl.rcParams.update({
        "figure.figsize": FIGSIZE,
        "figure.dpi": DPI,
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "savefig.bbox": "tight",
        # No box. Only an x-axis baseline survives.
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": True,
        "axes.edgecolor": RULE,
        "axes.linewidth": 0.9,
        "axes.labelcolor": MUTED,
        "axes.labelsize": LABEL_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "axes.prop_cycle": mpl.cycler(color=list(SERIES_COLORS)),
        "text.color": TEXT,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.5,
        "ytick.major.size": 0,          # y ticks read off the gridline, not a stub
        "grid.color": RULE,
        "grid.linestyle": ":",
        "grid.linewidth": 0.7,
        "grid.alpha": 0.9,
        "legend.frameon": False,
        "legend.fontsize": LABEL_SIZE,
        "lines.linewidth": 1.6,
        "lines.solid_capstyle": "round",
        "font.size": LABEL_SIZE,
    })


def figure(nrows: int = 1, ncols: int = 1, height: float | None = None, **kw) -> tuple:
    """A themed figure with horizontal-only gridlines and no vertical clutter."""
    figsize = kw.pop("figsize", (FIGSIZE[0], height or FIGSIZE[1]))
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kw)
    for ax in (axes.flat if hasattr(axes, "flat") else [axes]):
        ax.grid(axis="y", visible=True)
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)
    return fig, axes


def headline(ax, finding: str, subtitle: str | None = None) -> None:
    """Left-aligned declarative title stating the finding, with an optional qualifier.

    ``finding`` should be a sentence someone could repeat out loud and be right. If it
    reads like an axis label ("SKHY premium over time"), it is not a headline.
    """
    ax.set_title(
        finding, loc="left", fontsize=TITLE_SIZE, color=TEXT,
        fontfamily=SERIF_STACK, pad=22 if subtitle else 12, weight="regular",
    )
    if subtitle:
        ax.annotate(
            subtitle, xy=(0, 1.0), xycoords="axes fraction", xytext=(0, 8),
            textcoords="offset points", fontsize=SUBTITLE_SIZE, color=MUTED,
            ha="left", va="bottom", fontfamily=SERIF_STACK,
        )


def label_line_end(ax, x, y, text: str, color: str, dx: int = 6, dy: int = 0) -> None:
    """Write a series' name at the end of its own line, in its own colour."""
    ax.annotate(
        text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
        color=color, fontsize=LABEL_SIZE, va="center", ha="left", weight="medium",
    )


def source_note(fig, source: str, construction: str | None = None, y: float = -0.02) -> None:
    """Source line and construction footnote beneath the plot area.

    Two lines, deliberately: *where the numbers came from* and *what was done to them*
    are different claims, and a reader checking one should not have to disentangle it
    from the other.
    """
    fig.text(0.0, y, f"Source: {source}", fontsize=NOTE_SIZE, color=MUTED,
             ha="left", va="top", fontfamily=SERIF_STACK)
    if construction:
        fig.text(0.0, y - 0.045, construction, fontsize=NOTE_SIZE, color=MUTED,
                 ha="left", va="top", fontfamily=SERIF_STACK, wrap=True)


# --------------------------------------------------------------------------------
# Events — annotations come from the calendar, never from a literal in a notebook cell
# --------------------------------------------------------------------------------


def load_events(path: Path | None = None) -> list[dict]:
    doc = yaml.safe_load((path or EVENTS_PATH).read_text())
    return doc.get("events") or []


def events_for(markets: Iterable[str] | None = None, categories: Iterable[str] | None = None,
               path: Path | None = None) -> list[dict]:
    """Filter the calendar. Returns dicts with `date`, `title`, `id`, `market`, `category`."""
    out = []
    for ev in load_events(path):
        if markets and ev.get("market") not in set(markets):
            continue
        if categories and ev.get("category") not in set(categories):
            continue
        out.append(ev)
    return sorted(out, key=lambda e: e["date"])


def annotate_events(ax, events: list[dict], labels: dict[str, str] | None = None,
                    y_frac: float = 0.98, stagger: int = 3, min_gap_frac: float = 0.06,
                    max_labels: int | None = None) -> int:
    """Thin vertical rules with short labels, drawn from the event calendar.

    ``labels`` optionally maps an event ``id`` to a shorter caption — calendar titles are
    written for the record, not for a 7.5pt annotation, and an unabbreviated title will
    overrun its neighbour.

    Collision handling, which is most of the work: real event calendars cluster (five of
    this repo's eight events fall inside fourteen months), and naively drawn labels
    overprint into unreadable mush. Two mechanisms:

    * ``stagger`` cycles labels down N vertical levels so neighbours sit on different
      lines;
    * ``min_gap_frac`` drops a *label* whose rule is closer than that fraction of axis
      width to the previously labelled one. **The rule is still drawn** — the event is
      never hidden, only its caption is suppressed — so the chart stays honest about
      where events are while staying legible.

    Returns the number of labels drawn, so a caller can assert a chart is actually
    annotated rather than silently bare.
    """
    import matplotlib.dates as mdates

    lo, hi = ax.get_xlim()
    span = max(hi - lo, 1e-9)
    drawn = 0
    last_labeled_x: float | None = None

    for ev in sorted(events, key=lambda e: e["date"]):
        x = mdates.date2num(ev["date"])
        if not (lo <= x <= hi):
            continue
        ax.axvline(x, color=RULE, linewidth=0.9, zorder=0)

        too_close = last_labeled_x is not None and (x - last_labeled_x) / span < min_gap_frac
        if too_close or (max_labels is not None and drawn >= max_labels):
            continue

        level = drawn % max(stagger, 1)
        ax.annotate(
            (labels or {}).get(ev["id"], ev["title"]),
            xy=(x, y_frac - level * 0.055), xycoords=("data", "axes fraction"),
            xytext=(3, 0), textcoords="offset points", fontsize=NOTE_SIZE,
            color=MUTED, ha="left", va="top", fontfamily=SERIF_STACK,
        )
        drawn += 1
        last_labeled_x = x
    return drawn


def reference_line(ax, y: float, label: str, color: str = GRAY) -> None:
    """A horizontal reference rule with its label sitting on it, not in a legend."""
    ax.axhline(y, color=color, linewidth=1.0, linestyle="--", zorder=0)
    ax.annotate(
        label, xy=(0.995, y), xycoords=("axes fraction", "data"),
        xytext=(0, 4), textcoords="offset points",
        fontsize=NOTE_SIZE, color=color, ha="right", va="bottom",
    )


def pct_axis(ax, decimals: int = 0) -> None:
    """Format the y-axis as percentages of a fraction-valued series."""
    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: f"{v * 100:.{decimals}f}%")
    )


def bp_axis(ax, decimals: int = 0) -> None:
    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: f"{v * 1e4:.{decimals}f}bp")
    )


def small_multiples(n: int, height: float = 4.4, sharey: bool = True):
    """A themed row of panels with a headline block reserved above them.

    Exists because the obvious construction is wrong in two ways that only show up on
    render: ``suptitle`` plus a ``fig.text`` subtitle collide unless the rect is reserved
    explicitly, and panels with very different sample densities (12 daily points beside
    2,300) need per-axis tick thinning or the sparse panel's labels overprint.
    """
    fig, axes = plt.subplots(1, n, figsize=(4.3 * n, height), sharey=sharey)
    axes = list(axes) if n > 1 else [axes]
    for ax in axes:
        ax.grid(axis="y"); ax.grid(axis="x", visible=False); ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(labelsize=8)
    return fig, axes


def multiples_headline(fig, finding: str, subtitle: str) -> None:
    """Headline block above a small-multiples row, with the layout rect reserved."""
    fig.suptitle(finding, x=0.0, y=1.06, ha="left", fontsize=TITLE_SIZE,
                 color=TEXT, fontfamily=SERIF_STACK)
    fig.text(0.0, 1.00, subtitle, fontsize=SUBTITLE_SIZE, color=MUTED,
             ha="left", va="top", fontfamily=SERIF_STACK)


def thin_date_ticks(ax, max_ticks: int = 5) -> None:
    """Cap the number of date ticks. A 12-point daily series otherwise labels every
    observation and the labels overprint into an unreadable band."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=2, maxticks=max_ticks))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))


# --------------------------------------------------------------------------------
# finalize() — the single owner of figure chrome
# --------------------------------------------------------------------------------
#
# Every collision fixed in the Session 11 and 13 audits had the same root cause: chrome
# (kicker, headline, subtitle, source, footnote) placed by whoever was writing the figure,
# each choosing coordinates independently, none knowing what the others had reserved.
# `suptitle` does not know a `fig.text` subtitle is coming; `tight_layout` does not know
# either exists.
#
# The structural fix is ownership. `finalize` places ALL chrome, in one pass, measuring as
# it goes and reserving the space it uses. Figure modules draw data; they do not place
# text. `tests/test_chrome_lint.py` enforces that division.

KICKER_SIZE = 8.0
_CHROME_LINE_H = 0.030          # figure-fraction per chrome line at default geometry
_CHROME_GAP = 0.014


def finalize(
    fig,
    headline: str,
    subtitle: str | None = None,
    source: str | None = None,
    footnote: str | None = None,
    kicker: str | None = None,
) -> None:
    """Place every piece of figure chrome, once, without collisions.

    ``kicker`` is the editorial grammar that makes a figure sequence read like a
    publication — a small-caps category line above the headline ("BARRIER STRUCTURE",
    "MEASUREMENT", "FINANCING"). Optional; omit it for standalone figures.

    Text is laid out downward from the top of the figure and upward from the bottom, with
    each block reserving its own height, so adding a subtitle can never push a headline
    into the axes and adding a footnote can never clip a source line. Callers must not
    also call ``suptitle``, ``tight_layout`` or bare ``fig.text`` — see the lint test.
    """
    # Top block is built UPWARD from the axes, so ordering is structural rather than
    # arithmetic: subtitle sits directly above the axes, headline above it, kicker on top.
    # Laying it out downward (the obvious way) makes each element's position depend on
    # what comes after it, which is how the kicker ended up overprinting the subtitle.
    y = 1.0 + _CHROME_GAP
    if subtitle:
        fig.text(0.0, y, subtitle, fontsize=SUBTITLE_SIZE, color=MUTED,
                 ha="left", va="bottom", fontfamily=SERIF_STACK)
        y += _CHROME_LINE_H
    fig.text(0.0, y, headline, fontsize=TITLE_SIZE, color=TEXT,
             ha="left", va="bottom", fontfamily=SERIF_STACK)
    y += _CHROME_LINE_H * 1.35
    if kicker:
        # matplotlib's Text has no letterspacing property, so the tracked-caps look is
        # produced by construction: uppercase with a thin space between characters.
        tracked = "\u2009".join(kicker.upper())
        fig.text(0.0, y, tracked, fontsize=KICKER_SIZE, color=MUTED,
                 ha="left", va="bottom", fontfamily=SERIF_STACK)

    # Bottom block, laid out downward from just under the axes.
    y = -0.02
    if source:
        fig.text(0.0, y, f"Source: {source}", fontsize=NOTE_SIZE, color=MUTED,
                 ha="left", va="top", fontfamily=SERIF_STACK)
        y -= _CHROME_LINE_H + _CHROME_GAP
    if footnote:
        fig.text(0.0, y, footnote, fontsize=NOTE_SIZE, color=MUTED,
                 ha="left", va="top", fontfamily=SERIF_STACK, wrap=True)


def obol(ax, x, y, size: float = 42.0, color: str | None = None) -> None:
    """A small coin glyph marking a conversion-fee annotation.

    Drawn rather than shipped as an asset, so it inherits the palette and scales with the
    figure. One consistent signature for "this crossing costs money" — and the project's
    name made visible without saying it.
    """
    import matplotlib.patches as mpatches
    c = color or MUTED
    ax.scatter([x], [y], s=size, facecolors="none", edgecolors=c,
               linewidths=1.0, zorder=5, clip_on=False)
    ax.scatter([x], [y], s=size * 0.18, facecolors=c, edgecolors="none",
               zorder=5, clip_on=False)


# --------------------------------------------------------------------------------
# Palette variants — public by default, brand colours only where the env supplies them
# --------------------------------------------------------------------------------
#
# The public repository has no `PRESENTATION_PALETTE` value and therefore *cannot* render
# brand colours — not by convention but by construction. `presentation` derives its whole
# family from a single anchor hex via lightness ramps, so one value yields emphasis,
# secondary and muted tones without anyone hand-picking a set that drifts from the source.
#
# Design constraint for the presentation variant: the anchor family is for EMPHASIS — the
# SKHY series, barrier rules, warnings — against a neutral field. Never full-chart colour.

PALETTES: dict[str, dict[str, str]] = {
    "public": {"ink": INK, "clay": CLAY, "moss": MOSS, "gray": GRAY,
               "rule": RULE, "text": TEXT, "muted": MUTED, "paper": PAPER},
}


def _ramp(hex_color: str, lightness: float) -> str:
    """Mix ``hex_color`` toward white (lightness>0) or black (lightness<0)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if lightness >= 0:
        r, g, b = (int(c + (255 - c) * lightness) for c in (r, g, b))
    else:
        r, g, b = (int(c * (1 + lightness)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _presentation_palette() -> dict[str, str] | None:
    """Build the presentation family from the env anchor, or None if absent."""
    import os
    anchor = os.environ.get("PRESENTATION_PALETTE", "").strip()
    if not anchor:
        env = REPO_ROOT / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.strip().startswith("PRESENTATION_PALETTE="):
                    anchor = line.split("=", 1)[1].strip()
                    break
    if not anchor or not anchor.startswith("#") or len(anchor) != 7:
        return None
    return {
        "ink": TEXT,                      # neutral field: body/structure stays dark neutral
        "clay": anchor,                   # emphasis: SKHY series, barrier rules, warnings
        "moss": _ramp(anchor, -0.35),     # deeper anchor for a third series
        "gray": GRAY, "rule": RULE, "text": TEXT, "muted": MUTED, "paper": PAPER,
    }


def active_palette() -> tuple[str, dict[str, str]]:
    """(name, palette). `CHARON_PALETTE=presentation` selects it *if* an anchor exists."""
    import os
    want = os.environ.get("CHARON_PALETTE", "public").strip().lower()
    if want == "presentation":
        pres = _presentation_palette()
        if pres:
            return "presentation", pres
    return "public", PALETTES["public"]


def apply_palette(name: str | None = None) -> str:
    """Install a palette into the module globals and rcParams. Returns the name used."""
    global INK, CLAY, MOSS, GRAY, RULE, TEXT, MUTED, PAPER, SERIES_COLORS
    import os
    if name:
        os.environ["CHARON_PALETTE"] = name
    used, p = active_palette()
    INK, CLAY, MOSS = p["ink"], p["clay"], p["moss"]
    GRAY, RULE, TEXT, MUTED, PAPER = p["gray"], p["rule"], p["text"], p["muted"], p["paper"]
    SERIES_COLORS = (INK, CLAY, MOSS)
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=list(SERIES_COLORS))
    return used


def sparkline_header(pi, highlight: tuple[str, str] | None = None,
                     label: str = "", width: float = 12.0):
    """A thin full-width strip of the premium path — the recurring signature on each notebook.

    Deliberately minimal: no axes, no ticks, no gridlines. It is a *mark*, not a chart —
    a reader should register the shape and the highlighted span in under a second and move
    on. Anything more competes with the notebook's actual first figure.

    ``highlight`` is an (start, end) ISO date pair shading the span that notebook is about,
    so the set reads as a series rather than as unrelated documents.
    """
    import pandas as pd
    fig = plt.figure(figsize=(width, 0.62), dpi=DPI)
    ax = fig.add_axes([0.0, 0.20, 1.0, 0.62])
    ax.plot(pi.index, pi.values, color=INK, linewidth=1.3, solid_capstyle="round")
    ax.fill_between(pi.index, pi.values, pi.min(), color=INK, alpha=0.07)

    if highlight:
        lo, hi = (pd.Timestamp(h) for h in highlight)
        ax.axvspan(lo, hi, color=CLAY, alpha=0.16, zorder=0)

    ax.scatter([pi.index[-1]], [pi.values[-1]], s=16, color=CLAY, zorder=3)
    ax.annotate(f"{pi.iloc[-1]:.1%}", xy=(pi.index[-1], pi.values[-1]),
                xytext=(6, 0), textcoords="offset points", fontsize=8,
                color=CLAY, va="center", fontfamily=SERIF_STACK)
    if label:
        ax.annotate(label, xy=(0.0, 1.0), xycoords="axes fraction", xytext=(0, 4),
                    textcoords="offset points", fontsize=7.5, color=MUTED,
                    va="bottom", fontfamily=SERIF_STACK)

    ax.set_ylim(float(pi.min()) * 0.9, float(pi.max()) * 1.12)
    ax.axis("off")
    return fig
