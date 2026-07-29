"""Hedge construction — the identity, the FX residual, and the refusal to over-claim."""
from __future__ import annotations
import pytest
from pipeline.hedging import ratios as R

LIVE = R.HedgeLegs(adr_price_usd=130.17, local_price_krw=1_550_000.0, fx_krw_per_usd=1459.45)


class TestLegConstruction:
    def test_premium_matches_the_m1_identity(self):
        assert abs(LIVE.premium - 0.2257) < 1e-3

    def test_local_shares_use_the_documented_ratio(self):
        assert LIVE.local_shares == 0.1, "10 ADSs = 1 common share (424B4)"


class TestFxResidual:
    def test_residual_equals_pi_over_one_plus_pi(self):
        """The premium expressed as money. Algebraic, so it must hold exactly."""
        h = R.fx_hedge(LIVE)
        assert abs(h["identity_check"]) < 1e-9

    def test_residual_is_a_material_fraction_of_the_leg(self):
        h = R.fx_hedge(LIVE)
        assert h["residual_as_pct_of_adr_leg"] > 0.15, (
            "at pi=22.6% roughly 18% of the ADR leg is unhedged by a local-leg-only hedge")

    def test_hedge_note_warns_the_residual_is_uncovered(self):
        assert "LOCAL LEG only" in R.fx_hedge(LIVE)["note"]


class TestFxSensitivity:
    def test_direction_is_krw_weakness_widens(self):
        s = R.fx_sensitivity(0.2257)
        assert s["analytic_premium_change_pct_pts"] > 0
        assert "WIDENS" in s["direction"]

    def test_reports_both_analytic_and_empirical_never_one_number(self):
        """Collapsing them would present an imprecise relationship as a hedge ratio."""
        s = R.fx_sensitivity(0.2257)
        assert "analytic_premium_change_pct_pts" in s
        assert "empirical_central_pct_pts" in s
        assert "empirical_range_pct_pts" in s
        assert s["empirical_central_pct_pts"] < s["analytic_premium_change_pct_pts"], \
            "empirical coefficient is below 1, so the central estimate must be lower"

    def test_the_low_explanatory_power_is_surfaced(self):
        """FX explains ~1% of daily premium variance; a reader must see that."""
        s = R.fx_sensitivity(0.2257)
        assert s["fx_share_of_daily_premium_variance"] < 0.05
        assert "not the dominant daily risk" in s["caveat"]

    def test_theory_lies_inside_the_empirical_interval(self):
        assert R.FX_COEF_CI95[0] < 1.0 < R.FX_COEF_CI95[1], \
            "theory is not rejected — but the interval is wide, which is the point"


class TestGatedQuantities:
    def test_horizon_is_quoted_as_a_floor_and_never_as_a_point(self):
        """S17 replaced PENDING_M3 here with a floor. The invariant that matters is not
        'a number appears' but 'the number is a lower bound and the tail is declared open'
        — cost is linear in horizon, so a point estimate errs in the direction that
        flatters the trade."""
        sz = R.sizing_horizon()
        assert sz["holding_period_ceiling_days"] is None, "the 95% tail is open — no ceiling"
        assert sz["holding_period_floor_days"] > 0
        assert sz["holding_period_floor_days"] < sz["holding_period_point_days"]
        for field in ("expected_holding_period", "financed_cost_over_horizon"):
            text = sz[field].lower()
            assert "at least" in text or "floor" in text, f"{field} must read as a bound"
            assert "no upper bound" in text or "no finite upper bound" in text, \
                f"{field} must declare the open tail"

    def test_no_point_cost_is_derived_from_the_unidentified_crossing(self):
        """First passage sits at ~331d on ~6 independent spans. Multiplying a financing
        rate by that would be the exact fabrication S16 refused to commit."""
        sz = R.sizing_horizon()
        assert str(round(sz["holding_period_point_days"])) not in sz["financed_cost_over_horizon"]
        assert "underpowered" in sz["support"] or "interpolated" in sz["support"]

    def test_pending_fields_name_the_cell_that_fills_them(self):
        assert "run_panel" in R.sizing_horizon()["fills_from"]

    def test_what_is_usable_now_is_stated_alongside(self):
        """A gate report that only says 'blocked' is less useful than one that says what
        survives — here, the qualitative persistence contrast."""
        assert "0.94" in R.sizing_horizon()["what_is_usable_now"]

    def test_beta_hedge_is_blocked_on_m5_with_reason(self):
        b = R.beta_hedge()
        assert b["hedge_ratio"] == R.PENDING_M3
        assert "M5" in b["blocker"]

    def test_hedge_cost_is_gated_and_warns_on_exchange_marked(self):
        h = R.fx_hedge(LIVE)
        assert h["hedge_cost"] == R.PENDING_M3
        assert "exchange_marked" in h["hedge_cost_note"]


