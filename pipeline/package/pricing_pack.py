"""The PM-facing pricing pack: parameterisation and presentation, no new estimation.

WHAT THIS MODULE IS ALLOWED TO DO. Re-express machinery that already exists — the carry
decomposition, the breakeven, the margin sketch — at parameter values a portfolio manager will
want to vary. It fits nothing, estimates nothing, and pulls nothing. SKHY's forward-test status
depends on no model in this repository having been fitted to it, and a pricing pack is exactly
the kind of artifact that quietly breaks that by "calibrating" a parameter to make a chart look
better. Nothing here touches SKHY except to read its published premium.

THE DESK INPUTS ARE NOT ESTIMATES AND ARE NOT DEFAULTED. Borrow, the cross-currency basis and
the margin schedule are quotes the desk owns. They are declared in :data:`DESK_INPUTS` as None
until ratified, and every function that consumes one takes it as a REQUIRED argument. That is
deliberate and slightly inconvenient: a default would let a chart circulate carrying a number
nobody quoted, and the reader would have no way to tell. The inconvenience is the safety
feature. When the quotes land, one edit to DESK_INPUTS reprints the pack.

EPISTEMIC TAGS travel with every row: MEASURED (a published series), BRACKETED (a desk quote
pending, shown as a range), DOCUMENTED (a published fee or rule), ILLUSTRATIVE (a structural
sketch standing in for a schedule the desk owns).
"""

from __future__ import annotations

import pandas as pd

from pipeline.package.breakeven import CONVERSION_FEE_BP, critical_carry_bp
from pipeline.package.financing import ADR_BORROW_BRACKET_BP, BASIS_STATUS, rate_legs

#: Desk-owned inputs. None means UNRATIFIED, and every consumer requires the value explicitly
#: rather than reaching in here for a default.
#: TODO(ash: ratify — desk quote pending) for all three.
DESK_INPUTS: dict[str, float | None] = {
    "borrow_live_bps_yr": None,
    "xccy_basis_bps_yr": None,
    "initial_margin_pct": None,
}

#: Shown wherever a desk input is still unratified, so a placeholder can never be mistaken for
#: a quote by anyone reading the chart rather than the code.
BRACKETED_LABEL = "BRACKETED — desk quote pending"
LIVE_LABEL = "LIVE"

#: The illustrative initial margin used where the risk schedule has not landed. Quoted as a
#: number only so the arithmetic runs; every artifact using it is tagged ILLUSTRATIVE.
ILLUSTRATIVE_IM_PCT = 20.0


def borrow_status(borrow_bps_yr: float | None) -> str:
    """LIVE if the desk has ratified a borrow quote, BRACKETED otherwise."""
    return LIVE_LABEL if DESK_INPUTS["borrow_live_bps_yr"] is not None else BRACKETED_LABEL


def freshness(pair: str = "skhy") -> dict:
    """D7 — the one-line strip every artifact in this pack carries.

    A chart without an as-of date and a config pair is not a stale chart, it is an unfalsifiable
    one: a reader cannot tell whether it disagrees with today's screen because the market moved
    or because the chart was built differently. Both facts travel or neither is worth much.
    """
    from pipeline.measurement.premium import build_all_variants

    variant = build_all_variants(pair)[0]
    series = variant.series
    live = DESK_INPUTS["borrow_live_bps_yr"]
    return {
        "asof": str(series.index[-1].date()),
        "entry_premium_pct": round(float(series.iloc[-1]) * 100, 2),
        "close_def": variant.close_def,
        "fx_leg": variant.fx_leg,
        "borrow_status": borrow_status(live),
        "borrow_bps_yr": live,
        "pair": pair,
    }


def freshness_line(pair: str = "skhy") -> str:
    """The strip as one line of text, for a chart footer."""
    f = freshness(pair)
    borrow = f"{f['borrow_bps_yr']:.0f}bp/yr" if f["borrow_bps_yr"] else \
        f"{ADR_BORROW_BRACKET_BP['low']}-{ADR_BORROW_BRACKET_BP['high']}bp/yr"
    return (f"as of {f['asof']} · entry π {f['entry_premium_pct']:.2f}% · "
            f"config ({f['close_def']}, {f['fx_leg']}) · borrow {borrow} [{f['borrow_status']}]")


