"""Capacity and liquidity — how big, and how fast out.

The PM's third question, unanswered anywhere else in the repo. Both legs carry landed volume,
so dollar-ADV and days-to-unwind are computable now rather than bracketed.

Participation rates are a CONVENTION, not advice: 5/10/20% of ADV are the bands a desk would
normally quote against, and they are labelled that way on the figure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.ingest._common import latest_raw_file

PARTICIPATION = (0.05, 0.10, 0.20)
#: Extended upward after the first run: at $250m both legs unwind in under a third of a
#: session, so a grid stopping there shows a flat line at zero and hides where the constraint
#: actually appears. Both legs turn over ~$8bn/day in this dataset.
SIZES_USD = (25e6, 100e6, 250e6, 500e6, 1e9, 2.5e9, 5e9, 10e9)

LEGS = {
    "SKHY (ADR, USD)": ("d1_prices", "skhy_adr_daily.csv", 1.0),
    "000660 (local, KRW)": ("d1_prices", "skhynix_local_daily.csv", None),   # None -> convert
}


def _dollar_adv(source: str, fname: str, fx: pd.Series | None, window: int = 20) -> pd.Series:
    d = pd.read_csv(latest_raw_file(source, fname), parse_dates=["date"]).set_index("date")
    dv = d["close"] * d["volume"]
    if fx is not None:                       # KRW turnover -> USD
        dv = dv / fx.reindex(dv.index).ffill()
    return dv.rolling(window, min_periods=3).mean().dropna()


def adv_table() -> pd.DataFrame:
    """Dollar ADV per leg, with the freshness caveat carried in the row."""
    from pipeline.measurement.premium import _load_close
    fx = _load_close("d1_prices", "usdkrw_spot_daily")
    rows = []
    for label, (src, fname, direct) in LEGS.items():
        adv = _dollar_adv(src, fname, None if direct else fx)
        rows.append({
            "leg": label, "adv_usd": float(adv.iloc[-1]), "n_sessions": int(len(adv)),
            "first": str(adv.index[0].date()), "last": str(adv.index[-1].date()),
            "caveat": ("3-week history: regime-fresh, not a cycle-average ADV"
                       if len(adv) < 60 else "deep history"),
        })
    return pd.DataFrame(rows)


def days_to_unwind(sizes=SIZES_USD, participation=PARTICIPATION) -> pd.DataFrame:
    """Sessions to exit `size` at each participation rate, per leg. The binding leg is the max."""
    adv = adv_table().set_index("leg")
    rows = []
    for size in sizes:
        for p in participation:
            per_leg = {lg: size / (adv.loc[lg, "adv_usd"] * p) for lg in adv.index}
            rows.append({"size_usd": size, "participation": p,
                         **{f"days_{lg.split()[0]}": v for lg, v in per_leg.items()},
                         "days_binding": max(per_leg.values()),
                         "binding_leg": max(per_leg, key=per_leg.get)})
    return pd.DataFrame(rows)


def borrow_ceiling() -> dict:
    """Public ceiling indicator on the short leg, from landed KOFIA balances.

    An on-loan BALANCE is not lendable depth -- it is what is already out. Treated as a
    lower-bound indicator on what the market can source, and labelled as such, because
    presenting it as capacity would overstate a number the desk actually quotes.
    """
    try:
        from pipeline.measurement.utilization import current
        from pipeline.measurement.premium import _load_close
        u = current()
        px = float(_load_close("d1_prices", "skhynix_local_daily").iloc[-1])
        fx = float(_load_close("d1_prices", "usdkrw_spot_daily").iloc[-1])
        return {"as_of": u["as_of"], "on_loan_shares": u["balance_shares"],
                "on_loan_usd": u["balance_shares"] * px / fx,
                "percentile": u["balance_pctile"], "state": u["state"],
                "caveat": "on-loan BALANCE, not lendable depth. Indicator only; desk quotes depth."}
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}", "caveat": "hatched"}


if __name__ == "__main__":
    print(adv_table().to_string(index=False))
    print()
    d = days_to_unwind()
    print(d[d.participation == 0.10][["size_usd", "days_SKHY", "days_000660",
                                      "days_binding", "binding_leg"]].round(2).to_string(index=False))
    print()
    print(borrow_ceiling())
