"""Generic daily-series puller: fetch -> immutable write -> sidecar -> log -> checksum.

Every D-source that resolves to daily bars routes through :func:`pull_series`, so the
provenance guarantees are written once and cannot drift between pullers. A source that
needs different plumbing (a scraper, a hand-maintained file) gets its own module but
must produce the same four artefacts: raw payload, metadata sidecar, pull-log line, and
checksum manifest entry.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from . import _common as C
from . import _adapters, _yahoo
from .registry import SeriesSpec


def _fetch_via_chain(spec: SeriesSpec) -> tuple:
    """Try each routed provider in preference order; return the first that serves data.

    Ordering is by PROVENANCE, not convenience: for SKHY the Nasdaq adapter is the
    listing exchange itself and outranks any aggregator. The provider that actually
    served is returned so it can be recorded per-observation in the sidecar — a series
    assembled from a fallback must never be indistinguishable from one that was not.
    """
    errors = []
    for name in spec.providers:
        adapter = _adapters.get(name)
        symbol = spec.provider_symbols.get(name, spec.symbol)
        try:
            frame, url, params = adapter.fetch_daily(symbol, start=spec.start)
            if frame is not None and len(frame):
                return frame, url, params, adapter
        except Exception as exc:  # noqa: BLE001 — collected, then surfaced together
            errors.append(f"{name}({symbol}): {type(exc).__name__}: {exc}")
    raise _yahoo.ProviderError(
        f"{spec.series_id}: every routed provider failed.\n    " + "\n    ".join(errors)
    )


def pull_series(source: str, spec: SeriesSpec, pull_date: str | None = None) -> dict:
    """Pull one series and write all four provenance artefacts.

    Returns a summary dict for the caller's report. Failures are logged with
    ``status="failed"`` and re-raised: a puller that swallows a provider outage
    produces a short series that looks like a real one.
    """
    partition = C.pull_partition(source, pull_date)
    csv_path = partition / f"{spec.series_id}.csv"
    pulled_at = C.utc_now_iso()

    try:
        frame, url, params, provider = _fetch_via_chain(spec)
    except _yahoo.ProviderError as exc:
        C.append_pull_log(
            source,
            C.PullRecord(
                pulled_at_utc=pulled_at, source=source, series_id=spec.series_id,
                provider="|".join(spec.providers), source_url="(chain)",
                params={"error": str(exc)}, rows=0, first_obs_date=None, last_obs_date=None,
                sha256="", path=C.rel_to_repo(csv_path), status="failed",
            ),
        )
        raise

    payload = _adapters.to_csv_bytes(frame)
    digest, written = C.write_immutable(csv_path, payload)

    first_obs = str(frame["date"].iloc[0])
    last_obs = str(frame["date"].iloc[-1])

    C.write_sidecar(
        csv_path,
        {
            "series_id": spec.series_id,
            "symbol": spec.symbol,
            "provider": provider.name,
            "transport": provider.transport,
            "provider_chain": list(spec.providers),
            "provider_note": (
                "This series was served by the provider named above, selected from "
                "`provider_chain` in preference order. Provenance ordering is by source "
                "authority (issuer exchange > aggregator), not availability."
            ),
            "source_url": url,
            "request_params": {k: str(v) for k, v in params.items()},
            "pulled_at_utc": pulled_at,
            "native_timezone": spec.timezone,
            "market": spec.market,
            "close_local": spec.close_local.isoformat(),
            "availability_lag": _fmt_lag(spec),
            "availability_note": spec.availability_note,
            "availability_confirmed": spec.confirmed,
            "units": spec.units,
            "currency": spec.currency,
            "asset_class": spec.asset_class,
            "rows": int(len(frame)),
            "first_obs_date": first_obs,
            "last_obs_date": last_obs,
            # Worked example of the firewall, so a reader can verify the rule without
            # running code: what the last row's two timestamps actually are.
            "example_timing_last_row": {
                "obs_date": last_obs,
                "observation_ts_utc": spec.observation_ts_utc(date.fromisoformat(last_obs)).isoformat(),
                "availability_ts_utc": spec.availability_ts_utc(date.fromisoformat(last_obs)).isoformat(),
            },
            "sha256": digest,
            "notes": spec.notes,
        },
    )

    C.append_pull_log(
        source,
        C.PullRecord(
            pulled_at_utc=pulled_at, source=source, series_id=spec.series_id,
            provider=provider.name, source_url=url,
            params={k: str(v) for k, v in params.items()},
            rows=int(len(frame)), first_obs_date=first_obs, last_obs_date=last_obs,
            sha256=digest, path=C.rel_to_repo(csv_path),
            status="written" if written else "unchanged",
        ),
    )
    C.update_checksums(source, {C.rel_to_repo(csv_path): digest})

    return {
        "series_id": spec.series_id, "symbol": spec.symbol, "provider": provider.name,
        "rows": int(len(frame)),
        "first": first_obs, "last": last_obs, "sha256": digest[:12],
        "status": "written" if written else "unchanged",
    }


def _fmt_lag(spec: SeriesSpec) -> str:
    minutes = int(spec.availability_lag.total_seconds() // 60)
    return f"close {spec.close_local.isoformat()} {spec.timezone} + {minutes}min"


def run_specs(source: str, specs, pull_date: str | None = None) -> tuple[list[dict], list[tuple[str, str]]]:
    """Pull every spec; collect successes and failures rather than aborting on the first.

    Task 3 says to *stop and report* on an unavailable source rather than substitute.
    Collecting failures and surfacing them together at the end is that report — the
    caller prints them and exits non-zero, and nothing is quietly filled in.
    """
    ok: list[dict] = []
    failed: list[tuple[str, str]] = []
    for spec in specs:
        try:
            ok.append(pull_series(source, spec, pull_date=pull_date))
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            failed.append((spec.series_id, f"{type(exc).__name__}: {exc}"))
    return ok, failed


def print_report(source: str, ok: list[dict], failed: list[tuple[str, str]]) -> None:
    print(f"\n=== {source} ===")
    for row in ok:
        print(
            f"  {row['status']:9s} {row['series_id']:22s} {row['symbol']:12s} "
            f"via {row['provider']:12s} "
            f"rows={row['rows']:6d}  {row['first']}..{row['last']}  sha={row['sha256']}"
        )
    for series_id, err in failed:
        print(f"  FAILED    {series_id:24s} {err}")
    if failed:
        print(
            f"\n  {len(failed)} series unavailable. Per Task 3 these are reported, not "
            "substituted. Resolve the source before the S1 gate is signed."
        )
