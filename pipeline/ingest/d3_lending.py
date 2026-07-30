"""D3 — securities-lending balances for 000660, from KOFIA FreeSIS.

Approved source: `kofia_freesis_lending` (docs/data_sources.md D3-b, `approved: yes`).
D3-a (KRX short-selling via pykrx) is NOT used: it needs credentials the repo does not hold
and runs against KRX ToS Art. 10(2), which is a refusal regardless of enforcement.

Why this matters downstream, in one line each:
  * M5 listed utilization states as blocked on D3. They are no longer blocked.
  * The financing sheet names RECALL RISK as the binding risk on a short-premium position
    and lists term borrow as a desk follow-up. Lending balance is the public half of it.

    uv run python -m pipeline.ingest.d3_lending
"""

from __future__ import annotations

import argparse
import sys

from . import _common as C
from ._adapters import KofiaAdapter
from ._http import ProviderError, RateLimited
from .approval import SourceNotApprovedError, require_approved

SOURCE = "d3_lending"
SERIES_ID = "skhynix_lending_daily"
SOURCE_ID = "kofia_freesis_lending"
ISSUE_CODE = "000660"


def pull(start: str = "20100101", pull_date: str | None = None) -> dict:
    require_approved(SOURCE_ID)          # author's gate; not overridable in code
    adapter = KofiaAdapter()
    pulled_at = C.utc_now_iso()
    partition = C.pull_partition(SOURCE, pull_date)
    out_path = partition / f"{SERIES_ID}.csv"

    try:
        rows, prov = adapter.fetch(ISSUE_CODE, start=start)
    except (RateLimited, ProviderError) as exc:
        C.append_pull_log(SOURCE, C.PullRecord(
            pulled_at_utc=pulled_at, source=SOURCE, series_id=SERIES_ID,
            provider=adapter.URL, source_url=adapter.URL, params={"error": str(exc)},
            rows=0, first_obs_date=None, last_obs_date=None, sha256="",
            path=C.rel_to_repo(out_path), status="failed"))
        raise

    df = adapter.to_frame(rows)
    if df.empty:
        raise ProviderError(f"{SERIES_ID}: endpoint returned no dated rows")

    digest, written = C.write_immutable(out_path, df.to_csv(index=False).encode())
    C.write_sidecar(out_path, {
        "series_id": SERIES_ID, "source_id": SOURCE_ID, "provider": adapter.URL,
        "transport": "http_post_json", "source_url": adapter.URL,
        "pulled_at_utc": pulled_at, "native_timezone": "Asia/Seoul",
        "availability_lag": (
            "KOFIA publishes T+1 for the previous session. TODO(ash): confirm the exact "
            "publication hour before this enters any same-day decision."
        ),
        "units": (
            "shares for new_lending/repaid/balance. balance_value_unverified_unit is landed "
            "UNPARSED: tmpV40=1000000 implies 백만원 but the implied per-share value is ~3.5x "
            "the traded price, so the unit is not established."
        ),
        "rows": len(df),
        "first_obs_date": str(df.date.min()), "last_obs_date": str(df.date.max()),
        "sha256": digest,
        "rationale": (
            "D3 lending leg. Endpoint and payload recovered by running the eXBuilder6 SPA in "
            "a browser and reading its own XHR; docs/data_sources.md D3-b previously recorded "
            "the payload format as un-reverse-engineerable."
        ),
    })
    C.append_pull_log(SOURCE, C.PullRecord(
        pulled_at_utc=pulled_at, source=SOURCE, series_id=SERIES_ID,
        provider=adapter.URL, source_url=adapter.URL, params=prov["params"],
        rows=len(df), first_obs_date=str(df.date.min()), last_obs_date=str(df.date.max()),
        sha256=digest, path=C.rel_to_repo(out_path),
        status="written" if written else "unchanged"))
    C.update_checksums(SOURCE, {C.rel_to_repo(out_path): digest})
    return {"series_id": SERIES_ID, "rows": len(df),
            "first": str(df.date.min()), "last": str(df.date.max()),
            "status": "written" if written else "unchanged"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="20100101")
    ap.add_argument("--pull-date", default=None)
    # Same gap the other pullers had: a same-day re-pull that returns REVISED numbers hits the
    # raw-immutability guard and stops the whole refresh. A revision is a different request,
    # so it gets its own partition rather than being blocked or overwritten.
    ap.add_argument("--new-partition", action="store_true",
                    help="Pull into a fresh same-day partition (YYYY-MM-DD.N). Use when the "
                         "provider has REVISED a same-day series, so both results survive.")
    args = ap.parse_args(argv)
    print("\n=== d3_lending ===")
    try:
        from ._puller import resolve_pull_date
        r = pull(start=args.start,
                 pull_date=resolve_pull_date(SOURCE, args.pull_date, args.new_partition))
    except SourceNotApprovedError as exc:
        print(f"  BLOCKED  {exc}"); return 1
    except (RateLimited, ProviderError) as exc:
        print(f"  FAILED   {exc}"); return 1
    print(f"  {r['status']:9s}{r['series_id']:26s} rows={r['rows']:6d}  {r['first']}..{r['last']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
