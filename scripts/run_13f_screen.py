"""Run the D9 13F screens and snapshot the result.

    uv run python -m scripts.run_13f_screen

Writes data/raw/d9_13f/<date>/screen.json. Slow by design: the shared client paces itself per
host, and the alternative — fanning out — is what cost session 1 its entire remaining budget.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pipeline.ingest import d9_thirteenf as D9
from pipeline.ingest._common import RAW_ROOT

QUARTERS = 4


def main() -> int:
    out: dict[str, dict] = {}
    for name, provenance in D9.MANAGERS.items():
        entry: dict = {"provenance": provenance, "cik": None, "resolved_as": None,
                       "quarters": [], "error": None}
        try:
            resolved = D9.resolve_filer(name, limit=QUARTERS)
            if resolved is None:
                entry["error"] = "no candidate CIK for this name has any 13F-HR filing"
                out[name] = entry
                print(f"  {name:28} NO 13F FILER")
                continue
            cik, title, filings = resolved
            entry["cik"], entry["resolved_as"] = cik, title
            for f in filings:
                rows = D9.holdings(cik, f["accession"])
                korea = D9.korea_positions(rows)
                entry["quarters"].append({
                    "report_date": f["report_date"], "accession": f["accession"],
                    # `positions` is the breadth confound made visible: a discount-family hit
                    # from a 15,000-line book is not the same observation as one from 60 lines.
                    "positions": len(rows),
                    "korea": [{"issuer": k["issuer"], "cusip": k["cusip"],
                               "value": k["value"], "shares": k["shares"]} for k in korea],
                    "discount_dna": D9.discount_dna(rows),
                })
            k = sum(len(q["korea"]) for q in entry["quarters"])
            d = sum(len(q["discount_dna"]) for q in entry["quarters"])
            print(f"  {name:28} cik={cik} quarters={len(entry['quarters'])} "
                  f"korea_positions={k} discount_families={d}")
        except Exception as exc:                      # one manager's failure must not end the run
            entry["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  {name:28} ERROR {entry['error'][:70]}")
        out[name] = entry

    root = Path(RAW_ROOT) / "d9_13f" / date.today().isoformat()
    root.mkdir(parents=True, exist_ok=True)
    (root / "screen.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {root/'screen.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