def carry_waterfall(borrow_bps_yr: float, xccy_basis_bps_yr: float,
                    horizon_days: float = 252.0) -> pd.DataFrame:
    """D1 — the all-in carry decomposition in bp/month, at an explicit borrow and basis.

    Both desk inputs are REQUIRED arguments with no defaults. `financing.carry_components`
    takes a bracket NAME and hardcodes the basis at zero; this takes the numbers, so a live
    quote and a hypothetical differ only in what is passed in.

    Sign convention, kept from the existing decomposition: POSITIVE is a cost to the client.
    The USD leg is negative because the short's proceeds and the collateral earn it.
    """
    legs = rate_legs()
    obol = CONVERSION_FEE_BP * 252.0 / horizon_days

    rows = [
        {"component": "USD rate earned", "bp_per_year": -legs["usd_rate_pct"] * 100,
         "status": "MEASURED", "source": f"{legs['usd_series']}, {legs['usd_as_of']}"},
        {"component": "KRW funding paid", "bp_per_year": +legs["krw_rate_pct"] * 100,
         "status": "MEASURED", "source": f"{legs['krw_series']}, {legs['krw_as_of']}"},
        {"component": "ADR borrow", "bp_per_year": float(borrow_bps_yr),
         "status": "BRACKETED" if DESK_INPUTS["borrow_live_bps_yr"] is None else "MEASURED",
         "source": borrow_status(DESK_INPUTS["borrow_live_bps_yr"])},
        {"component": "cross-currency basis", "bp_per_year": float(xccy_basis_bps_yr),
         "status": "BRACKETED" if DESK_INPUTS["xccy_basis_bps_yr"] is None else "MEASURED",
         "source": BASIS_STATUS},
        {"component": "cancellation floor (the obol)", "bp_per_year": float(obol),
         "status": "DOCUMENTED",
         "source": f"{CONVERSION_FEE_BP}bp round trip over {horizon_days:.0f} sessions"},
    ]
    out = pd.DataFrame(rows)
    out["bp_per_month"] = out["bp_per_year"] / 12.0
    out["cumulative_bp_per_month"] = out["bp_per_month"].cumsum()
    return out


def carry_waterfall_table(borrow_grid=(150, 400, 900),
                          xccy_basis_bps_yr: float = 0.0,
                          horizon_days: float = 252.0) -> pd.DataFrame:
    """D1 annex — one column per borrow level, plus the live column when it exists."""
    frames = {}
    for b in borrow_grid:
        w = carry_waterfall(b, xccy_basis_bps_yr, horizon_days)
        frames[f"{b:.0f}bp"] = w.set_index("component").bp_per_month
    live = DESK_INPUTS["borrow_live_bps_yr"]
    label = f"LIVE {live:.0f}bp" if live is not None else "BORROW_LIVE (unratified)"
    if live is not None:
        w = carry_waterfall(live, xccy_basis_bps_yr, horizon_days)
        frames[label] = w.set_index("component").bp_per_month
    else:
        frames[label] = pd.Series(
            {c: float("nan") for c in frames[next(iter(frames))].index})

    table = pd.DataFrame(frames)
    table.loc["ALL-IN"] = table.sum(min_count=1)
    table.loc["breakeven (critical carry)"] = critical_carry_bp(
        horizon_days=horizon_days) / 12.0
    table.loc["headroom"] = (table.loc["breakeven (critical carry)"]
                             - table.loc["ALL-IN"])
    return table.round(1)


if __name__ == "__main__":
    # A desk input must never be silently defaulted: both are positional and required.
    import inspect

    sig = inspect.signature(carry_waterfall)
    for p in ("borrow_bps_yr", "xccy_basis_bps_yr"):
        assert sig.parameters[p].default is inspect.Parameter.empty, (
            f"{p} has a default — a chart could then circulate carrying a number nobody quoted")
    assert all(v is None for v in DESK_INPUTS.values()), "DESK_INPUTS ratified without a note?"

    w = carry_waterfall(400, 0.0)
    assert set(w.status) <= {"MEASURED", "BRACKETED", "DOCUMENTED", "ILLUSTRATIVE"}
    assert w.bp_per_month.notna().all()
    # Cheaper borrow must mean lower all-in carry, or the sign convention has drifted.
    assert (carry_waterfall(150, 0.0).bp_per_year.sum()
            < carry_waterfall(900, 0.0).bp_per_year.sum())
    print(freshness_line())
    print(carry_waterfall_table().to_string())


