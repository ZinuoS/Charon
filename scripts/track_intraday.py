"""Real-time intraday tracker for the SKHY premium legs. Run locally, in the background.

Why this exists
---------------
The intraday window around 2026-07-28→29 was lost forever — Yahoo was throttled and free
retention aged it out (docs/gate_reports/S4.md). That loss is only unrecoverable *once*.
This tracker makes sure the *next* informative window — a future earnings date, a
conversion-flow episode, a volatility spike — is captured as it happens, at the finest
cadence the available providers serve.

It is the forward-looking half of D1(b): the contemporaneous premium this repo could never
build from history, accumulated in real time from here on.

What it does
------------
Every ``--interval`` seconds it polls each configured leg, and appends one timestamped
observation to an **append-only** JSON-lines file per symbol per UTC day:

    data/raw/intraday/<YYYY-MM-DD>/<symbol>.jsonl

Each line carries the UTC capture instant AND the provider's own timestamp, so the
information-timing firewall (README §4) holds intraday too. Nothing is ever overwritten; a
parser bug downstream cannot destroy a capture that cannot be retaken.

Discipline
----------
* Uses the repo's fragility client (single-flight per host, jittered backoff) — a tracker
  that hammered a provider would get itself throttled, which is the exact failure it
  exists to prevent.
* One failed poll is logged and skipped, never fatal — an all-night run survives a blip.
* Market-hours aware by default: SKHY polls only during US cash hours, 000660 during KRX
  hours. ``--always`` overrides. Polling a closed market all night is wasted load.
* SKHY (Nasdaq realtime) is the reliable leg. The local and FX legs are *attempted* — if a
  keyless intraday source is unavailable they log a gap rather than a fake value.

Run it
------
Foreground (Ctrl-C to stop)::

    uv run python -m scripts.track_intraday

Background, surviving logout::

    nohup uv run python -m scripts.track_intraday > data/derived/intraday.log 2>&1 &

Unattended via launchd (survives sleep, restarts on wake) — see the plist printed by::

    uv run python -m scripts.track_intraday --print-launchd
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.ingest._http import FragileHttpClient, ProviderError, RateLimited  # noqa: E402

# Fast-fail client: a real-time poll must be bounded. One attempt, short timeout -- a
# throttled leg logs a gap in seconds rather than backing off for minutes (which would
# make one poll outlast the poll interval and stall the whole tracker).
CLIENT = FragileHttpClient(min_interval=0.0, max_attempts=1, use_cache=False)

INTRADAY_ROOT = ROOT / "data" / "raw" / "intraday"


@dataclass(frozen=True)
class Leg:
    symbol: str            # filename stem
    fetch: str             # which fetcher
    market_tz: str
    open_close: tuple[str, str]   # local HH:MM open/close for the market-hours gate
    note: str


def _nasdaq_quote(symbol: str) -> dict:
    """Realtime last-sale from Nasdaq (keyless). SKHY's own listing venue."""
    raw = CLIENT.get(f"https://api.nasdaq.com/api/quote/{symbol}/info", params={"assetclass": "stocks"}, timeout=12)
    d = json.loads(raw).get("data") or {}
    pd = d.get("primaryData") or {}
    price = pd.get("lastSalePrice")
    if not price:
        raise ProviderError(f"{symbol}: no lastSalePrice in Nasdaq quote")
    return {
        "last": float(str(price).lstrip("$").replace(",", "")),
        "provider_ts": pd.get("lastTradeTimestamp"),
        "pct_change": pd.get("percentageChange"),
        "provider": "nasdaq_realtime",
    }


def _yahoo_intraday_last(symbol: str) -> dict:
    """Last 1-minute bar from Yahoo (throttle-prone; the local/FX legs try this)."""
    raw = CLIENT.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", params={"interval": "1m", "range": "1d"}, timeout=12)
    res = (json.loads(raw).get("chart") or {}).get("result")
    if not res:
        raise ProviderError(f"{symbol}: no Yahoo intraday result")
    meta = res[0].get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        raise ProviderError(f"{symbol}: no regularMarketPrice")
    return {"last": float(price), "provider_ts": meta.get("regularMarketTime"),
            "provider": "yahoo_1m"}


