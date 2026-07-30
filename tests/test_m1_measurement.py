"""M1 measurement layer: config axes, ratio-awareness, and the asynchrony identity.

The premium formula's failure modes are covered in ``test_premium_formula.py``. What is
tested here is what M1 adds on top: that the two measurement axes behave as *axes*
(variants agree where they should and diverge where they should), that a ratio change is
handled rather than mistaken for a premium jump, and that the decomposition identity is
exact rather than approximate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.measurement import comparators, premium
from pipeline.measurement.asynchrony import (
    EQUITY_CLOSE_GAP_HOURS,
    FX_FIX_CALIBRATION,
    attribution_shares,
    decompose,
    event_window,
    fx_instant_band,
)
from pipeline.measurement.premium import compute_premium, variant_spread


def _s(pairs: dict[str, float]) -> pd.Series:
    return pd.Series(list(pairs.values()), index=pd.to_datetime(list(pairs.keys())))


DAYS = ["2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15"]
ADR = _s(dict(zip(DAYS, [100.0, 110.0, 105.0, 120.0])))
LOCAL = _s(dict(zip(DAYS, [1_000_000.0, 1_020_000.0, 1_010_000.0, 1_050_000.0])))
FX = _s(dict(zip(DAYS, [1000.0, 1010.0, 1005.0, 1020.0])))


class TestConfigAxesAreDeclared:
    def test_both_defaults_are_ratified_members_of_their_axis(self):
        """Was the inverse of this until 2026-07-29: it asserted NEITHER default was chosen,
        because an unratified default would silently become the measurement decision. Both are
        now ratified on measured evidence, so the guard becomes that they are real options
        rather than free text."""
        assert premium.DEFAULT_FX_LEG in premium.FX_LEGS
        assert premium.DEFAULT_CLOSE_DEF in premium.CLOSE_DEFS

    def test_yahoo_snapshot_is_not_an_fx_option(self):
        """Dropped deliberately: its snapshot instant was never documented, which is the
        property that made it unusable for an instant-sensitive measurement."""
        assert "yahoo_snapshot" not in premium.FX_LEGS

    def test_fx_legs_map_to_real_registry_series(self):
        from pipeline.ingest.registry import series_by_id
        for series_id in premium.FX_LEGS.values():
            assert series_by_id(series_id).asset_class == "fx"

    def test_both_close_definitions_exist_as_an_axis(self):
        assert set(premium.CLOSE_DEFS) == {"primary_official", "consolidated"}


class TestVariantEquivalenceAndDivergence:
    def test_identical_fx_inputs_give_identical_premium(self):
        """Where two variants share inputs they must agree exactly — otherwise the axis
        is introducing differences of its own."""
        a = compute_premium(ADR, LOCAL, FX, 0.1)
        b = compute_premium(ADR, LOCAL, FX.copy(), 0.1)
        pd.testing.assert_series_equal(a, b)

    def test_differing_fx_fix_diverges_by_the_fx_difference(self):
        """Deliberate-divergence fixture: a 50bp FX difference must move π by ~50bp and
        nothing else."""
        fx_b = FX * 1.005
        a = compute_premium(ADR, LOCAL, FX, 0.1)
        b = compute_premium(ADR, LOCAL, fx_b, 0.1)
        rel = ((1 + b) / (1 + a) - 1).abs()
        assert np.allclose(rel.values, 0.005, atol=1e-12)

    def test_close_definition_difference_propagates_one_for_one(self):
        """The 24.6bp close-definition gap must show up as ~24.6bp in π."""
        consolidated = ADR * 1.00246
        a = compute_premium(ADR, LOCAL, FX, 0.1)
        b = compute_premium(consolidated, LOCAL, FX, 0.1)
        rel = ((1 + b) / (1 + a) - 1)
        assert np.allclose(rel.values, 0.00246, atol=1e-12)

    def test_variant_spread_reports_basis_points(self):
        v1 = premium.PremiumVariant("skhy", "frankfurter", "primary_official",
                                    compute_premium(ADR, LOCAL, FX, 0.1), 4, None, None, 0, "x", True)
        v2 = premium.PremiumVariant("skhy", "fred", "primary_official",
                                    compute_premium(ADR, LOCAL, FX * 1.005, 0.1), 4, None, None, 0, "y", True)
        spread = variant_spread([v1, v2])
        assert len(spread) == 1
        assert spread.iloc[0]["mean_bp"] > 40  # ~50bp, scaled by (1+pi)


class TestRatioAwareness:
    def test_scalar_ratio_matches_series_ratio(self):
        const = pd.Series(0.1, index=ADR.index)
        pd.testing.assert_series_equal(
            compute_premium(ADR, LOCAL, FX, 0.1),
            compute_premium(ADR, LOCAL, FX, const),
        )

    def test_ratio_change_does_not_look_like_a_premium_jump(self):
        """The S3 Task 2.1 hazard: a depositary ratio change is indistinguishable from a
        premium jump unless the construction is ratio-aware by date.

        Here the ratio halves mid-sample and the ADR price halves with it — economically
        nothing happened, so a ratio-aware π must be flat.
        """
        adr = _s(dict(zip(DAYS, [100.0, 100.0, 50.0, 50.0])))
        local = _s(dict(zip(DAYS, [1_000_000.0] * 4)))
        fx = _s(dict(zip(DAYS, [1000.0] * 4)))
        ratio = _s(dict(zip(DAYS, [0.1, 0.1, 0.05, 0.05])))

        aware = compute_premium(adr, local, fx, ratio)
        assert np.allclose(aware.values, aware.values[0], atol=1e-12), "ratio-aware pi should be flat"

        naive = compute_premium(adr, local, fx, 0.1)
        assert abs(naive.iloc[2] - naive.iloc[1]) > 0.4, "naive pi should show a spurious ~50% jump"

    def test_ratio_history_not_covering_sample_start_raises(self):
        ratio = pd.Series([0.1], index=pd.to_datetime(["2026-07-14"]))
        with pytest.raises(ValueError, match="ratio history"):
            compute_premium(ADR, LOCAL, FX, ratio)


class TestAsynchronyIdentity:
    def test_identity_is_exact_not_approximate(self):
        d = decompose(ADR, LOCAL, FX)
        assert d.identity_max_error < 1e-12

    def test_components_sum_to_the_measured_change(self):
        d = decompose(ADR, LOCAL, FX)
        f = d.frame
        recomposed = f["adr_leg"] + f["fx_leg"] - f["local_leg"]
        pd.testing.assert_series_equal(f["d_ln_premium"], recomposed, check_names=False)

    def test_log_change_matches_the_premium_series_directly(self):
        """Cross-check against premium.py rather than only against itself."""
        pi = compute_premium(ADR, LOCAL, FX, 0.1)
        expected = np.log(1 + pi).diff().dropna()
        got = decompose(ADR, LOCAL, FX).frame["d_ln_premium"]
        assert np.allclose(expected.values, got.values, atol=1e-12)

    def test_two_fx_variants_measure_the_reducible_component(self):
        d = decompose(ADR, LOCAL, FX, FX * 1.003, "frankfurter", "fred")
        assert "fx_instant_artifact" in d.frame
        assert d.frame["irreducible_close_gap_hours"].eq(EQUITY_CLOSE_GAP_HOURS).all()

    def test_identical_fx_variants_give_zero_reducible_component(self):
        d = decompose(ADR, LOCAL, FX, FX.copy(), "a", "b")
        assert np.allclose(d.frame["fx_instant_artifact"].values, 0.0, atol=1e-15)

    def test_single_fx_variant_falls_back_to_calibration_and_says_so(self):
        d = decompose(ADR, LOCAL, FX)
        assert "fx_instant_artifact" not in d.frame
        assert any("Calibrated on CHANGES" in n for n in d.notes)
        assert "fx_instant_artifact_bp_calibrated_change_p95" in d.summary()

    def test_irreducibility_is_always_stated(self):
        for d in (decompose(ADR, LOCAL, FX), decompose(ADR, LOCAL, FX, FX * 1.001)):
            assert any("IRREDUCIBLE" in n for n in d.notes)

    def test_empty_overlap_is_handled(self):
        other = _s({"2020-01-02": 1.0})
        assert decompose(ADR, other, FX).frame.empty


class TestCalibration:
    def test_change_calibration_exceeds_level_calibration(self):
        """Differencing two independently-noisy fixes amplifies rather than cancels, so
        the change-basis artifact must be larger than the level-basis one. This is why
        the decomposition quotes the change figure."""
        assert fx_instant_band("change_mean_abs") > fx_instant_band("mean")
        assert fx_instant_band("change_p95_abs") > fx_instant_band("p95")

    def test_calibration_records_which_fixes_it_came_from(self):
        assert "ECB" in FX_FIX_CALIBRATION["fix_a"]
        assert "noon New York" in FX_FIX_CALIBRATION["fix_b"]
        assert FX_FIX_CALIBRATION["n_days"] > 2000

    def test_unknown_stat_raises(self):
        with pytest.raises(KeyError):
            fx_instant_band("not_a_stat")


class TestHelpers:
    def test_event_window_brackets_the_target_day(self):
        w = event_window(decompose(ADR, LOCAL, FX), "2026-07-14", before=1, after=1)
        assert len(w) <= 3

    def test_attribution_shares_are_labelled_as_non_summing(self):
        shares = attribution_shares(decompose(ADR, LOCAL, FX))
        assert "need not sum to 1" in shares["note"]


class TestComparatorsShareTheCodePath:
    def test_comparator_premium_is_literally_the_same_function(self):
        """README §8 makes D6 the training universe and SKHY a forward test, which is only
        valid if both are measured identically. Shared identity, not shared intent."""
        assert comparators.compute_premium is premium.compute_premium

    def test_skhy_is_rejected_as_a_comparator(self):
        with pytest.raises(ValueError, match="forward-test"):
            comparators.build_comparator("skhy")

    def test_skhy_absent_from_the_comparator_list(self):
        assert "skhy" not in comparators.COMPARATOR_PAIRS


class TestRatifiedDefaults:
    """RATIFIED 2026-07-29. These tests guard the reasoning, not the taste."""

    def test_fx_leg_default_is_the_fresher_series(self):
        """frankfurter was chosen because FRED H.10 is a weekly release and lags. If that
        ever inverts, the ratification is stale and this fails rather than quietly shipping
        a default chosen on last year's coverage."""
        from pipeline.measurement.premium import DEFAULT_FX_LEG, FX_LEGS, _load_close
        assert DEFAULT_FX_LEG in FX_LEGS
        chosen = _load_close("d1_prices", FX_LEGS[DEFAULT_FX_LEG])
        for name, sid in FX_LEGS.items():
            if name == DEFAULT_FX_LEG:
                continue
            other = _load_close("d1_prices", sid)
            assert chosen.index[-1] >= other.index[-1], \
                f"{name} is now fresher than the ratified default {DEFAULT_FX_LEG}"

    def test_close_def_labels_still_agree_so_the_choice_is_still_inert(self):
        """`consolidated` is a declared but EMPTY slot: both labels read the same column, so
        DEFAULT_CLOSE_DEF describes the landed data rather than choosing between options.

        This test FAILS the day a real consolidated series lands — which is exactly when the
        ratification needs revisiting, and when the 24.6bp gap becomes testable instead of
        merely hypothesised."""
        from pipeline.ingest.registry import PAIRS
        from pipeline.measurement.premium import CLOSE_DEFS, DEFAULT_CLOSE_DEF, build_variant
        assert DEFAULT_CLOSE_DEF in CLOSE_DEFS
        spec = next(p for p in PAIRS if p.pair_id == "skhy")
        a = build_variant(spec, "frankfurter", "primary_official").series
        b = build_variant(spec, "frankfurter", "consolidated").series
        assert a.equals(b), (
            "close_def is no longer inert — a consolidated series has landed. Revisit "
            "DEFAULT_CLOSE_DEF and test the 24.6bp gap instead of hypothesising it."
        )

    def test_no_ratify_todo_survives_in_the_measurement_layer(self):
        from pathlib import Path
        src = (Path(__file__).resolve().parents[1] / "pipeline" / "measurement" / "premium.py").read_text()
        assert "TODO(ash: ratify)" not in src
