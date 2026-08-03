"""The pricing pack's own guards: no unratified default, no artifact without its provenance.

D7 IS A TEST, NOT A FUNCTION. A freshness header that exists but is not carried by every chart
is worse than none: it trains the reader to assume provenance is present, so the one chart that
lacks it inherits the credibility of the ones that have it. The strip is therefore asserted onto
every pack figure here rather than left to whoever writes the next one.
"""

from __future__ import annotations

import inspect

import matplotlib
import pytest

matplotlib.use("Agg")

from pipeline.package import pricing_pack as PP  # noqa: E402
from pipeline.viz import figures  # noqa: E402

#: Every figure in the pack, and the pack object each is called with.
PACK_FIGURES = ("g39_carry_waterfall", "g40_breakeven_surface", "g41_margin_sizing",
                "g42_drawdown_budget", "g43_scenario_rom", "g44_exit_tree",
                "g45_carry_waterfall_card", "g46_breakeven_surface_card")


class TestDeskInputsAreNeverDefaulted:
    """Doctrine: no number in the pack may silently depend on an unratified default."""

    def test_desk_inputs_are_unratified_or_deliberately_ratified(self):
        assert set(PP.DESK_INPUTS) == {"borrow_live_bps_yr", "xccy_basis_bps_yr",
                                       "initial_margin_pct"}

    def test_carry_waterfall_requires_both_desk_inputs_explicitly(self):
        """A default here would let a chart circulate carrying a number nobody quoted.

        `borrow_bps_yr` became `name_special_bps_yr` when D1.1 split the borrow line. The guard
        moved with the rename rather than being dropped: what it protects is that a DESK INPUT
        cannot be supplied by accident, and the split made that more important, not less.
        The card arguments are deliberately exempt — a DOCUMENTED card level is published, and
        defaulting to it is not the same act as defaulting to an unratified quote.
        """
        sig = inspect.signature(PP.carry_waterfall)
        for name in ("name_special_bps_yr", "xccy_basis_bps_yr"):
            assert sig.parameters[name].default is inspect.Parameter.empty, (
                f"{name} acquired a default; the whole point of the pack is that a desk input "
                f"cannot be supplied by accident")

    def test_borrow_status_reports_bracketed_until_ratified(self):
        status = PP.borrow_status(PP.DESK_INPUTS["borrow_live_bps_yr"])
        if PP.DESK_INPUTS["borrow_live_bps_yr"] is None:
            assert status == PP.BRACKETED_LABEL
        else:
            assert status == PP.LIVE_LABEL

    def test_cheaper_borrow_lowers_all_in_carry(self):
        """Sign-convention guard. Positive is a cost, so more borrow must cost more."""
        cheap = PP.carry_waterfall(150, 0.0).bp_per_year.sum()
        dear = PP.carry_waterfall(900, 0.0).bp_per_year.sum()
        assert cheap < dear


