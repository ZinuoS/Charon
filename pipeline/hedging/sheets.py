"""Per-expression trade sheets. Facilitator voice, non-advisory, gate-honest.

Each sheet describes *how an expression is constructed, hedged, financed and monitored* —
never whether to put it on. Language rule: "clients seeking X may consider…", balanced by
the opposite expression, and the negative skew appears in the same block as any
convergence structure.

Every quantitative field that depends on the M3 convergence horizon renders as
``pending M3 estimate`` with the table cell that fills it. Those are not omissions; they
are the honest state of a research programme whose half-life estimate is still
extrapolated (docs/gate_reports/S16.md, Block 0).
"""

from __future__ import annotations

from functools import lru_cache

from dataclasses import dataclass, field

from .ratios import PENDING_M3, skew_note

LIVE = "live"
CONTINGENT = "contingent"



@lru_cache(maxsize=1)
def _horizon() -> dict:
    """Holding-period bounds, fetched once. Sheets must never carry a literal horizon."""
    from pipeline.hedging.ratios import sizing_horizon
    return sizing_horizon()


def _accrual_basis() -> str:
    h = _horizon()
    return (f"floor >={h['holding_period_floor_days']:.0f} trading days "
            f"(~{h['holding_period_floor_days'] / 21:.0f}m); NO upper bound at 95%")



def _borrow_reading() -> str:
    """Public half of the borrow question. Degrades to a stated absence, never to silence."""
    try:
        from pipeline.measurement.utilization import current
        u = current()
        return (f"on-loan balance {u['balance_shares']:,} sh, {u['balance_pctile']:.0%} of its own "
                f"1,250-session history ({u['state']}); net {u['net_lending_5d']:+,} sh over 5d "
                f"[{u['as_of']}]")
    except Exception:
        return "D3 lending not landed — run `just ingest-d3`"


@dataclass
class TradeSheet:
    name: str
    readiness: str                      # live | contingent
    structure: str
    monetizes: str
    hedge: list[str]
    residual_exposures: list[str]
    cost_stack: list[tuple[str, str]]   # (segment, value-or-status)
    stress: str
    constraints: list[str]
    risks: list[str]
    monitor: str
    monitor_reading: str
    alternative: str = ""
    contingency: str = ""
    # "expression" = a way to take the view. "operational" = how the position is carried or
    # the leg is booked. G10 charts expressions only; an operational sheet in an expressions
    # matrix would be answering a question the figure does not ask.
    kind: str = "expression"
    pending: list[str] = field(default_factory=list)

    def render(self) -> str:
        L = [f"{'=' * 78}", f"{self.name.upper()}   [{self.readiness}]", "=" * 78]
        if self.contingency:
            L += [f"CONTINGENT ON: {self.contingency}", ""]
        L += [f"STRUCTURE       {self.structure}", f"MONETIZES       {self.monetizes}", ""]
        L += ["HEDGE"] + [f"  - {h}" for h in self.hedge] + [""]
        L += ["RESIDUAL EXPOSURES (what the hedge does NOT cover)"]
        L += [f"  ! {r}" for r in self.residual_exposures] + [""]
        L += ["COST STACK"] + [f"  {seg:<34s} {val}" for seg, val in self.cost_stack] + [""]
        L += [f"MARGIN / STRESS  {self.stress}", ""]
        L += ["SIZING & FREQUENCY CONSTRAINTS (documented only)"]
        L += [f"  - {c}" for c in self.constraints] + [""]
        L += ["RISK"] + [f"  ! {r}" for r in self.risks] + [""]
        L += [f"MONITOR         {self.monitor}", f"  current reading: {self.monitor_reading}", ""]
        if self.alternative:
            L += ["ALTERNATIVE EXPRESSION", f"  {self.alternative}", ""]
        if self.pending:
            L += ["PENDING MODEL ESTIMATE"] + [f"  ? {p}" for p in self.pending] + [""]
        L += ["Informational only. Not investment advice, not a solicitation. The desk",
              "quotes live levels on request and does not recommend positions.", "=" * 78]
        return "\n".join(L)


