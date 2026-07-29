"""Daily snapshot harness for sources whose history may not be retrievable.

Some series can only be built *forward*. If a provider serves a live view rather than a
time series, then every day not captured is lost permanently — there is no later pull
that recovers it. Two D-sources are in that category:

*   **D4 — Naver ETF NAV/AUM.** The endpoint returns the current NAV and market cap for
    every listed ETF. Whether history is retrievable is UNVERIFIED
    (`docs/data_sources.md` D4-a). If it is not, the AUM series that README §4 D4's
    rebalance-notional estimate depends on starts the day capture starts.
*   **D5 — KSD/SEIBro DR conversion capacity.** This one *does* have history back to
    2010, so it is not strictly perishable — but it is included here because the daily
    cadence and the post-2026-07-29 flow window are the whole point of H5, and a missed
    day during the barrier's first live weeks is worth more than a missed day in 2014.

Design: **append-only, one dated file per run, never overwritten.** A re-run on the same
day is a no-op if the bytes match and an error if they differ, exactly as the D1/D6
pullers behave. The snapshot is the raw response, stored verbatim; parsing happens
downstream, so a parser bug never destroys a capture that cannot be retaken.

**This module does not pull anything until the source is approved.** Each source is
gated by :func:`pipeline.ingest.approval.require_approved`, which reads the
``approved:`` field from ``docs/data_sources.md``. Approval is the author's decision
(README §11) and is not overridable in code. Running this today, with all 19 sources
still ``TODO(ash)``, prints exactly what is blocked and exits non-zero without touching
the network.

Scheduling
----------
Once a source is approved, capture must run daily and unattended. On macOS use launchd
rather than cron — cron does not survive sleep, and a laptop that was closed at the
scheduled minute simply skips the day, which is the failure this harness exists to
prevent. `launchd` with ``StartCalendarInterval`` runs the job on wake if the window was
missed. See ``docs/gate_reports/S1.md`` for the plist and install commands.

Usage::

    uv run python -m pipeline.ingest.snapshot_daily --list
    uv run python -m pipeline.ingest.snapshot_daily --source naver_etf_navlist
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable

from . import _common as C
from ._http import DEFAULT_CLIENT, ProviderError, RateLimited
from .approval import SourceNotApprovedError, approval_status, require_approved

SOURCE = "snapshots"


@dataclass(frozen=True)
class SnapshotSpec:
    """One snapshot target: what to fetch, and what is known about its timing."""

    source_id: str            # must match the `source:` key in docs/data_sources.md
    series_id: str
    url: str
    method: str               # "GET" | "POST" — POST targets need a body builder
    native_timezone: str
    availability_lag: str
    units: str
    encoding: str
    extension: str
    rationale: str
    body: Callable[[], dict] | None = None


SNAPSHOTS: tuple[SnapshotSpec, ...] = (
    SnapshotSpec(
        source_id="kodex_issuer_disclosure",
        series_id="kodex_skhynix_2x",
        url="https://www.kodex.com/kr/etf/0193T0",
        method="GET",
        native_timezone="Asia/Seoul",
        availability_lag=(
            "page carries an embedded timestamp (observed 20260728070300). NAV is struck "
            "against the KRX close 15:30 KST. TODO(ash): confirm the strike time and "
            "whether the embedded stamp is publication or as-of."
        ),
        units="TODO — page carries a NAV token and large integers but no explicit 순자산 label; parsing unresolved",
        encoding="UTF-8",
        extension="html",
        rationale=(
            "D4, issuer disclosure — cleaner provenance than the portal (robots.txt "
            "allows /etf). KODEX SK하이닉스 2x. CAPTURED BEFORE PARSED, deliberately: the "
            "AUM series may be snapshot-only, in which case every uncaptured day is lost "
            "permanently, whereas a parser can be written at leisure against stored bytes."
        ),
    ),
    SnapshotSpec(
        source_id="tiger_issuer_disclosure",
        series_id="tiger_etf_index",
        url="https://investments.miraeasset.com/tigeretf/",
        method="GET",
        native_timezone="Asia/Seoul",
        availability_lag="TODO(ash): unverified. tigeretf.com redirects to investments.miraeasset.com/tigeretf/; the per-product path is still unidentified.",
        units="TODO — landing page only; the per-product endpoint is unresolved",
        encoding="UTF-8",
        extension="html",
        rationale=(
            "D4, issuer disclosure (robots.txt allows /tigeretf/). The per-product URL "
            "pattern was not identified — guessed paths returned 404 — so this captures "
            "the landing page to start the series and preserve whatever it carries while "
            "the correct path is found."
        ),
    ),
    SnapshotSpec(
        source_id="naver_etf_navlist",
        series_id="naver_etf_navlist",
        url="https://finance.naver.com/api/sise/etfItemList.nhn",
        method="GET",
        native_timezone="Asia/Seoul",
        availability_lag=(
            "live snapshot; NAV is struck against the KRX close 15:30 KST. Capture "
            "after 18:00 KST to be safe. TODO(ash): confirm the NAV strike time."
        ),
        units="NAV in KRW per unit; marketSum (AUM) in KRW (100M units per Naver convention — TODO(ash) verify)",
        encoding="EUC-KR",
        extension="json",
        rationale=(
            "D4. Serves NAV and AUM for all 1,150 listed ETFs including the 16 single-stock "
            "2x products. UNVERIFIED whether history is retrievable; if not, every uncaptured "
            "day is permanently lost."
        ),
    ),
    SnapshotSpec(
        source_id="seibro_dr_capacity",
        series_id="seibro_dr_program_list",
        url="https://m.seibro.or.kr/cnts/ovssec/selectOverSecDRPubSearch.do",
        method="GET",
        native_timezone="Asia/Seoul",
        availability_lag="TODO(ash): KSD publication time for the daily capacity figure is unverified.",
        units="shares (DR전환가능주식수량 = remaining ordinary shares convertible into DRs)",
        encoding="UTF-8",
        extension="html",
        rationale=(
            "D5. The program list; per-ISIN daily series needs a POST with ISIN + Korean name. "
            "NOTE the semantics: this is HEADROOM (issuance ceiling minus DRs outstanding), "
            "NOT DR outstanding. Level = barrier state (M2); first difference = creation/"
            "cancellation flow (H5). See docs/data_sources.md D5-a."
        ),
    ),
)


def capture(spec: SnapshotSpec, pull_date: str | None = None) -> dict:
    """Capture one snapshot. Raises if the source is not approved."""
    require_approved(spec.source_id)

    partition = C.pull_partition(SOURCE, pull_date)
    out_path = partition / f"{spec.series_id}.{spec.extension}"
    pulled_at = C.utc_now_iso()

    if spec.method != "GET":
        raise NotImplementedError(
            f"{spec.series_id}: {spec.method} snapshots need a body builder; not implemented "
            "because the source is not yet approved and the payload format is unverified."
        )

    try:
        payload = DEFAULT_CLIENT.get(spec.url)
    except (RateLimited, ProviderError) as exc:
        C.append_pull_log(
            SOURCE,
            C.PullRecord(
                pulled_at_utc=pulled_at, source=SOURCE, series_id=spec.series_id,
                provider=spec.url, source_url=spec.url, params={"error": str(exc)},
                rows=0, first_obs_date=None, last_obs_date=None, sha256="",
                path=C.rel_to_repo(out_path), status="failed",
            ),
        )
        raise

    digest, written = C.write_immutable(out_path, payload)

    C.write_sidecar(
        out_path,
        {
            "series_id": spec.series_id,
            "source_id": spec.source_id,
            "provider": spec.url,
            "transport": "http_get",
            "source_url": spec.url,
            "pulled_at_utc": pulled_at,
            "native_timezone": spec.native_timezone,
            "availability_lag": spec.availability_lag,
            "units": spec.units,
            "encoding": spec.encoding,
            "snapshot_semantics": (
                "Point-in-time capture, append-only. This file is the RAW response; "
                "parsing is downstream so a parser bug cannot destroy an unrepeatable capture."
            ),
            "rationale": spec.rationale,
            "bytes": len(payload),
            "sha256": digest,
        },
    )
    C.append_pull_log(
        SOURCE,
        C.PullRecord(
            pulled_at_utc=pulled_at, source=SOURCE, series_id=spec.series_id,
            provider=spec.url, source_url=spec.url, params={"method": "GET"},
            rows=len(payload), first_obs_date=None, last_obs_date=None,
            sha256=digest, path=C.rel_to_repo(out_path),
            status="written" if written else "unchanged",
        ),
    )
    C.update_checksums(SOURCE, {C.rel_to_repo(out_path): digest})
    return {"series_id": spec.series_id, "bytes": len(payload), "sha256": digest[:12],
            "status": "written" if written else "unchanged"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", default=None, help="Capture one source_id (default: all approved).")
    parser.add_argument("--list", action="store_true", help="Show approval status and exit.")
    parser.add_argument("--pull-date", default=None)
    args = parser.parse_args(argv)

    specs = SNAPSHOTS
    if args.source:
        specs = tuple(s for s in SNAPSHOTS if s.source_id == args.source)
        if not specs:
            print(f"unknown source: {args.source}", file=sys.stderr)
            return 2

    print("\n=== snapshot harness ===")
    blocked, captured = [], []
    for spec in specs:
        status = approval_status(spec.source_id)
        if status != "yes":
            blocked.append((spec.source_id, status))
            print(f"  BLOCKED  {spec.series_id:26s} approval={status}")
            continue
        if args.list:
            print(f"  ready    {spec.series_id:26s} approval=yes")
            continue
        try:
            result = capture(spec, pull_date=args.pull_date)
            captured.append(result)
            print(f"  {result['status']:9s}{spec.series_id:26s} {result['bytes']}B sha={result['sha256']}")
        except SourceNotApprovedError as exc:
            blocked.append((spec.source_id, "no"))
            print(f"  BLOCKED  {spec.series_id:26s} {exc}")
        except (RateLimited, ProviderError) as exc:
            print(f"  FAILED   {spec.series_id:26s} {exc}")

    if blocked:
        print(
            f"\n  {len(blocked)} snapshot source(s) awaiting sign-off. Set `approved: yes` "
            "under the matching `source:` key in docs/data_sources.md to authorise.\n"
            "  Nothing was fetched for these; no network request was made."
        )
    return 1 if blocked and not captured else 0


if __name__ == "__main__":
    raise SystemExit(main())
