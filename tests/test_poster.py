"""The poster (5.2): composition rules, derived numbers, and layout invariants.

Three things are worth pinning here, and they are the three that would break silently:

* the poster must **compose** the G-series painters rather than re-draw them — the
  builder-divergence defect class from the Session 13 audit;
* its numbers strip must be **derived** from the series it plots, not typed;
* its chrome must stack without overprinting **at any panel height**, which is exactly
  what the first draft got wrong.
"""
from __future__ import annotations

import ast
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pipeline.viz import figures, theme

ROOT = Path(__file__).resolve().parents[1]
POSTER = ROOT / "scripts" / "make_poster.py"

theme.apply()


@pytest.fixture
def fake_series():
    """Synthetic π paths. Layout and derivation are testable without ingested payloads —
    only the real render needs them, and that test skips when they are absent."""
    sk = pd.Series(
        [0.128, 0.318, 0.442, 0.517, 0.489, 0.402, 0.271, 0.192, 0.238,
         0.301, 0.329, 0.288, 0.244, 0.224],
        index=pd.bdate_range("2026-07-10", periods=14),
    )
    rng = np.random.default_rng(7)
    n = 400
    x = np.zeros(n); x[0] = 0.09
    for i in range(1, n):
        x[i] = x[i - 1] + 0.02 * (0.089 - x[i - 1]) + rng.normal(0, 0.0125)
    return sk, pd.Series(x, index=pd.bdate_range("2017-01-02", periods=n))


# --------------------------------------------------------------------------------
# Composition — the poster draws no charts of its own
# --------------------------------------------------------------------------------

#: Axes-level drawing primitives. If the poster calls one, it has started re-implementing
#: a panel instead of calling the painter that already draws it.
DRAWING_PRIMITIVES = {"plot", "bar", "axhline", "axvline", "axhspan", "axvspan",
                      "fill_between", "scatter", "add_patch"}


def test_poster_composes_painters_and_draws_nothing_itself():
    """The anti-divergence rule, enforced rather than remembered.

    A poster that re-drew G1's barriers would look right on the day it was written and
    drift from the figure the moment either changed — with the diff looking deliberate.
    """
    tree = ast.parse(POSTER.read_text())
    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    offending = called & DRAWING_PRIMITIVES
    assert not offending, (
        f"scripts/make_poster.py calls {sorted(offending)} directly. Panels are drawn by "
        "pipeline.viz.figures.paint_* so the poster and the notebooks cannot disagree."
    )
    painters = {n.func.attr for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr.startswith("paint_")}
    assert len(painters) >= 4, f"expected the poster to compose four panels, saw {painters}"


def test_every_painter_the_poster_uses_is_the_one_the_g_series_uses():
    """Same objects, not same-looking copies."""
    import inspect
    for g, painter in ((figures.g1_barrier_anatomy, "paint_barrier_anatomy"),
                       (figures.g2_plumbing_map, "paint_plumbing_map"),
                       (figures.g4_asymmetry, "paint_reversion_quintiles"),
                       (figures.g4_asymmetry, "paint_payoff_skew")):
        assert painter in inspect.getsource(g), \
            f"{g.__name__} no longer routes through {painter}; the poster would diverge"


def test_poster_titles_are_not_a_second_copy():
    """The bottom panels' titles are hoisted from the painters' own constants."""
    src = POSTER.read_text()
    assert "figures.REVERSION_TITLE" in src and "figures.PAYOFF_TITLE" in src
    assert "Mean reversion is asymmetric" not in src, "title retyped into the poster"


# --------------------------------------------------------------------------------
# Derivation — the numbers strip cannot disagree with the panels
# --------------------------------------------------------------------------------


def test_stat_tiles_are_derived_from_the_series(fake_series):
    from scripts.make_poster import _stat_tiles
    sk, tsm = fake_series
    tiles = dict((c, v) for v, c in _stat_tiles(sk, tsm))
    assert tiles[f"premium, {sk.index[-1]:%d %b %Y}"] == f"{sk.iloc[-1]:.1%}"
    assert tiles["peak, week one"] == f"{sk.max():.1%}"
    assert tiles["round-trip cost per ADS"] == f"${figures.FEE_PER_ADS * 2:.2f}"
    assert tiles["numeric deposit caps on file"] == "0", \
        "the documentary fact the whole thesis rests on"


def test_stat_tiles_follow_the_data_rather_than_a_literal(fake_series):
    """A re-pull must move the tiles. Hard-typed numbers are how a poster goes stale."""
    from scripts.make_poster import _stat_tiles
    sk, tsm = fake_series
    before = _stat_tiles(sk, tsm)
    after = _stat_tiles(sk * 2, tsm)
    assert before[0] != after[0] and before[1] != after[1]


# --------------------------------------------------------------------------------
# Chrome — stacking must hold at any panel height
# --------------------------------------------------------------------------------


def _poster_fig():
    return plt.figure(figsize=theme.POSTER_SIZE, dpi=50)


@pytest.mark.parametrize("height", [0.06, 0.15, 0.40])
def test_panel_head_never_overprints_at_any_panel_height(height):
    """The bug this file exists for.

    The first draft stacked the head block in *axes* fraction, so the gap between lines
    was proportional to the panel's height — identical calls overprinted on short panels
    and sprawled on tall ones.
    """
    fig = _poster_fig()
    rect = [0.055, 0.3, 0.89, height]
    theme.poster_panel_head(fig, rect, "kick", "HEAD", "SUB", scale=1.6)
    pos = {t.get_text(): t.get_position()[1] for t in fig.texts}
    kicker = next(y for t, y in pos.items() if t not in ("HEAD", "SUB"))
    assert kicker > pos["HEAD"] > pos["SUB"] >= rect[1] + rect[3], \
        "kicker above headline above subtitle, all above the axes"
    plt.close(fig)


