"""Hedge construction for expressions against the SKHY barrier. Non-advisory.

Every ratio here is derived from the premium identity or from documented deal terms, so
each traces to a source rather than to a fitted model. Where a quantity genuinely needs
the M3 convergence estimate (anything horizon-dependent — financing cost, carry, expected
holding period) the function returns ``PENDING_M3`` rather than a number, naming the table
cell that would fill it. See ``docs/gate_reports/S16.md``.

The finding that matters most here
----------------------------------
**A premium position is not FX-neutral even when the local leg is fully FX-hedged.**

From the identity  pi = P_adr * FX / (n * P_local) - 1  (FX in KRW per USD):

    d(pi)/d(FX) = P_adr / (n * P_local) = (1 + pi) / FX

so a proportional FX move dFX/FX shifts the premium by **(1 + pi) x dFX/FX in percentage
points.** At pi = 22.6%, a 1% KRW depreciation widens the premium by ~1.23pp *mechanically*,
with both equity legs unchanged.

The direction is the uncomfortable one for the obvious trade: **a short-premium position is
structurally short KRW weakness.** Hedging the local leg's KRW notional does not remove
this — that hedge neutralises the *local leg*, while the exposure lives in the *premium
itself*, which is the excess of ADR notional over local notional.

...but the mechanical coefficient is NOT the hedge ratio
--------------------------------------------------------
The derivative above holds **ceteris paribus** — equity prices fixed. Reality does not hold
them fixed. Tested on 5,063 days of the TSM pair (the deep comparator, 2005-2026):

======================================  ==========================
quantity                                value
======================================  ==========================
theoretical coefficient                 1.000
empirical coefficient                   **0.805**  (95% CI 0.507–1.103)
R^2 of FX alone on premium changes      **0.012**
beta(ADR return, dFX)                   −1.91
beta(local return, dFX)                 −1.69
======================================  ==========================

Three honest readings, in order of importance:

1. **Theory is now marginally rejected on the deep sample.** On 2,327 days the interval
   (0.507–1.103) contained 1.000 comfortably. On 5,063 days it is 0.653–1.058, and the
   pair's own analytic coefficient (1 + mean pi = 1.062) sits just outside it. The
   mechanical link is therefore real but partially offset, and calling it "1.0, unrejected"
   was a statement about a short sample.
2. **Both equity legs reprice strongly against FX** (betas ≈ −1.9 and −1.7), and those
   co-movements partially offset the mechanical term. That is *why* the empirical
   coefficient sits below 1.
3. **FX explains ~1.2% of daily premium variation.** The mechanical link is real and
   correctly signed, but it is not a dominant driver of day-to-day premium moves. A hedge
   built as though FX were the main risk would be solving the wrong problem.

So :func:`fx_sensitivity` reports the analytic figure *and* the empirical band, and refuses
to collapse them into a single hedge ratio. Doing so would present an imprecisely estimated
relationship as a precise one.
"""

from __future__ import annotations

from dataclasses import dataclass

PENDING_M3 = "pending M3 estimate"

# Documented deal terms (SK Hynix 424B4 [P]).
LOCAL_SHARES_PER_ADR = 0.1        # 10 ADSs = 1 common share
ADS_FEE_EACH_WAY = 0.05           # USD per ADS, issuance and cancellation


@dataclass(frozen=True)
class HedgeLegs:
    """One unit of the convergence expression: short 1 ADR against its underlying."""

    adr_price_usd: float
    local_price_krw: float
    fx_krw_per_usd: float
    n_adr: float = 1.0

    @classmethod
    def live(cls, pair_id: str = "skhy", n_adr: float = 1.0) -> "HedgeLegs":
        """Build from the legs' LAST SHARED date, never from each leg's own last close."""
        from pipeline.measurement.premium import latest_common_legs
        s = latest_common_legs(pair_id)
        return cls(s["adr"], s["local"], s["fx"], n_adr)

    @property
    def local_shares(self) -> float:
        """Underlying shares per ADR held, from the documented ratio."""
        return self.n_adr * LOCAL_SHARES_PER_ADR

    @property
    def adr_notional_usd(self) -> float:
        return self.n_adr * self.adr_price_usd

    @property
    def local_notional_krw(self) -> float:
        return self.local_shares * self.local_price_krw

    @property
    def local_notional_usd(self) -> float:
        return self.local_notional_krw / self.fx_krw_per_usd

    @property
    def premium(self) -> float:
        """pi implied by these three prices — the same construction as M1."""
        return (self.adr_price_usd * self.fx_krw_per_usd) / (
            LOCAL_SHARES_PER_ADR * self.local_price_krw) - 1.0


