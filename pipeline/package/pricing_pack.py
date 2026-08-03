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

#: THE HOUSE CARD — what the desk charges regardless of the name. DOCUMENTED, not bracketed:
#: these are published card levels, so they carry a different epistemic weight from the
#: name-specific special, and the waterfall never merges the two bars for exactly that reason.
#: A client who cannot see which part of their borrow line is card and which is scarcity cannot
#: negotiate either.
HOUSE_CARD_BPS_YR = {"fin_spread_bps": 50, "rebate_haircut_bps": 75}

#: JOINT stress states. Card widening and basis widening are BUNDLED, ratified 2026-08-03:
#: they are the same event seen from two desks. A funding squeeze that widens the house card is
#: the same squeeze that pushes the cross-currency basis more negative, so pricing them as
#: independent knobs would let a reader construct a state the market does not produce — a
#: crisis card with a flat basis — and read reassurance off it.
#:
#: The name special stays SEPARATE and unbundled. It widens for reasons specific to one issuer
#: (who holds the float, how tight recall is) rather than for market-wide funding reasons, so
#: tying it to the same multiplier would assert a correlation nothing here measures.
STRESS_STATES: dict[str, dict] = {
    "base":    {"card_mult": 1.0, "basis_bps": 0},
    "squeeze": {"card_mult": 1.5, "basis_bps": -25},
    "crisis":  {"card_mult": 2.0, "basis_bps": -50},
}

#: Kept as a derived view so a caller wanting only the card axis cannot silently get the
#: unbundled version by reaching for the old name.
CARD_STRESS_MULTS = {k: v["card_mult"] for k, v in STRESS_STATES.items()}
XCCY_BASIS_STRESS_BPS = tuple(v["basis_bps"] for v in STRESS_STATES.values())


def house_card_bps_yr(card_stress_mult: float = 1.0, card_locked: bool = False) -> float:
    """The card leg, stressed unless term financing has locked it.

    ``card_locked`` IS THE PRODUCT. Term financing does not make the card cheaper at inception;
    it makes the card's stress multiplier unable to move. Pricing that feature means rendering
    both states and reading the distance between them, which is why this returns the locked
    value rather than raising when the two arguments disagree.
    """
    base = sum(HOUSE_CARD_BPS_YR.values())
    return base * (1.0 if card_locked else card_stress_mult)


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


