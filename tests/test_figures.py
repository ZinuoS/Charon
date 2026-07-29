"""Smoke-render tests for the G-series figure modules.

These assert the figures *build* — axes, drawn barriers, no exception — not that they
look right. Rendering is the part that silently breaks when a data shape changes.
"""
from __future__ import annotations
import matplotlib; matplotlib.use("Agg")
import pandas as pd, pytest
from pipeline.viz import figures, theme

theme.apply()


@pytest.fixture(scope="module")
def series():
    from pipeline.measurement.premium import build_all_variants
    try:
        return build_all_variants("skhy")[0].series, build_all_variants("tsmc")[0].series
    except Exception:
        pytest.skip("panel data not ingested")


def test_g1_draws_both_barriers(series):
    sk, _ = series
    fig, ax = figures.g1_barrier_anatomy(sk)
    styles = {tuple(l.get_linestyle()) if isinstance(l.get_linestyle(), tuple)
              else l.get_linestyle() for l in ax.get_lines()}
    assert len(ax.get_lines()) >= 3, "expected path + floor + ceiling"
    assert any(isinstance(s, tuple) or s in ("--", "-.") for s in styles), \
        "the discretionary ceiling must be visually distinct from the solid floor"


def test_g1_quotes_the_deposit_agreement(series):
    sk, _ = series
    fig, ax = figures.g1_barrier_anatomy(sk)
    text = " ".join(t.get_text() for t in ax.texts)
    assert "level from time to time" in text, "the operative language must travel with the claim"
    assert "DISCRETIONARY" in text and "OPEN" in text


def test_g1_never_calls_the_upper_barrier_a_quota(series):
    """Session-wide language rule: the upper barrier is discretionary, not an exhausted quota."""
    sk, _ = series
    fig, ax = figures.g1_barrier_anatomy(sk)
    text = " ".join(t.get_text() for t in ax.texts).lower()
    assert "quota" not in text and "exhausted" not in text


def test_g2_plumbing_map_builds():
    fig, ax = figures.g2_plumbing_map()
    text = " ".join(t.get_text() for t in ax.texts)
    assert "MRFTA" in text and "20.0008%" in text
    assert "CANCELLATION" in text and "ISSUANCE" in text


def test_g4_shows_the_unbounded_side(series):
    sk, ts = series
    fig, axes = figures.g4_asymmetry(ts, sk)
    text = " ".join(t.get_text() for a in axes for t in a.texts)
    assert "UNBOUNDED" in text, "the negative skew must be drawn, not footnoted"
    assert "BOUNDED" in text


class TestExpressionReadiness:
    """G10 — the expressions menu as a matrix. Guards the claims the chart makes."""

    def _fig(self):
        from pipeline.hedging.sheets import all_sheets
        from pipeline.viz import figures
        return figures.g10_expression_readiness(all_sheets(0.226, "headroom 0"))

    def test_renders(self):
        fig, ax = self._fig()
        assert fig is not None

    def test_row_count_matches_the_sheet_count(self):
        """The chart must not silently drop an expression — a five-row menu drawn with four
        rows would read as a shorter menu, not as a bug."""
        from pipeline.hedging.sheets import all_sheets
        from pipeline.viz import figures
        sheets = [s for s in all_sheets(0.226, "headroom 0") if s.kind == "expression"]
        assert len(figures.g10_expression_readiness.__doc__) > 0
        fig, ax = figures.g10_expression_readiness(all_sheets(0.226, "headroom 0"))
        labels = [t.get_text() for t in ax.texts]
        for s in sheets:
            assert any(s.name.split("(")[0].strip() in t for t in labels), \
                f"{s.name} missing from the matrix"

    def test_horizon_is_drawn_bounded_not_landed(self):
        """The convergence-horizon column must not read as fully landed. A floor with an
        open tail is not the same as having the number, and the marker encodes that."""
        fig, ax = self._fig()
        note = " ".join(t.get_text() for t in fig.texts) + " ".join(t.get_text() for t in ax.texts)
        assert "floor" in note.lower() and "no ceiling" in note.lower() or "upper bound" in note.lower()

    def test_legend_explains_every_marker_state_used(self):
        fig, ax = self._fig()
        legend = [t.get_text() for t in ax.texts if "landed" in t.get_text()]
        assert legend, "marker legend missing"
        for state in ("landed", "bounded", "missing", "not required"):
            assert state in legend[0], f"legend does not explain '{state}'"


class TestAnnotationsStayInsideTheAxes:
    """The G1 defect, pinned.

    G1 shipped with its OPEN barrier label hanging below the axes onto the x tick labels.
    The fix is `theme.annotate_barrier`, which measures the rendered text and expands the
    limit to make room -- ITERATIVELY, because expanding the limit changes how many data
    units a point is worth, so a one-shot calculation lands short.

    This test asserts the geometric property rather than the pixel values, so it keeps
    holding when the figure size or font changes.
    """

    def _rendered(self, fig, ax):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        inv = fig.transFigure.inverted()
        box = ax.get_position()
        out = []
        for t in ax.texts:
            bb = inv.transform(t.get_window_extent(renderer))
            if bb[0][1] < box.y0 or bb[1][1] > box.y0 + box.height:
                out.append("".join(t.get_text().splitlines())[:40])
        return out

    def test_g1_has_no_annotation_outside_its_axes(self):
        import matplotlib
        matplotlib.use("Agg")
        from pipeline.measurement.premium import build_all_variants
        from pipeline.viz import figures, theme
        theme.apply()
        pi = build_all_variants("skhy")[0].series
        fig, ax = figures.g1_barrier_anatomy(pi, theme.events_for(markets=["US", "KR"]))
        strays = self._rendered(fig, ax)
        assert not strays, f"annotation(s) outside the axes: {strays}"

    def test_annotate_barrier_expands_the_limit_when_it_must(self):
        """A barrier sitting flush on the lower limit must push the limit down, not overflow."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from pipeline.viz import theme
        theme.apply()
        fig, ax = plt.subplots()
        ax.set_ylim(0.0, 1.0)
        theme.annotate_barrier(ax, 0.0, "two\nlines", side="below")
        assert ax.get_ylim()[0] < 0.0, "limit was not expanded to fit a below-line label"

    def test_annotate_barrier_leaves_a_roomy_axis_alone(self):
        """It must not expand when there is already space — otherwise every figure drifts."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from pipeline.viz import theme
        theme.apply()
        fig, ax = plt.subplots()
        ax.set_ylim(-5.0, 1.0)
        theme.annotate_barrier(ax, 0.5, "one line", side="below")
        assert ax.get_ylim()[0] == -5.0, "expanded an axis that already had room"