def fx_hedge(legs: HedgeLegs) -> dict:
    """FX hedge sizing, and the residual the local-leg hedge does not cover.

    Two distinct quantities, routinely conflated:

    * ``local_leg_krw_notional`` — the KRW to sell forward to neutralise the *local leg*.
    * ``residual_premium_notional_usd`` — the excess of ADR notional over local notional.
      This is the premium expressed as money, and it carries the FX sensitivity below.
    """
    residual_usd = legs.adr_notional_usd - legs.local_notional_usd
    pi = legs.premium
    return {
        "local_leg_krw_notional": round(legs.local_notional_krw, 2),
        "local_leg_usd_equivalent": round(legs.local_notional_usd, 2),
        "adr_leg_usd_notional": round(legs.adr_notional_usd, 2),
        "residual_premium_notional_usd": round(residual_usd, 2),
        "residual_as_pct_of_adr_leg": round(residual_usd / legs.adr_notional_usd, 4),
        "identity_check": round(residual_usd / legs.adr_notional_usd - pi / (1 + pi), 10),
        "note": (
            "Selling local_leg_krw_notional forward hedges the LOCAL LEG only. The "
            "residual — the premium expressed as money — remains FX-exposed; see "
            "fx_sensitivity()."
        ),
        "hedge_cost": PENDING_M3,
        "hedge_cost_note": (
            "Forward-points cost depends on tenor, and tenor depends on the expected "
            "holding period, which is the M3 half-life. Fill from the per-regime metrics "
            "table (docs/gate_reports/S4.md) once a non-extrapolated half-life exists. "
            "SGX exchange_marked months (3-12) are NOT executable and must not be used "
            "for a traded-cost claim."
        ),
    }


# Measured on the TSM pair. RE-ESTIMATED 2026-07-30 on 5,063 days (2005-2026) after the
# comparator's ADR leg was recovered back to 1997 -- the previous values came from 2,327 days
# because the leg's provider chain served a rolling ten-year window. Pinned by
# tests/test_lab_tsmc.py against pipeline.lab.tsmc.fx_sensitivity_deep(), so a constant that
# drifts from its own estimator fails the suite rather than shipping.
#
# TWO CAVEATS THAT TRAVEL WITH THIS NUMBER, and are drawn on G27 rather than buried:
#   * It is a TAIWANESE estimate applied to a KOREAN pair. The TWD is a managed float, so
#     this is a lower bound on the won's sensitivity, not a like-for-like.
#   * It is NOT stable across eras: 2016-2020 gives 0.31 with an interval containing zero;
#     2021-2026 gives 1.26. No single hedge ratio is right for all regimes.
FX_COEF_EMPIRICAL = 0.856
FX_COEF_CI95 = (0.653, 1.058)
FX_R2_ALONE = 0.0134
FX_COEF_SAMPLE = "TSM pair, 2005-01-03 to 2026-07-24, 5,063 daily changes"


