"""Regime taxonomy — ratified 2026-07-29 (docs/regime_taxonomy.md).

These tests do not check that the taxonomy is *right* — no test can ratify a research
judgement. They check the properties that make it a taxonomy rather than a pair of labels:
that membership is derivable from a written rule, that the rule was applied before the
outcome was seen, that both classes have enough members to be classes at all, and that the
documented caveats survive.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.convergence.jorda import (
    CONSTRAINT_SUBTYPE, FORWARD_TEST_PAIRS, PANEL_CAVEATS, REGIME_OF_PAIR,
    TAXONOMY_RATIFIED, run_panel,
)
from pipeline.ingest.registry import PAIRS
from pipeline.measurement.premium import build_all_variants

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "regime_taxonomy.md"


class TestRatificationRecord:
    def test_the_taxonomy_document_exists(self):
        assert DOC.is_file(), "a ratified taxonomy needs a written rule, not just a dict"

    def test_ratification_is_dated(self):
        assert TAXONOMY_RATIFIED and TAXONOMY_RATIFIED[:2] == "20"

    def test_every_classified_pair_appears_in_the_document(self):
        """A label in code with no entry in the rule document is an unratified label
        wearing a ratified one's clothes."""
        text = DOC.read_text()
        for pair in REGIME_OF_PAIR:
            assert f"`{pair}`" in text, f"{pair} is classified in code but absent from {DOC.name}"

    def test_document_states_falsification_criteria(self):
        """A classification that cannot be wrong is not a classification."""
        text = DOC.read_text().lower()
        assert "falsif" in text
        assert "misclassified" in text

    def test_forward_test_pair_is_classified_but_never_pooled(self):
        assert "skhy" in FORWARD_TEST_PAIRS
        assert "skhy" in CONSTRAINT_SUBTYPE, "SKHY still needs its sub-type on the record"
        for res in run_panel().values():
            assert res.n_pairs == len([p for p, r in REGIME_OF_PAIR.items()
                                       if r == res.regime and p not in FORWARD_TEST_PAIRS])


class TestClassesAreClasses:
    @pytest.mark.parametrize("regime", ["one_way_constrained", "fungible"])
    def test_each_class_has_at_least_two_pairs(self, regime):
        """The precondition for ratification. A taxonomy over two elements is a pair of
        names — with one pair per class, 'the class is persistent' and 'this pair is
        persistent' are the same sentence."""
        members = [p for p, r in REGIME_OF_PAIR.items() if r == regime]
        assert len(members) >= 2, f"{regime} has {len(members)} pair(s)"

    def test_every_constrained_pair_has_a_documented_subtype(self):
        for pair, regime in REGIME_OF_PAIR.items():
            if regime == "one_way_constrained":
                assert CONSTRAINT_SUBTYPE.get(pair) in ("revolving", "consent", "hard_cap"), \
                    f"{pair} has no documented constraint mechanism"

    def test_excluded_pairs_are_not_silently_pooled(self):
        excluded = {p.pair_id for p in PAIRS if p.excluded}
        assert excluded, "the exclusion mechanism should have at least one live user (auo)"
        for pair in excluded:
            assert pair not in REGIME_OF_PAIR, f"{pair} is excluded yet still classified"

    def test_every_sample_restriction_carries_a_reason(self):
        """A restriction without a written reason is indistinguishable from one made to
        improve a result."""
        for spec in PAIRS:
            if spec.sample_start or spec.sample_end or spec.excluded:
                assert len(spec.sample_reason) > 80, \
                    f"{spec.pair_id} is restricted with no substantive reason"


