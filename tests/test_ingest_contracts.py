"""Ingestion contracts: immutability, pull-log schema, sidecars, checksums.

These tests run against temporary directories rather than the live ``data/raw/`` tree,
so they pass on a clean checkout with no pulls performed. The separate
``test_checksums.py`` verifies whatever pulls *do* exist.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from pipeline.ingest import _common as C
from pipeline.ingest.registry import D1_SERIES, all_series, series_by_id


# --------------------------------------------------------------------------------
# Raw immutability
# --------------------------------------------------------------------------------


class TestImmutability:
    def test_first_write_creates_file(self, tmp_path: Path):
        target = tmp_path / "series.csv"
        digest, written = C.write_immutable(target, b"date,close\n2026-07-10,168.01\n")
        assert written is True
        assert target.read_bytes().startswith(b"date,close")
        assert digest == C.sha256_bytes(target.read_bytes())

    def test_identical_rewrite_is_a_free_noop(self, tmp_path: Path):
        """Re-running a puller the same day must be safe and cheap, not an error."""
        target = tmp_path / "series.csv"
        payload = b"date,close\n2026-07-10,168.01\n"
        d1, w1 = C.write_immutable(target, payload)
        d2, w2 = C.write_immutable(target, payload)
        assert (w1, w2) == (True, False)
        assert d1 == d2

    def test_differing_rewrite_raises_rather_than_overwrites(self, tmp_path: Path):
        """A provider revising history is a signal to record, not damage to absorb."""
        target = tmp_path / "series.csv"
        C.write_immutable(target, b"date,close\n2026-07-10,168.01\n")
        with pytest.raises(C.RawImmutabilityError) as exc:
            C.write_immutable(target, b"date,close\n2026-07-10,168.02\n")
        assert "immutable" in str(exc.value).lower()
        # Crucially: the original bytes survive the failed attempt.
        assert b"168.01" in target.read_bytes()


# --------------------------------------------------------------------------------
# Pull log
# --------------------------------------------------------------------------------


def _record(**overrides) -> C.PullRecord:
    base = dict(
        pulled_at_utc=C.utc_now_iso(), source="d1_prices", series_id="skhy_adr_daily",
        provider="yahoo_finance", source_url="https://example.invalid/chart/SKHY",
        params={"interval": "1d"}, rows=13, first_obs_date="2026-07-10",
        last_obs_date="2026-07-28", sha256="0" * 64, path="data/raw/x.csv", status="written",
    )
    base.update(overrides)
    return C.PullRecord(**base)


class TestPullLogSchema:
    def test_record_has_exactly_the_declared_fields(self):
        assert tuple(_record().__dataclass_fields__) == C.PULL_LOG_FIELDS

    def test_record_is_frozen(self):
        """A pull log that can be mutated after the fact is not provenance."""
        with pytest.raises(Exception):
            _record().rows = 99  # type: ignore[misc]

    def test_append_only_and_json_lines(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(C, "RAW_ROOT", tmp_path)
        C.append_pull_log("d1_prices", _record(series_id="a"))
        C.append_pull_log("d1_prices", _record(series_id="b"))
        lines = (tmp_path / "d1_prices" / "pull_log.jsonl").read_text().splitlines()
        assert len(lines) == 2
        assert [json.loads(x)["series_id"] for x in lines] == ["a", "b"]
        assert set(json.loads(lines[0])) == set(C.PULL_LOG_FIELDS)

    def test_utc_timestamp_is_offset_aware(self):
        assert C.utc_now_iso().endswith("+00:00")

    @pytest.mark.parametrize("status", ["written", "unchanged", "failed", "validated"])
    def test_known_statuses_round_trip(self, tmp_path: Path, monkeypatch, status):
        monkeypatch.setattr(C, "RAW_ROOT", tmp_path)
        C.append_pull_log("s", _record(status=status))
        assert C.read_pull_log("s")[0]["status"] == status


# --------------------------------------------------------------------------------
# Sidecars
# --------------------------------------------------------------------------------


class TestSidecar:
    REQUIRED = {"provider", "pulled_at_utc", "native_timezone", "availability_lag", "units"}

    def test_complete_sidecar_writes(self, tmp_path: Path):
        data = tmp_path / "s.csv"
        data.write_text("date,close\n")
        side = C.write_sidecar(data, {k: "x" for k in self.REQUIRED})
        assert side.name == "s.csv.meta.json"
        assert set(json.loads(side.read_text())) == self.REQUIRED

    @pytest.mark.parametrize("omit", sorted(REQUIRED))
    def test_missing_required_key_raises(self, tmp_path: Path, omit):
        """An undeclared availability lag is exactly what the firewall exists to stop,
        so it must fail loudly rather than default to zero."""
        data = tmp_path / "s.csv"
        data.write_text("date,close\n")
        meta = {k: "x" for k in self.REQUIRED if k != omit}
        with pytest.raises(ValueError, match=omit):
            C.write_sidecar(data, meta)


# --------------------------------------------------------------------------------
# Checksum manifest
# --------------------------------------------------------------------------------


class TestChecksumManifest:
    def test_merge_and_conflict(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(C, "CHECKSUM_ROOT", tmp_path)
        C.update_checksums("src", {"a.csv": "aa"})
        C.update_checksums("src", {"b.csv": "bb"})
        manifest = json.loads((tmp_path / "src.json").read_text())
        assert manifest["files"] == {"a.csv": "aa", "b.csv": "bb"}
        with pytest.raises(C.RawImmutabilityError):
            C.update_checksums("src", {"a.csv": "different"})

    def test_allow_update_retains_superseded_digest(self, tmp_path: Path, monkeypatch):
        """events.yaml is append-only, so its digest moves by design — but the chain of
        prior digests has to stay auditable."""
        monkeypatch.setattr(C, "CHECKSUM_ROOT", tmp_path)
        C.update_checksums("events", {"e.yaml": "v1"})
        C.update_checksums("events", {"e.yaml": "v2"}, allow_update=True)
        manifest = json.loads((tmp_path / "events.json").read_text())
        assert manifest["files"]["e.yaml"] == "v2"
        assert [h["sha256"] for h in manifest["history"]["e.yaml"]] == ["v1"]


# --------------------------------------------------------------------------------
# The information-timing firewall (README §4)
# --------------------------------------------------------------------------------


class TestAvailabilityTimestamps:
    def test_every_series_declares_lag_note_and_units(self):
        for spec in all_series():
            assert spec.availability_note.strip(), f"{spec.series_id} has no availability note"
            assert spec.units.strip(), f"{spec.series_id} has no units"
            assert spec.availability_lag >= timedelta(0), f"{spec.series_id} has a negative lag"

    def test_availability_is_never_before_observation(self):
        for spec in all_series():
            day = date(2026, 7, 28)
            assert spec.availability_ts_utc(day) >= spec.observation_ts_utc(day)

    def test_krx_close_precedes_nasdaq_close_by_about_13_5_hours(self):
        """The dual-close gap README §4 D1(a) calls a measurement artifact, asserted as
        a number so that a timezone regression cannot silently erase it."""
        day = date(2026, 7, 28)
        krx = series_by_id("skhynix_local_daily").observation_ts_utc(day)
        nasdaq = series_by_id("skhy_adr_daily").observation_ts_utc(day)
        gap_hours = (nasdaq - krx).total_seconds() / 3600
        assert gap_hours == pytest.approx(13.5, abs=0.01)

    def test_d1_series_cover_adr_local_and_fx(self):
        assert {s.asset_class for s in D1_SERIES} == {"adr", "local_equity", "fx"}

    def test_no_series_is_marked_confirmed_before_author_signoff(self):
        """Session 1 proposes timing assumptions; only the author ratifies them
        (README §11). Any True here means a session over-stepped."""
        assert [s.series_id for s in all_series() if s.confirmed] == []

    def test_every_series_a_pair_references_actually_resolves(self):
        """`all_series()` must span every D*_SERIES collection, not most of them.

        Korea and the Philippines were missing from the sum until 2026-08-03, so KT, SKM and
        PLDT were referenced by PAIRS, absent from `series_by_id`, and quietly exempt from
        every invariant in this class. The omission was invisible precisely because these
        tests iterate the same incomplete sum they were meant to police. Asserting reachability
        FROM PAIRS breaks that circularity: the pair registry is the independent witness.
        """
        from pipeline.ingest.registry import PAIRS, series_by_id

        missing = []
        for pair in PAIRS:
            for leg in (pair.adr, pair.local, pair.fx):
                try:
                    series_by_id(leg)
                except KeyError:
                    missing.append(f"{pair.pair_id}:{leg}")
        assert not missing, (
            f"PAIRS references series that all_series() cannot see: {missing}. A new "
            f"D*_SERIES collection must be added to all_series() in the same edit.")


class TestSequencedPartitions:
    """Same-day re-pulls under a DIFFERENT request must not destroy the earlier result.

    The motivating case is real: a provider tier upgrade widened 000660's available
    history from 243 rows to 2,839 mid-session. Both are legitimate records — the first
    of what was available under the free tier, the second under the upgraded one — and
    the newer must win for readers while the older survives on disk.
    """

    def test_sequenced_names_are_recognised_as_partitions(self):
        from pipeline.ingest._common import _is_date_dir
        assert _is_date_dir("2026-07-29")
        assert _is_date_dir("2026-07-29.2")
        assert _is_date_dir("2026-07-29.10")
        assert not _is_date_dir("2026-07-29.x")
        assert not _is_date_dir("scratch")

    def test_next_partition_skips_existing(self, tmp_path, monkeypatch):
        from pipeline.ingest import _common as C
        monkeypatch.setattr(C, "RAW_ROOT", tmp_path)
        assert C.next_partition_name("src", "2026-07-29") == "2026-07-29"
        (tmp_path / "src" / "2026-07-29").mkdir(parents=True)
        assert C.next_partition_name("src", "2026-07-29") == "2026-07-29.2"
        (tmp_path / "src" / "2026-07-29.2").mkdir()
        assert C.next_partition_name("src", "2026-07-29") == "2026-07-29.3"

    def test_sequenced_partition_wins_over_plain_same_day(self, tmp_path, monkeypatch):
        """The ordering that matters: a `.N` re-pull must resolve ahead of the plain one.

        Note this is NOT true of naive full-path sorting — '.' (46) sorts before '/' (47),
        so sorting paths puts the sequenced partition FIRST and silently returns the stale
        file. Sorting directory NAMES is what makes it correct, and this test pins that.
        """
        from pipeline.ingest import _common as C
        monkeypatch.setattr(C, "RAW_ROOT", tmp_path)
        for name, body in (("2026-07-29", b"old\n"), ("2026-07-29.2", b"new\n")):
            d = tmp_path / "src" / name
            d.mkdir(parents=True)
            (d / "s.csv").write_bytes(body)
        assert C.latest_raw_file("src", "s.csv").read_bytes() == b"new\n"
