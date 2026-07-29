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

from dataclasses import dataclass, field

from .ratios import PENDING_M3, skew_note

LIVE = "live"
CONTINGENT = "contingent"


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
            ("FX hedge (forward points)", f"{PENDING_M3} (tenor follows the horizon)"),
            ("funding differential", "— desk quotes live —"),
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
            "Persistence is high: rho_1 = 0.94 (t-HAC 129) on the comparator. The premium "
            "mean-reverts slowly, so the position must be financeable for a long horizon.",
        ],
        monitor="D5 headroom on ISIN US78392B2060 (the capped programme) — the barrier-state "
                "observable. A deposit clearing there is the first evidence consent operates.",
        monitor_reading=headroom_reading,
        alternative="Clients expecting convergence via the local leg may consider a long-local "
                    "expression without the ADR short, which carries no borrow and no skew "
                    "against the upper barrier, but forgoes any gain from ADR decline.",
        pending=[
            "Expected holding period — fills from S4 metrics table, half_life_days "
            "(one_way_constrained). Current figure is extrapolated beyond its fitting window.",
            "Financed cost over horizon — linear in the above, so it inherits the same gate.",
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
