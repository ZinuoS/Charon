"""Intraday tracker — the market-hours gate and honest gap logging, offline."""
from __future__ import annotations
from datetime import datetime, timezone
import pytest
from scripts import track_intraday as T


class TestMarketHoursGate:
    def _at(self, iso):
        return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)

    def test_skhy_open_during_us_cash_hours(self):
        skhy = next(l for l in T.LEGS if l.symbol == "skhy")
        # 2026-07-29 14:00 UTC = 10:00 ET, a weekday -> open
        assert T._market_open(skhy, self._at("2026-07-29T14:00:00"))

    def test_skhy_closed_overnight(self):
        skhy = next(l for l in T.LEGS if l.symbol == "skhy")
        assert not T._market_open(skhy, self._at("2026-07-29T03:00:00"))  # 23:00 ET prev day

    def test_weekend_is_closed(self):
        skhy = next(l for l in T.LEGS if l.symbol == "skhy")
        assert not T._market_open(skhy, self._at("2026-08-01T14:00:00"))  # Saturday

    def test_krx_leg_open_in_seoul_hours(self):
        loc = next(l for l in T.LEGS if l.symbol == "000660.KS")
        # 2026-07-29 02:00 UTC = 11:00 KST weekday -> open
        assert T._market_open(loc, self._at("2026-07-29T02:00:00"))


class TestFastFailClient:
    def test_client_is_bounded_to_one_attempt(self):
        """A real-time poll must not inherit the batch client's minutes-long backoff."""
        assert T.CLIENT.max_attempts == 1
        assert T.CLIENT.use_cache is False


class TestLegConfig:
    def test_skhy_is_the_reliable_leg(self):
        skhy = next(l for l in T.LEGS if l.symbol == "skhy")
        assert skhy.fetch == "nasdaq", "SKHY uses its own listing venue's realtime quote"

    def test_all_legs_have_a_fetcher(self):
        for leg in T.LEGS:
            assert leg.fetch in T.FETCHERS


class TestLaunchdPlist:
    def test_plist_is_wellformed_and_names_the_module(self):
        p = T._launchd_plist()
        assert "com.charon.intraday" in p and "scripts.track_intraday" in p
        assert "KeepAlive" in p  # restarts on wake/crash
