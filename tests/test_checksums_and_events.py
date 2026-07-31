"""Golden checksum verification and D7 event-calendar validation against live files.

These tests operate on whatever has actually been ingested. On a fresh clone the raw
payloads are absent (they are not tracked in git), so checksum tests skip rather than
fail — a missing file is a clone artefact, a *mismatched* file never is.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.ingest._common import CHECKSUM_ROOT, REPO_ROOT, sha256_file, verify_checksums
from pipeline.ingest.d7_events import (
    EVENTS_PATH,
    EventSchemaError,
    load_events,
    unresolved_known_from,
    validate,
)

MANIFESTS = sorted(p for p in CHECKSUM_ROOT.glob("*.json") if p.stem != "events_id_ledger")

# pytest evaluates the id callable even for an empty argvalues list, so it must
# tolerate the placeholder value it passes in that case (fresh clone, nothing ingested).
_manifest_id = lambda p: getattr(p, "stem", "none")  # noqa: E731


class TestChecksumManifests:
    @pytest.mark.skipif(not MANIFESTS, reason="nothing ingested yet")
    @pytest.mark.parametrize("manifest", MANIFESTS, ids=_manifest_id)
    def test_manifest_is_wellformed(self, manifest: Path):
        doc = json.loads(manifest.read_text())
        assert doc["source"] == manifest.stem
        assert doc["files"], f"{manifest.name} records no files"
        for rel, digest in doc["files"].items():
            assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), rel
            assert not Path(rel).is_absolute(), f"{rel} must be repo-relative"

    @pytest.mark.skipif(not MANIFESTS, reason="nothing ingested yet")
    @pytest.mark.parametrize("manifest", MANIFESTS, ids=_manifest_id)
    def test_present_files_match_their_recorded_digest(self, manifest: Path):
        """Missing is tolerated (fresh clone). MISMATCH never is."""
        results = verify_checksums(manifest.stem)
        mismatched = [rel for rel, status in results.items() if status == "MISMATCH"]
        assert not mismatched, (
            f"raw data changed after being recorded: {mismatched}\n"
            "Raw data is immutable (README §8). Do not regenerate the manifest."
        )

    @pytest.mark.skipif(not MANIFESTS, reason="nothing ingested yet")
    def test_every_recorded_file_has_a_metadata_sidecar(self):
        """Provenance is only complete if the payload, the sidecar and the manifest all
        agree; a file with no sidecar has no declared availability lag."""
        for manifest in MANIFESTS:
            doc = json.loads(manifest.read_text())
            for rel in doc["files"]:
                data_path = REPO_ROOT / rel
                if not data_path.exists():
                    continue
                side = data_path.with_suffix(data_path.suffix + ".meta.json")
                assert side.is_file(), f"{rel} has no .meta.json sidecar"
                meta = json.loads(side.read_text())
                assert meta["sha256"] == sha256_file(data_path), f"{rel}: sidecar digest disagrees with file"


class TestEventCalendar:
    def test_events_file_exists(self):
        assert EVENTS_PATH.is_file(), "D7 events.yaml is hand-maintained and must exist"

    def test_schema_validates(self):
        assert validate(load_events())

    def test_seeded_with_readme_section_2_events(self):
        ids = validate(load_events())
        for required in ("skhy_adr_listing", "skhy_conversion_open", "skhy_q2_earnings"):
            assert required in ids, f"{required} missing from the seeded calendar"

    def test_the_0729_confound_is_recorded_symmetrically(self):
        """README §5's confound register is only useful if both sides point at each
        other; a one-way link lets a design pick up the earnings event without
        inheriting the warning."""
        doc = load_events()
        by_id = {e["id"]: e for e in doc["events"]}
        conv, earn = by_id["skhy_conversion_open"], by_id["skhy_q2_earnings"]
        assert conv["date"] == earn["date"], "the confound is that these share a date"
        assert "skhy_q2_earnings" in conv["confounded_with"]
        assert "skhy_conversion_open" in earn["confounded_with"]

    def test_append_only_flag_is_set(self):
        assert load_events()["append_only"] is True

    def test_unresolved_known_from_is_surfaced_not_hidden(self):
        """`known_from` may legitimately be TODO(ash) at S1, but it must be reportable,
        because no event study may condition on an event whose announcement date is
        unknown (README §4 information-timing rule)."""
        pending = unresolved_known_from(load_events())
        assert isinstance(pending, list)

    def test_duplicate_ids_rejected(self):
        doc = load_events()
        doc["events"] = doc["events"] + [doc["events"][0]]
        with pytest.raises(EventSchemaError, match="duplicate"):
            validate(doc)

    def test_unknown_confound_reference_rejected(self):
        doc = load_events()
        doc["events"][0]["confounded_with"] = ["does_not_exist"]
        with pytest.raises(EventSchemaError, match="unknown id"):
            validate(doc)

    def test_append_only_false_rejected(self):
        doc = load_events()
        doc["append_only"] = False
        with pytest.raises(EventSchemaError, match="append_only"):
            validate(doc)


def test_supersessions_resolve_so_consumers_see_one_event_per_correction():
    """A corrected event must appear ONCE in the effective calendar, not twice.

    events.yaml is append-only, so a correction is a new entry and the original stays on
    disk. A consumer that reads the raw log draws both — the original and its correction —
    as two events on the same date. This is the check that the resolver is wired in.
    """
    from pipeline.viz import theme

    raw = theme.load_events(effective=False)
    eff = theme.load_events()
    superseded = {e["supersedes"] for e in raw if e.get("supersedes")}
    assert superseded, "no supersessions in the calendar — this test has nothing to protect"

    ids = {e["id"] for e in eff}
    assert not (ids & superseded), (
        f"superseded entries survived into the effective calendar: {sorted(ids & superseded)}. "
        "Every consumer would draw them alongside their own corrections."
    )
    assert len(eff) == len(raw) - len(superseded)
