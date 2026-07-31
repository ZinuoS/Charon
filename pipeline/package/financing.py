"""The financing chapter — what the swap-financed pair actually costs, by component.

WHAT THIS REPLACES. Until now the carry was a single bracket: 250/600/1200bp per year for
"the four hatched components combined". That bracket is honest but it is opaque, and a desk
cannot negotiate an opaque number. This module opens it: two of the four components are
MEASURABLE from series already landed, one is bracketed because it is a desk quote, and one
is not measurable at all with the data on hand and is marked as such rather than assumed
away.

THE STRUCTURE BEING PRICED. The client posts USD collateral. The desk swaps USD into KRW to
fund the local long, and borrows the ADR to establish the short. So the cash flows per unit
of notional per year are:

    + USD collateral and short proceeds earn the USD rate       MEASURED (EFFR, daily)
    - KRW funding costs the KRW rate                            MEASURED (3m, monthly)
    - the ADR borrow spread                                     BRACKETED (desk quote)
    - the cross-currency basis on the USD/KRW swap              NOT MEASURABLE — see below
    - the obol, amortised over the holding period               DOCUMENTED (7bp round trip)

THE SIGN THAT MATTERS, AND IT IS COUNTER-INTUITIVE. USD rates are currently ABOVE KRW rates,
and the position is long the KRW asset funded from USD. Under covered interest parity,
hedging a foreign asset back into the base currency earns (r_base - r_foreign). So the
funding differential on this trade is a TAILWIND, not a cost, and the whole of the carry
bracket is really the borrow spread plus the basis. That is the single most useful thing this
module says, and it is the opposite of what "financing cost" implies.

WHY THE FORWARD POINTS ARE NOT USED, though the plan called for them. SGX USD/KRW forwards
are not landed: there is no registry entry and no raw source on disk. `docs/features_m6.md`
already records why they were deferred -- the deferred months are `exchange_marked` rather
than executable, so a slope built from them would be part quote and part mark. What forward
points would add over the rate differential is exactly the cross-currency BASIS, which is
therefore the component this module cannot measure and does not estimate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.package.breakeven import CARRY_BRACKET_BP, CONVERSION_FEE_BP, critical_carry_bp

#: ADR borrow spread over the USD rate, in bp/yr. The one component that is purely a desk
#: quote: it is a function of who holds the float and how tight the recall risk is, and no
#: public series prices it. Bracketed until the desk conversation fills it.
ADR_BORROW_BRACKET_BP = {"low": 150, "mid": 400, "high": 900}

#: The cross-currency basis on USD/KRW, in bp/yr. NOT MEASURED and deliberately not guessed.
#: It is the wedge between the forward points and the rate differential, so measuring it
#: requires a forward curve this repository does not have. A negative KRW basis (the usual
#: sign for an Asian funding currency) makes swapping into KRW MORE expensive than parity,
#: which would cut into the differential tailwind below.
BASIS_STATUS = "not measured — needs a USD/KRW forward curve; see the probe in notebook 10"


def rate_legs() -> dict:
    """The two landed rate legs at their own last observation, at native frequency.

    No interpolation and no alignment to a common date. The Korea leg is published monthly
    and the US leg daily; resampling the monthly series onto the daily grid would manufacture
    observations nobody published, and the differential is a level comparison that does not
    need them to share a timestamp.
    """
    from pipeline.measurement.premium import _load_close

    us = _load_close("d2_macro", "us_rate_effr_daily")
    kr = _load_close("d2_macro", "kr_rate_3m_monthly")
    return {
        "usd_rate_pct": float(us.iloc[-1]), "usd_as_of": str(us.index[-1].date()),
        "usd_series": "EFFR, daily", "usd_n": int(len(us)),
        "krw_rate_pct": float(kr.iloc[-1]), "krw_as_of": str(kr.index[-1].date()),
        "krw_series": "Korea 3-month rate, monthly", "krw_n": int(len(kr)),
        "differential_bp": round((float(us.iloc[-1]) - float(kr.iloc[-1])) * 100, 1),
    }


def carry_components(bracket: str = "mid", horizon_days: float = 252.0) -> pd.DataFrame:
    """The carry, one row per component, in bp/yr. Signed: positive is a cost to the client.

    Every row carries its own status, because the point of the decomposition is that the
    components are not equally knowable and a stacked bar that hides that is worse than the
    single bracket it replaces.
    """
    legs = rate_legs()
    borrow = ADR_BORROW_BRACKET_BP[bracket]
    obol = CONVERSION_FEE_BP * 252.0 / horizon_days

    rows = [
        {"component": "USD rate earned on collateral and short proceeds",
         "short": "USD rate\nearned",
         "bp_per_year": -legs["usd_rate_pct"] * 100, "status": "MEASURED",
         "source": f"{legs['usd_series']}, {legs['usd_as_of']}"},
        {"component": "KRW funding on the local long",
         "short": "KRW\nfunding",
         "bp_per_year": +legs["krw_rate_pct"] * 100, "status": "MEASURED",
         "source": f"{legs['krw_series']}, {legs['krw_as_of']}"},
        {"component": "ADR borrow spread", "short": "ADR borrow\nspread",
         "bp_per_year": float(borrow), "status": "BRACKETED",
         "source": f"desk quote pending; {bracket} of "
                   f"{ADR_BORROW_BRACKET_BP['low']}-{ADR_BORROW_BRACKET_BP['high']}bp"},
        {"component": "cross-currency basis", "short": "cross-currency\nbasis",
         "bp_per_year": 0.0, "status": "NOT MEASURED",
         "source": BASIS_STATUS},
        {"component": "the obol (conversion, amortised)", "short": "the obol",
         "bp_per_year": float(obol), "status": "DOCUMENTED",
         "source": f"{CONVERSION_FEE_BP}bp round trip over {horizon_days:.0f} sessions"},
    ]
    out = pd.DataFrame(rows)
    out["bp_per_month"] = out["bp_per_year"] / 12.0
    return out


def carry_summary(bracket: str = "mid", horizon_days: float = 252.0) -> dict:
    """Totals, and the comparison the financing conversation actually turns on."""
    c = carry_components(bracket, horizon_days)
    total_bp = float(c.bp_per_year.sum())
    legs = rate_legs()
    critical = critical_carry_bp(horizon_days=horizon_days)
    measured = c[c.status == "MEASURED"].bp_per_year.sum()
    return {
        "total_bp_per_year": round(total_bp, 1),
        "total_bp_per_month": round(total_bp / 12.0, 1),
        "funding_differential_bp": round(float(measured), 1),
        "funding_is_tailwind": bool(measured < 0),
        "borrow_bracket_bp": ADR_BORROW_BRACKET_BP[bracket],
        "critical_carry_bp_per_year": round(critical, 1),
        "critical_carry_bp_per_month": round(critical / 12.0, 1),
        "headroom_bp_per_year": round(critical - total_bp, 1),
        "pays_at_this_bracket": bool(total_bp < critical),
        "legacy_bracket_bp": CARRY_BRACKET_BP[bracket],
        "unmeasured": [r.component.replace("\n", " ") for r in c.itertuples()
                       if r.status == "NOT MEASURED"],
        "rate_legs": legs,
    }


def fed_sensitivity(shift_bp: float = 25.0, horizon_days: float = 252.0) -> dict:
    """Carry per 25bp move in the USD leg — the sentence the financing slide needs.

    The USD rate enters with a NEGATIVE sign (it is earned, not paid), so a Fed HIKE makes
    this trade cheaper to hold and a cut makes it more expensive. That is the opposite of the
    reflex for a levered position, and it is worth saying out loud on the slide: the funding
    leg of this trade is long the front end.
    """
    base = carry_summary(horizon_days=horizon_days)["total_bp_per_year"]
    up = base - shift_bp        # USD rate earned rises -> total carry falls
    return {
        "shift_bp": shift_bp,
        "carry_now_bp_per_year": base,
        "carry_after_hike_bp_per_year": round(up, 1),
        "carry_after_cut_bp_per_year": round(base + shift_bp, 1),
        "bp_per_month_per_25bp": round(shift_bp / 12.0, 2),
        "direction": ("A HIKE REDUCES the cost of holding this trade and a CUT RAISES it. "
                      "The USD rate is earned on collateral and short proceeds, not paid, so "
                      "the funding leg is long the front end."),
        "caveat": ("Assumes the KRW leg and the borrow spread are unchanged. In practice a "
                   "Fed move that repriced the won would move both, and the cross-currency "
                   "basis is unmeasured here in either state."),
    }


if __name__ == "__main__":     # the smallest checks that fail if the signs invert
    legs = rate_legs()
    c = carry_components()
    s = carry_summary()

    # The identity the whole module rests on: the two MEASURED rows are the funding
    # differential, and its sign is (KRW rate - USD rate) in cost terms.
    measured = c[c.status == "MEASURED"].bp_per_year.sum()
    assert abs(measured - (legs["krw_rate_pct"] - legs["usd_rate_pct"]) * 100) < 1e-6, (
        "the two measured rows must sum to the funding differential in COST terms")
    # USD above KRW today, so the differential must read as a tailwind (negative cost).
    if legs["usd_rate_pct"] > legs["krw_rate_pct"]:
        assert measured < 0 and s["funding_is_tailwind"], (
            "USD rates above KRW rates means hedging the KRW asset back to USD EARNS the "
            "differential; a positive cost here is a sign inversion")
    # A hike must reduce the cost, never raise it.
    f = fed_sensitivity()
    assert f["carry_after_hike_bp_per_year"] < f["carry_now_bp_per_year"] < \
           f["carry_after_cut_bp_per_year"], "Fed sensitivity has the wrong sign"
    # Higher borrow bracket can only raise the total.
    assert (carry_summary("high")["total_bp_per_year"]
            > carry_summary("low")["total_bp_per_year"])

    print(f"ok: USD {legs['usd_rate_pct']:.2f}% vs KRW {legs['krw_rate_pct']:.2f}% "
          f"-> differential {measured:+.0f}bp/yr")
    print(f"    total carry {s['total_bp_per_year']:.0f}bp/yr "
          f"({s['total_bp_per_month']:.0f}bp/mo) against a critical "
          f"{s['critical_carry_bp_per_month']:.0f}bp/mo")
