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


# --------------------------------------------------------------------------------
# Execution reality — the vol context and the stress-window liquidity
# --------------------------------------------------------------------------------
#
# THE MICROSTRUCTURE LIMIT, STATED ONCE AND UP FRONT. Everything below is computed from DAILY
# BARS. Daily volume and the high-low range are the only liquidity evidence this repository
# holds; there is no tick data, no quoted spread and no depth. The high-low range is a
# well-behaved PROXY for a spread and it is not a spread -- it is bounded below by the true
# spread and inflated by genuine intraday direction. Every number here is labelled
# daily-resolution and no intraday claim rests on any of it.

#: Rolling window for realised vol, in sessions. One quarter, the convention used throughout.
VOL_WINDOW: int = 63


def realised_vol(series: pd.Series, window: int = VOL_WINDOW) -> pd.Series:
    """Annualised realised vol of log changes. sqrt(252) scaling, stated rather than implied."""
    return np.log(series).diff().rolling(window).std() * np.sqrt(252.0) * 100.0


def vol_context() -> pd.DataFrame:
    """Per-leg vol, so "both markets are volatile" becomes a number instead of an adjective.

    The US leg is IMPLIED (VIX) and every other leg is REALISED, because no Korean implied-vol
    series is freely reachable. They are not like-for-like and the caption says so; implied
    normally sits above realised, so the US leg is flattered by the comparison rather than the
    Korean one.
    """
    from pipeline.measurement.premium import _load_close, build_all_variants

    legs = {}
    for label, (src, sid) in {
        "KOSPI (realised)": ("d2_macro", "kospi_index_daily"),
        "SK hynix local (realised)": ("d1_prices", "skhynix_local_daily"),
        "SKHY ADR (realised)": ("d1_prices", "skhy_adr_daily"),
        "USD/KRW (realised)": ("d1_prices", "usdkrw_spot_daily"),
    }.items():
        try:
            legs[label] = realised_vol(_load_close(src, sid))
        except Exception:
            continue
    try:
        vix = _load_close("d2_macro", "vix_index_daily")
        legs["US VIX (implied)"] = vix
    except Exception:
        pass

    pi = build_all_variants("skhy")[0].series
    rows = []
    for label, s in legs.items():
        s = s.dropna()
        if not len(s):
            continue
        rows.append({"leg": label, "latest_vol_pct": round(float(s.iloc[-1]), 1),
                     "median_vol_pct": round(float(s.median()), 1),
                     "n": int(len(s)), "as_of": str(s.index[-1].date()),
                     "kind": "implied" if "implied" in label else "realised"})
    # The premium's own vol, on the same annualisation. The point of the panel: the pair nets
    # out most single-leg vol and what survives is this.
    d = pi.diff().dropna()
    if len(d) > 1:
        rows.append({"leg": "THE PREMIUM (what you hold)", "kind": "realised",
                     "latest_vol_pct": round(float(d.std() * np.sqrt(252) * 100), 1),
                     "median_vol_pct": None, "n": int(len(d)),
                     "as_of": str(pi.index[-1].date())})
    return pd.DataFrame(rows)


def stress_liquidity(pair: str = "skhy", window: int = 63) -> pd.DataFrame:
    """Volume and high-low range through the worst window, against the trailing normal.

    Daily-resolution evidence. The question it answers is narrow and worth answering: when this
    premium moved hardest, did the market thin out or deepen? A short cover into a thinning
    book is the trade's real execution risk, and it is not the same question as the average-day
    capacity number.
    """
    import pandas as pd

    from pipeline.ingest._common import latest_raw_file
    from pipeline.ingest.registry import PAIRS

    spec = next(p for p in PAIRS if p.pair_id == pair)
    source = "d1_prices" if pair == "skhy" else "d6_comparators"
    # The pair's declared sample, not the raw file: a stress window inside an excluded
    # corporate-action era would be measuring the artefact, not the market.
    out = []
    for label, sid in (("ADR", spec.adr), ("local", spec.local)):
        f = pd.read_csv(latest_raw_file(source, f"{sid}.csv"), parse_dates=["date"])
        f = f.set_index("date").sort_index()
        if getattr(spec, "sample_start", None):
            f = f[f.index >= spec.sample_start]
        if getattr(spec, "sample_end", None):
            f = f[f.index <= spec.sample_end]
        if not {"high", "low", "close", "volume"} <= set(f.columns):
            continue
        rng = (f["high"] - f["low"]) / f["close"] * 100.0
        vol_ratio = f["volume"] / f["volume"].rolling(window, min_periods=5).mean()
        # The stress window is the pair's own worst premium move, located on its own bars.
        peak = rng.idxmax()
        out.append({
            "leg": label, "n_sessions": int(len(f)),
            "stress_date": str(peak.date()),
            "stress_range_pct": round(float(rng.loc[peak]), 2),
            "median_range_pct": round(float(rng.median()), 2),
            "range_multiple": round(float(rng.loc[peak] / rng.median()), 1),
            "stress_volume_vs_trailing": (round(float(vol_ratio.loc[peak]), 2)
                                          if pd.notna(vol_ratio.loc[peak]) else None),
        })
    return pd.DataFrame(out)


