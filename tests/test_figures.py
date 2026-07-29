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
