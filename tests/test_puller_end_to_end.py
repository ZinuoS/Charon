"""End-to-end puller plumbing, with the network stubbed out.

`pull_series` is the single path every daily series takes, so the four provenance
artefacts it must produce — raw payload, metadata sidecar, pull-log line, checksum entry
— are asserted here against a fake provider response rather than against a live pull.
That keeps the guarantee testable offline and on a rate-limited day, which is exactly
when a provenance bug would otherwise slip through unnoticed.
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from pipeline.ingest import _common as C
from pipeline.ingest import _adapters, _puller, _yahoo
from pipeline.ingest.registry import series_by_id

SPEC = series_by_id("skhy_adr_daily")

FAKE = pd.DataFrame(
    {
        "date": ["2026-07-10", "2026-07-13", "2026-07-14"],
        "open": [170.0, 166.0, 160.0],
        "high": [172.5, 167.0, 162.0],
        "low": [165.0, 159.5, 157.0],
        "close": [168.01, 160.0, 158.5],
        "adj_close": [168.01, 160.0, 158.5],
        "volume": [41_000_000, 22_000_000, 18_500_000],
    }
)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Redirect every write target into tmp_path so the real data tree is untouched."""
    raw, checks = tmp_path / "raw", tmp_path / "checksums"
    raw.mkdir()
    checks.mkdir()
    monkeypatch.setattr(C, "RAW_ROOT", raw)
    monkeypatch.setattr(C, "CHECKSUM_ROOT", checks)
    monkeypatch.setattr(C, "REPO_ROOT", tmp_path)
    _install_adapter(
        monkeypatch,
        lambda symbol, start=None, end=None: (FAKE.copy(), f"https://stub/{symbol}", {"interval": "1d"}),
    )
    return tmp_path


class _StubAdapter:
    """Stands in for a real provider so the puller's chain logic is exercised without
    a network call. Carries name/transport because the sidecar records both."""

    name = "yahoo_finance"
    transport = "chart_api_v8"

    def __init__(self, fn):
        self._fn = fn

    def fetch_daily(self, symbol, start=None, end=None):
        return self._fn(symbol, start=start, end=end)


def _install_adapter(monkeypatch, fn):
    monkeypatch.setattr(_adapters, "get", lambda name: _StubAdapter(fn))


class TestArtefacts:
    def test_pull_writes_all_four_artefacts(self, sandbox):
        summary = _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        assert summary["rows"] == 3
        assert summary["status"] == "written"

        csv_path = C.RAW_ROOT / "d1_prices" / "2026-07-14" / "skhy_adr_daily.csv"
        assert csv_path.is_file()
        assert csv_path.with_suffix(".csv.meta.json").is_file()
        assert (C.RAW_ROOT / "d1_prices" / "pull_log.jsonl").is_file()
        assert (C.CHECKSUM_ROOT / "d1_prices.json").is_file()

    def test_csv_is_deterministic_across_serialisations(self, sandbox):
        """Byte-identical output for identical input is what makes the golden checksums
        meaningful rather than noise."""
        assert _yahoo.to_csv_bytes(FAKE.copy()) == _yahoo.to_csv_bytes(FAKE.copy())

    def test_rerun_same_day_is_a_noop_not_an_error(self, sandbox):
        first = _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        second = _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        assert (first["status"], second["status"]) == ("written", "unchanged")
        assert first["sha256"] == second["sha256"]
        log = C.read_pull_log("d1_prices")
        assert [r["status"] for r in log] == ["written", "unchanged"]


class TestSidecarContents:
    def test_sidecar_declares_timing_units_and_provenance(self, sandbox):
        _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        meta = json.loads(
            (C.RAW_ROOT / "d1_prices" / "2026-07-14" / "skhy_adr_daily.csv.meta.json").read_text()
        )
        assert meta["provider"] == "yahoo_finance"
        assert meta["native_timezone"] == "America/New_York"
        assert meta["units"] == "USD per ADR"
        assert meta["rows"] == 3
        assert meta["availability_confirmed"] is False

    def test_sidecar_worked_example_matches_the_registry(self, sandbox):
        """The sidecar's timing example must be derived, not decorative: it has to agree
        with what the registry computes for the same date."""
        _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        meta = json.loads(
            (C.RAW_ROOT / "d1_prices" / "2026-07-14" / "skhy_adr_daily.csv.meta.json").read_text()
        )
        example = meta["example_timing_last_row"]
        last = date.fromisoformat(example["obs_date"])
        assert example["observation_ts_utc"] == SPEC.observation_ts_utc(last).isoformat()
        assert example["availability_ts_utc"] == SPEC.availability_ts_utc(last).isoformat()
        assert example["availability_ts_utc"] > example["observation_ts_utc"]


