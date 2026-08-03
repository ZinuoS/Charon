"""Pull Schedule D 7.B.(1) Q24 prime-broker rosters for the screened advisers.

    uv run python -m scripts.run_pb_pull

Slow and heavy by design: the roster is per-private-fund and appears in no bulk file, so the
whole Form ADV has to be fetched per adviser. Several hundred pages each.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pipeline.ingest._common import RAW_ROOT
from pipeline.ingest.d10_adv import ADV_QUERY, firm_lookup, prime_brokers


def main() -> int:
    out: dict[str, dict] = {}
    for label, query in ADV_QUERY.items():
        firm = firm_lookup(query)
        if not firm:
            out[label] = {"error": "no US adviser registration"}
            print(f"  {label:28} no registration")
            continue
        try:
            res = prime_brokers(firm["crd"])
            out[label] = {"crd": firm["crd"], "firm_name": firm["firm_name"], **res}
            top = list(res["brokers"])[:3]
            print(f"  {label:28} {res['pages']:>4}pp  {len(res['brokers']):>3} brokers  "
                  f"{', '.join(top)[:60]}")
        except Exception as exc:
            out[label] = {"crd": firm["crd"], "error": f"{type(exc).__name__}: {exc}"}
            print(f"  {label:28} ERROR {str(exc)[:60]}")

    root = Path(RAW_ROOT) / "d10_adv" / date.today().isoformat()
    root.mkdir(parents=True, exist_ok=True)
    (root / "prime_brokers.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {root/'prime_brokers.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
