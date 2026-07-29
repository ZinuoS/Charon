# tests/golden/

Frozen artefacts that make a refactor provable rather than hopeful (README §8:
"Golden regression tests frozen before any refactor").

## `checksums/`

One JSON manifest per ingestion source, recording the SHA-256 of every raw file at the
moment it was first pulled. This is the S1 gate condition.

- `<source>.json` — `{"source": ..., "files": {"<repo-relative path>": "<sha256>"}}`.
  A `history` block appears only for the append-only D7 calendar, retaining superseded
  digests.
- `events_id_ledger.json` — the ordered event ids last validated in
  `data/raw/events/events.yaml`. `pipeline.ingest.d7_events` compares against it to
  enforce append-only structurally: existing ids must still be present, in order, at the
  head of the file. Adding entries at the bottom passes; editing or removing one fails.

Verify with `just checksums`.

**A MISMATCH is never fixed by regenerating the manifest.** Raw bytes changed after
being recorded, which means either a hand-edit or corruption; find the cause. A
*missing* file is different and expected — raw payloads are not tracked in git, so a
fresh clone has manifests with nothing to verify against until `just ingest` runs.

## Adding golden tests for later stages

When S2+ modules land, freeze their outputs here **before** touching the code that
produces them, not after. A golden file written after a refactor records the refactor's
behaviour, not the behaviour it was supposed to preserve, and proves nothing.

Golden fixtures should be small enough to read and diff by eye. If a regression can only
be seen by comparing a 50MB array, the test will not be understood when it fails, and a
test nobody understands gets deleted rather than investigated.
