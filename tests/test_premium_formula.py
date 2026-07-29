"""Premium formula: synthetic fixtures with hand-computable answers.

The premium calculation has exactly three ways to be silently wrong — inverted FX, a
misapplied ADR ratio, and a stale-leg join — and none of them announce themselves in
the output. Each gets a test with an arithmetic answer that can be checked by eye.
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.ingest.registry import pair_by_id
from pipeline.measurement.smoke_premium import compute_premium


def _s(values: dict[str, float]) -> pd.Series:
    """Date-indexed series from {"YYYY-MM-DD": value}.

    Values and index are passed positionally rather than letting pandas align a
    str-keyed dict against a DatetimeIndex — that alignment silently yields all-NaN.
    """
    return pd.Series(list(values.values()), index=pd.to_datetime(list(values.keys())))


class TestExactArithmetic:
    def test_zero_premium_when_legs_agree(self):
        # One ADR = 0.1 local shares. Local share 1,000,000 KRW at 1000 KRW/USD is
        # $1,000, so a tenth of it is $100. An ADR priced at exactly $100 is parity.
        pi = compute_premium(
            _s({"2026-07-10": 100.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=0.1,
        )
        assert pi.iloc[0] == pytest.approx(0.0, abs=1e-12)

    def test_known_premium(self):
        # Same fair value of $100, ADR marked at $122 => exactly 22% premium, the
        # order of magnitude README §2 records for 2026-07-28.
        pi = compute_premium(
            _s({"2026-07-10": 122.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=0.1,
        )
        assert pi.iloc[0] == pytest.approx(0.22, abs=1e-12)

    def test_discount_is_negative(self):
        # Below the conversion floor: ADR->local is uncapped, so this state is the one
        # the barrier actually reflects (README §3).
        pi = compute_premium(
            _s({"2026-07-10": 95.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=0.1,
        )
        assert pi.iloc[0] == pytest.approx(-0.05, abs=1e-12)

    def test_tsm_ratio_five_shares_per_adr(self):
        # 1 TSM ADR = 5 ordinary shares. 5 x 1000 TWD = 5000 TWD at 32 TWD/USD is
        # $156.25; an ADR at $171.875 is exactly 10% rich.
        pi = compute_premium(
            _s({"2026-07-10": 171.875}), _s({"2026-07-10": 1000.0}),
            _s({"2026-07-10": 32.0}), local_shares_per_adr=5.0,
        )
        assert pi.iloc[0] == pytest.approx(0.10, abs=1e-12)


class TestFailureModes:
    def test_inverted_fx_is_catastrophic_not_subtle(self):
        """Guards the claim in smoke_premium's docstring that an inverted FX leg is
        obvious rather than plausible. If this ever fails, the docstring's advice to
        'check FX direction first' has stopped being good advice."""
        good = compute_premium(
            _s({"2026-07-10": 122.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=0.1,
        ).iloc[0]
        inverted = compute_premium(
            _s({"2026-07-10": 122.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1 / 1000.0}), local_shares_per_adr=0.1,
        ).iloc[0]
        assert good == pytest.approx(0.22)
        assert inverted < -0.999

    def test_ratio_error_scales_premium_by_the_ratio(self):
        """Using TSM's 5.0 on a SKHY-shaped observation is off by 50x, not by noise."""
        right = compute_premium(
            _s({"2026-07-10": 122.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=0.1,
        ).iloc[0]
        wrong = compute_premium(
            _s({"2026-07-10": 122.0}), _s({"2026-07-10": 1_000_000.0}),
            _s({"2026-07-10": 1000.0}), local_shares_per_adr=5.0,
        ).iloc[0]
        assert (1 + right) / (1 + wrong) == pytest.approx(50.0)


class TestJoinSemantics:
    def test_inner_join_drops_unmatched_dates_rather_than_filling(self):
        """A holiday on one exchange must shrink the sample, never carry a stale leg.

        Forward-filling here would manufacture premium moves out of calendar
        mismatch — the exact artifact D1(a) is already labelled for.
        """
        adr = _s({"2026-07-10": 122.0, "2026-07-13": 130.0, "2026-07-14": 125.0})
        local = _s({"2026-07-10": 1_000_000.0, "2026-07-14": 1_000_000.0})  # 07-13 KRX holiday
        fx = _s({"2026-07-10": 1000.0, "2026-07-13": 1000.0, "2026-07-14": 1000.0})
        pi = compute_premium(adr, local, fx, local_shares_per_adr=0.1)
        assert list(pi.index.strftime("%Y-%m-%d")) == ["2026-07-10", "2026-07-14"]
        assert pi.iloc[1] == pytest.approx(0.25)

    def test_nan_rows_are_dropped(self):
        adr = _s({"2026-07-10": 122.0, "2026-07-13": float("nan")})
        local = _s({"2026-07-10": 1_000_000.0, "2026-07-13": 1_000_000.0})
        fx = _s({"2026-07-10": 1000.0, "2026-07-13": 1000.0})
        assert len(compute_premium(adr, local, fx, 0.1)) == 1


class TestRegistryRatios:
    def test_skhy_ratio_matches_the_constitution(self):
        """README §2: '10 ADRs = 1 Korean common share' => 0.1 local shares per ADR."""
        assert pair_by_id("skhy").local_shares_per_adr == 0.1
        assert pair_by_id("skhy").confirmed is True

    def test_unconfirmed_ratios_are_flagged_not_assumed(self):
        """Every ratio the author has not signed off must advertise that fact, so no
        S3+ code can treat it as settled (README §11: sessions propose, never ratify)."""
        for pair_id in ("tsmc", "infy", "ibn", "baba"):
            pair = pair_by_id(pair_id)
            assert pair.confirmed is False
            assert "TODO(ash)" in pair.notes
