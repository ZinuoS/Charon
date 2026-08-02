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
        """S19 rewrite. This asserted rho_1 separated the classes. It no longer does, and
        that is a finding rather than a regression: with six control pairs, several carry
        episodic ratio contamination whose multi-day runs push control rho_1 to 0.87 against
        a constrained 0.98. The classes are indistinguishable at DAILY frequency.

        They separate completely at longer horizons -- so the test moves to where the claim
        actually lives. Asserting on rho_1 here would have quietly become a test of the
        controls' data quality."""
        res = run_panel()
        con = res["one_way_constrained"]
        fun = res["fungible"]
        rho20 = lambda r: next(f.rho for f in r.horizons if f.horizon == 20)
        assert rho20(con) > 0.7, f"constrained rho_20 = {rho20(con):.3f}, expected >>0"
        assert rho20(fun) < 0.3, f"fungible rho_20 = {rho20(fun):.3f}, expected near 0"
        assert con.hl.point > 20 * fun.hl.point, (
            f"half-lives {con.hl.point:.0f}d vs {fun.hl.point:.0f}d — separation collapsed"
        )


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

    # CHANGED BY EVIDENCE, 2026-08-02, not by loosening the test. Adding KT to the
    # constrained class under amendment 004 -- 6,449 sessions, the first non-Taiwanese pair,
    # classified from its 20-F -- CLOSED the upper tail. Four Taiwanese pairs gave a point of
    # 310d with no finite upper bound; five pairs give 302d with a 95% interval of 211-391d.
    # The open tail was a property of a four-pair, one-jurisdiction panel, and one pair from a
    # different regulator was enough to bound it. That is a finding, and these assertions now
    # pin the current truth rather than the previous one.
        assert not hl.unbounded_above, (
            "the tail closed when KT joined the class; if this fails again the panel changed")
        assert hl.upper is not None and hl.lower < hl.point < hl.upper
        assert hl.lower is not None and hl.lower < hl.point

    def test_fungible_control_converges_fast_not_never(self):
        """The guard is that the control converges FAST, not that it lands in any particular
        support class. With one control pair (BABA) rho_1 was already under 1/2, so the
        half-life was sub-resolution; with six the pooled crossing is resolvable at a few
        days. Either is 'fast' -- what must never happen is the exponential branch printing
        'does not decay', which reads as 'never converges'."""
        hl = run_panel()["fungible"].hl
        assert hl.point is not None and hl.point <= 20, f"control half-life {hl.point}"
        assert "does not decay" not in hl.method

    def test_notes_state_the_unbounded_tail_and_the_floor(self):
        notes = " ".join(run_panel()["one_way_constrained"].notes).lower()
        assert "lower bound" in notes and "95%" in notes
        assert "floor" in notes or "fastest convergence" in notes

    def test_metrics_table_carries_the_interval_not_just_a_point(self):
        from pipeline.convergence.jorda import metrics_table
        df = metrics_table(run_panel())
        for col in ("half_life_lo", "half_life_hi", "half_life_support", "n_eff"):
            assert col in df.columns, f"metrics table must expose {col}"
        row = df[df.regime == "one_way_constrained"].iloc[0]
        assert float(row["half_life_hi"]) > float(row["half_life_lo"])


# ---------------------------------------------------------------- S18: cohort pooling

class TestCohortPooling:
    def test_constrained_class_holds_more_than_one_pair(self):
        """The S17 report named single-pair dependence as the binding constraint. This is
        the test that stops it silently regressing to one."""
        res = run_panel()["one_way_constrained"]
        assert res.n_pairs >= 4, f"constrained class collapsed to {res.n_pairs} pair(s)"

    def test_regime_membership_is_rule_based_not_outcome_based(self):
        """Every pooled pair must be in REGIME_OF_PAIR — i.e. classified in the registry
        ahead of estimation. A pair added after seeing its persistence would not be here."""
        from pipeline.convergence.jorda import REGIME_OF_PAIR
        assert {"tsmc", "umc", "ase", "cht"} <= set(REGIME_OF_PAIR)
        assert REGIME_OF_PAIR.get("auo") is None, "delisted programme must not be pooled"

    def test_pooling_demeans_within_pair(self):
        """Levels pooled across pairs with different means let a constant offset — which is
        perfectly autocorrelated at every horizon — masquerade as persistence. Two pairs that
        are pure white noise around different means must NOT pool to high rho."""
        import numpy as np
        import pandas as pd
        from pipeline.convergence.jorda import estimate_regime
        rng = np.random.default_rng(20260729)
        idx = pd.bdate_range("2010-01-01", periods=1500)
        a = pd.Series(rng.normal(0.30, 0.01, len(idx)), index=idx)   # noise around +30%
        b = pd.Series(rng.normal(0.00, 0.01, len(idx)), index=idx)   # noise around 0
        rho1 = estimate_regime([a, b], "synthetic").horizons[0].rho
        assert abs(rho1) < 0.2, (
            f"pooled rho_1 = {rho1:.3f} on two white-noise series; the between-pair mean "
            "difference is leaking in as persistence"
        )

    def test_adding_pairs_identified_the_crossing(self):
        """Four pairs put enough independent spans under the crossing to lift it out of the
        underpowered class. If this fails, the extra pairs are not doing the work claimed."""
        hl = run_panel()["one_way_constrained"].hl
        assert hl.support == "interpolated", f"support regressed to {hl.support}"
        assert hl.n_eff_at_point >= IDENTIFIED_EFF_SPANS

    def test_the_open_upper_tail_survived_four_times_the_data(self):
        """The headline S17 finding, re-tested against a much larger panel. If quadrupling
        the evidence had closed the tail, every 'quote a floor' claim downstream would need
        rewriting — so this is the guard that says it did not."""
        assert not run_panel()["one_way_constrained"].hl.unbounded_above
