"""D1 — core premium legs: SKHY ADR, 000660.KS local, USDKRW spot (daily bars).

README §4 D1. This session builds the *close-to-close* inputs only — variant D1(a),
the stale measure, with a ~13.5h gap between the KRX and Nasdaq closes. The
contemporaneous variant D1(b) needs the KRW NDF and the Eurex night-session KOSPI200
futures leg, neither of which has a confirmed public source yet (docs/data_sources.md).

Usage::

    uv run python -m pipeline.ingest.d1_prices
"""

from __future__ import annotations

import argparse
import sys

from ._puller import print_report, run_specs
from .registry import D1_SERIES

SOURCE = "d1_prices"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--pull-date", default=None,
        help="Override the YYYY-MM-DD raw partition (default: today, UTC).",
    )
    parser.add_argument(
        "--new-partition", action="store_true",
        help="Pull into a fresh same-day partition (YYYY-MM-DD.N). Use when a re-pull is "
             "a DIFFERENT request than the earlier one — widened window, changed provider, "
             "upgraded tier — so both results survive on disk.",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Bypass the local response cache. REQUIRED after a provider capability "
             "change (tier upgrade, new entitlement): the cache is keyed on URL+params, "
             "which do not change when your plan does, so a cached pre-upgrade response "
             "will be served indefinitely and silently.",
    )
    parser.add_argument(
        "--only", default=None,
        help="Comma-separated series_ids to pull (default: all D1 series).",
    )
    args = parser.parse_args(argv)

    specs = D1_SERIES
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        specs = tuple(s for s in specs if s.series_id in wanted)
        if not specs:
            print(f"no D1 series matched {sorted(wanted)}", file=sys.stderr)
            return 2

    if args.no_cache:
        from . import _adapters, _http, _yahoo
        client = _http.FragileHttpClient(use_cache=False)
        _http.DEFAULT_CLIENT = _adapters.DEFAULT_CLIENT = _yahoo.DEFAULT_CLIENT = client
        print("cache bypassed for this pull")

    pull_date = args.pull_date
    if args.new_partition and not pull_date:
        from ._common import next_partition_name
        pull_date = next_partition_name(SOURCE)
        print(f"pulling into fresh partition: {pull_date}")
    ok, failed = run_specs(SOURCE, specs, pull_date=pull_date)
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
