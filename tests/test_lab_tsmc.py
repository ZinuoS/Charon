"""The TSMC lab's guards — the deep history's provenance, and the claims that quote it.

Three classes of test here, and the middle one is the reason the file exists:

1.  **Provenance.** The deep extension is admitted only because the aggregator agrees with
    the listing venue over the whole overlap. If that stops being true, the registry's
    provider ordering must be reverted, so the agreement is a test rather than a note.
2.  **No re-admission of the artefact.** The pre-2005 sample is excluded for a corporate-action
    reason. A future widening of the sample would silently re-admit a -55% premium, so both
    the restriction and the only sanctioned override are pinned.
3.  **Constants that must equal their own estimators.** `FX_COEF_EMPIRICAL` is a cached
    regression result. A cached number that drifts from the thing it caches is worse than no
    cache, so the test recomputes it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.ingest._common import RAW_ROOT
from pipeline.ingest.reconcile import reconcile
from pipeline.ingest.registry import PAIRS, series_by_id
from pipeline.lab import tsmc as L


def _spec():
    return next(p for p in PAIRS if p.pair_id == "tsmc")


# --------------------------------------------------------------------------------
# 1. Provenance of the deep history
# --------------------------------------------------------------------------------


@pytest.mark.parametrize("series_id,venue", [("tsm_adr_daily", "nasdaq"),
                                             ("tsmc_local_daily", "twse")])
def test_eodhd_is_preferred_and_the_listing_venue_is_still_routed(series_id, venue):
    """Depth came from a reordering, not a new source. Both providers stay in the chain."""
    spec = series_by_id(series_id)
    assert spec.providers[0] == "eodhd", (
        f"{series_id}: the deep history depends on eodhd being preferred. Reverting this "
        "ordering is legitimate ONLY if the overlap agreement test below fails."
    )
    assert venue in spec.providers, (
        f"{series_id}: {venue} must stay routed — it is the corroborating source, and "
        "dropping it would leave the deep history uncheckable."
    )


@pytest.mark.parametrize("series_id,venue", [("tsm_adr_daily", "nasdaq"),
                                             ("tsmc_local_daily", "twse")])
def test_deep_history_agrees_with_the_listing_venue_over_the_whole_overlap(series_id, venue):
    """The aggregator's closes must match the venue's on every shared date, to the cent.

    This is the entire justification for preferring an aggregator over a listing venue. It
    passed at max_rel_diff == 0.0 on 2,513 (ADR) and 4,060 (local) shared dates when the
    ordering was changed on 2026-07-30.
    """
    parts = sorted([p for p in (RAW_ROOT / "d6_comparators").iterdir()
                    if (p / f"{series_id}.csv").exists()], key=lambda p: p.name)
    if len(parts) < 2:
        pytest.skip(f"{series_id}: only one partition on disk, nothing to corroborate against")

    new = pd.read_csv(parts[-1] / f"{series_id}.csv", parse_dates=["date"])
    prev = None
    for p in reversed(parts[:-1]):
        f = pd.read_csv(p / f"{series_id}.csv", parse_dates=["date"])
        if len(f) and f["date"].min() > new["date"].min():
            prev = f
            break
    if prev is None:
        pytest.skip(f"{series_id}: no shallower partition to corroborate against")

    r = reconcile(new, prev, series_id, "eodhd", venue)
    assert r.overlap_days > 2000, f"{series_id}: only {r.overlap_days} shared dates"
    assert not r.mismatches, (
        f"{series_id}: eodhd and {venue} disagree on {len(r.mismatches)} shared dates "
        f"(max {r.max_rel_diff:.2%}). The deep extension is no longer corroborated — revert "
        "the provider ordering in the registry rather than loosening this tolerance."
    )


# --------------------------------------------------------------------------------
# 2. The excluded era stays excluded
# --------------------------------------------------------------------------------


def test_sample_restriction_is_declared_with_its_reason():
    spec = _spec()
    assert spec.sample_start == "2005-01-03"
    assert spec.sample_reason and "stock-dividend" in spec.sample_reason
    assert L.CAUSE_BASED_START in spec.sample_reason, (
        "the cause-based alternative must be named in the registry, so the conservative "
        "choice is visible as a choice"
    )


def test_the_excluded_era_really_is_broken():
    """The screen has to be justified by the artefact, not asserted. Rebuild it and look."""
    from pipeline.measurement.premium import _load_close, compute_premium
    spec = _spec()
    legs = [_load_close("d6_comparators", s) for s in (spec.adr, spec.local, spec.fx)]
    pi = compute_premium(*legs, spec.local_shares_per_adr)
    early = pi[pi.index < "2002-01-01"]
    if not len(early):
        pytest.skip("pre-2002 history not on disk")
    assert early.mean() < -0.20, (
        f"pre-2002 mean premium is {early.mean():.1%}. The exclusion was justified by an "
        "economically impossible level; if that level is gone the reason must be rewritten."
    )


def test_only_the_documented_override_can_widen_the_sample():
    assert L.premium().index[0] == pd.Timestamp("2005-01-03")
    assert L.premium(L.CAUSE_BASED_START).index[0] == pd.Timestamp(L.CAUSE_BASED_START)
    with pytest.raises(AssertionError, match="sanctioned override"):
        L.legs("1997-10-08")


def test_curation_sensitivity_reports_both_starts_and_does_not_flatter():
    s = L.curation_sensitivity()
    assert len(s) == 2
    wide = s[s["sample"].str.contains("cause-based")].iloc[0]
    narrow = s[s["sample"].str.contains("registry")].iloc[0]
    assert wide.n_obs > narrow.n_obs
    # Not a requirement of nature, but it IS the current fact, and if the wider sample ever
    # becomes the more favourable one the notebook's argument has to be rewritten.
    assert wide.frac_beats_carry <= narrow.frac_beats_carry, (
        "the wider sample is now MORE favourable than the restricted one, which inverts the "
        "curation argument in notebook 09 §1.0a — rewrite it rather than deleting this test"
    )


# --------------------------------------------------------------------------------
# 3. Episodes, outcomes, excursions
# --------------------------------------------------------------------------------


def test_reversal_walk_alternates_before_the_min_days_filter():
    d = list(L.episodes(L.premium(), 5.0, 0)["direction"])
    assert len(d) > 50
    assert all(a != b for a, b in zip(d, d[1:]))


def test_min_days_filter_reports_what_it_dropped():
    ep = L.episodes(L.premium(), 5.0, 10)
    assert ep.attrs["dropped_short"] > 0
    assert ep.attrs["n_swings_before_min_days"] == len(ep) + ep.attrs["dropped_short"]


def test_resolution_channel_is_an_identity_not_a_regression():
    f = L.legs()
    ch = L.resolution_channel(f, L.episodes(f["pi"], 5.0, 10))
    assert ch["identity_residual"].abs().max() < 1e-9


def test_raw_swing_count_falls_as_the_reversal_threshold_rises():
    """Monotone in the WALK's threshold, which is the invariant that actually exists.

    The post-filter count is NOT monotone -- at min_days=5 the 3pp rule reports 355 episodes
    against the 2pp rule's 346. That is the two-part rule behaving correctly, not the walk
    misbehaving: a larger reversal threshold produces fewer but LONGER swings, so a smaller
    share of them is dropped by min_days. Asserting monotonicity on the reported count would
    have been asserting something false about a correct census, which is why the invariant is
    stated on the raw swing count instead.
    """
    cen = L.census()
    for md in cen.min_days.unique():
        d = cen[cen.min_days == md].sort_values("min_move_pp")
        raw = d.n_episodes + d.dropped_short
        assert (raw.diff().dropna() <= 0).all(), (
            f"min_days={md}: a larger reversal threshold produced MORE raw swings, which "
            "means the reversal walk is not monotone in its own threshold"
        )


def test_entry_percentile_is_expanding_and_cannot_see_its_own_future():
    pi = L.premium()
    pct = L.expanding_pctile(pi)
    assert pct.iloc[:L.PCTILE_WARMUP_D - 1].isna().all(), "warmup must be masked"
    # Recompute one point from its own past only.
    i = 3000
    manual = float((pi.iloc[:i + 1] <= pi.iloc[i]).mean())
    assert abs(manual - float(pct.iloc[i])) < 1e-12


def test_higher_carry_never_increases_the_fraction_that_beats_carry():
    eo = L.entry_outcomes(L.premium(), pctiles=(0.90,), horizons=(252,))
    m = eo.set_index("bracket")
    assert m.loc["low", "frac_beats_carry"] >= m.loc["mid", "frac_beats_carry"] \
        >= m.loc["high", "frac_beats_carry"]


def test_every_grid_cell_is_reported():
    """No selection: the grid's size is the product of its axes, not a filtered subset."""
    eo = L.entry_outcomes(L.premium())
    assert len(eo) == len(L.ENTRY_PCTILES) * len(L.HORIZONS_D) * 3


