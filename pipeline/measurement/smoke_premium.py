"""Smoke test for INGESTION CORRECTNESS. Not the M1 measurement layer.

Scope discipline
----------------
This module exists only to prove that S1 ingestion produced usable, correctly oriented
data. It is explicitly *not* stage S2: there is no asynchronicity decomposition, no
D1(b) contemporaneous variant, no modelling, and nothing here is a deliverable. M1 will
supersede it (README §9).

The formula
-----------
README §3 defines the premium as

    pi_t = P_ADR,t / (P_local,t * FX_t / 10) - 1

where the ``/ 10`` is the SKHY deal ratio (10 ADRs = 1 common share, README §2) and
``FX_t`` is written as USD-per-local, so that ``P_local * FX`` is the local share in
USD. Public FX series are quoted the other way round — ``KRW=X`` is *KRW per USD* — so
substituting ``FX = 1 / FX_local_per_usd`` and generalising the ratio gives the form
actually implemented here:

    pi_t = (P_ADR,t * FX_local_per_usd,t) / (local_shares_per_adr * P_local,t) - 1

with ``local_shares_per_adr = 0.1`` for SKHY (one ADR is one tenth of a common share)
and ``5.0`` for TSM (one ADR is five ordinary shares). The two forms are algebraically
identical; this one is stated in the units the data actually arrives in, because the
FX direction is the single most common way this calculation is silently wrong.

Reading the units aloud is the check. The denominator
``local_shares_per_adr * P_local`` is the local-currency cost of the shares underlying
**one** ADR. Multiplying the numerator by ``FX_local_per_usd`` converts that ADR's USD
price into the same local currency. Both sides are then local currency, the ratio is
dimensionless, and ``pi`` is a clean percentage. Inverting FX does not produce a
subtly wrong answer — it produces roughly -99.99%, which is why this is worth checking
before anything else when a premium looks implausible.

Prices are RAW closes, never adjusted closes: an ADR and its local line adjust on
different dividend calendars, and mixing the two injects a spurious premium step on
every ex-date.

Honesty label
-------------
Both series here are **close-to-close** premia — README's D1(a), the stale variant. The
KRX close (15:30 KST) and the Nasdaq close (16:00 ET) are ~13.5 hours apart, so a given
row's two legs are not contemporaneous and part of every move shown is a measurement
artifact rather than a change in the economic premium. The charts say so on their axes.

No network access. Reads only what ingestion already wrote to ``data/raw/``.

Usage::

    uv run python -m pipeline.measurement.smoke_premium
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # deterministic, headless; no display backend dependency
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from pipeline.ingest._common import DERIVED_ROOT, latest_raw_file  # noqa: E402
from pipeline.ingest.registry import PairSpec, pair_by_id, series_by_id  # noqa: E402

OUT_DIR = DERIVED_ROOT / "smoke"

# Which raw source directory each pair's legs were pulled into. Only the SKHY pair
# lives under D1; every comparator is D6.
PAIR_SOURCE = {"skhy": "d1_prices"}
DEFAULT_SOURCE = "d6_comparators"


def compute_premium(
    adr_close: pd.Series,
    local_close: pd.Series,
    fx_local_per_usd: pd.Series,
    local_shares_per_adr: float,
) -> pd.Series:
    """Close-to-close premium, inner-joined on date. See the module docstring.

    All three inputs are date-indexed. The inner join is deliberate: a forward-fill
    across a market holiday would pair a stale leg against a live one and manufacture
    premium moves out of calendar mismatch. Rows where any leg is missing are dropped,
    and the drop count is reported.
    """
    frame = pd.concat(
        {"adr": adr_close, "local": local_close, "fx": fx_local_per_usd}, axis=1, join="inner"
    ).dropna()
    return (frame["adr"] * frame["fx"]) / (local_shares_per_adr * frame["local"]) - 1.0


def _load_leg(source: str, series_id: str) -> pd.Series:
    path = latest_raw_file(source, f"{series_id}.csv")
    if path is None:
        raise FileNotFoundError(
            f"no raw file for {series_id} under data/raw/{source}/. "
            f"Run the ingestion step first (`just ingest`)."
        )
    frame = pd.read_csv(path, parse_dates=["date"])
    return frame.set_index("date")["close"].rename(series_id)


def build_pair(pair: PairSpec, start: str | None = None) -> tuple[pd.Series, dict]:
    source = PAIR_SOURCE.get(pair.pair_id, DEFAULT_SOURCE)
    adr = _load_leg(source, pair.adr)
    local = _load_leg(source, pair.local)
    fx = _load_leg(source, pair.fx)

    if start:
        adr, local, fx = (s[s.index >= start] for s in (adr, local, fx))

    pi = compute_premium(adr, local, fx, pair.local_shares_per_adr)

    diag = {
        "pair": pair.pair_id,
        "local_shares_per_adr": pair.local_shares_per_adr,
        "ratio_confirmed": pair.confirmed,
        "rows_adr": len(adr), "rows_local": len(local), "rows_fx": len(fx),
        "rows_joined": len(pi),
        "dropped_to_join": max(len(adr), len(local), len(fx)) - len(pi),
        "first": str(pi.index[0].date()) if len(pi) else None,
        "last": str(pi.index[-1].date()) if len(pi) else None,
        "min_pct": round(float(pi.min()) * 100, 2) if len(pi) else None,
        "max_pct": round(float(pi.max()) * 100, 2) if len(pi) else None,
        "last_pct": round(float(pi.iloc[-1]) * 100, 2) if len(pi) else None,
        "mean_pct": round(float(pi.mean()) * 100, 2) if len(pi) else None,
    }
    return pi, diag


def plot_pair(pi: pd.Series, title: str, ylabel: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(pi.index, pi.values * 100, linewidth=1.4, color="#1f3a5f")
    ax.axhline(0.0, color="#999999", linewidth=0.8, linestyle="--")
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel("date", fontsize=9)
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.tick_params(labelsize=8)
    fig.autofmt_xdate()
    # The zero line is the one-sided barrier: below it the ADR->local crossing is live
    # and uncapped, so pi is reflected from below (README §3). Above it there is no
    # barrier at all while quota headroom is zero.
    ax.annotate(
        "conversion floor (ADR->local, uncapped)",
        xy=(0.01, 0.02), xycoords="axes fraction", fontsize=7, color="#666666",
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingestion smoke test: close-to-close premium.")
    parser.add_argument("--pairs", default="skhy,tsmc")
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    rows: list[dict] = []

    for pair_id in [p.strip() for p in args.pairs.split(",") if p.strip()]:
        pair = pair_by_id(pair_id)
        # TSM history is long; the smoke test looks at the last 2 years per Task 4.
        start = "2024-07-28" if pair_id == "tsmc" else None
        try:
            pi, diag = build_pair(pair, start=start)
        except FileNotFoundError as exc:
            print(f"  SKIP {pair_id}: {exc}")
            failures.append(pair_id)
            continue

        adr_spec, local_spec = series_by_id(pair.adr), series_by_id(pair.local)
        label = (
            f"close-to-close premium (%)  [STALE: {local_spec.market} close "
            f"{local_spec.close_local.strftime('%H:%M')} {local_spec.timezone.split('/')[-1]} vs "
            f"{adr_spec.market} close {adr_spec.close_local.strftime('%H:%M')} ET]"
        )
        title = (
            f"{pair.pair_id.upper()}: {adr_spec.symbol} vs {local_spec.symbol} — "
            f"D1(a) close-to-close premium, NOT contemporaneous"
        )
        out_path = OUT_DIR / f"premium_{pair.pair_id}_close_to_close.png"
        plot_pair(pi, title, label, out_path)

        pi.rename("premium").to_frame().to_csv(OUT_DIR / f"premium_{pair.pair_id}.csv")
        rows.append(diag)
        print(
            f"  {pair_id:6s} n={diag['rows_joined']:5d} {diag['first']}..{diag['last']}  "
            f"min={diag['min_pct']}%  max={diag['max_pct']}%  last={diag['last_pct']}%  "
            f"mean={diag['mean_pct']}%  (dropped {diag['dropped_to_join']} to join)  -> {out_path.name}"
        )

    if rows:
        pd.DataFrame(rows).to_csv(OUT_DIR / "smoke_diagnostics.csv", index=False)

    print("\n  Sanity anchors (README §2 / Task 4):")
    print("    SKHY  expect ~51% early peak decaying toward ~20-33% by late July.")
    print("    TSMC  expect low double digits (5y average ~12.6%).")
    print("    A wildly wrong number means FX direction or ADR ratio — check those first.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
