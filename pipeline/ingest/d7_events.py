"""D7 — event calendar: validate and checksum the hand-maintained YAML.

``data/raw/events/events.yaml`` is the one file under ``data/raw/`` that a human edits
(README §4 D7 / Task 3.5). Because it is not machine-generated, its integrity is
enforced here instead: this module validates the schema, enforces the append-only rule
against the previously recorded checksum, and logs each validation as a pull.

"Append-only" is checked structurally, not just by trust: the ids present in the
previous checksummed version must all still be present, in the same order, at the head
of the current file. Adding entries at the bottom passes; editing or removing one
fails.

Usage::

    uv run python -m pipeline.ingest.d7_events
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import yaml

from . import _common as C

SOURCE = "events"
EVENTS_PATH = C.RAW_ROOT / "events" / "events.yaml"
ID_LEDGER = C.CHECKSUM_ROOT / "events_id_ledger.json"

REQUIRED_EVENT_KEYS = {"id", "date", "known_from", "market", "category", "title", "detail", "source"}
VALID_MARKETS = {"US", "KR", "TW", "IN", "HK", "GLOBAL"}


class EventSchemaError(ValueError):
    pass


def load_events(path: Path = EVENTS_PATH) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found; D7 is hand-maintained and must exist.")
    return yaml.safe_load(path.read_text())


def validate(doc: dict) -> list[str]:
    """Return the ordered list of event ids, raising on any schema violation."""
    if doc.get("schema_version") != 1:
        raise EventSchemaError(f"unsupported schema_version: {doc.get('schema_version')!r}")
    if doc.get("append_only") is not True:
        raise EventSchemaError("append_only must be true; D7's exception to immutability is conditional on it.")

    events = doc.get("events") or []
    if not events:
        raise EventSchemaError("no events defined")

    ids: list[str] = []
    for i, ev in enumerate(events):
        missing = REQUIRED_EVENT_KEYS - set(ev)
        if missing:
            raise EventSchemaError(f"event[{i}] missing keys: {sorted(missing)}")
        if not isinstance(ev["date"], date):
            raise EventSchemaError(f"event {ev['id']!r}: `date` must parse as a YAML date, got {ev['date']!r}")
        if ev["market"] not in VALID_MARKETS:
            raise EventSchemaError(f"event {ev['id']!r}: market {ev['market']!r} not in {sorted(VALID_MARKETS)}")
        if ev["id"] in ids:
            raise EventSchemaError(f"duplicate event id: {ev['id']!r}")
        # `known_from` may legitimately still be TODO(ash) at S1: the announcement
        # dates are the author's to fill. It must be *present and declared*, though,
        # and no event study may run while any remain unresolved.
        ids.append(ev["id"])

    for ev in events:
        for other in ev.get("confounded_with") or []:
            if other not in ids:
                raise EventSchemaError(f"event {ev['id']!r}: confounded_with references unknown id {other!r}")
    return ids


def unresolved_known_from(doc: dict) -> list[str]:
    # Report on the EFFECTIVE calendar. A superseding entry that resolves a known_from is
    # the whole reason the supersedes mechanism exists; reading the raw log here meant a TODO
    # could never be closed and the OPEN list only ever grew.
    from pipeline.viz.theme import resolve_supersessions
    effective = resolve_supersessions(doc["events"])
    return [ev["id"] for ev in effective if str(ev.get("known_from", "")).startswith("TODO")]


def _entry_digest(ev: dict) -> str:
    """Stable digest of one event's content, for detecting an EDIT rather than an append."""
    return C.sha256_bytes(json.dumps(ev, sort_keys=True, default=str).encode())


