"""Package modules: netting, capacity. Guards on the claims the sheets will quote."""
from __future__ import annotations

import pytest

from pipeline.package import capacity as C, netting as N


class TestNetting:
    def test_stress_is_defined_by_magnitude_not_by_a_date_range(self):
        """The first version used SKHY's excursion dates for every pair, which gave TSMC four
        arbitrary days and a 'stress ratio' on n=4 — the shape of evidence with none of the
        content. Both rows must carry real sample size."""
        d = N.calm_vs_stress("tsmc")
        assert d.n.min() > 100, f"stress row has n={d.n.min()}, too few to quote"

    def test_netting_benefit_erodes_in_stress(self):
        """The sell and the warning are the same measurement in two states. If stress ever
        showed a LARGER benefit, the pitch's honesty paragraph would be wrong."""
        d = N.calm_vs_stress("tsmc").set_index("regime_label")
        calm = d[d.index.str.startswith("calm")].ratio.iloc[0]
        stress = d[d.index.str.startswith("stress")].ratio.iloc[0]
        assert stress > calm, f"stress ratio {stress:.3f} <= calm {calm:.3f}"

    def test_pair_risk_is_below_the_sum_of_legs_in_calm(self):
        d = N.calm_vs_stress("tsmc")
        assert d.ratio.min() < 1.0

    def test_wrong_way_risk_is_named(self):
        assert "WRONG-WAY" in N.wrong_way_note()
        assert "recall" in N.wrong_way_note().lower()


class TestCapacity:
    def test_days_to_unwind_scales_with_size_and_inversely_with_participation(self):
        d = C.days_to_unwind()
        at10 = d[d.participation == 0.10].sort_values("size_usd")
        assert list(at10.days_binding) == sorted(at10.days_binding)
        one = d[d.size_usd == 1e9].set_index("participation").days_binding
        assert one[0.05] > one[0.20], "more participation must mean fewer sessions"

    def test_the_binding_leg_is_reported_not_averaged(self):
        """A pair exits when BOTH legs are out, so the honest figure is the slower leg."""
        d = C.days_to_unwind()
        assert d.binding_leg.notna().all()
        assert (d.days_binding >= d[["days_SKHY", "days_000660"]].max(axis=1) - 1e-9).all()

    def test_skhy_adv_carries_its_freshness_caveat(self):
        """A 12-session ADV is not a cycle average and must not be quoted as one."""
        a = C.adv_table().set_index("leg")
        skhy = [i for i in a.index if "SKHY" in i][0]
        if a.loc[skhy, "n_sessions"] < 60:
            assert "regime-fresh" in a.loc[skhy, "caveat"]

    def test_borrow_ceiling_says_it_is_not_lendable_depth(self):
        """An on-loan balance is what is already out. Presenting it as capacity would
        overstate a number the desk actually quotes."""
        b = C.borrow_ceiling()
        assert "not lendable depth" in b["caveat"].lower() or b.get("available") is False