class TestMembershipIsNotSelectedOnOutcome:
    def test_constrained_class_contains_a_near_parity_pair(self):
        """The strongest available evidence that labels came from the RULE and not from the
        premiums. Had membership been chosen by looking at which pairs showed a big premium,
        the constrained class would not contain one that spends its life near parity."""
        means = {p: abs(build_all_variants(p)[0].series.mean())
                 for p, r in REGIME_OF_PAIR.items() if r == "one_way_constrained"}
        assert min(means.values()) < 0.05, (
            f"every constrained pair has |mean pi| >= 5% ({means}) — consistent with "
            "membership having been picked from the outcome"
        )

    def test_dynamics_separate_the_classes_far_more_sharply_than_level_does(self):
        """The non-circularity claim, stated so it can fail.

        An earlier version asserted the classes OVERLAP on level. They do not — constrained
        min |mean pi| is 1.96% against a control max of 0.91%. The defensible claim is the
        comparison of gaps: if the label were merely a proxy for "big premium", level would
        separate the classes at least as sharply as dynamics do. It does not, by a wide
        margin."""
        from pipeline.convergence.jorda import estimate_regime

        # SUB-RESOLUTION PAIRS ARE EXCLUDED FROM THE DYNAMICS SIDE, symmetrically in both
        # classes, and the reason is that their half-life is not a measurement of speed. When
        # rho_1 already sits below one half at the first horizon the series does not persist at
        # daily resolution at all, and the estimator returns 1.0 as a floor rather than as a
        # finding. Comparing that floor against a real estimate is comparing a non-measurement
        # to a measurement.
        #
        # This surfaced 2026-08-03 when SK Telecom was classified from its 20-F: its 1,073
        # post-restriction sessions come back `sub_resolution`, which dragged
        # min(constrained) to 1.0 and collapsed the ratio. `baba` carries the same flag on the
        # fungible side, so excluding the flag is symmetric rather than tailored to rescue a
        # result. LEVEL is left alone -- resolvability has no bearing on a mean.
        lv, hl = {}, {}
        for pair, regime in REGIME_OF_PAIR.items():
            s = build_all_variants(pair)[0].series
            lv.setdefault(regime, []).append(abs(s.mean()))
            est = estimate_regime([s], regime).hl
            if est.support != "sub_resolution":
                hl.setdefault(regime, []).append(est.point)
        level_gap = min(lv["one_way_constrained"]) / max(lv["fungible"])
        dyn_gap = min(hl["one_way_constrained"]) / max(hl["fungible"])
        assert dyn_gap > 2 * level_gap, (
            f"level gap {level_gap:.1f}x vs dynamics gap {dyn_gap:.1f}x — the regime label is "
            "not adding information beyond premium size, which is what selection would look like"
        )


class TestTheClassesActuallySeparate:
    """This is a RESULT, not a definition — reported as such in the taxonomy document."""

    def test_persistence_separates_by_orders_of_magnitude(self):
        res = run_panel()
        con = res["one_way_constrained"].hl
        fun = res["fungible"].hl
        assert con.point > 20 * fun.point, (
            f"constrained half-life {con.point:.0f}d vs fungible {fun.point:.0f}d — the "
            "taxonomy's discriminating power has collapsed"
        )

    def test_control_contamination_biases_against_the_thesis(self):
        """The control pairs carry episodic ratio contamination that RAISES their measured
        persistence. That means the reported contrast is a LOWER bound: cleaning the controls
        widens the gap. Reporting the contaminated number cannot flatter the result, which is
        why it is reported as landed."""
        from pipeline.convergence.jorda import estimate_regime
        raw = [build_all_variants(p)[0].series
               for p, r in REGIME_OF_PAIR.items() if r == "fungible"]
        clean = [s[s.abs() <= 0.25] for s in raw]
        assert estimate_regime(clean, "f").horizons[0].rho < estimate_regime(raw, "f").horizons[0].rho


class TestCaveatsSurvive:
    def test_panel_caveats_are_stated_and_specific(self):
        assert len(PANEL_CAVEATS) >= 2
        joined = " ".join(PANEL_CAVEATS).lower()
        assert "regulator" in joined, "the one-regulator limit must survive in code"
        assert "brazil" in joined, "the one-country control limit must survive in code"

    def test_document_separates_rule_from_binding_state(self):
        """The correction that keeps the design non-circular: classifying on binding-ness
        would mean selecting on the premium and then measuring the premium."""
        text = DOC.read_text().lower()
        assert "binding-ness is a state" in text or "binding-ness" in text
        assert "circle" in text or "circular" in text

    def test_document_records_the_ownership_vs_programme_cap_correction(self):
        text = DOC.read_text().lower()
        assert "programme cap" in text
        assert "49" in text, "the Korean exhausted-FOL counterexample should be cited"
