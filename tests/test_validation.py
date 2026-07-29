"""Validation layer: splitters and the four leakage detectors, on synthetic fixtures.

Each leakage test is written against a deliberately leaky fixture with a known answer.
A detector that has never been shown a leak is a detector nobody knows works.
"""
from __future__ import annotations
import numpy as np, pandas as pd, pytest
from pipeline.validation.splitters import (
    LeakageError, Split, assert_availability_respected, assert_filtered_not_smoothed,
    assert_no_forward_test_instrument, assert_scaler_fitted_on_train_only,
    expanding_walk_forward, purged_kfold, split_report,
)


class TestWalkForward:
    def test_training_never_reaches_past_the_test_block(self):
        for s in expanding_walk_forward(200, 5):
            assert len(s.train) == 0 or s.train.max() < s.test.min()

    def test_training_window_expands(self):
        sizes = [len(s.train) for s in expanding_walk_forward(200, 5)]
        assert sizes == sorted(sizes) and sizes[-1] > sizes[0]

    def test_embargo_shrinks_training(self):
        a = [len(s.train) for s in expanding_walk_forward(200, 5, embargo=0)]
        b = [len(s.train) for s in expanding_walk_forward(200, 5, embargo=10)]
        assert all(y <= x for x, y in zip(a, b)) and sum(b) < sum(a)

    def test_overlapping_split_is_rejected_at_construction(self):
        with pytest.raises(LeakageError):
            Split(np.array([1, 2, 3]), np.array([3, 4]), 0)


class TestPurgedKFold:
    def test_no_train_label_window_touches_test(self):
        H = 5
        for s in purged_kfold(120, 4, label_horizon=H):
            t0, t1 = s.test.min(), s.test.max()
            for i in s.train:
                assert not (i + H - 1 >= t0 and i <= t1), \
                    f"index {i}'s label window overlaps test [{t0},{t1}]"

    def test_longer_horizon_purges_more(self):
        short = sum(len(s.train) for s in purged_kfold(200, 5, label_horizon=1))
        long_ = sum(len(s.train) for s in purged_kfold(200, 5, label_horizon=20))
        assert long_ < short

    def test_embargo_removes_the_band_after_test(self):
        E = 7
        for s in purged_kfold(200, 5, label_horizon=1, embargo=E):
            t1 = s.test.max()
            assert not any(t1 < i <= t1 + E for i in s.train)

    def test_every_observation_is_tested_exactly_once(self):
        tested = np.concatenate([s.test for s in purged_kfold(100, 5)])
        assert sorted(tested) == list(range(100))

    def test_zero_horizon_rejected(self):
        with pytest.raises(ValueError):
            list(purged_kfold(50, 3, label_horizon=0))


class TestForwardTestExclusion:
    def test_skhy_in_a_fitting_index_raises(self):
        """README §8 is structural here, not a convention someone remembers."""
        with pytest.raises(LeakageError, match="forward-test instrument"):
            assert_no_forward_test_instrument(["tsmc", "baba", "skhy"])

    def test_panel_without_skhy_passes(self):
        assert_no_forward_test_instrument(["tsmc", "baba", "infy"])

    def test_case_insensitive(self):
        with pytest.raises(LeakageError):
            assert_no_forward_test_instrument(["SKHY"])


class TestAvailabilityFirewall:
    def test_feature_published_after_the_decision_is_caught(self):
        ts = pd.Series(pd.to_datetime(["2026-07-28 20:15", "2026-07-29 06:45"]))
        with pytest.raises(LeakageError, match="not yet public"):
            assert_availability_respected(ts, pd.Timestamp("2026-07-29 00:00"))

    def test_all_features_public_before_decision_passes(self):
        ts = pd.Series(pd.to_datetime(["2026-07-27 20:15", "2026-07-28 06:45"]))
        assert_availability_respected(ts, pd.Timestamp("2026-07-29 00:00"))

    def test_boundary_is_exclusive(self):
        """A feature published AT the decision instant is not yet usable."""
        ts = pd.Series(pd.to_datetime(["2026-07-29 00:00"]))
        with pytest.raises(LeakageError):
            assert_availability_respected(ts, pd.Timestamp("2026-07-29 00:00"))


class TestScalerLeak:
    def test_full_sample_scaler_is_caught(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=500)
        full = {"mean": float(x.mean()), "std": float(x.std())}
        with pytest.raises(LeakageError, match="fitted on all data"):
            assert_scaler_fitted_on_train_only(full, full)

    def test_train_only_scaler_passes(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=500)
        train = {"mean": float(x[:300].mean()), "std": float(x[:300].std())}
        full = {"mean": float(x.mean()), "std": float(x.std())}
        assert_scaler_fitted_on_train_only(train, full)


class TestFilteredNotSmoothed:
    def test_smoothed_probabilities_rejected(self):
        p = pd.DataFrame({"regime_0": [0.4, 0.6], "regime_1": [0.6, 0.4]})
        with pytest.raises(LeakageError, match="smoothed"):
            assert_filtered_not_smoothed(p, is_smoothed=True)

    def test_filtered_probabilities_pass(self):
        p = pd.DataFrame({"regime_0": [0.4, 0.6], "regime_1": [0.6, 0.4]})
        assert_filtered_not_smoothed(p, is_smoothed=False)

    def test_empty_frame_rejected(self):
        p = pd.DataFrame({"regime_0": [np.nan, np.nan]})
        with pytest.raises(LeakageError, match="empty"):
            assert_filtered_not_smoothed(p, is_smoothed=False)


class TestReport:
    def test_report_surfaces_purge_cost(self):
        splits = list(purged_kfold(100, 4, label_horizon=5, embargo=3))
        df = split_report(splits, 100)
        assert (df["purged_or_embargoed"] > 0).all(), "purge cost must be visible, not silent"
        assert len(df) == 4