def test_panel_head_height_reserves_what_the_head_actually_uses():
    fig = _poster_fig()
    rect = [0.055, 0.3, 0.89, 0.15]
    head = "A headline\nthat runs to two lines"
    reserved = theme.poster_head_height(fig, head, "sub", scale=1.6)
    theme.poster_panel_head(fig, rect, "kick", head, "sub", scale=1.6)
    top = max(t.get_position()[1] for t in fig.texts)
    assert top <= rect[1] + rect[3] + reserved, "head block overflows its reservation"
    plt.close(fig)


def test_multi_line_headline_reserves_more_than_a_single_line():
    fig = _poster_fig()
    one = theme.poster_head_height(fig, "one line", scale=1.6)
    two = theme.poster_head_height(fig, "two\nlines", scale=1.6)
    assert two > one
    plt.close(fig)


def test_masthead_and_footer_do_not_meet_in_the_middle():
    fig = _poster_fig()
    bottom = theme.poster_frame(fig, title="T", standfirst="S", source="Src",
                                footnote="F", scale=1.6)
    assert 0.5 < bottom < 0.95, "masthead should end in the top fifth of the page"
    footer_ys = [t.get_position()[1] for t in fig.texts if t.get_text().startswith("Source:")]
    assert footer_ys and max(footer_ys) < bottom
    plt.close(fig)


# --------------------------------------------------------------------------------
# Panel geometry — the collisions the poster render exposed
# --------------------------------------------------------------------------------


def test_d5_gauge_sits_outside_the_depositary_box():
    """Regression: the gauge and its caption were drawn inside the depositary box, printing
    the headroom label through "Depositary (Citibank, N.A.)". Wrong in G2 as well as on the
    poster — a squashed panel aspect only made it legible."""
    fig, ax = theme.figure()
    figures.paint_plumbing_map(ax)
    gauge = [p for p in ax.patches if type(p).__name__ == "Rectangle"
             and abs(p.get_width() - 1.5) < 1e-6]
    assert len(gauge) == 1, "expected exactly one D5 gauge rectangle"
    gx, gy = gauge[0].get_xy()
    # Depositary box occupies x 4.1-6.0, y 2.6-3.85.
    assert not (4.1 <= gx <= 6.0 and 2.6 <= gy <= 3.85), \
        f"D5 gauge at ({gx}, {gy}) is inside the depositary box"
    label = next(t for t in ax.texts if "D5 observable" in t.get_text())
    lx, ly = label.get_position()
    assert not (4.1 <= lx <= 6.0 and 2.6 <= ly <= 3.85)
    plt.close(fig)


def test_reversion_t_stats_sit_inside_the_axes(fake_series):
    """They used to sit at 1.005 axes fraction, in the same band as the second line of a
    two-line panel title, and overprinted it."""
    _, tsm = fake_series
    fig, ax = theme.figure()
    figures.paint_reversion_quintiles(ax, tsm)
    t = next(t for t in ax.texts if "quintile" in t.get_text())
    assert t.get_position()[1] <= 1.0, "t-stat annotation must not reach into the title band"
    plt.close(fig)


def test_barrier_floor_label_clears_the_date_ticks(fake_series):
    """The OPEN label was drawn below a rule sitting at ~7bp — visually the axis — and
    overprinted the date tick labels."""
    sk, _ = fake_series
    fig, ax = theme.figure()
    figures.paint_barrier_anatomy(ax, sk)
    t = next(t for t in ax.texts if t.get_text().startswith("OPEN"))
    assert t.get_va() == "bottom", "the floor label sits above its rule, not under it"
    plt.close(fig)


@pytest.mark.parametrize("painter,args", [
    ("paint_plumbing_map", ()),
    ("paint_barrier_anatomy", ("sk",)),
    ("paint_reversion_quintiles", ("tsm",)),
    ("paint_payoff_skew", ("sk",)),
])
def test_scale_grows_the_type(painter, args, fake_series):
    """`scale` is the poster's only type knob; if a painter ignores it, that panel renders
    at notebook size on 24-inch paper."""
    sk, tsm = fake_series
    resolved = [{"sk": sk, "tsm": tsm}[a] for a in args]
    sizes = []
    for scale in (1.0, 2.0):
        fig, ax = theme.figure()
        getattr(figures, painter)(ax, *resolved, scale=scale)
        sizes.append(max((t.get_fontsize() for t in ax.texts), default=0))
        plt.close(fig)
    assert sizes[1] > sizes[0], f"{painter} ignores scale"


# --------------------------------------------------------------------------------
# End to end — needs the payloads, so it skips without them
# --------------------------------------------------------------------------------


def test_poster_builds_end_to_end(tmp_path, monkeypatch):
    from pipeline.measurement.premium import build_all_variants
    try:
        build_all_variants("skhy")[0]
        build_all_variants("tsmc")[0]
    except Exception:
        pytest.skip("panel data not ingested")

    import scripts.make_poster as mp
    monkeypatch.setattr(mp, "OUT", tmp_path)
    path = mp.build("public", dpi=50)
    assert path.exists() and path.stat().st_size > 0
