"""Borrow-utilization state, and the ablation that cannot be run.

The load-bearing test here is the last one: it asserts, by computation rather than by comment,
that this feature reaches zero fitted pairs. That is the reason it is not in the metrics table,
and a claim like that should fail loudly if the panel ever changes.
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.measurement import utilization as U


@pytest.fixture(scope="module")
def frame():
    rng = pd.date_range("2015-01-01", periods=400, freq="B")
    bal = pd.Series(range(400), index=rng) * 1000 + 5_000_000
    return pd.DataFrame({"balance_shares": bal,
                         "new_lending_shares": 1000, "repaid_shares": 400}, index=rng)


def test_percentile_uses_only_the_past(frame):
    """Information timing (README §4) applied to a feature. A monotone-rising balance must
    sit at the TOP of its trailing window every day — if the window leaked future values the
    percentile would sag below 1."""
    u = U.utilization_state(frame).dropna(subset=["balance_pctile"])
    assert u.balance_pctile.min() > 0.99, "percentile is seeing values it should not"


def test_state_is_terciled_into_the_declared_labels(frame):
    states = set(U.utilization_state(frame).state.dropna().astype(str))
    assert states <= set(U.TERCILES)


def test_net_lending_is_new_minus_repaid(frame):
    u = U.utilization_state(frame)
    assert (u.net_lending_shares == 600).all()


def test_current_reading_declares_it_is_relative_not_a_ratio():
    """Lendable supply is not public, so calling this "utilization" without the caveat would
    imply a fraction of supply that was never measured."""
    try:
        c = U.current()
    except Exception:
        pytest.skip("d3 not pulled in this environment")
    assert "not a utilization ratio" in c["caveat"]
    assert 0.0 <= c["balance_pctile"] <= 1.0
    assert c["state"] in U.TERCILES


def test_hardcoded_coverage_set_matches_what_is_actually_landed():
    """`_LENDING_COVERAGE` in jorda.py is a hardcoded set; `lending_readiness()` reads the
    disk. A hardcoded coverage claim is how a stale one survives, so the two are compared
    and this fails when they diverge — including the good divergence, when TWSE SBL
    accumulates enough sessions to become usable."""
    from pipeline.convergence.jorda import _LENDING_COVERAGE
    ready = set(U.lending_readiness()["ready"])
    assert ready == _LENDING_COVERAGE, (
        f"landed coverage {sorted(ready)} != declared {sorted(_LENDING_COVERAGE)}. If TWSE SBL "
        "has reached the fold minimum, add its pairs and run the real ablation."
    )


def test_twse_sbl_capture_has_started():
    """The forward series only exists from the day capture began, so a gap is unrecoverable."""
    r = U.lending_readiness()["rows_per_pair"]
    assert r.get("tsmc", 0) >= 1, "no TWSE SBL snapshot landed — `just snapshot` is not running"


def test_the_feature_reaches_zero_fitted_pairs_so_it_cannot_be_ablated():
    """THE POINT. D3 covers 000660 only; 000660 is SKHY's local leg; SKHY is forward-test-only.
    So there is no fold structure to ablate this in — not "we did not get to it".

    If lending data for a panel pair ever lands, `usable_in_panel_fit` stops being empty and
    this test fails, which is the correct moment to run the ablation for real."""
    st = U.ablation_status()
    assert st["usable_in_panel_fit"] == [], (
        f"lending data now covers fitted pair(s) {st['usable_in_panel_fit']} — run the "
        "ablation instead of documenting why it is impossible"
    )
    assert st["ablatable"] is False
    assert "TWSE SBL" in st["route_to_a_real_ablation"]


def test_financing_sheet_carries_the_public_borrow_state():
    from pipeline.hedging.sheets import financing_margin_sheet
    r = financing_margin_sheet("headroom 0").render()
    assert "BORROW STATE" in r
    assert "public half" in r


def test_the_ablation_runs_and_is_exactly_vacuous():
    """Stronger than the status check: run the in/out ablation and assert every delta is
    exactly zero. Toggling a family that reaches no fitted pair cannot change a metric, so a
    non-zero delta here would mean the feature is leaking in somewhere it should not be."""
    from pipeline.convergence.jorda import s4_metrics_table
    b = s4_metrics_table(horizons=(1,), families=("util",), use_features=False)
    x = s4_metrics_table(horizons=(1,), families=("util",), use_features=True)
    j = b.merge(x, on=["regime", "horizon"], suffixes=("_b", "_x"))
    assert (j.n_b == j.n_x).all()
    assert (j.rmse_x - j.rmse_b).abs().max() == 0.0, "util family is reaching a fitted pair"
    assert (j.r2_x - j.r2_b).abs().max() == 0.0
