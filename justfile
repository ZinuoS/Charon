# charon — task runner.  `just <target>`, or `just` to list.
#
# Ingestion and analysis are separate targets by doctrine (README §8): `ingest` is the
# only target permitted to touch the network, and `smoke` must run correctly with
# networking unavailable.

set shell := ["bash", "-uc"]

default:
    @just --list

# ---------------------------------------------------------------- environment

# Install the pinned environment from uv.lock.
setup:
    uv sync --python 3.12

# ---------------------------------------------------------------- S1: ingestion

# Full ingestion: D1 core legs, D6 TSMC comparator, D7 event calendar.
# Paced to stay inside the provider's rate limit; a full run takes a few minutes.
ingest: ingest-d1 ingest-d6 ingest-d7

# D1 — SKHY ADR, 000660.KS local, USDKRW spot.
ingest-d1:
    uv run python -m pipeline.ingest.d1_prices

# D6 — comparator panel. `just ingest-d6 all` for the extended tier (Indian pairs, BABA).
ingest-d6 tier="tsmc":
    uv run python -m pipeline.ingest.d6_comparators --tier {{tier}}

# D7 — validate the hand-maintained event calendar (schema + append-only + checksum).
ingest-d7:
    uv run python -m pipeline.ingest.d7_events

# ---------------------------------------------------------------- provenance

# Verify every raw file against tests/golden/checksums/. Non-zero on any mismatch.
checksums:
    uv run python -m scripts.verify_checksums

# What is on disk: series, row counts, date ranges, coverage gaps.
coverage:
    uv run python -m scripts.coverage_report

# ---------------------------------------------------------------- validation

# Ingestion smoke test (NOT S2): close-to-close premium for the SKHY and TSM pairs.
smoke:
    uv run python -m pipeline.measurement.smoke_premium

test:
    uv run pytest

# Everything an S1 gate review needs, offline.
check: test checksums coverage smoke

clean-derived:
    rm -rf data/derived/smoke

# ---------------------------------------------------------------- S4: validation

# The hard gate. Nothing downstream is trustworthy while this is red.
validate:
    uv run python -m scripts.validate

# ---------------------------------------------------------------- S4

# The per-regime metrics table. Regenerates from landed data; no network.
s4:
    uv run python -m scripts.s4_table

# D3 — securities-lending balances for 000660 (KOFIA FreeSIS).
ingest-d3:
    uv run python -m pipeline.ingest.d3_lending

# Perishable daily captures (TWSE SBL lendable supply, SEIBro DR headroom).
# No date inside these payloads, so an uncaptured day is lost permanently -- but NOT on the
# pitch path: TWSE SBL feeds only the utilization row-counter, and the cross-pair ablation it
# was for needs ~60 sessions. Run it when convenient; nothing in the pitch depends on it.
snapshot:
    uv run python -m pipeline.ingest.snapshot_daily

# ---------------------------------------------------------------- pitch day

# Everything the pitch reads, refreshed in dependency order. This is the ONLY thing that has
# to run on the morning: fresh borrow state -> table -> notebooks -> gate.
#
# Deliberately not a launchd job. It is one command on one morning; a scheduled job for that
# is more moving parts than the thing it automates.
pitch-refresh:
    uv run python -m scripts.pitch_refresh

# D2 — macro context (KOSPI, US/KR short rates).
ingest-d2:
    uv run python -m pipeline.ingest.d2_macro

# Push, then PROVE it: re-fetch the rendered public page and check the commit count moved
# and the expected paths are visible. A `git push` that exits 0 proves a ref moved on some
# remote, not that a reader sees it.
publish:
    uv run pytest -q
    uv run python -m scripts.pre_push_audit
    uv run python -m scripts.publish --push

# Verify the public page without pushing anything.
verify-public:
    uv run python -m scripts.publish