def convergence_rv(premium: float, headroom_reading: str) -> TradeSheet:
    return TradeSheet(
        name="1. Convergence relative value",
        readiness=LIVE,
        structure="Short 1 ADR (SKHY) vs long 0.1 common shares (000660), FX-hedged. "
                  "Ratio is the documented deal term: 10 ADSs = 1 share [424B4].",
        monetizes="Compression of the ADR premium toward the conversion floor.",
        hedge=[
            "FX: sell KRW forward against the local leg's KRW notional.",
            "Optional beta overlay against a Korea market proxy — pending M5.",
        ],
        residual_exposures=[
            "The PREMIUM ITSELF is FX-exposed. A local-leg-only hedge leaves ~18% of the "
            "ADR notional uncovered at pi=22.6%; that residual is structurally short KRW "
            "weakness (analytic 1.23pp per 1% FX; empirically 0.99pp, 95% CI 0.62-1.35).",
            "FX explains only ~1.2% of daily premium variance — hedging FX does not make "
            "this a low-variance position.",
            skew_note(),
        ],
        cost_stack=[
            ("conversion round trip", "0.07% of notional [424B4]"),
            ("local short borrow", "— desk quotes live —"),
            ("ADR borrow", "— desk quotes live —"),
            ("FX hedge (forward points)", "— desk quotes live at >=7m tenor —"),
            ("funding differential", "— desk quotes live —"),
            ("ACCRUAL BASIS", _accrual_basis()),
        ],
        stress="Realized week-one excursion: pi 15.98% -> 51.60%, i.e. ~36pp marked "
               "against a short-premium position BEFORE any convergence. Not modelled.",
        constraints=[
            "Local->ADR issuance requires the Company's consent against an undisclosed "
            "level; there is no numeric deposit cap on file. Size is not quota-limited so "
            "much as permission-limited.",
            "ADR->local cancellation is uncapped and is a holder right [17 CFR 239.36(a)].",
            "Settlement runs depositary -> KSD -> KRX.",
            "Local short-sale availability is a live regulatory variable (resumed 2025-03-31).",
        ],
        risks=[
            "Structural negative skew: bounded gain to the conversion floor, unbounded "
            "loss above. The upper barrier is discretionary, not a cap.",
            "Convergence may arrive via the LOCAL leg appreciating rather than the ADR "
            "falling — in which case a short-ADR expression captures none of it.",
            # Derived, never hardcoded: this line moved from 143d to 220d when the panel
            # went from one constrained pair to four, and a literal would have silently
            # gone stale in the one place a client reads it.
            f"Persistence is high across the constrained comparator panel. The premium "
            f"mean-reverts slowly, so the position must be financeable for a long horizon — "
            f"{_horizon()['expected_holding_period'].lower()}. A financing line that can be "
            f"pulled inside that floor is the binding risk on this trade.",
        ],
        monitor="TRIGGERS ARE MECHANISM-OBSERVABLES, NOT FORECASTS -- by demonstrated "
                "preference, not default. Directional model timing was tested head-to-head "
                "against an overparameterised alternative (notebook 06, DEV-004). The shallow "
                "model won and produced a GROSS panel Sharpe of +0.54 at h=20 that survives a "
                "vol-managed benchmark (HAC t=5.3) -- but it is pre-cost, at 0.21 turnover per "
                "step, on the comparator panel with SKHY never fitted. An unquantified cost "
                "stack can plausibly consume it, so entry and unwind reference observables "
                "whose reading does not depend on that. "
                "D5 headroom on ISIN US78392B2060 (the capped programme) — the barrier-state "
                "observable. A deposit clearing there is the first evidence consent operates.",
        monitor_reading=headroom_reading,
        alternative="Clients expecting convergence via the local leg may consider a long-local "
                    "expression without the ADR short, which carries no borrow and no skew "
                    "against the upper barrier, but forgoes any gain from ADR decline.",
        pending=[
            # S17 moved the first two from "pending" to "quoted as a floor" — see
            # ratios.sizing_horizon(). What remains pending is the CEILING, which the data
            # say does not exist at 95%, and that is a finding rather than a gap.
            "Upper bound on holding period — NONE EXISTS at 95%: rho's upper band never "
            "crosses 0.5 at any estimable horizon. Financed cost is therefore unbounded "
            "above and is quoted as a floor, never a point.",
            "Beta hedge ratio and interval — requires M5.",
        ],
    )


