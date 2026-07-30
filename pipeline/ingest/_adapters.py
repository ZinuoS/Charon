"""Provider adapters. One class per source; all emit the same column contract.

The Session 1 outage established that a single provider is a single point of failure.
Each adapter here converts one provider's payload into ``_yahoo.COLUMNS`` and nothing
else — retry, backoff, spacing, single-flight and caching all live in
:mod:`pipeline.ingest._http`. Adding a provider means writing one class; no module
outside ``pipeline/ingest/`` changes, because provenance travels in the sidecar rather
than in an import path.

Coverage as probed 2026-07-29 (see ``docs/gate_reports/S1.md`` for the full findings):

======================  =========================================  ==========
Adapter                 Covers                                     Access
======================  =========================================  ==========
``NasdaqAdapter``       US equities/ADRs: SKHY, TSM, INFY, IBN...   keyless
``TwseAdapter``         Taiwan listed equities: 2330                keyless
``FrankfurterAdapter``  ECB reference FX: KRW, HKD, INR (no TWD)    keyless
``YahooAdapter``        everything, when not throttled              keyless
======================  =========================================  ==========

Provenance note worth carrying into the notebook: for **SKHY the Nasdaq adapter is the
listing exchange's own data**, and for **2330 the TWSE adapter is the issuer exchange's**.
Both are strictly better provenance than the aggregator this repo started on.
"""

from __future__ import annotations

import re
import datetime as _dt

import io
import json
from datetime import date, datetime, timedelta
from pathlib import Path as _Path
from typing import Any

import pandas as pd

from . import _yahoo
from ._http import DEFAULT_CLIENT, ProviderError

COLUMNS = _yahoo.COLUMNS
_REPO_ROOT = _Path(__file__).resolve().parents[2]


def _frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=list(COLUMNS))
    for col in COLUMNS:
        if col not in frame:
            frame[col] = pd.NA
    frame = frame.dropna(subset=["close"])
    frame = frame.drop_duplicates(subset=["date"], keep="last")
    return frame.sort_values("date").reset_index(drop=True)[list(COLUMNS)]