def breakeven_surface(borrow_bps=range(150, 926, 25), half_lives=None,
                      xccy_basis_bps_yr: float = 0.0, pi_0: float | None = None,
                      horizon_days: float = 252.0) -> pd.DataFrame:
    """D2 — carry the trade BEARS minus carry it COSTS, bp/month, over borrow x half-life.

    Positive means the trade pays at that combination; the zero contour is the boundary the PM
    is actually interrogating, and it moves with half-life as much as with borrow — which is
    the point of promoting the 1-D breakeven curve to a surface.

    HALF-LIFE BOUNDS ARE READ LIVE, not typed. The session brief quoted 211-391 days; the panel
    currently returns 205.0-385.5. Nothing is wrong with either — the interval is re-estimated
    whenever the panel is rebuilt — but a hardcoded pair would have silently frozen a stale
    estimate into a PM-facing artifact and disagreed with the notebook that renders beside it.
    """
    from pipeline.convergence.jorda import run_panel

    hl = run_panel()["one_way_constrained"].hl
    if half_lives is None:
        half_lives = [round(x) for x in
                      pd.Series(range(0, 13)).mul((hl.upper - hl.lower) / 12).add(hl.lower)]
    if pi_0 is None:
        pi_0 = freshness()["entry_premium_pct"] / 100.0

    grid = {}
    for b in borrow_bps:
        cost = carry_waterfall(b, xccy_basis_bps_yr, horizon_days).bp_per_month.sum()
        grid[b] = {h: critical_carry_bp(pi_0=pi_0, horizon_days=horizon_days,
                                        half_life_days=h) / 12.0 - cost
                   for h in half_lives}
    out = pd.DataFrame(grid).T
    out.index.name = "borrow_bps_yr"
    out.columns.name = "half_life_days"
    return out


def surface_marker(xccy_basis_bps_yr: float = 0.0) -> dict:
    """The (point-estimate half-life, BORROW_LIVE) cell D2 marks — or why it cannot be marked."""
    from pipeline.convergence.jorda import run_panel

    hl = run_panel()["one_way_constrained"].hl
    live = DESK_INPUTS["borrow_live_bps_yr"]
    return {"half_life_days": hl.point, "borrow_bps_yr": live,
            "markable": live is not None,
            "note": ("marks the live quote against the point half-life" if live is not None
                     else "BORROW_LIVE unratified, so the cell cannot be marked; the borrow "
                          "axis is shown in full and the reader picks their own column")}


#: The realised SKHY excursion window the D3 replay uses. Not a scenario and not a simulation:
#: these are the dates on which the premium actually went from roughly 16% to roughly 52%.
EXCURSION_WINDOW = ("2026-07-10", "2026-07-29")

#: Notionals the sizing table is replayed at, USD.
SIZING_NOTIONALS = (25e6, 50e6, 100e6, 250e6)


def margin_sizing_table(notionals=SIZING_NOTIONALS, pair: str = "skhy",
                        window: tuple[str, str] | None = None,
                        margin_fn=None) -> pd.DataFrame:
    """D3 — the realised excursion replayed through the margin sketch at each notional.

    ENTIRELY ILLUSTRATIVE, and structured so it stops being so without a rewrite. ``margin_fn``
    defaults to the repository's parametric sketch; pass the desk's real schedule with the same
    (pair, notional, window) -> path signature and the replay does not change. That separation
    is the point: the excursion is MEASURED and the margin response is ILLUSTRATIVE, and a table
    that mixed them would let a desk schedule silently inherit a research assumption.
    """
    from pipeline.package.margin_path import peak_call

    fn = margin_fn or peak_call
    rows = []
    for n in notionals:
        p = fn(pair, n, window or EXCURSION_WINDOW)
        rows.append({
            "notional_usd": n,
            "premium_start_pct": p["premium_start"] * 100,
            "premium_peak_pct": p["premium_peak"] * 100,
            "peak_call_netted_usd": p["peak_total_pair_usd"],
            "peak_call_netted_pct_of_notional": p["peak_total_pair_pct"] * 100,
            "peak_call_two_ticket_usd": p["peak_total_standalone_usd"],
            "peak_call_two_ticket_pct_of_notional": p["peak_total_standalone_pct"] * 100,
            "netting_ratio": p["pair_vs_standalone"],
            "sessions_in_window": p["sessions"],
            "status": "ILLUSTRATIVE",
        })
    return pd.DataFrame(rows)


