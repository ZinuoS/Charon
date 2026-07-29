"""S4 metrics table. One check per property that would silently corrupt the deliverable."""
from __future__ import annotations

from pipeline.convergence.jorda import s4_metrics_table


def test_table_has_both_classes_and_a_labelled_pooled_row_last():
    df = s4_metrics_table(horizons=(1, 20))
    assert {"fungible", "one_way_constrained"} <= set(df.regime)
    assert df.regime.iloc[-1].startswith("POOLED"), "pooled must be last and labelled"
    assert not any(r.startswith("POOLED") for r in df.regime[:-2]), "pooled row mixed in"


def test_ablation_arms_score_identical_samples():
    """The first version of this ablation dropped rows when the macro column was added, so
    the in/out arms scored different samples -- RMSE 'improved' while R2 fell, which is only
    possible when the sample moves. Alignment now always includes the column; only its use
    as a feature is toggled."""
    a = s4_metrics_table(horizons=(1, 20), with_macro=False)
    b = s4_metrics_table(horizons=(1, 20), with_macro=True)
    j = a.merge(b, on=["regime", "horizon"], suffixes=("_a", "_b"))
    assert (j.n_a == j.n_b).all(), "ablation arms are not on identical folds"


def test_sign_hit_rate_scores_the_change_not_the_level():
    """Scoring the sign of the level would read ~100% for an almost-always-positive premium.
    A change-based hit rate has to sit near a coin flip, not near certainty."""
    df = s4_metrics_table(horizons=(1,))
    assert df.hit_rate.max() < 0.75, f"hit rate {df.hit_rate.max():.2f} looks like level-scoring"


def test_constrained_class_is_forecastable_and_the_control_is_not():
    """The mechanism's out-of-sample signature. If this inverts, the taxonomy is not
    describing what it claims to."""
    df = s4_metrics_table(horizons=(20,)).set_index("regime")
    assert df.loc["one_way_constrained", "r2"] > 0.5
    assert df.loc["fungible", "r2"] < 0.1


def test_skhy_never_enters_a_fit():
    from pipeline.convergence.jorda import FORWARD_TEST_PAIRS, _regime_series
    for series in _regime_series().values():
        for s in series:
            assert len(s) > 100, "a 12-point series would be SKHY leaking into the panel"
    assert "skhy" in FORWARD_TEST_PAIRS