def _contingent(name: str, structure: str, monetizes: str, blocker: str,
                monitor: str) -> TradeSheet:
    return TradeSheet(
        name=name, readiness=CONTINGENT, structure=structure, monetizes=monetizes,
        hedge=["Construction defined; ratios pending the data below."],
        residual_exposures=[skew_note()],
        cost_stack=[("all segments", f"{PENDING_M3} — expression not yet constructible")],
        stress="Inherits the realized 36pp excursion as the premium-leg stress case.",
        constraints=["Same permission-limited issuance constraint as sheet 1."],
        risks=["Structural negative skew on any short-premium leg.",
               "Expression is not yet constructible from landed data — see contingency."],
        monitor=monitor, monitor_reading="n/a until the data lands",
        contingency=blocker,
        pending=[f"All quantitative fields — {blocker}"],
    )


def all_sheets(premium: float, headroom_reading: str) -> list[TradeSheet]:
    return [
        # Part 3 first: how the position is carried and how the leg is booked come before
        # the expression, because both can make the trade impossible regardless of the view.
        financing_margin_sheet(headroom_reading),
        local_access_sheet(headroom_reading),
        convergence_rv(premium, headroom_reading),
        _contingent(
            "2. Local-access substitute (index synthetic)",
            "Long KOSPI200 futures / short ex-Hynix basket, as a proxy for local exposure "
            "where direct local access is constrained.",
            "Offshore demand for local exposure that cannot be expressed directly.",
            "H2 data status: the Eurex-KRX link was terminated 2025-06-06; KRX night-session "
            "day/night bar separability is unverified and no sanctioned KOSPI200 series is landed.",
            "KOSPI200 basis vs fair value on premium-widening days."),
        _contingent(
            "3. Term-structure relative value",
            "Long ADR forward / short local forward at front expiries, reversed at the back, "
            "FX-forwarded. Trades convergence SPEED, not level; requires no conversion.",
            "Mispricing of the implied convergence schedule between two disjoint pools.",
            "No sanctioned listed-derivatives source for 000660 options or SKHY options has "
            "landed. Any curve shown would be SAMPLE data, not market data.",
            "Implied premium term structure once a derivatives source lands."),
        _contingent(
            "4. Volatility relative value",
            "Long SKHY straddles / short 000660 straddles + USDKRW vol, ratio-weighted by "
            "the variance decomposition.",
            "A structural premium in ADR implied vol over the local+FX implied stack.",
            "Realized side is computed (H4); the IMPLIED side requires an options surface "
            "that is unsourced. The decomposition motivates the trade but cannot price it.",
            "Realized variance shares (H4) vs the implied stack when it lands."),
        _contingent(
            "5. Flow-aware execution overlay",
            "Timing execution around mechanical LETF rebalance windows at each market close. "
            "Framed as execution timing, NOT as alpha.",
            "Reduced slippage against predictable mechanical flow — an execution service.",
            "H3 is data-blocked: no landed AUM. Issuer pages are JS SPAs; the data-bearing "
            "Naver route is terms-withheld.",
            "Estimated rebalance notional vs close-window premium changes."),
    ]