class TestCardSplit:
    """D1.1 — the card and the special must stay separable and separately stressable."""

    def test_card_and_special_are_never_one_row(self):
        w = PP.carry_waterfall(400, 0.0)
        assert {"house card", "name special"} <= set(w.component), (
            "the borrow line was merged; a client cannot see which half is negotiable")
        assert w[w.component == "house card"].status.iloc[0] == "DOCUMENTED"
        assert w[w.component == "name special"].status.iloc[0] == "BRACKETED"

    def test_non_borrow_subtotal_excludes_only_the_special(self):
        w = PP.carry_waterfall(400, 0.0)
        expected = float(w[w.component != "name special"].bp_per_month.sum())
        assert PP.non_borrow_subtotal_bp_month() == pytest.approx(expected)

    def test_non_borrow_subtotal_is_positive_once_the_card_is_counted(self):
        """The card more than consumes the rate tailwind — the D1.1 headline, asserted."""
        without_card = PP.non_borrow_subtotal_bp_month(0.0, 0.0)   # mult 0 -> no card
        with_card = PP.non_borrow_subtotal_bp_month(0.0, 1.0)
        assert without_card < 0 < with_card

    def test_card_stress_moves_the_card_and_not_the_special(self):
        base = PP.carry_waterfall(400, 0.0, 1.0).set_index("component").bp_per_year
        crisis = PP.carry_waterfall(400, 0.0, 2.0).set_index("component").bp_per_year
        assert crisis["house card"] == pytest.approx(2 * base["house card"])
        assert crisis["name special"] == base["name special"]

    def test_term_financing_locks_the_card_against_stress(self):
        """card_locked IS the product: it makes the multiplier unable to move."""
        stressed = PP.house_card_bps_yr(2.0, card_locked=False)
        locked = PP.house_card_bps_yr(2.0, card_locked=True)
        assert locked == PP.house_card_bps_yr(1.0)
        assert locked < stressed

    def test_a_negative_basis_eats_the_tailwind(self):
        """The stress axis must RAISE cost. This test caught a live sign error.

        Written first as `stressed < flat`, which passed — and was wrong. A negative KRW basis
        makes swapping into KRW more expensive, as financing.py already documented, so the
        {0, -25, -50} stress axis was making the trade progressively cheaper. A stress that
        flatters is worse than no stress at all, because it is read as reassurance.
        """
        flat = PP.carry_waterfall(400, 0.0).bp_per_year.sum()
        mild = PP.carry_waterfall(400, -25.0).bp_per_year.sum()
        stressed = PP.carry_waterfall(400, -50.0).bp_per_year.sum()
        assert flat < mild < stressed, "a more negative basis must cost MORE, not less"


class TestFreshnessTravelsWithEveryArtifact:

    def test_strip_carries_asof_config_pair_and_borrow_status(self):
        line = PP.freshness_line()
        f = PP.freshness()
        for token in (f["asof"], f["close_def"], f["fx_leg"], f["borrow_status"]):
            assert token in line, f"freshness strip is missing {token!r}"

    @pytest.mark.parametrize("name", PACK_FIGURES)
    def test_every_pack_figure_carries_the_freshness_strip(self, name):
        """The D7 guarantee, enforced per figure rather than promised in a docstring."""
        fig, _meta = getattr(figures, name)(PP)
        text = " ".join(t.get_text() for t in fig.findobj(match=matplotlib.text.Text))
        assert PP.freshness()["asof"] in text, f"{name} renders without an as-of date"
        assert PP.freshness()["close_def"] in text, f"{name} renders without its config pair"


class TestDrawdownInversion:

    def test_max_notional_inverts_the_budget(self):
        assert PP.max_notional(5.0, 10.0) == pytest.approx(0.5)
        assert PP.max_notional(10.0, 10.0) == pytest.approx(1.0)

    def test_a_larger_excursion_permits_a_smaller_position(self):
        assert PP.max_notional(5.0, 30.0) < PP.max_notional(5.0, 10.0)

    def test_zero_excursion_raises_rather_than_returning_infinity(self):
        with pytest.raises(ValueError):
            PP.max_notional(5.0, 0.0)

    def test_skhy_excursion_exceeds_the_comparator_maximum(self):
        """The fact that makes SKHY a stress OVERRIDE rather than a quantile of the sample.

        If this ever flips, the D4 caption is wrong: it would then be legitimate to read SKHY's
        path as an extreme draw from the comparator distribution, and the chart says it is not.
        """
        qs = PP.excursion_quantiles()
        assert qs["realised SKHY"]["pp"] > qs["comparator max"]["pp"], (
            "SKHY's realised excursion no longer exceeds the comparator maximum — D4's "
            "'not a quantile' caption must be revisited")


