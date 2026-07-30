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
    a = s4_metrics_table(horizons=(1, 20), use_features=False)
    b = s4_metrics_table(horizons=(1, 20), use_features=True)
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
    for members in _regime_series().values():
        for pair, series in members:
            assert pair not in FORWARD_TEST_PAIRS, f"{pair} is forward-test-only"
            assert len(series) > 100, "a 12-point series would be SKHY leaking into the panel"
    assert "skhy" in FORWARD_TEST_PAIRS


def test_m5_and_m6_ablations_both_run_on_identical_folds():
    """Every arm must score one sample. Alignment includes the family in both arms; only its
    use as features is toggled."""
    for fams in (("m5",), ("m6",), ("m5", "m6")):
        b = s4_metrics_table(horizons=(1,), families=fams, use_features=False)
        x = s4_metrics_table(horizons=(1,), families=fams, use_features=True)
        j = b.merge(x, on=["regime", "horizon"], suffixes=("_b", "_x"))
        assert (j.n_b == j.n_x).all(), f"{fams} arms differ"


def test_m5_features_are_per_pair_local_not_000660():
    """M5 as specified ("000660 deep history") could never enter a panel fit: 000660 is
    SKHY's leg and SKHY is never fitted. Built per-pair instead."""
    from pipeline.convergence.jorda import _m5_features
    f = _m5_features("tsmc")
    assert list(f.columns) == ["rv20", "dd60"]
    assert f.rv20.dropna().gt(0).all(), "realized vol must be positive"
    assert f.dd60.dropna().le(1e-9).all(), "drawdown vs rolling max cannot be positive"


def test_change_target_is_a_different_and_harder_problem():
    """The level's R² is persistence. An RV expression is paid by the CHANGE, and for the
    class the trade is in that R² is negative — worse than forecasting no move. If this ever
    flips positive, something either improved or leaked, and both deserve a look."""
    lvl = s4_metrics_table(horizons=(20,), target="level").set_index("regime")
    chg = s4_metrics_table(horizons=(20,), target="change").set_index("regime")
    assert lvl.loc["one_way_constrained", "r2"] > 0.5
    assert chg.loc["one_way_constrained", "r2"] < 0.0


def test_permutation_placebo_collapses():
    """The full-stop diagnostic. Shuffled labels must destroy performance; if they do not,
    the folds leak and nothing downstream can be trusted."""
    p = s4_metrics_table(horizons=(20,), target="change", shuffle_seed=11)
    assert p.r2.max() < 0.02, f"placebo R² {p.r2.max():.4f} — harness is leaking"
    assert (p.hit_rate - 0.5).abs().max() < 0.05


def test_track_b_shares_track_a_folds_by_construction():
    """Not by two implementations agreeing — both consume jorda.fold_iter, so a divergence is
    impossible rather than merely tested for. This asserts the shared consumption."""
    import inspect
    from pipeline.convergence import voc
    assert "fold_iter" in inspect.getsource(voc.run)
    from pipeline.convergence.jorda import _oof_predictions
    assert "fold_iter" in inspect.getsource(_oof_predictions)


def test_track_b_placebo_collapses():
    """Full stop if this fails: a 60% hit rate on shuffled labels would mean the harness leaks."""
    from pipeline.convergence import voc
    p = voc.run("one_way_constrained", h=20, complexity=(2.0,), shrinkage=(1.0,), shuffle_seed=11)
    assert (p.hit_rate - 0.5).abs().max() < 0.03, f"placebo hit rate {p.hit_rate.max():.3f}"


def test_parsimony_beats_complexity_and_the_position_sign_is_right():
    """The session's verdict, pinned — and REWRITTEN after a sign error.

    The first version of this test asserted Track B's Sharpe and alpha were NEGATIVE. They were,
    because `strategy_diagnostics` built `pnl = -sign(pred) * y`: a strategy that faded its own
    forecast. The magnitude-decile table caught it — P&L was negative in every decile including
    buckets with a 67% hit rate, which is arithmetically impossible for a strategy trading WITH
    its signal.

    TRIPWIRE INTENT: a red run here means **re-open DEV-004**, not "fix the test". The deviation
    was granted on the premise that complexity did not win. If complexity starts winning, that
    premise is stale and the exception needs re-argument.
    """
    from pipeline.convergence.voc import strategy_diagnostics
    d = strategy_diagnostics("one_way_constrained", h=20)
    # Sanity on the sign convention itself: a >55% hit rate trading WITH the signal cannot
    # produce a negative Sharpe.
    assert d["sharpe_track_a"] > 0 and d["sharpe_track_b"] > 0, \
        "positive hit rates with negative Sharpe means the position sign is inverted again"
    assert d["sharpe_track_a"] > d["sharpe_track_b"], \
        "COMPLEXITY NOW BEATS PARSIMONY — re-open DEV-004 rather than adjusting this test"


def test_alpha_t_is_reported_with_overlap_correction():
    """t on h=20 overlapping returns must be HAC-corrected. The naive figure was 11.5; the
    honest one is ~5.3. Both are kept so the size of the correction stays auditable."""
    from pipeline.convergence.voc import strategy_diagnostics
    d = strategy_diagnostics("one_way_constrained", h=20)
    assert abs(d["track_b_t_alpha_hac"]) < abs(d["track_b_t_alpha_naive"]), \
        "HAC t is not smaller than naive t — the overlap correction is not biting"
    assert d["n_effective_blocks"] * 20 <= d["n"] * 1.05
