"""D2 — macro context: KOSPI level, and both legs of the US-Korea short-rate differential.

Closes the three gaps G20 named, to the extent a sanctioned route existed:

  KOSPI                 LANDED   EODHD index symbology KS11.INDX
  US-KR rate diff       LANDED   FRED, public domain; Korea leg MONTHLY (OECD)
  foreign-investor flows  GAP    no route without a registration this repo does not hold

    uv run python -m pipeline.ingest.d2_macro
"""

from __future__ import annotations

import argparse

from ._puller import (add_common_flags, bypass_cache, print_report,
                      resolve_pull_date, run_specs, select_specs)
from .registry import D2_MACRO_SERIES

SOURCE = "d2_macro"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_common_flags(ap)
    args = ap.parse_args(argv)
    if args.no_cache:
        bypass_cache()
    ok, failed = run_specs(SOURCE, select_specs(D2_MACRO_SERIES, args.only),
                           pull_date=resolve_pull_date(SOURCE, args.pull_date,
                                                       args.new_partition))
    print_report(SOURCE, ok, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
