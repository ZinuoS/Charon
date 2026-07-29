"""Per-currency FX convention fixtures, hand-checked.

Every value below was checked by hand against a real observation. The point is not to
verify arithmetic — it is to make the *direction* of each quote a tested fact, because a
single reversed currency in a multi-pair panel corrupts one pair while the rest look
correct, which reads as "mostly working" rather than "broken".
"""

from __future__ import annotations

import pytest

from pipeline.panel.fx_conventions import (
    CONVENTIONS,
    convention,
    for_series,
    pegged_currencies,
    validate_quote_direction,
)

# Hand-checked live observations, all LOCAL PER USD.
OBSERVED = {
    "USDKRW": 1453.67,
    "USDTWD": 32.39,
    "USDINR": 95.84,
    "USDHKD": 7.84,
}


class TestDirectionIsCorrect:
    @pytest.mark.parametrize("code,value", sorted(OBSERVED.items()))
    def test_real_observation_passes(self, code, value):
        validate_quote_direction(code, value)

    @pytest.mark.parametrize("code,value", sorted(OBSERVED.items()))
    def test_reciprocal_is_rejected(self, code, value):
        """The exact bug this module exists to prevent."""
        with pytest.raises(ValueError):
            validate_quote_direction(code, 1.0 / value)

    @pytest.mark.parametrize("code,value", sorted(OBSERVED.items()))
    def test_reciprocal_error_names_the_actual_fix(self, code, value):
        """An error that says 'out of range' sends someone hunting a data problem. This
        one has to say 'you have it upside down, fix it in the adapter'."""
        with pytest.raises(ValueError, match="inverting in its adapter"):
            validate_quote_direction(code, 1.0 / value)

    def test_every_convention_is_local_per_usd(self):
        assert {c.quote for c in CONVENTIONS.values()} == {"local_per_usd"}


class TestRangesDiscriminate:
    def test_ranges_do_not_admit_their_own_reciprocals(self):
        """A range wide enough to contain both a value and its reciprocal would pass a
        reversed series silently — the check would be decorative."""
        for c in CONVENTIONS.values():
            assert not (c.expected_min <= 1.0 / c.expected_min <= c.expected_max), c.code
            assert not (c.expected_min <= 1.0 / c.expected_max <= c.expected_max), c.code

    def test_krw_and_hkd_ranges_are_disjoint(self):
        """~1450 and ~7.8 must never both satisfy one band, or a mis-mapped series slips."""
        krw, hkd = convention("USDKRW"), convention("USDHKD")
        assert krw.expected_min > hkd.expected_max


class TestPeg:
    def test_hkd_is_declared_pegged_with_its_design_consequence(self):
        assert pegged_currencies() == ["USDHKD"]
        assert "isolates cross-listing" in convention("USDHKD").peg

    def test_hkd_band_matches_the_convertibility_undertaking(self):
        c = convention("USDHKD")
        assert c.expected_min <= 7.75 and c.expected_max >= 7.85


class TestSeriesMapping:
    @pytest.mark.parametrize("series_id", [
        "usdkrw_spot_daily", "usdkrw_spot_fred_daily",
        "usdtwd_spot_daily", "usdinr_spot_daily", "usdhkd_spot_daily",
    ])
    def test_every_registry_fx_series_maps_to_a_convention(self, series_id):
        assert for_series(series_id).quote == "local_per_usd"

    def test_both_usdkrw_variants_share_one_convention(self):
        """Two fixes of one pair must not drift into two conventions."""
        assert for_series("usdkrw_spot_daily") is for_series("usdkrw_spot_fred_daily")

    def test_unknown_series_raises(self):
        with pytest.raises(KeyError):
            for_series("not_an_fx_series")


class TestRegistryAgreement:
    def test_registry_fx_series_all_have_declared_conventions(self):
        """A new FX series must not reach the panel without a declared direction."""
        from pipeline.ingest.registry import all_series
        for spec in all_series():
            if spec.asset_class == "fx":
                assert for_series(spec.series_id) is not None
                assert "per 1 USD" in spec.units, f"{spec.series_id} units disagree with convention"
