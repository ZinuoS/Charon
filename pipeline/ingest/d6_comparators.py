"""D6 — comparator panel: the training universe (README §4 D6, §8).

SKHY is a forward test and nothing is ever backtested on it. Every backtest in this
repo lives on this panel, so its coverage is the binding constraint on what S4/S5 can
claim.

Legs, in the priority order set by Task 3.2:

*   **TSMC** (``--tier tsmc``, the default) — TSM / 2330.TW / USDTWD. The structural
    twin: same asymmetric, quota-bound conversion regime as SKHY.
*   **Extended** (``--tier extended``) — Indian ADR pairs under conversion caps
    (INFY, IBN) plus BABA US/HK as the *unconstrained* control, where both lines are
    fully fungible and pi should sit at conversion cost with no one-sided drift. The
    contrast between constrained and unconstrained pairs is the identifying variation.

Dual-listed companies (Shell A/B, Rio/BHP) are the no-channel limit case and are
deferred to session 2 per Task 3.2.

Usage::

    uv run python -m pipeline.ingest.d6_comparators --tier all
"""

from __future__ import annotations

import argparse

from ._puller import (add_common_flags, bypass_cache, print_report,
                      resolve_pull_date, run_specs, select_specs)
from .registry import (D6_BRAZIL_SERIES, D6_EXTRA_SERIES, D6_PHILIPPINES_SERIES,
                       D6_TAIWAN_SERIES, D6_TSMC_SERIES)

SOURCE = "d6_comparators"

TIERS = {
    "tsmc": D6_TSMC_SERIES,
    "extended": D6_EXTRA_SERIES,
    "taiwan": D6_TAIWAN_SERIES,
    "brazil": D6_BRAZIL_SERIES,
    "philippines": D6_PHILIPPINES_SERIES,
    "all": (D6_TSMC_SERIES + D6_EXTRA_SERIES + D6_TAIWAN_SERIES + D6_BRAZIL_SERIES
            + D6_PHILIPPINES_SERIES),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", choices=sorted(TIERS), default="tsmc")
    add_common_flags(parser)
    args = parser.parse_args(argv)

    if args.no_cache:
        bypass_cache()
    specs = select_specs(TIERS[args.tier], args.only)
    pull_date = resolve_pull_date(SOURCE, args.pull_date, args.new_partition)

    ok, failed = run_specs(SOURCE, specs, pull_date=pull_date)
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