class TestScenarioGridAndExitTree:

    def test_rom_uses_two_terms_and_a_narrowing_premium_pays(self):
        """Short the premium: a negative terminal move must be a gain, positive a loss."""
        g = PP.scenario_rom(delta_pi_pp=(-10.0, 10.0), borrow_grid=(400,), horizons=(252,))
        gain = g[g.delta_pi_pp == -10.0].rom_x.iloc[0]
        loss = g[g.delta_pi_pp == 10.0].rom_x.iloc[0]
        assert gain > 0 > loss

    def test_longer_horizon_costs_more_carry_at_the_same_move(self):
        g = PP.scenario_rom(delta_pi_pp=(0.0,), borrow_grid=(400,), horizons=(126, 252))
        short_h = g[g.horizon_sessions == 126].rom_x.iloc[0]
        long_h = g[g.horizon_sessions == 252].rom_x.iloc[0]
        assert long_h < short_h, "carry must accumulate with horizon"

    def test_the_payoff_is_asymmetric_and_the_grid_shows_it(self):
        """The repository's central finding, asserted in the unit a book is run on."""
        g = PP.scenario_rom()
        assert abs(g.rom_x.min()) > g.rom_x.max(), (
            "the worst cell must cost more than the best cell pays; if this flips, the "
            "bounded-gain/unbounded-loss claim in the pitch no longer holds in ROM terms")

    def test_exit_tree_is_complete_and_uses_only_agreed_actions(self):
        tree = PP.exit_tree()
        assert len(tree) == 27, "3 premium bands x 3 borrow states x 3 headroom bands"
        assert set(tree.action) <= set(PP.EXIT_ACTIONS)
        assert not tree.duplicated(
            ["premium_band", "borrow_state", "margin_headroom"]).any()

    def test_margin_overrides_everything_else(self):
        """The override order is the one thing in D6 that cannot be inferred from research."""
        crit = PP.exit_tree().query("margin_headroom == 'critical'")
        assert (crit.action == "unwind at ADV band").all(), (
            "a critical margin cell must unwind regardless of premium or borrow")

    def test_a_recall_converts_rather_than_unwinding_while_margin_allows(self):
        """Losing the short leg is a financing event, not an investment one."""
        recalled = PP.exit_tree().query(
            "borrow_state == 'recalled' and margin_headroom != 'critical'")
        assert (recalled.action == "convert to long-local TRS only").all()

    def test_every_exit_threshold_states_its_ratification_status(self):
        """A threshold must always say whether it is signed. Never silently either way.

        This test previously asserted the OPPOSITE — that every basis carried
        TODO(ash: ratify). The author signed the thresholds on 2026-08-03, so the assertion is
        inverted rather than deleted: the guard is not "these are unratified", it is "these
        never lose their provenance", and that holds in both directions.
        """
        marker = "RATIFIED" if PP.EXIT_THRESHOLDS_RATIFIED else "TODO(ash: ratify)"
        for name, group in PP.EXIT_THRESHOLDS.items():
            assert marker in group["basis"], (
                f"{name} does not state its ratification status; a threshold whose provenance "
                f"is unreadable is worse than one that is openly unsigned")

    def test_signing_the_thresholds_did_not_clear_the_structural_decisions(self):
        """Signing NUMBERS must not silently mark an ORDERING as agreed.

        The override order and the leaf set are not thresholds. If ratifying the numbers ever
        empties this list, the tree would present an unagreed override order as settled policy.
        """
        owed = PP.ratification_owed()
        assert owed, "structural decisions cannot be cleared by signing threshold values"
        joined = " ".join(owed).lower()
        assert "override order" in joined and "leaf set" in joined

    def test_ratified_thresholds_propagate_to_every_tree_row(self):
        if PP.EXIT_THRESHOLDS_RATIFIED:
            assert set(PP.exit_tree().status) == {"RATIFIED"}