def fx_sensitivity(premium: float, fx_move_pct: float = 0.01) -> dict:
    """Premium response to a proportional FX move — analytic figure AND empirical band.

    Deliberately returns both and does not collapse them. The analytic coefficient is a
    ceteris-paribus derivative; the empirical one absorbs the equity legs' own FX betas.
    Reporting a single number would present an imprecisely estimated relationship as a
    precise hedge ratio.
    """
    analytic = (1.0 + premium) * fx_move_pct
    lo, hi = (c * premium_scale for c, premium_scale in
              ((FX_COEF_CI95[0], (1.0 + premium) * fx_move_pct),
               (FX_COEF_CI95[1], (1.0 + premium) * fx_move_pct)))
    return {
        "premium": round(premium, 4),
        "fx_move_pct": fx_move_pct,
        "analytic_premium_change_pct_pts": round(analytic * 100, 3),
        "empirical_central_pct_pts": round(analytic * FX_COEF_EMPIRICAL * 100, 3),
        "empirical_range_pct_pts": (round(lo * 100, 3), round(hi * 100, 3)),
        "fx_share_of_daily_premium_variance": FX_R2_ALONE,
        "direction": (
            "KRW DEPRECIATION (FX up) WIDENS the premium mechanically. A short-premium "
            "position is therefore structurally short KRW weakness, and this exposure "
            "survives a hedge sized off the local leg alone."
        ),
        "derivation": "d(pi)/d(FX) = P_adr/(n*P_local) = (1+pi)/FX  — from the pi identity",
        "caveat": (
            f"Analytic coefficient is ceteris paribus. Empirically {FX_COEF_EMPIRICAL} "
            f"(95% CI {FX_COEF_CI95[0]}-{FX_COEF_CI95[1]}) because both equity legs carry "
            f"strong negative FX betas that partly offset it. FX explains only "
            f"{FX_R2_ALONE:.1%} of daily premium variation — the link is real and correctly "
            "signed, but it is not the dominant daily risk."
        ),
    }


def beta_hedge(*_args, **_kwargs) -> dict:
    """Market-beta overlay. Requires M5, which is not built."""
    return {
        "hedge_ratio": PENDING_M3,
        "confidence_interval": PENDING_M3,
        "blocker": (
            "Requires the M5 beta estimate against a Korea market proxy. M5 is not built "
            "(no index series is landed in-repo, and the proxy source is unproposed). A "
            "point beta without its interval would be the exact over-claim this repo "
            "avoids."
        ),
    }


def sizing_horizon() -> dict:
    """Holding period and financed cost, as a floor with an open tail (S17).

    This function used to return PENDING_M3 for both fields, because the half-life was an
    extrapolation and financing cost is linear in horizon. Extending the local-projection
    window to h=400 (S17) did not produce the point estimate that was expected — it produced
    something more useful and less flattering: rho's 95% upper band never crosses 0.5 at any
    estimable horizon, so the holding period has NO FINITE UPPER BOUND, while its lower bound
    is identified.

    So the honest output is a FLOOR, not a point, and it is quotable. A client can be told
    the minimum financed cost and told plainly that it is unbounded above. That is a real
    number where there was previously a blank.
    """
    from pipeline.convergence.jorda import run_panel

    hl = run_panel()["one_way_constrained"].hl
    floor_days = hl.lower
    return {
        "expected_holding_period": (
            f"AT LEAST {floor_days:.0f} trading days (~{floor_days / 21:.0f} months); "
            "NO FINITE UPPER BOUND at 95%"
        ),
        "holding_period_floor_days": floor_days,
        "holding_period_point_days": hl.point,
        "holding_period_ceiling_days": None,           # None means unbounded, not missing
        "financed_cost_over_horizon": (
            "Quote as a FLOOR: (borrow + funding + hedge points) accrued over at least "
            f"{floor_days:.0f} trading days, with no upper bound. Cost is linear in horizon "
            "and the horizon's upper tail is open, so a point cost would misstate the risk "
            "in the direction that flatters the trade."
        ),
        "fills_from": (
            "pipeline.convergence.jorda.run_panel()['one_way_constrained'].hl — first passage "
            "of rho below 0.5 with a 95% Newey-West band, h to 400."
        ),
        "support": hl.support,
        "why_no_point_estimate": (
            f"First passage sits at {hl.point:.0f}d but only ~{hl.n_eff_at_point:.0f} "
            "independent spans support it, and the band's upper edge never crosses 0.5. The "
            "data locate a floor precisely and the tail not at all."
        ),
        "what_is_usable_now": (
            "The qualitative result is robust: persistence rho_1 = 0.94 (t-HAC 129) versus "
            "0.04 for the fungible control. The premium mean-reverts SLOWLY, and the floor "
            "on how slowly is now measured rather than assumed."
        ),
    }


def skew_note() -> str:
    """Attached to every hedge output, by design."""
    return (
        "The hedge neutralises FX and (optionally) market beta. It does NOT neutralise the "
        "barrier asymmetry: the upper barrier is the Company's discretion with no numeric "
        "cap on file, so the residual remains short a one-sided barrier — bounded gain to "
        "the conversion floor, unbounded loss above. See G4."
    )