class TestFailureHandling:
    def test_provider_failure_is_logged_then_raised(self, sandbox, monkeypatch):
        """A puller that swallows an outage produces a short series that looks real."""
        def boom(symbol, start=None, end=None):
            raise _yahoo.ProviderError(f"{symbol}: stubbed outage")

        _install_adapter(monkeypatch, boom)
        with pytest.raises(_yahoo.ProviderError):
            _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")

        log = C.read_pull_log("d1_prices")
        assert log[-1]["status"] == "failed"
        assert log[-1]["rows"] == 0
        assert not (C.RAW_ROOT / "d1_prices" / "2026-07-14" / "skhy_adr_daily.csv").exists()

    def test_run_specs_reports_failures_instead_of_aborting(self, sandbox, monkeypatch):
        """Task 3: an unavailable source is reported, never silently substituted — and
        one bad symbol must not hide the ones that did work."""
        good = series_by_id("skhy_adr_daily")
        bad = series_by_id("usdkrw_spot_daily")

        # The FX leg is routed to frankfurter under a DIFFERENT symbol ("KRW", not
        # "KRW=X"), so the stub must fail on every alias the chain might try — otherwise
        # a fallback quietly succeeds and the test asserts nothing.
        bad_aliases = {bad.symbol, *bad.provider_symbols.values()}

        def selective(symbol, start=None, end=None):
            if symbol in bad_aliases:
                raise _yahoo.ProviderError(f"{symbol}: stubbed outage")
            return FAKE.copy(), f"https://stub/{symbol}", {"interval": "1d"}

        _install_adapter(monkeypatch, selective)
        ok, failed = _puller.run_specs("d1_prices", (good, bad), pull_date="2026-07-14")
        assert [r["series_id"] for r in ok] == ["skhy_adr_daily"]
        assert [f[0] for f in failed] == ["usdkrw_spot_daily"]


class TestImmutabilityAcrossPulls:
    def test_revised_history_raises_rather_than_overwriting(self, sandbox, monkeypatch):
        _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        revised = FAKE.copy()
        revised.loc[0, "close"] = 168.02  # provider silently restates day one
        _install_adapter(monkeypatch, lambda symbol, start=None, end=None: (revised.copy(), f"https://stub/{symbol}", {}))
        with pytest.raises(C.RawImmutabilityError):
            _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        # Original bytes survive; the revision goes to a new partition by the operator.
        csv_path = C.RAW_ROOT / "d1_prices" / "2026-07-14" / "skhy_adr_daily.csv"
        assert b"168.01" in csv_path.read_bytes()

    def test_new_partition_accepts_revised_history(self, sandbox, monkeypatch):
        _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-14")
        revised = FAKE.copy()
        revised.loc[0, "close"] = 168.02
        _install_adapter(monkeypatch, lambda symbol, start=None, end=None: (revised.copy(), f"https://stub/{symbol}", {}))
        summary = _puller.pull_series("d1_prices", SPEC, pull_date="2026-07-15")
        assert summary["status"] == "written"
        # latest_raw_file must resolve to the newest partition.
        assert C.latest_raw_file("d1_prices", "skhy_adr_daily.csv").parent.name == "2026-07-15"


class TestParsing:
    def test_chart_result_parses_into_the_declared_columns(self):
        result = {
            "meta": {"exchangeTimezoneName": "America/New_York"},
            "timestamp": [1783690200, 1783949400],
            "indicators": {
                "quote": [{
                    "open": [170.0, 166.0], "high": [172.5, 167.0],
                    "low": [165.0, 159.5], "close": [168.01, 160.0],
                    "volume": [41_000_000, 22_000_000],
                }],
                "adjclose": [{"adjclose": [168.01, 160.0]}],
            },
        }
        frame = _yahoo._parse_chart_result(result)
        assert list(frame.columns) == list(_yahoo.COLUMNS)
        assert len(frame) == 2
        assert frame["date"].is_monotonic_increasing

    def test_empty_timestamp_block_yields_empty_frame(self):
        frame = _yahoo._parse_chart_result({"meta": {}, "timestamp": [], "indicators": {}})
        assert frame.empty
        assert list(frame.columns) == list(_yahoo.COLUMNS)

    def test_all_null_price_rows_are_dropped(self):
        result = {
            "meta": {"exchangeTimezoneName": "America/New_York"},
            "timestamp": [1783690200, 1783949400],
            "indicators": {
                "quote": [{
                    "open": [170.0, None], "high": [172.5, None], "low": [165.0, None],
                    "close": [168.01, None], "volume": [41_000_000, None],
                }],
                "adjclose": [{"adjclose": [168.01, None]}],
            },
        }
        assert len(_yahoo._parse_chart_result(result)) == 1

    def test_fx_series_without_volume_still_serialises(self):
        """FX bars carry no volume; the nullable-int cast must tolerate that."""
        frame = FAKE.copy()
        frame["volume"] = None
        payload = _yahoo.to_csv_bytes(frame)
        assert payload.startswith(b"date,open,high,low,close,adj_close,volume")