# ================================================================================
# Part-3-first sheets (S16 Block 5). Operational depth before the view.
#
# Both reuse TradeSheet rather than introducing a second sheet type -- the fields already
# cover structure / hedge / residuals / cost / stress / constraints / monitor, and the only
# thing these two need that the convergence sheet did not is a longer constraints list.
#
# PUBLIC-DATA HALVES ONLY. Anything that needs a firm's own borrow book, prime line or
# booking entity is listed as a desk follow-up, not guessed at.
# ================================================================================

def _table_cell(regime: str, horizon: int) -> str:
    """Cite the S4 metrics table by cell, so a hedge number traces to its evidence."""
    return f"data/derived/s4/metrics_table.csv [{regime}, h={horizon}]"


def financing_margin_sheet(headroom_reading: str) -> TradeSheet:
    """Short-SKHY: the financing and margin-stress sheet. Part 3 first."""
    h = _horizon()
    return TradeSheet(
        name="A. SHORT-SKHY FINANCING & MARGIN STRESS",
        readiness=LIVE,
        structure="Short 1 ADR (SKHY). Financing and margin treatment only -- this sheet "
                  "prices CARRYING the position, not the view. Pair with the convergence RV "
                  "sheet for the expression.",
        monetizes="Nothing on its own. It states what holding the short costs and what it "
                  "posts under stress.",
        hedge=[
            "Not a hedge sheet. The FX and beta legs live on the convergence RV sheet; the "
            "residual premium notional it leaves unhedged (~18% of the ADR leg) is the "
            "quantity margined here.",
        ],
        residual_exposures=[
            f"BORROW STATE (public half): {_borrow_reading()}. A LOW reading is not "
            "reassurance -- it says borrow is plentiful today, on a series with no forward "
            "commitment in it. The tenor question is the firm half.",
            "RECALL RISK is the binding one. The position must be financeable across the "
            f"whole holding floor -- {h['expected_holding_period'].lower()}. A borrow "
            "recalled inside that floor forces a close at whatever the premium is on the "
            "day, which converts a convergence view into a liquidation.",
            "Margin is marked to the OBSERVABLE premium, so the stress case is a realized "
            "excursion rather than a modelled shock.",
            skew_note(),
        ],
        cost_stack=[
            ("conversion round trip", "0.07% of notional [424B4]"),
            ("local borrow (public state)", _borrow_reading()),
            ("ADR borrow", "— desk quotes live —"),
            ("financing spread on short proceeds", "— desk quotes live —"),
            ("ACCRUAL BASIS", _accrual_basis()),
            ("half-life evidence", _table_cell("one_way_constrained", 60)),
        ],
        stress="MARKED STRESS: pi 22.57% -> 51.60%, the realized week-one excursion. On a "
               "$130 ADR leg that is ~$29/ADR of additional margin against a short, before "
               "any convergence. Not a modelled shock -- it happened, in the first five "
               "sessions of the programme's life.",
        constraints=[
            "Locate must survive the holding floor, not the trade date. A 220-day floor "
            "against an overnight-recallable borrow is a maturity mismatch, and it is the "
            "single most likely way this position ends early.",
            "Short-sale regime: Korean short selling resumed 2025-03-31; Korea has twice "
            "responded to sharp declines with bans. The ADR leg is US-listed and unaffected, "
            "but the local hedge leg is not.",
            "DESK FOLLOW-UP (firm half): term-borrow availability and rate on SKHY; whether "
            "the prime line can commit borrow for >=12 months; haircut schedule on the "
            "premium leg.",
        ],
        risks=[
            "Unbounded above. No numeric deposit cap appears in any SEC filing, so there is "
            "no level at which the margin requirement stops growing.",
            "Financing cost is LINEAR in holding horizon and the horizon's upper tail is "
            "open, so the cost is quoted as a floor and never as a point.",
        ],
        monitor="D5 headroom on ISIN US78392B2060 for the barrier state, and KOFIA 000660 "
                "lending balance for the borrow state. Two different constraints, two feeds.",
        monitor_reading=f"{headroom_reading}  ·  borrow: {_borrow_reading()}",
        alternative="A defined-risk expression caps the margin path at the cost of the "
                    "premium carry, if listed options on SKHY become available.",
        pending=[
            "Term-borrow rate and availability -- firm half, desk follow-up.",
            "Haircut schedule -- firm half, desk follow-up.",
        ],
        kind="operational",
    )


