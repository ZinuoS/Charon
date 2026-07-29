"""Coverage report: what is actually on disk, per series (README §9, S1/S3 gates).

Reports rows, date range, trading-day gaps and the declared availability timing for
every ingested series, plus which registry series have never been pulled. Coverage of
the D6 comparator panel — not of SKHY — is the binding constraint on what S4/S5 can
claim (README §8), so this is the report that decides whether S3 can open.

Offline: reads data/raw/ only.
"""

from __future__ import annotations

import sys
from datetime import date

import pandas as pd

from pipeline.ingest._common import RAW_ROOT, latest_raw_file
from pipeline.ingest.registry import PAIRS, all_series

SOURCE_OF = {
    "d1_prices": ("skhy_adr_daily", "skhynix_local_daily", "usdkrw_spot_daily"),
}


def _source_for(series_id: str) -> str:
    for source, ids in SOURCE_OF.items():
        if series_id in ids:
            return source
    return "d6_comparators"


def main() -> int:
    print(f"raw root: {RAW_ROOT}")
    rows = []
    missing = []

    for spec in all_series():
        path = latest_raw_file(_source_for(spec.series_id), f"{spec.series_id}.csv")
        if path is None:
            missing.append(spec.series_id)
            continue
        frame = pd.read_csv(path, parse_dates=["date"])
        d = frame["date"]
        # Largest gap in calendar days: a long gap is either a real market closure or a
        # silently truncated pull, and the two must not be confused at S3.
        gaps = d.diff().dt.days.dropna()
        rows.append({
            "series_id": spec.series_id,
            "symbol": spec.symbol,
            "rows": len(frame),
            "first": d.min().date(),
            "last": d.max().date(),
            "max_gap_days": int(gaps.max()) if len(gaps) else 0,
            "nan_close": int(frame["close"].isna().sum()),
            "tz": spec.timezone,
            "close_local": spec.close_local.strftime("%H:%M"),
            "timing_confirmed": spec.confirmed,
            "partition": path.parent.name,
        })

    if rows:
        table = pd.DataFrame(rows)
        print("\n=== series coverage ===")
        print(table.to_string(index=False))
    else:
        print("\nno ingested series found.")

    if missing:
        print(f"\n=== not yet pulled ({len(missing)}) ===")
        for series_id in missing:
            print(f"  {series_id}")

    print("\n=== pair readiness (all three legs present) ===")
    have = {r["series_id"] for r in rows}
    for pair in PAIRS:
        legs = {"adr": pair.adr, "local": pair.local, "fx": pair.fx}
        absent = [f"{k}:{v}" for k, v in legs.items() if v not in have]
        flag = "READY" if not absent else "incomplete"
        ratio_flag = "" if pair.confirmed else "  [ratio UNCONFIRMED — TODO(ash)]"
        print(f"  {pair.pair_id:6s} {flag:11s}{' missing ' + ', '.join(absent) if absent else ''}{ratio_flag}")

    print("\n=== timing declarations ===")
    unconfirmed = [s.series_id for s in all_series() if not s.confirmed]
    print(f"  {len(unconfirmed)}/{len(all_series())} series carry UNCONFIRMED availability assumptions.")
    print("  Per README §11 these are the author's to ratify; no S2+ work should treat them as settled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
