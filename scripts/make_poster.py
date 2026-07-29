"""The poster — the whole argument on one page, at large format.

Item 5.2, deferred at the Session 13 close as "a single-artifact job needing a clean run
rather than the tail of a long session".

    uv run python -m scripts.make_poster
    -> data/derived/deck_export/poster.png                 (public palette)
    -> data/derived/deck_export/poster_presentation.png    (only with an anchor configured)

What it is for
--------------
The notebooks are read in sequence by someone who chose to. A poster is read standing up,
out of order, by someone who did not — so it inverts the structure: the finding first, the
numbers second, the evidence third, and the reason not to trade it naively printed at the
same size as the reason to.

Composition rule
----------------
Every panel is drawn by a ``figures.paint_*`` function — the same ones the G-series
notebooks call. Nothing here re-implements a chart. Session 13's audit added *builder
divergence* to the defect catalogue (two renderings of the same content drifting apart
silently, with the diff looking deliberate), and a poster that re-drew G1's barriers would
be that defect by construction. This module owns only the page: which panel goes where,
and what the numbers strip says.

Chrome — masthead, tiles, panel heads, footer — belongs to ``theme``.

Layout discipline
-----------------
Panels are stacked **downward from the masthead's measured bottom**, each one subtracting
the height its own head block reports via ``theme.poster_head_height``. No rect in this
file is a tuned constant that happens to clear the block above it at today's font sizes;
the first draft was written that way and its stat-tile captions printed straight through
the first panel's kicker.

No network. Reads only what ingestion wrote to ``data/raw/``.
"""
from __future__ import annotations

import matplotlib; matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from pipeline.measurement.premium import build_all_variants
from pipeline.viz import figures, theme

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "derived" / "deck_export"

#: Type/line multiplier for poster distance. Panel painters are tuned for a 9.5in-wide
#: notebook figure; on 24in paper they need to grow with it. One knob, applied uniformly,
#: rather than a parallel set of poster-sized constants that can drift from the originals.
SCALE = 1.6

#: Panel heights and the gap under each, in figure fractions. Heights are chosen so each
#: panel keeps roughly its notebook aspect; the gap under a panel clears its tick labels
#: and axis title before the next head block starts.
H_BARRIER, GAP_BARRIER = 0.215, 0.024
H_PLUMBING, GAP_PLUMBING = 0.150, 0.020
H_BOTTOM = 0.265

BARRIER_HEAD = ("barrier structure",
                "The premium has a floor that works and a ceiling that is somebody's decision",
                "One direction is a holder's right; the other requires the issuer's consent.")
PLUMBING_HEAD = ("plumbing",
                 "One direction is a right; the other is a permission",
                 "Why the classic create-to-arbitrage trade is unavailable here.")


def _stat_tiles(sk: pd.Series, tsm: pd.Series) -> list[tuple[str, str]]:
    """The numbers strip, every entry derived from the series the panels plot.

    Hand-typing these is how a poster ends up disagreeing with its own charts after a
    re-pull. The two constants — the round-trip fee and the count of numeric deposit caps
    on file — are documentary facts rather than measurements, and are cited in the footer.
    """
    return [
        (f"{sk.iloc[-1]:.1%}", f"premium, {sk.index[-1]:%d %b %Y}"),
        (f"{sk.max():.1%}", "peak, week one"),
        (f"{sk.max() - sk.min():.0%}", f"range over {len(sk)} sessions"),
        (f"${figures.FEE_PER_ADS * 2:.2f}", "round-trip cost per ADS"),
        ("0", "numeric deposit caps on file"),
        (f"+{tsm.mean():.2%}", f"TSMC mean, {len(tsm):,} days"),
    ]


def _panel(fig, top: float, height: float, head: tuple[str, str, str],
           width: float = theme.POSTER_RIGHT - theme.POSTER_LEFT,
           left: float = theme.POSTER_LEFT) -> list[float]:
    """Reserve a rect whose head block ends exactly at ``top``, and draw that head.

    Returns the rect, so the caller adds an axes at it. The head is measured before the
    rect is placed rather than after, which is what keeps a three-line headline from
    reaching up into the panel above.
    """
    kicker, headline, subtitle = head
    reserved = theme.poster_head_height(fig, headline, subtitle, scale=SCALE)
    rect = [left, top - reserved - height, width, height]
    theme.poster_panel_head(fig, rect, kicker, headline, subtitle, scale=SCALE)
    return rect


