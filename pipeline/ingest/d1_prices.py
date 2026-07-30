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

from ._puller import (add_common_flags, bypass_cache, print_report,
                      resolve_pull_date, run_specs, select_specs)
from .registry import D1_SERIES

SOURCE = "d1_prices"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_common_flags(parser)
    args = parser.parse_args(argv)

    specs = select_specs(D1_SERIES, args.only)
    if args.no_cache:
        bypass_cache()

    pull_date = resolve_pull_date(SOURCE, args.pull_date, args.new_partition)
    ok, failed = run_specs(SOURCE, specs, pull_date=pull_date)
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
