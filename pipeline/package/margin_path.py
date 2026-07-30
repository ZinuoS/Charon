"""The margin-call illustration — the realised excursion replayed against the pair.

The stress honesty and the netting sell on one artifact: the same window that shows a
cross-margined pair calling for less capital also shows how much it still calls for.

ILLUSTRATIVE MARGINING, and the label is not a hedge. Initial margin is a parametric
z-sigma sketch; variation margin is the daily mark-to-market on the position. Real schedules
are the desk's and the sheets say so. What is NOT illustrative is the price path: the
15.98 -> 51.60 run happened, in the programme's first five sessions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.package.netting import VAR_Z, _legs

#: Initial-margin sketch: z * annualised sigma / sqrt(252), applied to notional.
def _im(sigma_ann: float) -> float:
    return VAR_Z * sigma_ann / np.sqrt(252.0)


def margin_path(pair: str = "skhy", notional_usd: float = 100e6,
                window: tuple[str, str] | None = None) -> pd.DataFrame:
    """Day-by-day variation margin for the cross-margined pair vs two standalone tickets.

    The position is short the premium: short 1 ADR, long its local equivalent. Standalone
    means two independently margined tickets on the same two legs; pair means one netted
    ticket whose risk is the premium.
    """
    d = _legs(pair)
    if window:
        d = d.loc[window[0]:window[1]]
    if len(d) < 3:
        raise ValueError(f"{pair}: {len(d)} rows in window, too few for a path")

    r_adr = np.log(d.adr).diff()
    r_loc = np.log(d.loc_usd).diff()
    r_pi = np.log1p(d.pi).diff()

    # Sigmas from the window itself -- this is a stress illustration, so the point is what
    # margin does WHEN vol is high, not what a calm-period model would have asked for.
    im_pair = _im(float(r_pi.std(ddof=1) * np.sqrt(252)))
    im_stand = (_im(float(r_adr.std(ddof=1) * np.sqrt(252)))
                + _im(float(r_loc.std(ddof=1) * np.sqrt(252))))

    # Short the premium: P&L = -(change in premium). Standalone legs: short ADR, long local.
    pnl_pair = -r_pi.fillna(0.0)
    pnl_stand = (-r_adr.fillna(0.0)) + r_loc.fillna(0.0)

    out = pd.DataFrame({
        "premium": d.pi,
        "vm_pair_pct": -pnl_pair.cumsum(),              # cumulative call = cumulative loss
        "vm_standalone_pct": -pnl_stand.cumsum(),
        "im_pair_pct": im_pair,
        "im_standalone_pct": im_stand,
    })
    out["total_pair_pct"] = out.im_pair_pct + out.vm_pair_pct.clip(lower=0)
    out["total_standalone_pct"] = out.im_standalone_pct + out.vm_standalone_pct.clip(lower=0)
    for c in ("total_pair", "total_standalone"):
        out[f"{c}_usd"] = out[f"{c}_pct"] * notional_usd
    return out


def peak_call(pair: str = "skhy", notional_usd: float = 100e6,
              window: tuple[str, str] | None = None) -> dict:
    p = margin_path(pair, notional_usd, window)
    return {
        "notional_usd": notional_usd,
        "premium_start": float(p.premium.iloc[0]), "premium_peak": float(p.premium.max()),
        "peak_total_pair_pct": float(p.total_pair_pct.max()),
        "peak_total_standalone_pct": float(p.total_standalone_pct.max()),
        "peak_total_pair_usd": float(p.total_pair_usd.max()),
        "peak_total_standalone_usd": float(p.total_standalone_usd.max()),
        "pair_vs_standalone": float(p.total_pair_pct.max() / p.total_standalone_pct.max()),
        "sessions": int(len(p)),
        "illustrative": "parametric IM sketch + realised daily marks; desk quotes real schedules",
    }


if __name__ == "__main__":
    k = peak_call()
    print(f"premium {k['premium_start']:.2%} -> {k['premium_peak']:.2%} over {k['sessions']} sessions")
    print(f"peak margin, pair       {k['peak_total_pair_pct']:.2%} of notional "
          f"= USD {k['peak_total_pair_usd']/1e6:.1f}m on USD {k['notional_usd']/1e6:.0f}m")
    print(f"peak margin, standalone {k['peak_total_standalone_pct']:.2%} of notional "
          f"= USD {k['peak_total_standalone_usd']/1e6:.1f}m")
    print(f"pair / standalone       {k['pair_vs_standalone']:.2f}")
