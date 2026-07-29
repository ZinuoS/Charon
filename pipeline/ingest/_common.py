"""Shared ingestion plumbing: paths, immutability, pull logging, checksums, sidecars.

This module is the only place in the repo that is allowed to *write* under
``data/raw/``. It enforces three doctrine rules from README §8 mechanically rather
than by convention:

1.  **Raw data is immutable.** :func:`write_immutable` refuses to change bytes that
    already exist on disk. A re-pull that produces identical bytes is a no-op; a
    re-pull that produces different bytes is an error the caller must resolve by
    pulling into a new date partition. The provider revising history is a *signal*,
    not a nuisance to be silently overwritten.
2.  **Every pull is logged.** :func:`append_pull_log` writes one JSON line per pull
    attempt with a UTC timestamp, the request parameters, the source URL, the row
    count and the resulting checksum. The log is append-only.
3.  **Ingestion is the only networked stage.** Nothing in this module is imported by
    analysis code; ``tests/test_no_network_in_analysis.py`` asserts that separation.

Layout written by this module::

    data/raw/<source>/pull_log.jsonl
    data/raw/<source>/<YYYY-MM-DD>/<series_id>.csv
    data/raw/<source>/<YYYY-MM-DD>/<series_id>.meta.json
    tests/golden/checksums/<source>.json
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = REPO_ROOT / "data" / "raw"
DERIVED_ROOT = REPO_ROOT / "data" / "derived"
CHECKSUM_ROOT = REPO_ROOT / "tests" / "golden" / "checksums"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """UTC timestamp, second precision, explicit offset. Used for every pull record."""
    return utc_now().replace(microsecond=0).isoformat()


def pull_partition(source: str, pull_date: str | None = None, *, create: bool = False) -> Path:
    """``data/raw/<source>/<YYYY-MM-DD>/`` for today's (or a given) pull.

    Does not create the directory by default: the path is needed *before* the fetch, to
    name the file in a failure log line, and a failed pull should not leave an empty
    partition behind for :func:`latest_raw_file` to walk past. The directory is created
    by :func:`write_immutable` when there is actually something to write.
    """
    day = pull_date or utc_now().date().isoformat()
    p = RAW_ROOT / source / day
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def next_partition_name(source: str, pull_date: str | None = None) -> str:
    """Next free same-day partition name, adding a ``.N`` suffix if needed."""
    day = pull_date or utc_now().date().isoformat()
    root = RAW_ROOT / source
    if not (root / day).exists():
        return day
    n = 2
    while (root / f"{day}.{n}").exists():
        n += 1
    return f"{day}.{n}"


def latest_partition(source: str) -> Path | None:
    """Most recent date partition for ``source``, or None if never pulled."""
    root = RAW_ROOT / source
    if not root.is_dir():
        return None
    days = sorted(d for d in root.iterdir() if d.is_dir() and _is_date_dir(d.name))
    return days[-1] if days else None


def latest_raw_file(source: str, filename: str) -> Path | None:
    """Newest existing copy of ``filename``, searching date partitions backwards.

    Analysis code reads raw data through this function so that a partition which
    happens to be missing one series falls back to the last partition that has it,
    rather than silently producing a short series.
    """
    root = RAW_ROOT / source
    if not root.is_dir():
        return None
    for day in sorted((d for d in root.iterdir() if d.is_dir() and _is_date_dir(d.name)), reverse=True):
        candidate = day / filename
        if candidate.is_file():
            return candidate
    return None


def _is_date_dir(name: str) -> bool:
    """``YYYY-MM-DD`` or ``YYYY-MM-DD.N`` (a sequenced same-day re-pull).

    The sequence suffix exists for the legitimate case of pulling the *same* series
    twice in one day under a *different* request — a widened date window, a changed
    provider, an upgraded data tier. Those produce different bytes, which
    :func:`write_immutable` correctly refuses to write over the earlier file, and the
    earlier file must survive: it is the record of what was actually available at the
    time. A sequenced partition keeps both, and sorts after the unsuffixed one so
    :func:`latest_raw_file` resolves to the newer pull.
    """
    base = name.split(".")[0]
    try:
        datetime.strptime(base, "%Y-%m-%d")
    except ValueError:
        return False
    suffix = name[len(base):]
    return suffix == "" or (suffix.startswith(".") and suffix[1:].isdigit())


# --------------------------------------------------------------------------------
# Checksums and immutability
# --------------------------------------------------------------------------------


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class RawImmutabilityError(RuntimeError):
    """Raised when a pull would change bytes that already exist under data/raw/."""


def write_immutable(path: Path, payload: bytes) -> tuple[str, bool]:
    """Write ``payload`` to ``path`` unless it already exists with different bytes.

    Returns ``(sha256, written)``. ``written`` is False when the file already existed
    with byte-identical content, which makes re-running a puller on the same day safe
    and free.

    Raises :class:`RawImmutabilityError` if the file exists with *different* bytes.
    That is not a failure to route around: it means the provider revised history, and
    the correct response is a new date partition plus a note in ``docs/deviations.md``.
    """
    digest = sha256_bytes(payload)
    if path.exists():
        existing = sha256_file(path)
        if existing == digest:
            return digest, False
        raise RawImmutabilityError(
            f"{path} already exists with a different checksum.\n"
            f"  on disk: {existing}\n"
            f"  new    : {digest}\n"
            "Raw data is immutable (README §8). Pull into a new date partition and "
            "record the provider revision in docs/deviations.md."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return digest, True


def update_checksums(source: str, entries: dict[str, str], *, allow_update: bool = False) -> Path:
    """Merge ``{relative_path: sha256}`` into ``tests/golden/checksums/<source>.json``.

    For immutable pulls the first write for a given relative path wins and is never
    silently replaced: a changed checksum for the same partition file would already
    have raised in :func:`write_immutable`, so a conflict here means the manifest was
    hand-edited.

    ``allow_update=True`` is for the single append-only file (``events.yaml``, README
    §4 D7), whose checksum is *expected* to move every time an event is appended. Its
    integrity is enforced structurally by the id ledger in ``d7_events`` instead, and
    the superseded digest is retained under ``history`` so the chain stays auditable.
    """
    CHECKSUM_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path = CHECKSUM_ROOT / f"{source}.json"
    manifest: dict[str, Any] = {"source": source, "files": {}}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest.setdefault("files", {})
    manifest.setdefault("history", {})
    for rel, digest in entries.items():
        prior = manifest["files"].get(rel)
        if prior is not None and prior != digest:
            if not allow_update:
                raise RawImmutabilityError(
                    f"checksum manifest conflict for {rel}: manifest has {prior}, pull produced {digest}"
                )
            manifest["history"].setdefault(rel, []).append({"sha256": prior, "superseded_at_utc": utc_now_iso()})
        manifest["files"][rel] = digest
    manifest["updated_at_utc"] = utc_now_iso()
    manifest["files"] = dict(sorted(manifest["files"].items()))
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def verify_checksums(source: str) -> dict[str, str]:
    """Verify every manifest entry for ``source``. Returns ``{rel: status}``.

    Status is one of ``ok``, ``missing``, ``MISMATCH``.
    """
    manifest_path = CHECKSUM_ROOT / f"{source}.json"
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text())
    out: dict[str, str] = {}
    for rel, expected in sorted(manifest.get("files", {}).items()):
        path = REPO_ROOT / rel
        if not path.is_file():
            out[rel] = "missing"
        elif sha256_file(path) == expected:
            out[rel] = "ok"
        else:
            out[rel] = "MISMATCH"
    return out


# --------------------------------------------------------------------------------
# Pull log
# --------------------------------------------------------------------------------

PULL_LOG_FIELDS = (
    "pulled_at_utc",
    "source",
    "series_id",
    "provider",
    "source_url",
    "params",
    "rows",
    "first_obs_date",
    "last_obs_date",
    "sha256",
    "path",
    "status",
)


@dataclass(frozen=True)
class PullRecord:
    """One line of ``pull_log.jsonl``. Field set is asserted by tests/test_pull_log.py."""

    pulled_at_utc: str
    source: str
    series_id: str
    provider: str
    source_url: str
    params: dict[str, Any]
    rows: int
    first_obs_date: str | None
    last_obs_date: str | None
    sha256: str
    path: str
    status: str  # "written" | "unchanged" | "failed"


def append_pull_log(source: str, record: PullRecord) -> Path:
    """Append one JSON line to ``data/raw/<source>/pull_log.jsonl`` (append-only)."""
    log_path = RAW_ROOT / source / "pull_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    return log_path


def read_pull_log(source: str) -> list[dict[str, Any]]:
    log_path = RAW_ROOT / source / "pull_log.jsonl"
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]


# --------------------------------------------------------------------------------
# Metadata sidecars
# --------------------------------------------------------------------------------


def write_sidecar(data_path: Path, meta: dict[str, Any]) -> Path:
    """Write ``<data_path>.meta.json`` describing provenance and timing semantics.

    Required keys (README §4 information-timing rule and the Task-3 sidecar spec):
    ``provider``, ``pulled_at_utc``, ``native_timezone``, ``availability_lag``,
    ``units``. Missing keys raise rather than defaulting — an undeclared availability
    lag is exactly the failure the firewall exists to prevent.
    """
    required = {"provider", "pulled_at_utc", "native_timezone", "availability_lag", "units"}
    missing = required - set(meta)
    if missing:
        raise ValueError(f"sidecar for {data_path.name} missing required keys: {sorted(missing)}")
    side = data_path.with_suffix(data_path.suffix + ".meta.json")
    side.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return side


def rel_to_repo(path: Path) -> str:
    return os.path.relpath(path, REPO_ROOT)
