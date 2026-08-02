"""Pair-netting quantification — the number that sells cross-margining.

Standalone legs move with the *name*; the hedged pair moves with the *premium*. The premium is
the smaller quantity, so a cross-margined pair should require materially less capital than two
independent tickets. This measures how much less, from landed data only.

    ratio = sigma(pair) / [ sigma(ADR) + sigma(local, USD terms) ]

Reported for the SKHY window and TSMC's deep history, and — this is the part that must never be
dropped — **through the realised excursion as well as in calm.** The netting benefit is computed
on normal covariation; the 22.57 -> 51.60 run shows the premium itself gapping, which is exactly
when the benefit thins. Both numbers on one chart or neither.

Margin methodology is the desk's. The VaR figure here is an ILLUSTRATIVE sketch (parametric,
stated confidence) and the sheet says the desk quotes real schedules.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.ingest.registry import PAIRS
from pipeline.measurement.premium import DEFAULT_SOURCE, PAIR_SOURCE, _load_close, build_all_variants

#: Illustrative only. 1.645 = one-tailed 95%.
VAR_Z = 1.645
EXCURSION = ("2026-07-10", "2026-07-16")     # the realised 22.57 -> 51.60 window


def _legs(pair: str) -> pd.DataFrame:
    """ADR in USD, local converted to USD, and the premium — on one joined index."""
    spec = next(p for p in PAIRS if p.pair_id == pair)
    src = PAIR_SOURCE.get(pair, DEFAULT_SOURCE)
    from pipeline.measurement.premium import _load_fx
    adr, loc = (_load_close(src, s) for s in (spec.adr, spec.local))
    fx = _load_fx(src, spec.fx)
    df = pd.concat({"adr": adr, "loc": loc, "fx": fx}, axis=1).dropna()
    # Local leg in USD terms, scaled to one ADR-equivalent so the two legs are comparable.
    df["loc_usd"] = spec.local_shares_per_adr * df["loc"] / df["fx"]
    df["pi"] = build_all_variants(pair)[0].series.reindex(df.index)
    return df.dropna()


def ratios(pair: str, window: tuple[str, str] | None = None, ann: float = 252.0) -> dict:
    """Capital-efficiency ratio for one pair, optionally restricted to a window."""
    d = _legs(pair)
    if window:
        d = d.loc[window[0]:window[1]]
    if len(d) < 3:
        return {"pair": pair, "n": len(d), "ratio": None}
    r_adr = np.log(d.adr).diff().dropna()
    r_loc = np.log(d.loc_usd).diff().dropna()
    # The hedged pair's P&L per ADR-equivalent is the change in the premium leg: long ADR,
    # short the local equivalent, so the residual exposure IS the premium.
    r_pair = np.log1p(d.pi).diff().dropna()
    s = lambda x: float(x.std(ddof=1) * np.sqrt(ann))
    sa, sl, sp = s(r_adr), s(r_loc), s(r_pair)
    denom = sa + sl
    return {
        "pair": pair, "n": int(len(d)),
        "window": "full" if not window else f"{window[0]}..{window[1]}",
        "vol_adr": sa, "vol_local_usd": sl, "vol_pair": sp,
        "sum_standalone": denom,
        "ratio": float(sp / denom) if denom else None,
        # Illustrative parametric VaR per unit notional, one day, stated confidence.
        "var95_1d_standalone": float(VAR_Z * denom / np.sqrt(ann)),
        "var95_1d_pair": float(VAR_Z * sp / np.sqrt(ann)),
        "illustrative": "parametric VaR sketch at 95% one-tailed; the desk quotes real schedules",
    }


#: Stress is the top quintile of |premium move|. Defined by MAGNITUDE, not by a date range.
#: The first version used SKHY's excursion dates for every pair, which gave TSMC four
#: arbitrary days off SKHY's calendar and a "stress ratio" computed on n=4 -- a number with
#: the shape of evidence and none of the content.
STRESS_QUANTILE = 0.80


def calm_vs_stress(pair: str = "skhy", ann: float = 252.0) -> pd.DataFrame:
    """The netting case and its erosion, side by side. Never one without the other.

    Both rows are conditional on the pair's OWN move distribution, so `n` is real on any pair
    with history and the two rows are directly comparable.
    """
    d = _legs(pair)
    r_adr = np.log(d.adr).diff()
    r_loc = np.log(d.loc_usd).diff()
    r_pair = np.log1p(d.pi).diff()
    joined = pd.concat({"a": r_adr, "l": r_loc, "p": r_pair}, axis=1).dropna()
    if len(joined) < 10:
        return pd.DataFrame([{"pair": pair, "regime_label": "insufficient history",
                              "n": len(joined), "ratio": None}])

    cut = joined.p.abs().quantile(STRESS_QUANTILE)
    rows = []
    for label, mask in (("calm (lower 80% of |Δπ|)", joined.p.abs() <= cut),
                        ("stress (top 20% of |Δπ|)", joined.p.abs() > cut)):
        g = joined[mask]
        s = lambda x: float(x.std(ddof=1) * np.sqrt(ann))
        sa, sl, sp = s(g.a), s(g.l), s(g.p)
        rows.append({"pair": pair, "regime_label": label, "n": int(len(g)),
                     "vol_adr": sa, "vol_local_usd": sl, "vol_pair": sp,
                     "sum_standalone": sa + sl,
                     "ratio": float(sp / (sa + sl)) if (sa + sl) else None,
                     "capital_saving": float(1 - sp / (sa + sl)) if (sa + sl) else None})
    return pd.DataFrame(rows)


def wrong_way_note() -> str:
    """The package's concentrated risk, named rather than implied."""
    return (
        "WRONG-WAY DYNAMICS. When the premium widens, the short ADR leg loses AND borrow on "
        "that same leg tends to tighten -- recall risk rises exactly when the position is "
        "underwater and most needs to be held. The netting benefit is measured on normal "
        "covariation and thins in precisely that state, so the capital saving and the risk "
        "concentrate on the same event. This is the package's single most concentrated risk."
    )


if __name__ == "__main__":
    for p in ("skhy", "tsmc"):
        df = calm_vs_stress(p)
        print(f"\n{p}:")
        print(df[["regime_label", "n", "vol_adr", "vol_local_usd", "vol_pair",
                  "ratio"]].round(4).to_string(index=False))
