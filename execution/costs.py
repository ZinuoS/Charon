"""Execution & cost layer (README §7) — documented figures only, non-advisory.

This module answers the desk prompt's Part 3 the way the rest of the repo answers Parts 1
and 2: with numbers traceable to a source, gaps stated rather than filled, and no
recommendation of any kind. It quantifies what a relative-value expression against this
barrier *costs* and what it *risks* — not whether to put one on.

Every constant carries its source. Where a real desk would quote a live level (borrow,
funding, hedge points) the repo does not have a public number, and the function returns
``None`` with a documented reason rather than an invented figure — the "hatched segment"
of the cost stack.

Compliance note. This is a public research artifact. Nothing here is a solicitation,
recommendation, or price target. The convergence expression is described alongside its
structural negative skew, always, because a cost table that omitted the skew would
misrepresent the trade.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Sourced constants (docs/research_notes.md; [P] = primary, SK Hynix 424B4) ---
ADS_FEE_EACH_WAY = 0.05          # [P] US$5.00 per 100 ADSs issued AND cancelled
ADS_PRICE_REF = 149.00           # [P] offering price per ADS
LOCAL_SHARES_PER_ADR = 0.1       # [P] 10 ADRs = 1 common share

# Realized stress path (repo data, docs/gate_reports S3/S4)
REALIZED_ENTRY_PREMIUM = 0.1598  # 2026-07-10 close-to-close pi
REALIZED_PEAK_PREMIUM = 0.5160   # 2026-07-14

@dataclass(frozen=True)
class CostSegment:
    name: str
    value_pct: float | None      # as a fraction of notional; None = not publicly documented
    source: str
    note: str = ""

    @property
    def documented(self) -> bool:
        return self.value_pct is not None


def conversion_round_trip() -> CostSegment:
    """ADR->local->ADR crossing cost. The 'obol' — small, symmetric, documented [P]."""
    rt = 2 * ADS_FEE_EACH_WAY                    # $0.10 per ADS
    pct = rt / ADS_PRICE_REF
    return CostSegment(
        "conversion round trip", pct,
        "SK Hynix 424B4 'Fees and Charges' [P]",
        f"${rt:.2f}/ADS (= ${rt / LOCAL_SHARES_PER_ADR:.2f}/common share) ≈ {pct:.2%} of "
        "price. Trivial against a 16–52% premium — cost is NOT what sustains the barrier.",
    )


def cost_stack() -> list[CostSegment]:
    """The full stack for a convergence expression. Undocumented legs are explicit, not zero."""
    return [
        conversion_round_trip(),
        CostSegment("local short borrow", None,
                    "no public source (docs/data_sources.md D3)",
                    "Korean short-sale resumed 2025-03-31 [P]; indicative borrow not publicly "
                    "documented at usable granularity. A desk quotes this live."),
        CostSegment("ADR borrow", None,
                    "no public source",
                    "indicative ADR borrow not publicly observable for a 3-week-old listing."),
        CostSegment("USD/KRW hedge (forward points)", None,
                    "SGX curve available but not carried into a live hedge calc here",
                    "SGX USD/KRW futures give the curve; the exchange_marked deferred months "
                    "are not executable. A live hedge cost is a desk quote."),
        CostSegment("USD vs KRW funding differential", None,
                    "FRED rate legs probeable, not yet assembled",
                    "US-Korea short-rate differential is buildable from public series; not "
                    "assembled this session."),
    ]


def margin_stress(entry: float = REALIZED_ENTRY_PREMIUM,
                  peak: float = REALIZED_PEAK_PREMIUM) -> dict:
    """The short-premium convergence expression marked through the realized week-one move.

    Not hypothetical: the premium went 16% -> 52% in the first days of trading. A short-
    premium position entered near the open was marked against by the full excursion before
    any convergence. The mark-to-market drawdown on the premium leg is peak - entry.
    """
    drawdown = peak - entry
    return {
        "entry_premium": entry,
        "peak_premium": peak,
        "premium_leg_drawdown_pct_pts": round(drawdown * 100, 1),
        "interpretation": (
            f"A short-premium expression entered at {entry:.1%} was marked against by "
            f"{drawdown * 100:.0f} percentage points as the premium ran to {peak:.1%} in "
            "week one — before any convergence. This is the stress case, and it is realized, "
            "not modelled."
        ),
        "structural_skew": (
            "The loss side is unbounded: there is no numeric ceiling on the premium (the "
            "upper barrier is the Company's discretion, not a cap). The gain side is bounded "
            "by the conversion floor. Every short-premium expression is negatively skewed by "
            "construction — see G4."
        ),
    }


def summary_table():
    """Cost stack as a frame; undocumented legs shown as 'quoted live', never as 0."""
    import pandas as pd
    rows = [{
        "segment": c.name,
        "cost": f"{c.value_pct:.2%}" if c.documented else "— quoted live —",
        "documented": c.documented,
        "source": c.source,
    } for c in cost_stack()]
    return pd.DataFrame(rows)
