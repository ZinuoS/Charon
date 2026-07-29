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
them fixed. Tested on 2,327 days of the TSM pair (the deep comparator):

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

1. **Theory is not rejected** — 1.000 sits inside the confidence interval — but it is not
   precisely pinned either. The interval is wide.
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


# Measured on 2,327 days of the TSM pair; see the module docstring.
FX_COEF_EMPIRICAL = 0.805
FX_COEF_CI95 = (0.507, 1.103)
FX_R2_ALONE = 0.012


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
    """Holding period and financed cost — gated on a usable half-life."""
    return {
        "expected_holding_period": PENDING_M3,
        "financed_cost_over_horizon": PENDING_M3,
        "fills_from": (
            "docs/gate_reports/S4.md, per-regime metrics table, `half_life_days` for the "
            "one_way_constrained row."
        ),
        "why_not_yet": (
            "The current figure (~227d) is an EXTRAPOLATION: rho does not cross 0.5 inside "
            "the 20-day fitting window, the regime holds a single pair, and the taxonomy is "
            "unratified. Financing cost scales linearly with horizon, so using it would "
            "convert an extrapolation into a fabricated cost."
        ),
        "what_is_usable_now": (
            "The qualitative result is robust: persistence rho_1 = 0.94 (t-HAC 129) versus "
            "0.04 for the fungible control. The premium mean-reverts SLOWLY. Any expression "
            "must be financeable over a long, and currently unquantified, horizon."
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
