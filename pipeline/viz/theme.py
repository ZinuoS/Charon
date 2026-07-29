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

# --------------------------------------------------------------------------------
# Palette — TODO(ash: ratify). Every constant below is an aesthetic decision.
# --------------------------------------------------------------------------------

INK = "#1c3d5a"        # TODO(ash: ratify) — primary series: deep slate blue
CLAY = "#b4532a"       # TODO(ash: ratify) — secondary series: burnt sienna
MOSS = "#4a6b4a"       # TODO(ash: ratify) — third series, used sparingly
GRAY = "#9a9a94"       # TODO(ash: ratify) — context/reference series
RULE = "#d6d3cc"       # TODO(ash: ratify) — gridlines and event rules
TEXT = "#22201d"       # TODO(ash: ratify) — titles and body text
MUTED = "#6e6a64"      # TODO(ash: ratify) — subtitles, footnotes, annotations
PAPER = "#ffffff"      # TODO(ash: ratify) — figure background

#: Ordered cycle. Three series maximum before a chart should be split or small-multipled.
SERIES_COLORS = (INK, CLAY, MOSS)

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