def local_access_sheet(headroom_reading: str) -> TradeSheet:
    """Long-000660: the access-regime sheet. Mechanics, not a view."""
    return TradeSheet(
        name="B. LONG-000660 ACCESS REGIME",
        readiness=LIVE,
        structure="Long 0.1 common shares (000660.KS) per ADR-equivalent. This sheet is "
                  "about GETTING THE LEG ON as a non-resident, which is the part that "
                  "actually gates the trade, not about the view.",
        monetizes="Nothing on its own. It is the access half of any convergence expression.",
        hedge=["FX: sell KRW forward against the KRW notional. Tenor follows the holding "
               "floor, so the forward is a >=12m instrument, not a spot-adjacent one."],
        residual_exposures=[
            "SETTLEMENT MISMATCH. KRX settles T+2 and the ADR leg T+1, so a paired trade "
            "carries a one-day funding gap on every rebalance. Small per turn, not small "
            "over a 220-day floor.",
            "The premium notional itself stays FX-exposed even with this leg hedged -- see "
            "the convergence RV sheet's residual section.",
        ],
        cost_stack=[
            ("KRX transaction tax + fees", "— desk quotes live —"),
            ("FX hedge (forward points)", "— desk quotes live at >=12m tenor —"),
            ("custody / omnibus", "— desk quotes live —"),
            ("ACCRUAL BASIS", _accrual_basis()),
        ],
        stress="The long leg's stress is the mirror of the short's: the same 22.57 -> 51.60 "
               "excursion is a MARK-UP here. It is stated because a paired position nets "
               "them and an unpaired one does not.",
        constraints=[
            "INVESTMENT REGISTRATION CERTIFICATE. A non-resident needs an IRC to hold "
            "Korean listed equity directly; it is obtained through a standing proxy, and it "
            "is a prerequisite rather than a formality.",
            "OMNIBUS vs SEGREGATED. Omnibus accounts reduce the per-account registration "
            "burden but the beneficial-owner reporting still resolves to the underlying "
            "holder, so the aggregation is operational, not regulatory.",
            "BOOKING ENTITY is the live operational question: which entity holds the IRC "
            "determines which entity can hold the leg, and a convergence trade booked "
            "against an entity without one cannot be assembled at all. Framed here as a "
            "question, because the answer is a firm fact.",
            "SKHY is FORWARD-TEST ONLY in this repo (README section 8). Nothing on this "
            "sheet is a forecast of the pair.",
            "DESK FOLLOW-UP (firm half): which booking entity holds a Korean IRC; standing- "
            "proxy arrangement and its custodian; whether omnibus is available for this "
            "strategy or segregation is required.",
        ],
        risks=[
            "Access risk is not price risk and does not net against it. If the leg cannot be "
            "booked, the expression does not exist -- there is no partial version.",
            "Korean short-sale regime changes affect the paired trade even when this leg is "
            "the long one, because the pairing needs the other side.",
        ],
        monitor="Standing-proxy and IRC status at the booking entity, plus the Korean "
                "short-sale regime notice board. Both are state, not price.",
        monitor_reading=headroom_reading,
        alternative="Index-synthetic local exposure avoids the IRC entirely but introduces "
                    "basis to the name -- see the local-access substitute sheet, which is "
                    "contingent on KOSPI200 data this programme has not landed.",
        pending=[
            "H3 POWER: at n=11 SKHY observations the minimum detectable close-window effect "
            "is far larger than any plausible LETF rebalance impact; the design is not "
            "decision-capable until roughly 60 sessions accumulate (~2026-10-02).",
            "Booking entity / IRC / omnibus -- firm halves, desk follow-ups.",
        ],
        kind="operational",
    )
