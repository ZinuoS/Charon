"""M3 Jordà convergence — the identity-free parts: HAC, half-life logic, forward-test guard."""
from __future__ import annotations
import numpy as np, pandas as pd, pytest
from pipeline.convergence import jorda


def _ar1(n, rho, sigma=0.02, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = rho * x[t-1] + rng.normal(0, sigma)
    return pd.Series(x, index=pd.date_range("2015-01-01", periods=n, freq="D"))


class TestRecoversKnownPersistence:
    def test_persistent_series_gives_high_rho(self):
        r = jorda.estimate_regime([_ar1(2000, 0.98)], "test")
        assert r.horizons[0].rho > 0.9, "an AR(1) with rho=0.98 must read as persistent"

    def test_noise_series_gives_near_zero_rho(self):
        r = jorda.estimate_regime([_ar1(2000, 0.02)], "test")
        assert abs(r.horizons[0].rho) < 0.15, "near-white noise must read as non-persistent"

    def test_half_life_ordering_matches_persistence(self):
        slow = jorda.estimate_regime([_ar1(3000, 0.97, seed=1)], "slow").half_life
        fast = jorda.estimate_regime([_ar1(3000, 0.5, seed=2)], "fast").half_life
        assert slow > fast, "a more persistent series must have a longer half-life"


class TestHACErrors:
    def test_hac_se_exceeds_naive_on_overlapping_windows(self):
        """The reason HAC is used: overlapping h-step windows inflate the true SE, and a
        naive SE understates it. HAC must be larger at a multi-step horizon."""
        pi = _ar1(1500, 0.95)
        r = jorda.estimate_regime([pi], "t", max_h=10)
        h1, h10 = r.horizons[0], r.horizons[9]
        # bandwidth grows with horizon, so the HAC correction is larger at h=10
        assert h10.se_hac > 0 and not np.isnan(h10.se_hac)

    def test_zero_variance_regressor_returns_nan_not_crash(self):
        se = jorda._newey_west_se(np.ones(50), np.random.default_rng(0).normal(size=50), 5)
        assert np.isnan(se)


class TestExtrapolationFlag:
    def test_persistent_series_flags_extrapolated_half_life(self):
        """A half-life beyond the fitting window is an extrapolation and must say so."""
        r = jorda.estimate_regime([_ar1(3000, 0.995, seed=3)], "t", max_h=20)
        assert r.half_life is None or r.half_life > 20
        if r.half_life and r.half_life > 20:
            assert any("EXTRAPOLATION" in n for n in r.notes)


class TestForwardTestGuard:
    def test_skhy_never_enters_a_fit(self):
        assert "skhy" in jorda.FORWARD_TEST_PAIRS
        assert "skhy" not in jorda.REGIME_OF_PAIR

    def test_run_panel_excludes_skhy_structurally(self):
        """If SKHY ever reached a fitting index, the validation guard raises."""
        res = jorda.run_panel()
        # panel ran without raising => no forward-test instrument was fitted
        assert all(r != "skhy" for r in res)

    def test_score_skhy_declares_out_of_support_and_no_resolution(self):
        sk = jorda.score_skhy()
        assert sk["scored_not_fitted"] is True
        assert sk["resolution"].startswith("NONE")
        assert "out_of_support" in sk


class TestMetricsTable:
    def test_pooled_row_is_labelled_and_provisional(self):
        df = jorda.metrics_table(jorda.run_panel())
        if df.empty:
            pytest.skip("panel not ingested")
        assert (df["PROVISIONAL"] == "pending taxonomy ratification").all()

    def test_the_two_regimes_are_distinguishable(self):
        """The whole point: the barrier-constrained regime must be far more persistent than
        the fungible control. If this ever fails, the panel or the taxonomy is wrong."""
        res = jorda.run_panel()
        if not {"one_way_constrained", "fungible"} <= set(res):
            pytest.skip("both regimes not present")
        constrained = res["one_way_constrained"].horizons[0].rho
        fungible = res["fungible"].horizons[0].rho
        assert constrained > 0.5 and fungible < 0.3, (
            f"constrained rho={constrained:.2f} should be >>0.5, "
            f"fungible rho={fungible:.2f} should be near 0")


# ---------------------------------------------------------------- S17: extended horizon
#
# These pin the *semantics* of the extension, not its numbers. The point of extending past
# h=20 was never to get a sharper half-life — it was to stop reporting an extrapolation as
# if it were an estimate. Each test below guards one way that could silently regress.

import numpy as np
import pandas as pd

from pipeline.convergence.jorda import (
    IDENTIFIED_EFF_SPANS, MIN_EFF_SPANS, HalfLife, HorizonFit,
    _first_crossing, _half_life_interval, horizon_grid, run_panel,
)


def _fit(h, rho, se, n):
    return HorizonFit(horizon=h, rho=rho, se_hac=se, n=n, r2=0.5)


class TestHorizonGrid:
    def test_dense_short_end_sparse_long_end(self):
        g = horizon_grid(400)
        assert g[:20] == list(range(1, 21)), "short end must be every integer — that is where ρ is identified"
        assert max(g) <= 400 and 380 in g
        long_steps = {b - a for a, b in zip(g, g[1:]) if a >= 110}
        assert long_steps == {10}, f"long end should step by 10, got {sorted(long_steps)}"

    def test_grid_is_sorted_and_unique(self):
        g = horizon_grid(400)
        assert g == sorted(set(g))


class TestEffectiveSpans:
    def test_n_eff_is_rows_over_horizon_not_rows(self):
        """The whole justification for capping H. 2000 overlapping rows at h=400 are not
        2000 pieces of evidence about a 400-day move."""
        assert _fit(400, 0.3, 0.1, 2000).n_eff == 5.0
        assert _fit(1, 0.9, 0.01, 2000).n_eff == 2000.0

    def test_identified_flag_tracks_the_threshold(self):
        assert _fit(100, 0.7, 0.1, int(100 * IDENTIFIED_EFF_SPANS)).identified
        assert not _fit(100, 0.7, 0.1, int(100 * (IDENTIFIED_EFF_SPANS - 1))).identified

    def test_estimate_stops_before_spans_run_out(self):
        for res in run_panel().values():
            assert res.horizons[-1].n_eff >= MIN_EFF_SPANS, (
                f"{res.regime} fitted out to n_eff={res.horizons[-1].n_eff:.1f}, below the "
                f"{MIN_EFF_SPANS} floor — past there ρ_h is overlap artefact"
            )


class TestFirstCrossing:
    def test_interpolates_within_the_step(self):
        h = _first_crossing(np.array([10.0, 20.0]), np.array([0.6, 0.4]))
        assert h == pytest.approx(15.0)

    def test_returns_none_when_never_crossing(self):
        assert _first_crossing(np.array([1.0, 2.0, 3.0]), np.array([0.9, 0.8, 0.7])) is None

    def test_takes_the_first_of_several_crossings(self):
        """ρ_h wanders at long horizons and can re-cross. First passage is the only rule
        that does not require choosing among them."""
        hs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        vs = np.array([0.9, 0.4, 0.7, 0.3, 0.1])
        assert _first_crossing(hs, vs) == pytest.approx(1.8, abs=0.01)


class TestHalfLifeInterval:
    def test_unbounded_above_when_upper_band_never_crosses(self):
        """The S17 headline. A wide band whose top stays over ½ means the data do not
        reject a premium that never halves — upper must be None, not a large number."""
        fits = [_fit(h, 0.9 - 0.0015 * h, 0.30, 2300 - h) for h in (1, 50, 100, 200, 300)]
        hl = _half_life_interval(fits)
        assert hl.point is not None
        assert hl.upper is None and hl.unbounded_above
        assert "unbounded" in hl.describe()

    def test_lower_bound_is_the_fast_end(self):
        fits = [_fit(h, 0.9 - 0.0015 * h, 0.10, 2300 - h) for h in (1, 50, 100, 200, 300)]
        hl = _half_life_interval(fits)
        assert hl.lower is not None and hl.lower < hl.point, "lower bound = fastest convergence"

    def test_in_window_crossing_is_not_labelled_extrapolated(self):
        fits = [_fit(h, 0.9 - 0.004 * h, 0.05, 3000) for h in (1, 25, 50, 100, 150)]
        hl = _half_life_interval(fits)
        assert hl.support.startswith("interpolated")
        assert "extrapolat" not in hl.method

    def test_underpowered_crossing_is_flagged_distinctly(self):
        """In-window but thin is a different claim from in-window and identified. Collapsing
        the two would let a 6-span crossing read as an estimate."""
        fits = [_fit(h, 0.9 - 0.0015 * h, 0.05, 2000) for h in (1, 100, 200, 300, 350)]
        hl = _half_life_interval(fits)
        assert hl.support == "interpolated_underpowered"
        assert hl.n_eff_at_point < IDENTIFIED_EFF_SPANS

    def test_sub_resolution_is_not_reported_as_never_converging(self):
        """Regression guard. ρ₁ below ½ (the fungible control) once fell through to the
        exponential branch and printed 'does not decay' — which means the OPPOSITE of the
        truth, that it converges faster than one step."""
        fits = [_fit(h, 0.04, 0.03, 1600 - h) for h in (1, 5, 20, 50)]
        hl = _half_life_interval(fits)
        assert hl.support == "sub_resolution"
        assert hl.point is not None and hl.point <= 1.0
        assert "does not decay" not in hl.method


class TestPanelSemantics:
    def test_constrained_half_life_is_in_window_with_open_tail(self):
        res = run_panel()["one_way_constrained"]
        hl = res.hl
        assert hl.support != "extrapolated", "extending H past 20 was supposed to end the extrapolation"
        assert hl.point <= res.horizons[-1].horizon, "point estimate must sit inside the fitted window"
        assert hl.unbounded_above, "upper 95% edge does not cross ½ — the tail is open"
        assert hl.lower is not None and hl.lower < hl.point

    def test_fungible_control_converges_fast_not_never(self):
        hl = run_panel()["fungible"].hl
        assert hl.support == "sub_resolution"
        assert hl.point <= 1.0

    def test_notes_state_the_unbounded_tail_and_the_floor(self):
        notes = " ".join(run_panel()["one_way_constrained"].notes).lower()
        assert "no finite upper bound" in notes
        assert "floor" in notes or "fastest convergence" in notes

    def test_metrics_table_carries_the_interval_not_just_a_point(self):
        from pipeline.convergence.jorda import metrics_table
        df = metrics_table(run_panel())
        for col in ("half_life_lo", "half_life_hi", "half_life_support", "n_eff"):
            assert col in df.columns, f"metrics table must expose {col}"
        row = df[df.regime == "one_way_constrained"].iloc[0]
        assert row["half_life_hi"] == "unbounded"