def _bare_axes(fig, rect: list[float], grid: bool = True):
    ax = fig.add_axes(rect)
    if grid:
        ax.grid(axis="y"); ax.grid(axis="x", visible=False); ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    return ax


def build(palette: str = "public", dpi: int = 150) -> Path:
    used = theme.apply_palette(palette)
    theme.apply()

    sk = build_all_variants("skhy")[0].series
    tsm = build_all_variants("tsmc")[0].series
    events = theme.events_for(markets=["US", "KR"])

    fig = plt.figure(figsize=theme.POSTER_SIZE, dpi=dpi)

    masthead_bottom = theme.poster_frame(
        fig,
        title="Pricing a one-sided arbitrage barrier",
        standfirst="The SK Hynix ADR premium as a reflected process",
        subtitle="Public data · every claim sourced · reproducible offline",
        source="Nasdaq (SKHY); EODHD (000660.KO, 2330.TW); TWSE; FRED H.10; frankfurter/ECB. "
               "Barrier language: SEC 424B4 and Deposit Agreement F-6 Ex. 99(a); 17 CFR "
               "§239.36(a). Fee per ADS from the 424B4 \"Fees and Charges\" schedule. "
               "Repo-computed; see docs/research_notes.md.",
        footnote="π = P_ADR · FX / (0.1 · P_local) − 1, raw closes. STALE: KRX closes 15:30 KST, "
                 "Nasdaq 16:00 ET — 13.5h apart, so each point pairs non-contemporaneous legs. "
                 "Hypotheses are exploratory unless preregistration/calls.yaml says otherwise.",
        scale=SCALE,
    )

    # Each chrome call returns the fraction where it ended, trailing gap included, so the
    # cursor walks down the page instead of landing on numbers written in this file.
    cursor = theme.stat_tiles(fig, _stat_tiles(sk, tsm), y=masthead_bottom, scale=SCALE)

    # --- the finding -------------------------------------------------------------
    rect = _panel(fig, cursor, H_BARRIER, BARRIER_HEAD)
    figures.paint_barrier_anatomy(_bare_axes(fig, rect), sk, events, scale=SCALE)
    cursor = rect[1] - GAP_BARRIER

    # --- the evidence ------------------------------------------------------------
    rect = _panel(fig, cursor, H_PLUMBING, PLUMBING_HEAD)
    # `quote=False`: the deposit-agreement language is already printed on the barrier panel
    # above. Twice on one page reads as a layout accident, not as emphasis. With it gone the
    # band it occupied is dead space, so the box is cropped to the diagram itself.
    figures.paint_plumbing_map(_bare_axes(fig, rect, grid=False), scale=SCALE,
                               quote=False, ylim=(1.15, 5.95))
    cursor = rect[1] - GAP_PLUMBING

    # --- the reason not to trade it naively --------------------------------------
    # Titles come from the painters' own constants: the poster hoists them into head blocks
    # (with `title=False` below) instead of keeping a second copy that can go stale.
    col_w = (theme.POSTER_RIGHT - theme.POSTER_LEFT - 0.05) / 2
    rev_head = ("evidence", figures.REVERSION_TITLE, "TSM, 2,328 days — conditional on starting level.")
    pay_head = ("risk", figures.PAYOFF_TITLE, "What the convergence expression actually pays.")

    rect = _panel(fig, cursor, H_BOTTOM, rev_head, width=col_w)
    figures.paint_reversion_quintiles(_bare_axes(fig, rect), tsm, scale=SCALE, title=False)

    rect = _panel(fig, cursor, H_BOTTOM, pay_head, width=col_w,
                  left=theme.POSTER_LEFT + col_w + 0.05)
    figures.paint_payoff_skew(_bare_axes(fig, rect), sk, scale=SCALE, title=False)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (f"poster_{used}.png" if used != "public" else "poster.png")
    # theme.apply() sets savefig.bbox='tight' globally, which trims to the drawn extent and
    # silently changes the page geometry. Passing bbox_inches=None does NOT override it --
    # None means "use the rcParam" -- so the rcParam itself must be overridden. A poster is
    # printed at a fixed paper size, so fixed geometry beats tight framing.
    with matplotlib.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(path, dpi=dpi, facecolor=theme.PAPER)
    plt.close(fig)
    return path


if __name__ == "__main__":
    for pal in ("public", "presentation"):
        p = build(pal)
        print(f"{pal:13s} -> {p.relative_to(ROOT)}")
