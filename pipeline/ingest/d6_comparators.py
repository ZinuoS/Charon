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

from ._puller import print_report, run_specs
from .registry import D6_EXTRA_SERIES, D6_TSMC_SERIES

SOURCE = "d6_comparators"

TIERS = {
    "tsmc": D6_TSMC_SERIES,
    "extended": D6_EXTRA_SERIES,
    "all": D6_TSMC_SERIES + D6_EXTRA_SERIES,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", choices=sorted(TIERS), default="tsmc")
    parser.add_argument("--pull-date", default=None, help="Override the YYYY-MM-DD raw partition.")
    args = parser.parse_args(argv)

    ok, failed = run_specs(SOURCE, TIERS[args.tier], pull_date=args.pull_date)
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