def test_excursions_are_non_negative_and_stop_curves_are_monotone():
    ex = L.excursions(L.premium())
    assert (ex.attrs["mae_pp"] >= 0).all(), "an adverse excursion cannot be negative"
    assert (ex.frac_stopped.diff().dropna() <= 0).all()
    assert (ex.frac_stopped_but_would_have_won <= ex.frac_stopped).all()


def test_skhy_week_one_exceeds_the_comparators_worst_case():
    """The project's most quotable number. If it stops being true, every claim built on it
    has to be rewritten, so it is pinned rather than remembered."""
    ex = L.excursions(L.premium())
    sk = L.skhy_week_one_excursion()
    assert sk["excursion_pp"] > ex.attrs["max_mae_pp"], (
        f"SKHY week one ({sk['excursion_pp']:.1f}pp) no longer exceeds the comparator's "
        f"worst 252-day excursion ({ex.attrs['max_mae_pp']:.1f}pp) — notebook 09 §4 and "
        "G26b both assert that it does"
    )


# --------------------------------------------------------------------------------
# 4. Cached constants must equal their estimators
# --------------------------------------------------------------------------------


def test_fx_coefficient_constant_matches_its_own_deep_estimate():
    from pipeline.hedging import ratios
    full = L.fx_sensitivity_deep().iloc[0]
    assert abs(ratios.FX_COEF_EMPIRICAL - full.empirical_coef) < 5e-3, (
        f"ratios.FX_COEF_EMPIRICAL={ratios.FX_COEF_EMPIRICAL} but the estimator now gives "
        f"{full.empirical_coef}. The constant is a cache of this regression; update it."
    )
    assert abs(ratios.FX_COEF_CI95[0] - full.ci95_lo) < 5e-3
    assert abs(ratios.FX_COEF_CI95[1] - full.ci95_hi) < 5e-3
    assert abs(ratios.FX_R2_ALONE - full.r2) < 5e-4