def carry_waterfall(name_special_bps_yr: float, xccy_basis_bps_yr: float,
                    card_stress_mult: float = 1.0, card_locked: bool = False,
                    horizon_days: float = 252.0) -> pd.DataFrame:
    """D1.1 — the all-in carry in bp/month, with the borrow line SPLIT.

    THE SPLIT IS THE POINT. `house card` is the desk's published financing spread plus rebate
    haircut and is DOCUMENTED; `name special` is what SK hynix specifically costs to borrow and
    is BRACKETED, because no public series prices it. Rendering them as one bar would hide which
    half of the borrow line is negotiable and which is scarcity — and they stress independently,
    so a merged bar cannot even be stressed correctly.

    ``name_special_bps_yr`` and ``xccy_basis_bps_yr`` remain REQUIRED with no defaults: both are
    desk inputs. The card arguments DO default, because a documented card level is not a quote
    pending — it is published, and defaulting to it is not the same act as defaulting to an
    unratified number.

    Sign convention: POSITIVE is a cost to the client. The USD leg is negative because the
    short's proceeds and the collateral earn it.
    """
    legs = rate_legs()
    obol = CONVERSION_FEE_BP * 252.0 / horizon_days
    card = house_card_bps_yr(card_stress_mult, card_locked)
    card_note = ("LOCKED by term financing" if card_locked
                 else f"stress x{card_stress_mult:g}")

    rows = [
        {"component": "USD rate earned", "bp_per_year": -legs["usd_rate_pct"] * 100,
         "status": "MEASURED", "leg": "non-borrow",
         "source": f"{legs['usd_series']}, {legs['usd_as_of']}"},
        {"component": "KRW funding paid", "bp_per_year": +legs["krw_rate_pct"] * 100,
         "status": "MEASURED", "leg": "non-borrow",
         "source": f"{legs['krw_series']}, {legs['krw_as_of']}"},
        {"component": "house card", "bp_per_year": float(card),
         "status": "DOCUMENTED", "leg": "non-borrow",
         "source": f"fin spread {HOUSE_CARD_BPS_YR['fin_spread_bps']}bp + rebate haircut "
                   f"{HOUSE_CARD_BPS_YR['rebate_haircut_bps']}bp, {card_note}"},
        # SIGN: the argument is the quoted BASIS, which is negative for KRW; its COST
        # contribution is its negation. A first version added the basis directly, so the
        # stress axis {0, -25, -50} made the trade progressively CHEAPER — a stress that
        # flatters. financing.py already documents the economics ("a negative KRW basis makes
        # swapping into KRW MORE expensive than parity"); the code simply disagreed with it.
        {"component": "cross-currency basis", "bp_per_year": -float(xccy_basis_bps_yr),
         "status": "BRACKETED" if DESK_INPUTS["xccy_basis_bps_yr"] is None else "MEASURED",
         "leg": "non-borrow",
         "source": f"quoted basis {xccy_basis_bps_yr:+.0f}bp/yr; {BASIS_STATUS}"},
        {"component": "cancellation floor (the obol)", "bp_per_year": float(obol),
         "status": "DOCUMENTED", "leg": "non-borrow",
         "source": f"{CONVERSION_FEE_BP}bp round trip over {horizon_days:.0f} sessions"},
        {"component": "name special", "bp_per_year": float(name_special_bps_yr),
         "status": "BRACKETED" if DESK_INPUTS["borrow_live_bps_yr"] is None else "MEASURED",
         "leg": "borrow", "source": borrow_status(DESK_INPUTS["borrow_live_bps_yr"])},
    ]
    out = pd.DataFrame(rows)
    out["bp_per_month"] = out["bp_per_year"] / 12.0
    out["cumulative_bp_per_month"] = out["bp_per_month"].cumsum()
    return out


def non_borrow_subtotal_bp_month(xccy_basis_bps_yr: float = 0.0,
                                 card_stress_mult: float = 1.0,
                                 card_locked: bool = False,
                                 horizon_days: float = 252.0) -> float:
    """Everything except the name special, bp/month. Computed, never quoted from a brief."""
    w = carry_waterfall(0.0, xccy_basis_bps_yr, card_stress_mult, card_locked, horizon_days)
    return float(w[w.leg == "non-borrow"].bp_per_month.sum())


def carry_waterfall_table(borrow_grid=(150, 400, 900),
                          xccy_basis_bps_yr: float = 0.0,
                          card_stress_mult: float = 1.0, card_locked: bool = False,
                          horizon_days: float = 252.0) -> pd.DataFrame:
    """D1.1 annex — one column per name special, at one card state."""
    frames = {}
    for b in borrow_grid:
        w = carry_waterfall(b, xccy_basis_bps_yr, card_stress_mult, card_locked, horizon_days)
        frames[f"{b:.0f}bp"] = w.set_index("component").bp_per_month
    live = DESK_INPUTS["borrow_live_bps_yr"]
    label = f"LIVE {live:.0f}bp" if live is not None else "BORROW_LIVE (unratified)"
    if live is not None:
        w = carry_waterfall(live, xccy_basis_bps_yr, card_stress_mult, card_locked,
                            horizon_days)
        frames[label] = w.set_index("component").bp_per_month
    else:
        frames[label] = pd.Series(
            {c: float("nan") for c in frames[next(iter(frames))].index})

    table = pd.DataFrame(frames)
    table.loc["NON-BORROW SUBTOTAL"] = table.drop(index=["name special"]).sum(min_count=1)
    table.loc["ALL-IN"] = table.drop(index=["NON-BORROW SUBTOTAL"]).sum(min_count=1)
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
                      horizon_days: float = 252.0, card_stress_mult: float = 1.0,
                      card_locked: bool = False) -> pd.DataFrame:
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
        cost = carry_waterfall(b, xccy_basis_bps_yr, card_stress_mult, card_locked,
                               horizon_days).bp_per_month.sum()
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


