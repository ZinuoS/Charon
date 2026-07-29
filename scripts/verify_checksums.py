"""Verify every raw file against its recorded golden checksum (README §9, S1 gate).

Exit codes: 0 all ok, 1 any MISMATCH, 2 any missing file (and no mismatch).

A MISMATCH means bytes under ``data/raw/`` changed after they were recorded. That is
either a hand-edit or a corrupted file; neither is acceptable and neither should be
resolved by regenerating the manifest.
"""

from __future__ import annotations

import sys

from pipeline.ingest._common import CHECKSUM_ROOT, verify_checksums


def main() -> int:
    manifests = sorted(p.stem for p in CHECKSUM_ROOT.glob("*.json") if p.stem != "events_id_ledger")
    if not manifests:
        print("no checksum manifests found — nothing has been ingested yet.")
        return 0

    worst = 0
    for source in manifests:
        results = verify_checksums(source)
        ok = sum(1 for v in results.values() if v == "ok")
        print(f"\n=== {source} ===  {ok}/{len(results)} ok")
        for rel, status in results.items():
            if status != "ok":
                print(f"  {status:9s} {rel}")
                worst = max(worst, 1 if status == "MISMATCH" else 2)
    if worst == 1:
        print("\nCHECKSUM MISMATCH: raw data changed after it was recorded. Do not "
              "regenerate the manifest — find out what edited the file.")
    elif worst == 2:
        print("\nMissing files: recorded pulls are absent from data/raw/ (expected on a "
              "fresh clone, since raw payloads are not tracked in git).")
    else:
        print("\nAll recorded raw files verify.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
