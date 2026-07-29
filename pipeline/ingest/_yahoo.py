"""Yahoo Finance daily-bar adapter.

Provider substitution note (see docs/deviations.md, 2026-07-28)
--------------------------------------------------------------
Session 1 was authorised to use ``yfinance``. In this environment ``yfinance==0.2.51``
fails on every symbol during its cookie/crumb handshake (``Expecting value: line 1
column 1``) while Yahoo's underlying public chart endpoint returns complete data for
the same symbols over plain HTTP. This module therefore talks to that endpoint directly,
through the shared fragility client in :mod:`pipeline.ingest._http`.

This is a change of *transport*, not of *provider*: the bytes originate from the same
Yahoo Finance service that ``yfinance`` wraps. The pull log records
``provider="yahoo_finance"`` and ``transport="chart_api_v8"`` so the distinction is
auditable and the swap is reversible — replacing :func:`fetch_daily` is the entire
migration surface.

Layering
--------
This module holds **no** retry, backoff, spacing or caching logic — all of that lives in
:mod:`pipeline.ingest._http`, the repo's single networked module. An adapter's whole job
is to turn one provider's payload into the repo's column contract, which is what keeps
providers swappable: a replacement reimplements :func:`fetch_daily` and nothing outside
``pipeline/ingest/`` changes.

Determinism
-----------
Analysis never calls this module (``tests/test_no_network_in_analysis.py`` enforces it).
Rows are emitted sorted by date with a fixed column order and fixed float formatting, so
the same response always produces the same bytes and therefore the same checksum.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from ._http import DEFAULT_CLIENT, ProviderError, RateLimited

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
PROVIDER = "yahoo_finance"
TRANSPORT = "chart_api_v8"


COLUMNS = ("date", "open", "high", "low", "close", "adj_close", "volume")


def build_url(symbol: str) -> str:
    return CHART_URL.format(symbol=symbol)


def build_params(start: str | None, end: str | None) -> dict[str, Any]:
    """Chart-API query parameters.

    ``events=div,split`` is requested so that adjusted closes are reproducible, and
    ``includeAdjustedClose=true`` so the adjusted series is present for total-return
    work later. Premium construction uses the RAW close, not the adjusted close —
    an ADR and its local line adjust on different dividend calendars, and mixing
    adjusted with raw across the legs silently injects a spurious premium step.
    """
    params: dict[str, Any] = {
        "interval": "1d",
        "events": "div,split",
        "includeAdjustedClose": "true",
    }
    if start is None:
        params["range"] = "max"
    else:
        params["period1"] = _to_epoch(start)
        params["period2"] = _to_epoch(end) if end else int(datetime.now(timezone.utc).timestamp())
    return params


def _to_epoch(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def fetch_daily(symbol: str, start: str | None = None, end: str | None = None) -> tuple[pd.DataFrame, str, dict]:
    """Fetch daily OHLCV for ``symbol``.

    Returns ``(frame, url, params)``. The frame has :data:`COLUMNS`, one row per
    trading day, sorted ascending, with rows that are entirely null dropped (Yahoo
    emits placeholder nulls for halted or non-trading sessions).
    """
    url = build_url(symbol)
    params = build_params(start, end)

    # All retry, backoff, jitter, spacing, single-flight and caching live in _http.
    # This adapter's only job is to turn Yahoo's JSON into the repo's column contract,
    # which is what makes the provider swappable: a replacement adapter reimplements
    # `fetch_daily` and nothing outside pipeline/ingest/ changes.
    try:
        raw = DEFAULT_CLIENT.get(url, params=params)
    except RateLimited as exc:
        raise ProviderError(f"{symbol}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"{symbol}: provider returned non-JSON ({len(raw)} bytes)") from exc

    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ProviderError(f"{symbol}: provider error {chart['error']}")
    result = chart.get("result")
    if not result:
        raise ProviderError(f"{symbol}: provider returned no result block")

    frame = _parse_chart_result(result[0])
    if frame.empty:
        raise ProviderError(f"{symbol}: provider returned zero usable rows")
    return frame, url, params


def _parse_chart_result(result: dict) -> pd.DataFrame:
    timestamps = result.get("timestamp") or []
    if not timestamps:
        # A valid response with no bars: a symbol that exists but has no history in the
        # requested window. Return empty rather than letting the DataFrame constructor
        # choke on scalar-None columns against an empty index.
        return pd.DataFrame(columns=list(COLUMNS))

    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    adj = (result.get("indicators", {}).get("adjclose") or [{}])
    adj_close = adj[0].get("adjclose") if adj else None

    tz_name = result.get("meta", {}).get("exchangeTimezoneName", "UTC")

    frame = pd.DataFrame(
        {
            "epoch": timestamps,
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "adj_close": adj_close if adj_close is not None else quote.get("close"),
            "volume": quote.get("volume"),
        }
    )
    if frame.empty:
        return pd.DataFrame(columns=list(COLUMNS))

    # Yahoo stamps each daily bar with the session-open instant in the exchange's own
    # timezone. Localising to the exchange tz before taking .date() is what keeps a
    # 09:00 KST bar from being filed under the previous UTC day.
    local = pd.to_datetime(frame["epoch"], unit="s", utc=True).dt.tz_convert(tz_name)
    frame["date"] = local.dt.date.astype(str)
    frame = frame.drop(columns=["epoch"])

    price_cols = ["open", "high", "low", "close", "adj_close"]
    frame = frame.dropna(subset=price_cols, how="all")
    frame = frame.drop_duplicates(subset=["date"], keep="last")
    frame = frame.sort_values("date").reset_index(drop=True)
    return frame[list(COLUMNS)]


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialise deterministically: fixed column order, fixed float repr, LF endings.

    ``float_format`` is pinned so that a re-pull of unchanged data yields byte-identical
    output and therefore an identical checksum. Without it, pandas' repr can vary across
    versions and the golden checksums become noise.
    """
    buf = io.StringIO()
    out = frame.copy()
    # FX series carry no volume at all, so the column can arrive as all-None object
    # dtype; coerce before the nullable-int cast rather than letting it raise.
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").astype("Int64")
    out.to_csv(buf, index=False, lineterminator="\n", float_format="%.6f")
    return buf.getvalue().encode("utf-8")
