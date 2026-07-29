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