def unwind_table(notionals=SIZING_NOTIONALS, participation=(0.05, 0.10, 0.20),
                 stress_multiple: float = 10.0) -> pd.DataFrame:
    """D3 — sessions to exit each notional, normal and under a 10x range-widening assumption.

    The stressed column is the same arithmetic with participation divided by the stress
    multiple: a market whose range widens tenfold does not let you take the same share of it.
    That is a STRUCTURAL assumption, not a measurement, and it is labelled as one.
    """
    from pipeline.package.capacity import days_to_unwind

    base = days_to_unwind(sizes=tuple(notionals), participation=tuple(participation))
    base = base.rename(columns={"days_binding": "sessions_normal"})
    stressed = days_to_unwind(sizes=tuple(notionals),
                              participation=tuple(p / stress_multiple for p in participation))
    stressed = stressed[["size_usd", "days_binding"]].rename(
        columns={"days_binding": "sessions_stressed"})
    stressed["participation"] = [round(p * stress_multiple, 4)
                                 for p in days_to_unwind(
                                     sizes=tuple(notionals),
                                     participation=tuple(p / stress_multiple
                                                         for p in participation)).participation]
    out = base.merge(stressed, on=["size_usd", "participation"], how="left")
    out["status"] = "ILLUSTRATIVE"
    return out


#: Drawdown budgets to invert, as % of the risk capital the position is sized against.
DRAWDOWN_BUDGETS_PCT = (3.0, 5.0, 10.0)


def excursion_quantiles() -> dict:
    """The adverse-excursion axis D4 inverts: MEASURED, from the comparator and from SKHY.

    The SKHY row is not a quantile of the same distribution and must never be read as one. It is
    a single realised path, and it lands ABOVE the maximum of all 822 comparator entries — so
    treating it as, say, a P99 would understate it. It is carried as a named stress override.
    """
    from pipeline.lab import tsmc as LAB

    ex = LAB.excursions(LAB.premium())
    skhy = LAB.skhy_week_one_excursion()
    return {
        "P50": {"pp": round(ex.attrs["median_mae_pp"], 2), "status": "MEASURED",
                "source": f"median MAE, n={len(ex.attrs['mae_pp'])} comparator entries"},
        "P95": {"pp": round(ex.attrs["p95_mae_pp"], 2), "status": "MEASURED",
                "source": f"95th percentile MAE, n={len(ex.attrs['mae_pp'])}"},
        "comparator max": {"pp": round(ex.attrs["max_mae_pp"], 2), "status": "MEASURED",
                           "source": "worst single comparator entry"},
        "realised SKHY": {"pp": skhy["excursion_pp"], "status": "MEASURED",
                          "source": f"SKHY {skhy['from_pp']}% to {skhy['peak_pp']}% in "
                                    f"{skhy['sessions']} sessions — a realised path, NOT a "
                                    f"quantile, and larger than the comparator maximum"},
    }


def max_notional(drawdown_budget_pct: float, excursion_pp: float,
                 risk_capital_usd: float = 1.0) -> float:
    """D4 — the largest position whose adverse excursion fits inside a drawdown budget.

    Inverting the loss leg of the P&L identity. A short-premium position of notional N loses
    approximately N x (Delta pi) when the premium widens, so the budget binds at

        N = budget / excursion

    Returned as a MULTIPLE of risk capital when ``risk_capital_usd`` is left at 1.0. Carry is
    deliberately excluded: over the horizon in which an excursion of this size arrives, carry is
    a rounding error against it, and including it would flatter the answer.
    """
    if excursion_pp <= 0:
        raise ValueError("excursion must be positive; a zero excursion implies infinite size")
    return risk_capital_usd * (drawdown_budget_pct / excursion_pp)


def drawdown_budget_table(budgets=DRAWDOWN_BUDGETS_PCT) -> pd.DataFrame:
    """D4 — budget x excursion, as position size in multiples of risk capital."""
    qs = excursion_quantiles()
    rows = []
    for label, q in qs.items():
        for b in budgets:
            rows.append({"excursion": label, "excursion_pp": q["pp"],
                         "drawdown_budget_pct": b,
                         "max_notional_x_capital": round(max_notional(b, q["pp"]), 3),
                         "status": q["status"]})
    return pd.DataFrame(rows)
