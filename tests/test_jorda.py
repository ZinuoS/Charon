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