class TestSkewNote:
    def test_skew_note_says_the_hedge_does_not_cover_the_barrier(self):
        n = R.skew_note()
        assert "does NOT neutralise the barrier" in n
        assert "unbounded loss" in n


class TestTradeSheets:
    """Voice and honesty rules, asserted rather than trusted."""

    def _sheets(self):
        from pipeline.hedging.sheets import all_sheets
        return all_sheets(0.2257, "headroom 0; sealed by observation")

    def test_every_sheet_declares_readiness(self):
        from pipeline.hedging.sheets import LIVE, CONTINGENT
        for s in self._sheets():
            assert s.readiness in (LIVE, CONTINGENT)

    def test_contingent_sheets_state_their_contingency(self):
        from pipeline.hedging.sheets import CONTINGENT
        for s in self._sheets():
            if s.readiness == CONTINGENT:
                assert s.contingency, f"{s.name} is contingent but does not say on what"
                assert "CONTINGENT ON" in s.render()

    def test_every_sheet_carries_the_skew_warning(self):
        """The skew must appear in the same document as any convergence structure."""
        for s in self._sheets():
            joined = " ".join(s.residual_exposures + s.risks)
            assert "skew" in joined.lower() or "unbounded" in joined.lower(), \
                f"{s.name} lacks the negative-skew warning"

    def test_live_sheet_shows_the_alternative_expression(self):
        """Balanced treatment: the opposite expression sits beside the first."""
        live = self._sheets()[0]
        assert live.alternative and "local leg" in live.alternative

    def test_no_advisory_language_in_rendered_sheets(self):
        banned = ("we recommend", "you should buy", "buy signal", "target price of",
                  "strong buy", "attractive entry")
        for s in self._sheets():
            text = s.render().lower()
            for b in banned:
                assert b not in text, f"{s.name}: advisory phrase {b!r}"

    def test_every_sheet_carries_the_disclaimer(self):
        for s in self._sheets():
            assert "not investment advice" in s.render().lower()

    def test_cost_stack_declares_its_accrual_basis_as_a_floor(self):
        """A cost stack without a horizon is unreadable: every line accrues. S17 added the
        basis row, and it must carry both the floor and the open tail."""
        live = self._sheets()[0]
        costs = dict(live.cost_stack)
        basis = costs["ACCRUAL BASIS"].lower()
        assert "floor" in basis and "no upper bound" in basis

    def test_remaining_pending_field_is_the_ceiling_and_says_none_exists(self):
        live = self._sheets()[0]
        assert any("upper bound" in p.lower() for p in live.pending), \
            "the open tail must survive as an explicit pending line, not vanish"
        assert any("m5" in p.lower() for p in live.pending)

    def test_undocumented_costs_say_quoted_live_never_zero(self):
        live = self._sheets()[0]
        for seg, val in live.cost_stack:
            assert val != "0" and val != "0%", f"{seg} rendered as zero"

    def test_stress_is_the_realized_excursion(self):
        live = self._sheets()[0]
        assert "51.60" in live.stress and "Not modelled" in live.stress