FETCHERS = {"nasdaq": _nasdaq_quote, "yahoo": _yahoo_intraday_last}

LEGS = (
    Leg("skhy", "nasdaq", "America/New_York", ("09:30", "16:00"),
        "ADR leg — reliable realtime from the listing venue"),
    Leg("000660.KS", "yahoo", "Asia/Seoul", ("09:00", "15:30"),
        "local leg — Yahoo intraday, throttle-prone; logs a gap if blocked"),
    Leg("KRW=X", "yahoo", "UTC", ("00:00", "23:59"),
        "USD/KRW — 24h; Yahoo intraday, throttle-prone"),
)


def _market_open(leg: Leg, now_utc: datetime) -> bool:
    tz = ZoneInfo(leg.market_tz)
    local = now_utc.astimezone(tz)
    if local.weekday() >= 5:
        return False
    o, c = leg.open_close
    return o <= local.strftime("%H:%M") <= c


def _append(symbol: str, record: dict) -> Path:
    day = datetime.now(timezone.utc).date().isoformat()
    d = INTRADAY_ROOT / day
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{symbol}.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def poll_once(always: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    captured, skipped, failed = [], [], []
    for leg in LEGS:
        if not always and not _market_open(leg, now):
            skipped.append(leg.symbol)
            continue
        try:
            q = FETCHERS[leg.fetch](leg.symbol)
            _append(leg.symbol, {"captured_at_utc": now.replace(microsecond=0).isoformat(), **q})
            captured.append(f"{leg.symbol}={q['last']}")
        except (RateLimited, ProviderError) as exc:
            # A gap is data: record that we tried and failed, so silence is never
            # mistaken for a flat market.
            _append(leg.symbol, {"captured_at_utc": now.replace(microsecond=0).isoformat(),
                                 "error": str(exc)[:120]})
            failed.append(f"{leg.symbol}:{type(exc).__name__}")
    return {"captured": captured, "skipped": skipped, "failed": failed}


def _launchd_plist() -> str:
    uv = "/Users/$(whoami)/.local/bin/uv"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.charon.intraday</string>
  <key>WorkingDirectory</key><string>{ROOT}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{uv}</string><string>run</string><string>python</string>
    <string>-m</string><string>scripts.track_intraday</string><string>--interval</string><string>60</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{ROOT}/data/derived/intraday.log</string>
  <key>StandardErrorPath</key><string>{ROOT}/data/derived/intraday.err</string>
</dict></plist>

# Install (survives sleep, restarts on wake or crash):
#   uv run python -m scripts.track_intraday --print-launchd > ~/Library/LaunchAgents/com.charon.intraday.plist
#   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.charon.intraday.plist
# Stop:
#   launchctl bootout gui/$(id -u)/com.charon.intraday
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--interval", type=int, default=60, help="seconds between polls (default 60)")
    ap.add_argument("--always", action="store_true", help="poll even when the market is closed")
    ap.add_argument("--once", action="store_true", help="poll once and exit (for testing/cron)")
    ap.add_argument("--print-launchd", action="store_true", help="print the launchd plist and exit")
    args = ap.parse_args(argv)

    if args.print_launchd:
        print(_launchd_plist())
        return 0

    print(f"charon intraday tracker — interval {args.interval}s, "
          f"{'always' if args.always else 'market-hours only'}. Append-only to {INTRADAY_ROOT}.")
    print("legs:", ", ".join(f"{l.symbol} ({l.fetch})" for l in LEGS))
    if args.once:
        r = poll_once(args.always)
        print(f"  {datetime.now(timezone.utc).strftime('%H:%M:%S')}Z  "
              f"captured {r['captured']}  skipped {r['skipped']}  failed {r['failed']}")
        return 0

    try:
        while True:
            r = poll_once(args.always)
            stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"  {stamp}Z  captured={len(r['captured'])} {r['captured']}  "
                  f"skipped={len(r['skipped'])}  failed={r['failed']}", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
