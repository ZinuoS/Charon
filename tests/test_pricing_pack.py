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
                "g42_drawdown_budget")


class TestDeskInputsAreNeverDefaulted:
    """Doctrine: no number in the pack may silently depend on an unratified default."""

    def test_desk_inputs_are_unratified_or_deliberately_ratified(self):
        assert set(PP.DESK_INPUTS) == {"borrow_live_bps_yr", "xccy_basis_bps_yr",
                                       "initial_margin_pct"}

    def test_carry_waterfall_requires_both_desk_inputs_explicitly(self):
        """A default here would let a chart circulate carrying a number nobody quoted."""
        sig = inspect.signature(PP.carry_waterfall)
        for name in ("borrow_bps_yr", "xccy_basis_bps_yr"):
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