#: Terminal premium moves for D5, in percentage POINTS. Each is sourced, not invented.
#: TODO(ash: ratify) — the ladder itself is a presentation choice; the anchors are measured.
SCENARIO_DELTA_PI_PP = (-19.0, -9.5, 0.0, 10.0, 35.6)

#: Horizons for D5, in sessions.
SCENARIO_HORIZONS = (126, 252)


def scenario_rom(delta_pi_pp=SCENARIO_DELTA_PI_PP, borrow_grid=(150, 400, 900),
                 horizons=SCENARIO_HORIZONS, im_pct: float | None = None,
                 xccy_basis_bps_yr: float = 0.0) -> pd.DataFrame:
    """D5 — return on margin at each (terminal move, borrow, horizon).

    TWO P&L TERMS ONLY, per the identity already used by `scenarios.pnl`: the premium term and
    the carry term. Zero drift, no path dependence, no rebalancing. A short-premium position
    earns when the premium narrows, so a negative delta is a gain.

        pnl_pct_notional = -delta_pi - carry_bp_yr/1e4 * horizon/252
        rom              = pnl_pct_notional / initial_margin

    Initial margin defaults to the ILLUSTRATIVE 20% rather than to a desk schedule, and every
    row is tagged accordingly. It is a divisor, so an unratified value moves every number in the
    grid proportionally — which is exactly why it must not be mistaken for a quote.
    """
    im = (im_pct if im_pct is not None
          else DESK_INPUTS["initial_margin_pct"] or ILLUSTRATIVE_IM_PCT) / 100.0
    rows = []
    for d in delta_pi_pp:
        for b in borrow_grid:
            carry_yr = carry_waterfall(b, xccy_basis_bps_yr).bp_per_year.sum() / 1e4
            for h in horizons:
                pnl = (-d / 100.0) - carry_yr * (h / 252.0)
                rows.append({
                    "delta_pi_pp": d, "borrow_bps_yr": b, "horizon_sessions": h,
                    "pnl_pct_notional": round(pnl * 100, 2),
                    "rom_x": round(pnl / im, 2),
                    "initial_margin_pct": im * 100,
                    "status": ("ILLUSTRATIVE" if DESK_INPUTS["initial_margin_pct"] is None
                               else "MEASURED"),
                })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# D6 — the exit tree.
#
# THE THRESHOLDS ARE RATIFIED; TWO STRUCTURAL CHOICES ARE NOT. Signing changed the status of the
# NUMBERS that cut each branch — the premium bands, the borrow brackets, the headroom bands —
# from proposals to desk policy. It did not convert them into measurements, and nothing here
# pretends otherwise: a ratified threshold is an authored decision with an owner, which is a
# different and more useful thing than an estimate.
#
# Still open, because neither is a threshold: the OVERRIDE ORDER (margin beats borrow beats
# premium) and the LEAF SET (whether the desk will really quote a long-local TRS on a recall).
# Both are listed by ratification_owed().
# ----------------------------------------------------------------------------------

#: When the author signed the threshold values. Structure and leaf set remain open.
EXIT_THRESHOLDS_RATIFIED: str | None = "2026-08-03"

