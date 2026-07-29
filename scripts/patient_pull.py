"""Patient single-symbol pull for a throttled provider.

Yahoo never prohibited access — a 14-symbol burst tripped a rate limit, and a rate limit
is a request to slow down rather than a refusal. This script complies with it patiently:
one symbol, one host, a long initial delay, wide jitter, and a hard cap on attempts, with
the shared cache making every partial success permanent.

Usage:  uv run python -m scripts.patient_pull skhynix_local_daily
"""
from __future__ import annotations

import random
import sys
import time

from pipeline.ingest import _http, _puller
from pipeline.ingest.registry import series_by_id

SERIES = sys.argv[1] if len(sys.argv) > 1 else "skhynix_local_daily"
SOURCE = sys.argv[2] if len(sys.argv) > 2 else "d1_prices"

# Deliberately slow: 90s minimum spacing, 5-minute base backoff, 8 attempts. At worst
# this waits ~40 minutes; it will not add load to a host that is already refusing.
_http.DEFAULT_CLIENT = _http.FragileHttpClient(
    min_interval=90.0, base_backoff=300.0, max_attempts=8, rng=random.Random(20260729)
)
_puller._adapters.DEFAULT_CLIENT = _http.DEFAULT_CLIENT
import pipeline.ingest._adapters as _ad
_ad.DEFAULT_CLIENT = _http.DEFAULT_CLIENT
import pipeline.ingest._yahoo as _y
_y.DEFAULT_CLIENT = _http.DEFAULT_CLIENT

spec = series_by_id(SERIES)
print(f"patient pull: {spec.series_id} ({spec.symbol}) via {spec.providers}", flush=True)
t0 = time.monotonic()
try:
    result = _puller.pull_series(SOURCE, spec)
    print(f"OK {result}  in {time.monotonic()-t0:.0f}s", flush=True)
except Exception as exc:
    print(f"STILL BLOCKED after {time.monotonic()-t0:.0f}s: {exc}", flush=True)
    raise SystemExit(1)