def check_append_only(ids: list[str], events: list[dict] | None = None) -> str:
    """Compare against the recorded ledger. Returns a human-readable status.

    THE ID CHECK ALONE WAS A HOLE. It compared the id sequence and nothing else, so editing
    an existing entry's CONTENT -- a date, a known_from, a detail -- passed silently, while
    the guard's own error message told the reader that existing entries may not be edited.
    A calendar that can be quietly rewritten destroys every event study built on it, which is
    the exact failure the append-only rule exists to prevent, so the ledger now carries a
    per-entry digest and an edit is caught.
    """
    if not ID_LEDGER.exists():
        return "no prior ledger (first validation)"
    led = json.loads(ID_LEDGER.read_text())
    prior: list[str] = led["ids"]
    prior_digests: dict = led.get("entries", {})

    if events is not None and prior_digests:
        by_id = {e["id"]: e for e in events}
        edited = [i for i in prior
                  if i in by_id and _entry_digest(by_id[i]) != prior_digests.get(i)]
        if edited:
            raise EventSchemaError(
                "append-only violation in events.yaml: EXISTING ENTRIES WERE EDITED.\n"
                f"  changed: {edited}\n"
                "The id sequence is intact, so only the content digests catch this. To "
                "correct an event, append a new entry with `supersedes: <id>` and leave the "
                "original in place -- the record of what was believed when is itself data."
            )
    if ids[: len(prior)] != prior:
        raise EventSchemaError(
            "append-only violation in events.yaml.\n"
            f"  recorded head: {prior}\n"
            f"  current head : {ids[: len(prior)]}\n"
            "Existing entries may not be edited, reordered or removed. To correct an "
            "event, append a new entry with `supersedes: <id>`."
        )
    added = ids[len(prior):]
    return f"append-only ok (+{len(added)} new: {added})" if added else "append-only ok (unchanged)"


def write_ledger(ids: list[str], events: list[dict] | None = None) -> None:
    C.CHECKSUM_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {"ids": ids, "updated_at_utc": C.utc_now_iso()}
    if events is not None:
        payload["entries"] = {e["id"]: _entry_digest(e) for e in events}
    ID_LEDGER.write_text(json.dumps(payload, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check-only", action="store_true", help="Validate without updating the ledger or checksums.")
    args = parser.parse_args(argv)

    pulled_at = C.utc_now_iso()
    doc = load_events()
    ids = validate(doc)
    status = check_append_only(ids, doc.get("events"))
    digest = C.sha256_file(EVENTS_PATH)

    print(f"\n=== {SOURCE} ===")
    print(f"  events   : {len(ids)}  {ids}")
    print(f"  integrity: {status}")
    print(f"  sha256   : {digest[:12]}")

    pending = unresolved_known_from(doc)
    if pending:
        print(
            f"  OPEN     : known_from unresolved for {pending}. Event studies conditioned "
            "on these are blocked until you set the announcement dates."
        )

    if args.check_only:
        return 0

    C.write_sidecar(
        EVENTS_PATH,
        {
            "series_id": "events",
            "provider": "hand_maintained",
            "transport": "none",
            "pulled_at_utc": pulled_at,
            "native_timezone": "per-event (see `market`)",
            "availability_lag": "per-event `known_from` field; TODO(ash) where unresolved",
            "units": "discrete events",
            "rows": len(ids),
            "event_ids": ids,
            "unresolved_known_from": pending,
            "append_only": True,
            "sha256": digest,
            "notes": "README §4 D7. The one documented exception to raw-immutability; append-only.",
        },
    )
    C.append_pull_log(
        SOURCE,
        C.PullRecord(
            pulled_at_utc=pulled_at, source=SOURCE, series_id="events",
            provider="hand_maintained", source_url="file://data/raw/events/events.yaml",
            params={"check": "schema+append_only"}, rows=len(ids),
            first_obs_date=str(min(ev["date"] for ev in doc["events"])),
            last_obs_date=str(max(ev["date"] for ev in doc["events"])),
            sha256=digest, path=C.rel_to_repo(EVENTS_PATH), status="validated",
        ),
    )
    write_ledger(ids, doc.get("events"))
    # allow_update: events.yaml is append-only, so its digest is *supposed* to move.
    # Integrity is enforced by the id ledger above, not by digest stability.
    C.update_checksums(SOURCE, {C.rel_to_repo(EVENTS_PATH): digest}, allow_update=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