EXIT_THRESHOLDS: dict[str, dict] = {
    "premium_band": {
        # Anchored on the comparator's 5-year mean rather than on entry: entry is where we
        # happened to start, and the anchor is what the thesis argues the level should approach.
        "at_or_below_anchor_pp": 15.0,
        "mid_pp": 25.0,
        "above_entry_pp": 40.0,
        "basis": "RATIFIED 2026-08-03 — anchored on the comparator mean, not on entry",
    },
    "borrow_state": {
        "stable_max_bp": 400,
        "tightening_max_bp": 900,
        "recalled": "any involuntary buy-in notice, at any rate",
        "basis": "RATIFIED 2026-08-03 — brackets mirror the quoted low/mid/high",
    },
    "margin_headroom": {
        "comfortable_pct": 50.0,
        "watch_pct": 25.0,
        "critical_pct": 10.0,
        "basis": "RATIFIED 2026-08-03 — % of posted collateral still unencumbered",
    },
}

#: The four agreed actions. Deliberately few: a tree whose leaves are all different is a tree
#: nobody follows under pressure.
EXIT_ACTIONS = ("hold", "reduce to D4 size", "convert to long-local TRS only",
                "unwind at ADV band")


def exit_tree() -> pd.DataFrame:
    """D6 — premium band x borrow state x margin headroom -> agreed action.

    THE ASYMMETRY IS THE WHOLE DESIGN. A borrow recall does not damage the thesis; it removes
    the ability to express it as a pair. The long-local TRS survives a recall, so 'convert'
    exists as a distinct leaf from 'unwind' — losing the short leg is not the same event as
    losing the trade, and a tree that collapsed them would force a full exit on a financing
    event rather than an investment one.

    Margin headroom overrides everything, because a margin event is the one branch where the
    decision is taken for you if you do not take it first.
    """
    bands = ["at/below anchor", "mid", "above entry"]
    borrows = ["stable", "tightening", "recalled"]
    headrooms = ["comfortable", "watch", "critical"]

    rows = []
    for band in bands:
        for borrow in borrows:
            for head in headrooms:
                if head == "critical":
                    action = "unwind at ADV band"
                    why = "margin overrides; below the critical band the decision is forced"
                elif borrow == "recalled":
                    action = "convert to long-local TRS only"
                    why = "the short leg is gone, the thesis is not; the local leg survives"
                elif head == "watch":
                    action = "reduce to D4 size"
                    why = "size back to the drawdown-budget number before the next excursion"
                elif borrow == "tightening" and band == "at/below anchor":
                    action = "unwind at ADV band"
                    why = "little left to earn and the financing is deteriorating"
                elif band == "at/below anchor":
                    action = "unwind at ADV band"
                    why = "the level the thesis argued for has arrived"
                elif borrow == "tightening":
                    action = "reduce to D4 size"
                    why = "carry rising into an unconverged position"
                else:
                    action = "hold"
                    why = "thesis intact, financing stable, margin comfortable"
                rows.append({"premium_band": band, "borrow_state": borrow,
                             "margin_headroom": head, "action": action, "rationale": why,
                             "status": ("RATIFIED" if EXIT_THRESHOLDS_RATIFIED
                                        else "TODO(ash: ratify)")})
    return pd.DataFrame(rows)


def ratification_owed() -> list[str]:
    """What D6 is still waiting on. Empties as decisions are signed; never silently.

    The three THRESHOLD groups were signed 2026-08-03. What remains is not a threshold, which
    is why signing the numbers did not clear it: one is an ordering and one is a question about
    what the desk will actually quote.
    """
    owed = []
    if EXIT_THRESHOLDS_RATIFIED is None:
        owed += [
            "Premium bands: is 15pp the right 'arrived' level, given the comparator 5-year "
            "mean, and is 40pp the right 'above entry' cut?",
            "Borrow states: do 400bp and 900bp separate stable from tightening from "
            "unquotable, or should the cuts follow the desk's recall-risk read, not the price?",
            "Margin headroom: are 50/25/10% of unencumbered collateral the right three bands, "
            "and is headroom measured against posted or against the schedule's peak?",
        ]
    owed += [
        "Override order: margin overrides borrow, which overrides premium. This is the one "
        "ordering that cannot be inferred from the research, and it is not a threshold — "
        "signing the numbers did not settle it.",
        "Leaf set: is 'convert to long-local TRS only' a product the desk will really quote on "
        "a recall, or should that branch also read 'unwind'? A leaf nobody will honour is worse "
        "than one fewer leaf.",
    ]
    return owed