def test_fx_coefficient_is_recorded_as_era_unstable():
    fx = L.fx_sensitivity_deep()
    eras = fx.iloc[1:]
    assert (eras.ci95_lo < 0).any(), (
        "no era's interval contains zero any more, so the 'not stable across eras' claim on "
        "G27 and in ratios.py must be restated"
    )


def test_hedge_legs_live_uses_one_shared_observation_date():
    """The defect this replaced: each leg's own last close, which are not one moment."""
    from pipeline.hedging.ratios import HedgeLegs
    from pipeline.measurement.premium import latest_common_legs, build_all_variants
    snap = latest_common_legs("skhy")
    joined = build_all_variants("skhy")[0].series
    assert snap["date"] == joined.index[-1]
    assert abs(HedgeLegs.live("skhy").premium - float(joined.iloc[-1])) < 1e-9


def test_structural_audit_rows_all_carry_a_source_and_a_direction():
    assert len(L.STRUCTURAL_ROWS) >= 10
    for dim, tsmc, skhy, cuts, src in L.STRUCTURAL_ROWS:
        assert all(len(x) > 10 for x in (tsmc, skhy, cuts, src)), dim
    joined = " ".join(r[3] for r in L.STRUCTURAL_ROWS)
    assert "DECISIVE" in joined and "OVERSTATES" in joined
    assert "revolv" in L.ASYMMETRY and "reflected" in L.ASYMMETRY


def test_rule_grid_declares_its_ratification_state():
    note = L.rule_grid_note()
    if L.RULE_GRID_RATIFIED is None:
        assert "PROVISIONAL" in note
    else:
        assert L.RULE_GRID_RATIFIED in note
