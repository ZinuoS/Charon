"""D2 — macro context: KOSPI level, and both legs of the US-Korea short-rate differential.

Closes the three gaps G20 named, to the extent a sanctioned route existed:

  KOSPI                 LANDED   EODHD index symbology KS11.INDX
  US-KR rate diff       LANDED   FRED, public domain; Korea leg MONTHLY (OECD)
  foreign-investor flows  GAP    no route without a registration this repo does not hold

    uv run python -m pipeline.ingest.d2_macro
"""

from __future__ import annotations

import argparse

from ._puller import print_report, run_specs
from .registry import D2_MACRO_SERIES

SOURCE = "d2_macro"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pull-date", default=None)
    args = ap.parse_args(argv)
    ok, failed = run_specs(SOURCE, D2_MACRO_SERIES, pull_date=args.pull_date)
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