def threshold_special_bp(half_life_days: float, card_stress_mult: float = 1.0,
                         card_locked: bool = False, xccy_basis_bps_yr: float = 0.0,
                         pi_0: float | None = None,
                         horizon_days: float = 252.0) -> float:
    """D2.1 — the name special at which the trade exactly breaks even, bp/yr.

    SOLVED, NOT SCANNED. The surface is linear in the special — every other component is
    independent of it — so the zero crossing is

        special* = critical_carry(H) - non_borrow_carry

    A grid scan would report the crossing only to the resolution of its own steps and would
    quietly move if the step size changed, which is a poor property for a number a client is
    quoted against.
    """
    if pi_0 is None:
        pi_0 = freshness()["entry_premium_pct"] / 100.0
    crit = critical_carry_bp(pi_0=pi_0, horizon_days=horizon_days,
                             half_life_days=half_life_days)
    non_borrow = non_borrow_subtotal_bp_month(xccy_basis_bps_yr, card_stress_mult,
                                              card_locked, horizon_days) * 12.0
    return crit - non_borrow


def threshold_special_table(half_lives=None) -> pd.DataFrame:
    """D2.1 annex — threshold special per half-life x JOINT stress state, plus locked.

    The basis argument was removed rather than defaulted: each state now carries its own basis,
    and leaving a separate override would have allowed a table whose column labels disagreed
    with the numbers under them.
    """
    from pipeline.convergence.jorda import run_panel

    hl = run_panel()["one_way_constrained"].hl
    if half_lives is None:
        half_lives = [round(hl.lower), round(hl.point), round(hl.upper)]

    rows = []
    for h in half_lives:
        row = {"half_life_days": h}
        for label, st in STRESS_STATES.items():
            row[f"{label} (x{st['card_mult']:g}, basis {st['basis_bps']:+d})"] = round(
                threshold_special_bp(h, st["card_mult"], False, st["basis_bps"]), 0)
        crisis = STRESS_STATES["crisis"]
        row["crisis, card LOCKED"] = round(
            threshold_special_bp(h, crisis["card_mult"], True, crisis["basis_bps"]), 0)
        rows.append(row)
    return pd.DataFrame(rows).set_index("half_life_days")


def term_financing_value_bp_yr(xccy_basis_bps_yr: float = 0.0) -> dict:
    """What locking the card buys, in bp/yr of name special. Exact and horizon-invariant.

    The locked and crisis surfaces differ only in the card term, so the distance between their
    zero contours is the card stress that locking removes — the SAME number at every half-life,
    which is worth stating: term financing does not buy more room when convergence is slow, it
    buys the same room regardless, and that is precisely why it can be priced as a flat feature.
    """
    crisis = STRESS_STATES["crisis"]
    stressed = house_card_bps_yr(crisis["card_mult"], card_locked=False)
    locked = house_card_bps_yr(crisis["card_mult"], card_locked=True)
    return {"value_bp_yr_of_special": stressed - locked,
            "stressed_card_bp_yr": stressed, "locked_card_bp_yr": locked,
            "basis_not_bought_back_bps": -crisis["basis_bps"],
            "note": "distance between the crisis contour and the crisis-with-locked-card "
                    "contour, in bp/yr of name special; identical at every half-life because "
                    "the two differ only in the card term. TERM FINANCING DOES NOT BUY BACK "
                    "THE BASIS: under the bundled crisis state the locked contour sits below "
                    "the base contour by the basis cost, because locking the card does nothing "
                    "about the cross-currency leg."}