# --------------------------------------------------------------------------------
# The segmentation — which expression fits which borrow, and who buys it
# --------------------------------------------------------------------------------
#
# RATIFICATION STATUS: RATIFIED 2026-07-31 by the author. The cutoffs are read off the
# entry-outcome win rates -- 56% at low borrow, 42% at mid, 16% at high, on 90th-percentile
# entries held 252 sessions over 21.6 years -- and placed where that crossing happens. The
# evidence is the win rates; the placement was a judgement, and it is signed rather than
# asserted by the model.

SEGMENTATION_RATIFIED: str | None = "2026-07-31"   # author-signed

#: Borrow spread cutoffs in bp/yr. Derived, not chosen: the all-in carry is
#: borrow - 65bp/yr at today's rate legs, so these correspond to roughly 15 and 45bp/mo,
#: which bracket the levels at which the 21.6-year win rate crosses and then leaves 50%.
BORROW_CUTOFF_BP = {"linear_max": 250, "standby_max": 600}


def segmentation() -> list[dict]:
    """The four tiers, with the borrow band that selects each and what the desk earns."""
    def carry_at(borrow_bp: float) -> float:
        legs = rate_legs()
        return ((legs["krw_rate_pct"] - legs["usd_rate_pct"]) * 100 + borrow_bp
                + CONVERSION_FEE_BP) / 12.0

    lo, hi = BORROW_CUTOFF_BP["linear_max"], BORROW_CUTOFF_BP["standby_max"]
    return [
        {"expression": "linear pair",
         "borrow": f"borrow <= {lo}bp/yr  (all-in <= {carry_at(lo):.0f}bp/mo)",
         "who": "Level conviction, 6-12 month horizon, and a risk budget that can carry the "
                "skew.",
         "why": "This is the only band where the 21.6-year win rate sits at or above a coin "
                "flip. Below this carry the wait is cheap enough that the view required is "
                "about the LEVEL, not the timing.",
         "earns": "financing spread on both swap legs, borrow spread, execution, FX"},
        {"expression": "standby",
         "borrow": f"borrow {lo}-{hi}bp/yr, or catalyst-contingent conviction",
         "who": "Wants the trade if a catalyst fires and will not pay to wait for one. The "
                "RV-arb profile.",
         "why": "Zero bleed. Monitoring, the trigger list and a registered call with a "
                "resolution date, and the position is only initiated when an observable "
                "fires. At this borrow the linear pair loses more often than it wins.",
         "earns": "monitoring fee; the full ticket if and when it initiates"},
        {"expression": "long-local via TRS",
         "borrow": f"borrow > {hi}bp/yr, or no ADR borrow available at any price",
         "who": "Holds the compression view but will not or cannot pay for the short leg.",
         "why": "Drops the ADR borrow entirely, so the carry collapses to the funding "
                "differential — which is a tailwind. It is a directional position on the "
                "local line, not the pair, and the resolution-channel evidence says the local "
                "leg does close a large minority of these gaps.",
         "earns": "swap financing on the local leg; no borrow, no short"},
        {"expression": "pass",
         "borrow": "any borrow, if the view is about timing",
         "who": "Needs a dated exit, or has no level view.",
         "why": "We tested the timing and the shallow model won, which means there is no "
                "signal here to sell. A client who needs this to resolve by a date is buying "
                "something we did not build.",
         "earns": "nothing, and saying so is why the other three rows are believed"},
    ]


def segmentation_note() -> str:
    if SEGMENTATION_RATIFIED:
        return f"Cutoffs ratified {SEGMENTATION_RATIFIED}."
    return ("Cutoffs PROVISIONAL — read off the win rates, but where to cut a continuum is the "
            "author's judgement to sign.")


def indicated_tier() -> dict:
    """Which segmentation tier today's OBSERVABLE borrow state points at.

    THE DISTINCTION THIS FUNCTION EXISTS TO PRESERVE. Utilization is not price. D3 measures how
    many shares are out on loan, not what the desk will charge to lend one more, and the two
    can disconnect: a name can be lightly utilised and still quote wide because the lendable
    pool is concentrated in holders who will not lend. So this returns an INDICATION with the
    state that produced it, and it never returns a bracket as though it were a quote. The quote
    is the desk's, and the tier is not settled until it arrives.
    """
    from pipeline.measurement.utilization import utilization_state

    u = utilization_state()
    last = u.iloc[-1]
    state, pctile = str(last["state"]), float(last["balance_pctile"])
    tier = {"low": "linear pair", "mid": "standby", "high": "long-local via TRS"}.get(
        state, "standby")
    return {
        "as_of": str(u.index[-1].date()),
        "utilization_state": state,
        "balance_pctile": round(pctile, 4),
        "balance_shares": int(last["balance_shares"]),
        "net_lending_shares": int(last["net_lending_shares"]),
        "indicated_tier": tier,
        "is_a_quote": False,
        "caveat": ("Utilization, not price. D3 measures shares on loan, not the spread to "
                   "borrow one more. A lightly-utilised name can still quote wide if the "
                   "lendable pool sits with holders who will not lend. The tier is indicated, "
                   "not settled — the desk quote settles it."),
    }