class TestThresholdSpecial:
    """D2.1 — the boundary is solved, so it must agree with the surface it is drawn on."""

    def test_threshold_is_where_the_surface_actually_crosses_zero(self):
        """Solved-vs-scanned agreement. If these drift apart, one of them is lying."""
        h = 300.0
        thr = PP.threshold_special_bp(h)
        surf = PP.breakeven_surface(borrow_bps=(round(thr) - 25, round(thr), round(thr) + 25),
                                    half_lives=[h])
        col = surf[h]
        assert col.iloc[0] > 0 > col.iloc[-1], "the surface does not cross at the solved point"
        assert abs(col.iloc[1]) < 3.0, "solved threshold is not on the surface's zero"

    def test_stress_states_shift_the_threshold_by_a_constant(self):
        """Contours must be parallel — that is what makes the feature flat-priceable."""
        base, crisis = PP.STRESS_STATES["base"], PP.STRESS_STATES["crisis"]
        gaps = [PP.threshold_special_bp(h, base["card_mult"], False, base["basis_bps"])
                - PP.threshold_special_bp(h, crisis["card_mult"], False, crisis["basis_bps"])
                for h in (205.0, 295.0, 385.0)]
        assert gaps[0] == pytest.approx(gaps[1]) == pytest.approx(gaps[2]), (
            "stress contours are not parallel; the feature cannot be flat-priced")

    def test_locking_the_card_does_not_buy_back_the_basis(self):
        """The consequence of bundling, and the one a client could be misled about.

        Before the crisis state bundled a basis widening, the locked contour coincided with
        base and the chart said so. It no longer does: term financing removes the card
        multiplier and nothing else, so the locked contour sits below base by the basis cost.
        Asserting the INEQUALITY rather than the old equality is the point of this test.
        """
        crisis = PP.STRESS_STATES["crisis"]
        for h in (205.0, 295.0, 385.0):
            base = PP.threshold_special_bp(h, 1.0, False, 0)
            locked = PP.threshold_special_bp(h, crisis["card_mult"], True,
                                             crisis["basis_bps"])
            stressed = PP.threshold_special_bp(h, crisis["card_mult"], False,
                                               crisis["basis_bps"])
            assert stressed < locked < base, "locked must sit between crisis and base"
            assert base - locked == pytest.approx(-crisis["basis_bps"]), (
                "the gap between base and locked must be exactly the un-bought-back basis")

    def test_stress_states_are_monotone_in_severity(self):
        """base -> squeeze -> crisis must get strictly worse, or the ladder is mislabelled."""
        thr = [PP.threshold_special_bp(295.0, st["card_mult"], False, st["basis_bps"])
               for st in PP.STRESS_STATES.values()]
        assert thr[0] > thr[1] > thr[2]

    def test_term_financing_value_equals_the_card_stress_removed(self):
        v = PP.term_financing_value_bp_yr()
        assert v["value_bp_yr_of_special"] == pytest.approx(
            sum(PP.HOUSE_CARD_BPS_YR.values()))

    def test_the_briefs_slow_end_numbers_reproduce_from_the_pipeline(self):
        """Amendment D2.1 quoted ~744 / ~569. They reproduce, but NOT at today's entry.

        Both land within 1bp at the repository's LEGACY reference premium of 22.6% and a 391-day
        half-life — and the crisis figure needs the basis stress bundled with the card stress,
        which the brief did not state. Recorded as a test so the reconciliation is checkable
        rather than asserted in a commit message: today's entry of ~31% puts the same thresholds
        several hundred bp higher, and the charts render at today's entry.
        """
        b, c = PP.STRESS_STATES["base"], PP.STRESS_STATES["crisis"]
        base = PP.threshold_special_bp(391, b["card_mult"], False, b["basis_bps"], pi_0=0.226)
        crisis = PP.threshold_special_bp(391, c["card_mult"], False, c["basis_bps"],
                                         pi_0=0.226)
        assert base == pytest.approx(744, abs=2)
        assert crisis == pytest.approx(569, abs=2)
