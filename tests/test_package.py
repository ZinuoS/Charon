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


class TestPackageSheets:
    def _s(self):
        from pipeline.hedging.sheets import all_sheets
        return {x.name: x for x in all_sheets(0.226, "headroom 0")}

    def test_packages_come_first(self):
        from pipeline.hedging.sheets import all_sheets
        names = [x.name for x in all_sheets(0.226, "headroom 0")]
        assert names[0].startswith("PACKAGE A") and names[1].startswith("PACKAGE B")

    def test_package_a_names_the_critical_carry_and_calls_the_view_the_clients(self):
        """The sheet must not imply the desk holds the convergence view. Above the critical
        carry, entering IS a faster-than-base-rate view, and the sheet says whose it is."""
        r = self._s()["PACKAGE A. CONVERGENCE ACCESS"].render()
        assert "CRITICAL CARRY" in r
        assert "client's view" in r or "client's to bring" in r

    def test_package_a_shows_both_netting_numbers(self):
        """Calm without stress would be the sell without the warning."""
        r = self._s()["PACKAGE A. CONVERGENCE ACCESS"].render().lower()
        assert "calm" in r and ("stress" in r or "quintile" in r)

    def test_bracketed_costs_are_labelled_bracketed_not_quoted(self):
        r = self._s()["PACKAGE A. CONVERGENCE ACCESS"].render()
        assert r.count("BRACKETED") >= 3, "hatched components must be visibly bracketed"

    def test_package_b_cites_the_registered_call_without_resolving_it(self):
        r = self._s()["PACKAGE B. EVENT-CONDITIONAL STANDBY"].render()
        assert "Class C" in r and "2026-10-31" in r
        for banned in ("confirmed", "refuted", "resolves as"):
            assert banned not in r.lower(), f"sheet resolves H5: '{banned}'"

    def test_convexity_variant_is_contingent_and_unpriced(self):
        r = self._s()["PACKAGE B. EVENT-CONDITIONAL STANDBY"].render()
        assert "CONTINGENT" in r and "will not price" in r

    def test_numbers_are_derived_not_literal(self):
        """Every quoted figure comes from the package modules, so none can go stale."""
        import inspect
        from pipeline.hedging import sheets
        src = inspect.getsource(sheets.package_convergence_access)
        assert "_pkg_numbers()" in src
        assert "954" not in src and "43.6" not in src, "a literal figure crept into the sheet"
