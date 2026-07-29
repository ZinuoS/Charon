"""Execution cost layer — sourced numbers, honest gaps, the skew always present."""
from __future__ import annotations
from execution import costs


class TestConversionCost:
    def test_round_trip_is_the_documented_symmetric_fee(self):
        c = costs.conversion_round_trip()
        assert c.documented
        assert abs(c.value_pct - 0.10 / 149.0) < 1e-9, "2 x $0.05/ADS over the $149 price"
        assert "424B4" in c.source

    def test_cost_is_framed_as_not_sustaining_the_barrier(self):
        assert "NOT what sustains" in costs.conversion_round_trip().note


class TestGapsAreGapsNotZeros:
    def test_undocumented_segments_return_none_not_zero(self):
        stack = costs.cost_stack()
        undoc = [c for c in stack if not c.documented]
        assert undoc, "the honest stack has undocumented legs"
        for c in undoc:
            assert c.value_pct is None, f"{c.name} must be None, never an invented 0"
            assert c.source and c.note, f"{c.name} must say WHY it is undocumented"

    def test_summary_table_shows_quoted_live_never_zero(self):
        df = costs.summary_table()
        undoc = df[~df["documented"]]
        assert (undoc["cost"] == "— quoted live —").all(), "a gap must never render as 0.00%"


class TestMarginStress:
    def test_drawdown_is_the_realized_excursion_not_hypothetical(self):
        ms = costs.margin_stress()
        assert ms["premium_leg_drawdown_pct_pts"] > 30, "week one ran 16% -> 52%"
        assert "realized, not modelled" in ms["interpretation"]

    def test_the_skew_warning_is_attached_to_the_stress(self):
        """A cost/margin figure that omitted the negative skew would misrepresent the trade."""
        ms = costs.margin_stress()
        assert "unbounded" in ms["structural_skew"]
        assert "negatively skewed" in ms["structural_skew"]

    def test_ordering_entry_below_peak(self):
        ms = costs.margin_stress(entry=0.16, peak=0.52)
        assert ms["premium_leg_drawdown_pct_pts"] == 36.0


class TestNonAdvisory:
    def test_no_function_output_carries_advisory_language(self):
        """Checks the OUTPUTS, not the source — the source legitimately names the banned
        phrases in its own disclaimer ('nothing here is a recommendation or price target').
        A crude source-grep would flag the disclaimer that forbids the thing, the same
        way an over-literal guard punishes a correct caveat."""
        text = " ".join(str(v) for c in costs.cost_stack() for v in (c.name, c.note, c.source))
        text += " " + " ".join(str(v) for v in costs.margin_stress().values())
        text = text.lower()
        for banned in ("we recommend", "you should buy", "buy signal", "sell signal", "target price of"):
            assert banned not in text, f"advisory language in output: {banned!r}"

    def test_the_compliance_disclaimer_is_present_in_the_module(self):
        import inspect
        src = inspect.getsource(costs).lower()
        assert "non-advisory" in src and "is a solicitation" in src  # "Nothing here IS a solicitation..."