def _num(value: Any) -> float | None:
    """Parse a provider's number: strips $ , % and treats '--'/'' as missing."""
    if value is None:
        return None
    text = str(value).replace("$", "").replace(",", "").replace("%", "").strip()
    if text in ("", "--", "N/A", "null", "-"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


# --------------------------------------------------------------------------------


class NasdaqAdapter:
    """Nasdaq's public quote API. Keyless.

    For SKHY this is the **listing exchange itself** (README §2: SKHY lists on Nasdaq),
    which makes it the authoritative source rather than a redistribution of one.

    ``totalRecords`` is echoed by the provider and is checked against the parsed row
    count: a silent truncation would otherwise look like a short history.
    """

    name = "nasdaq"
    transport = "api_quote_historical"
    URL = "https://api.nasdaq.com/api/quote/{symbol}/historical"

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        url = self.URL.format(symbol=symbol)
        params = {
            "assetclass": "stocks",
            "fromdate": start or "1990-01-01",
            "todate": end or date.today().isoformat(),
            "limit": "99999",
        }
        payload = json.loads(DEFAULT_CLIENT.get(url, params=params))
        data = (payload or {}).get("data") or {}
        table = data.get("tradesTable") or {}
        rows_in = table.get("rows") or []
        if not rows_in:
            raise ProviderError(f"{symbol}: nasdaq returned no rows ({payload.get('status')})")

        rows = []
        for r in rows_in:
            try:
                obs = datetime.strptime(r["date"], "%m/%d/%Y").date().isoformat()
            except (KeyError, ValueError):
                continue
            close = _num(r.get("close"))
            rows.append({
                "date": obs, "open": _num(r.get("open")), "high": _num(r.get("high")),
                "low": _num(r.get("low")), "close": close,
                # Nasdaq serves raw prices only. adj_close is set equal to close and the
                # sidecar records that: premium construction uses raw closes anyway
                # (mixing adjusted and raw across legs injects a phantom premium step).
                "adj_close": close, "volume": _num(r.get("volume")),
            })
        frame = _frame(rows)
        declared = data.get("totalRecords")
        if declared and len(frame) < int(declared) * 0.9:
            raise ProviderError(
                f"{symbol}: nasdaq declared {declared} records, parsed {len(frame)} — possible truncation"
            )
        return frame, url, params


class TwseAdapter:
    """Taiwan Stock Exchange `STOCK_DAY`. Keyless, and the issuer exchange for 2330.

    Two conventions that will silently corrupt a series if missed:

    *   **Dates are Republic-of-China calendar.** ``115/07/28`` is 2026-07-28: add 1911
        to the year. A naive parse yields year 115 AD.
    *   **The endpoint is monthly.** One request returns one calendar month for one
        stock, so history is assembled by iterating months — which is why this adapter
        is the slowest and why the shared cache matters most here.
    """

    name = "twse"
    transport = "exchangeReport_STOCK_DAY"
    URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        stock_no = symbol.split(".")[0]
        first = date.fromisoformat(start) if start else date(2010, 1, 1)
        last = date.fromisoformat(end) if end else date.today()

        rows: list[dict] = []
        cursor = date(first.year, first.month, 1)
        while cursor <= last:
            params = {"response": "json", "date": cursor.strftime("%Y%m01"), "stockNo": stock_no}
            try:
                payload = json.loads(DEFAULT_CLIENT.get(self.URL, params=params))
            except ProviderError:
                payload = {}
            if payload.get("stat") == "OK":
                rows.extend(self._parse_month(payload))
            cursor = (cursor.replace(day=28) + timedelta(days=8)).replace(day=1)

        if not rows:
            raise ProviderError(f"{symbol}: twse returned no rows for {first}..{last}")
        frame = _frame(rows)
        frame = frame[(frame["date"] >= first.isoformat()) & (frame["date"] <= last.isoformat())]
        return frame.reset_index(drop=True), self.URL, {"stockNo": stock_no, "months": "iterated"}

    @staticmethod
    def _parse_month(payload: dict) -> list[dict]:
        out = []
        for row in payload.get("data") or []:
            try:
                roc_y, mm, dd = row[0].split("/")
                obs = date(int(roc_y) + 1911, int(mm), int(dd)).isoformat()
            except (ValueError, IndexError):
                continue
            close = _num(row[6])
            out.append({
                "date": obs, "open": _num(row[3]), "high": _num(row[4]),
                "low": _num(row[5]), "close": close, "adj_close": close,
                "volume": _num(row[1]),
            })
        return out


class FrankfurterAdapter:
    """ECB daily reference rates via frankfurter.dev. Keyless.

    **Timing provenance, which is the reason to prefer this over an aggregator:** ECB
    reference rates are struck at a *published, documented* time (~14:15 CET / 16:00 CET
    publication), whereas the Yahoo FX snapshot instant is undocumented and had to be
    assumed (``pipeline/ingest/registry.py``). A known fix time is directly useful to
    confound C2, which is about mismatched observation instants.

    **Caveat that must reach the sidecar:** ECB publishes EUR-based rates, so USD/KRW
    here is a *cross* (EUR/KRW ÷ EUR/USD), not a directly quoted pair. It is a reference
    rate, not a tradable one.

    **Coverage:** 30 currencies. KRW, HKD and INR are present; **TWD is not** — verified,
    the endpoint 404s — so the TSM pair's FX leg cannot be sourced here.
    """

    name = "frankfurter"
    transport = "ecb_reference_v1"
    BASE = "https://api.frankfurter.dev/v1"

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        quote = symbol.upper()
        first = start or "1999-01-04"
        last = end or date.today().isoformat()
        url = f"{self.BASE}/{first}..{last}"
        params = {"base": "USD", "symbols": quote}
        payload = json.loads(DEFAULT_CLIENT.get(url, params=params))
        rates = (payload or {}).get("rates") or {}
        if not rates:
            raise ProviderError(f"{symbol}: frankfurter has no data for {quote} (ECB set excludes TWD)")
        rows = [
            {"date": day, "open": None, "high": None, "low": None,
             "close": vals.get(quote), "adj_close": vals.get(quote), "volume": None}
            for day, vals in sorted(rates.items())
        ]
        return _frame(rows), url, params


class YahooAdapter:
    """Yahoo chart API, wrapping the existing parser. Kept as a fallback.

    Demoted from primary after the Session 1 outage: it throttles an unauthenticated
    client for hours and covers no series that a better-provenance source cannot.
    """

    name = "yahoo_finance"
    transport = "chart_api_v8"

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        return _yahoo.fetch_daily(symbol, start=start, end=end)


ADAPTERS: dict[str, Any] = {
    a.name: a() for a in (NasdaqAdapter, TwseAdapter, FrankfurterAdapter, YahooAdapter)
}


def get(name: str):
    if name not in ADAPTERS:
        raise KeyError(f"unknown adapter {name!r}; known: {sorted(ADAPTERS)}")
    return ADAPTERS[name]


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return _yahoo.to_csv_bytes(frame)


class FredAdapter:
    """FRED (St. Louis Fed) observations API. Requires a free key.

    Why this matters beyond filling the TWD gap: FRED's H.10 rates are **noon buying
    rates in New York**, a *published, documented* fix instant. Every other FX source in
    this repo is either an undocumented snapshot (Yahoo) or a different documented fix
    (ECB ~16:00 CET via frankfurter). Holding two differently-timed fixes for USD/KRW is
    what lets the FX-observation-instant component of confound C2 be **measured** rather
    than assumed.

    That also means **FRED and frankfurter are not expected to agree tightly**. They are
    different fixes of the same pair, hours apart. Reconciling them with the default
    equity tolerance would flag every day; see ``FX_FIX_RTOL`` in
    :mod:`pipeline.ingest.reconcile` and the per-series tolerance in the registry.

    Key handling: the key is read from ``FRED_API_KEY`` (or a gitignored ``.env``) and is
    **scrubbed from the returned url and params**, because those are written verbatim
    into the pull log and the metadata sidecar, both of which are committed.

    Licence: DEXKOUS/DEXTAUS are Public Domain (citation requested). FRED's terms require
    any application built on the API to state that it uses the FRED API and is **not
    endorsed or certified by the Federal Reserve Bank of St. Louis** — that notice
    belongs on the dashboard and in the notebook footer.
    """

    name = "fred"
    transport = "fred_observations_v1"
    URL = "https://api.stlouisfed.org/fred/series/observations"

    @staticmethod
    def _key() -> str:
        import os
        key = os.environ.get("FRED_API_KEY")
        if not key:
            env = _REPO_ROOT / ".env"
            if env.is_file():
                for line in env.read_text().splitlines():
                    if line.strip().startswith("FRED_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
        if not key:
            raise ProviderError(
                "FRED_API_KEY is not set. Obtain a free key at "
                "https://fredaccount.stlouisfed.org/apikeys (email only, no identity "
                "verification) and put it in .env as FRED_API_KEY=... — .env is gitignored."
            )
        return key

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        params = {
            "series_id": symbol,
            "file_type": "json",
            "observation_start": start or "1990-01-01",
            "observation_end": end or date.today().isoformat(),
        }
        payload = json.loads(DEFAULT_CLIENT.get(self.URL, params={**params, "api_key": self._key()}))
        obs = (payload or {}).get("observations") or []
        if not obs:
            raise ProviderError(f"{symbol}: fred returned no observations")
        rows = []
        for o in obs:
            # FRED encodes a missing value (market holiday) as ".", not null.
            v = _num(o.get("value")) if o.get("value") != "." else None
            if v is None:
                continue
            rows.append({"date": o["date"], "open": None, "high": None, "low": None,
                         "close": v, "adj_close": v, "volume": None})
        frame = _frame(rows)
        if frame.empty:
            raise ProviderError(f"{symbol}: fred returned only missing values")
        # Key deliberately absent from both returned values — they are persisted verbatim.
        return frame, self.URL, params


ADAPTERS["fred"] = FredAdapter()


class EodhdAdapter:
    """EODHD end-of-day API. Requires a free key.

    Covers KRX, where the keyless providers do not: SK Hynix resolves as **``000660.KO``**
    — note the exchange code is ``KO``, *not* Yahoo's ``.KS`` — so a symbol ported from a
    Yahoo-based pipeline needs the suffix changed or it silently 404s.

    Free tier is documented as one year of history at 20 API calls/day. That is thin in
    general but **ample for this repo's binding need**: the SKHY ADR listed 2026-07-10, so
    the local leg only has to reach back ~13 trading days for the premium series to exist.
    Deeper local history (for S3 panel work) is what the paid tier buys.

    ⚠️ **Licence.** EODHD's terms prohibit *"Selling, reselling, retransmitting,
    redistributing, displaying, or granting access to the Information or Services, whether
    in its original or repackaged form"*, with **no derived-data carve-out**. This repo
    commits derived series and README §0 contemplates publication, so that clause is
    live and unresolved — see ``docs/data_sources.md``. The adapter is written; whether it
    is *used* is an approval decision, and whether its output may be published is a
    question for EODHD in writing.

    Key handling matches the FRED adapter: read from ``EODHD_API_KEY`` (or a gitignored
    ``.env``) and **scrubbed from the returned url and params**, which are persisted
    verbatim into the pull log and metadata sidecar.
    """

    name = "eodhd"
    transport = "eod_api_v1"
    URL = "https://eodhd.com/api/eod/{symbol}"

    @staticmethod
    def _key() -> str:
        import os
        key = os.environ.get("EODHD_API_KEY")
        if not key:
            env = _REPO_ROOT / ".env"
            if env.is_file():
                for line in env.read_text().splitlines():
                    if line.strip().startswith("EODHD_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
        if not key:
            raise ProviderError(
                "EODHD_API_KEY is not set. Register free (email or OAuth, no card) at "
                "https://eodhd.com/register, then add EODHD_API_KEY=... to .env "
                "(.env is gitignored)."
            )
        return key

    def fetch_daily(self, symbol: str, start: str | None = None, end: str | None = None):
        url = self.URL.format(symbol=symbol)
        params = {
            "fmt": "json",
            "period": "d",
            "from": start or "1990-01-01",
            "to": end or date.today().isoformat(),
        }
        payload = json.loads(DEFAULT_CLIENT.get(url, params={**params, "api_token": self._key()}))
        if not isinstance(payload, list) or not payload:
            raise ProviderError(f"{symbol}: eodhd returned no rows ({str(payload)[:120]})")
        rows = []
        for o in payload:
            close = _num(o.get("close"))
            rows.append({
                "date": o.get("date"), "open": _num(o.get("open")), "high": _num(o.get("high")),
                "low": _num(o.get("low")), "close": close,
                # EODHD serves a genuine adjusted close; keep it distinct from raw. Premium
                # construction uses RAW closes (mixing adjusted and raw across legs injects
                # a phantom premium step on every ex-date).
                "adj_close": _num(o.get("adjusted_close")) or close,
                "volume": _num(o.get("volume")),
            })
        frame = _frame(rows)
        if frame.empty:
            raise ProviderError(f"{symbol}: eodhd rows had no usable closes")
        # Key deliberately absent from both returned values — they are persisted verbatim.
        return frame, url, params


ADAPTERS["eodhd"] = EodhdAdapter()


class KofiaAdapter:
    """KOFIA FreeSIS securities-lending (대차거래) — D3-b.

    `docs/data_sources.md` D3-b carried `[U] It is an eXBuilder6 SPA and the XHR payload
    format could not be reverse-engineered.` Resolved 2026-07-29 by loading the SPA in a
    browser and reading the request it actually sends, rather than guessing servlet names
    (five guesses all returned the same 2661-byte error page).

        POST /meta/getMetaDataList.do
        {"dmSearch": {"tmpV1": "D",            # frequency: D daily
                      "tmpV45": "YYYYMMDD",    # from
                      "tmpV46": "YYYYMMDD",    # to
                      "tmpV72": "000660",      # issue code; "" = whole market
                      "tmpV40": "1000000", "tmpV41": "1",
                      "OBJ_NM": "STATSCU0100000140BO"}}

    Response columns, confirmed against the rendered table:
        TMPV1 date (YYYYMMDD) · TMPV2 issue name · TMPV3 new lending (shares)
        TMPV4 repaid (shares) · TMPV5 balance (shares) · TMPV6 balance (value)

    Two traps, both real:

    *   **The response is not always valid JSON.** When an aggregate overflows its column
        width the server emits the digits followed by bare ``######`` — unquoted — so
        ``json.loads`` fails partway through. Repaired to ``null`` before parsing.
    *   **The last two rows are 합계 and 평균** (total and mean), not dates. Left in, they
        would enter a time series as two observations with garbage timestamps.
    """

    URL = "https://freesis.kofia.or.kr/meta/getMetaDataList.do"
    OBJ = "STATSCU0100000140BO"
    AGGREGATE_ROWS = ("합계", "평균")
    _MASKED = re.compile(rb"(:\s*)\d*#+")

    def fetch(self, issue_code: str = "", start: str = "20100101",
              end: str | None = None) -> tuple[list[dict], dict]:
        end = end or _dt.date.today().strftime("%Y%m%d")
        body = {"dmSearch": {"tmpV40": "1000000", "tmpV41": "1", "tmpV1": "D",
                             "tmpV45": start, "tmpV46": end,
                             "tmpV72": issue_code, "OBJ_NM": self.OBJ}}
        raw = DEFAULT_CLIENT.get(self.URL, json_body=body)
        payload = json.loads(self._MASKED.sub(rb"\1null", raw).decode("utf-8"))
        rows = [r for r in payload.get("ds1", []) if r.get("TMPV1") not in self.AGGREGATE_ROWS]
        return rows, {"url": self.URL, "params": body}

    @staticmethod
    def to_frame(rows: list[dict]) -> "pd.DataFrame":
        import pandas as pd
        df = pd.DataFrame([{
            "date": _dt.datetime.strptime(r["TMPV1"], "%Y%m%d").date(),
            "issue_name": r["TMPV2"],
            "new_lending_shares": r["TMPV3"],
            "repaid_shares": r["TMPV4"],
            "balance_shares": r["TMPV5"],
            # TODO(ash): confirm the unit. tmpV40=1000000 implies 백만원, but 14.3m shares
            # against a 20.1m figure implies ~1.4m KRW/share where SK Hynix trades near
            # 400k. Landed unparsed rather than asserted wrong.
            "balance_value_unverified_unit": r["TMPV6"],
        } for r in rows])
        return df.sort_values("date").reset_index(drop=True)
