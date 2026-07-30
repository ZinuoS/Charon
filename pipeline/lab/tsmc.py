"""The TSMC lab — 21.6 years of the nearest regime, and the boundary on what it can say.

WHY THIS PAIR. SKHY's ADR programme is fourteen sessions old. Every question the sheet has
to answer -- how long does an elevated premium take to resolve, which leg closes it, how
far does it go against you first, does hedging the currency matter -- is a question about a
distribution, and fourteen observations cannot describe one. TSMC is the deepest pair in the
same family: a Taiwanese ADR whose local line trades in a market with a foreign-ownership
architecture and a managed currency, priced against a common share by a fixed depositary
ratio. It is the nearest thing to a long history of this trade that exists.

WHY IT IS NOT SKHY, AND WHY THAT MATTERS MORE THAN THE SIMILARITY. The decisive difference
is the conversion regime. TSMC's ADR facility refills: cancelled ADSs return to a pool that
can be re-issued, so arbitrage pushes from BOTH sides and the premium is a two-sided
process. SKHY's issuance requires Company consent under the F-6 Ex. 99(a) undertaking, so
arbitrage pushes from one side only and the premium is a REFLECTED process with an open
upper tail. A two-sided history therefore describes the mean-reverting case, which is the
FAVOURABLE case for a convergence trade. Every number in this module inherits that: it is a
floor on how badly this can go, not a central estimate of how it will go.

The full similarity/difference table is :data:`STRUCTURAL_ROWS`; the bounding paragraph is
:data:`ASYMMETRY`. Nothing here is a forecast, and nothing here is fitted on SKHY.

SAMPLE. 2005-01-03 onward, 5,064 joined sessions. The pre-2005 exclusion is declared in the
registry (``PairSpec.sample_reason`` for ``tsmc``) and is a corporate-action artefact, not a
result screen; :func:`curation_sensitivity` re-runs the headline number on the wider
cause-based cut so the choice can be checked rather than trusted.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.ingest.registry import PAIRS
from pipeline.measurement.premium import _load_close, compute_premium
from pipeline.package.breakeven import CARRY_BRACKET_BP, FLOOR, carry_bp

# --------------------------------------------------------------------------------
# 1.0 — the structural audit
# --------------------------------------------------------------------------------
#
# Every row carries its own source. "repo" means computed in this repository by the named
# module and is therefore reproducible; a citation means a filing or a rule, quoted for its
# content and not paraphrased into something stronger.

#: (dimension, TSMC, SKHY, which way it cuts, source)
STRUCTURAL_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "Conversion regime",
        "Revolving. Cancelled ADSs return to a re-issuable pool; the facility refills.",
        "Discretionary. Issuance needs Company consent (F-6 Ex. 99(a) undertaking); "
        "cancellation is a holder right (17 CFR 239.36(a)).",
        "DECISIVE, and against the lab. Two-sided arbitrage makes TSMC's premium "
        "mean-reverting; SKHY's is reflected with an open upper tail.",
        "F-6 Ex. 99(a); 17 CFR 239.36(a); README section 2",
    ),
    (
        "Ratio mechanics",
        "1 ADS = 5 common shares, fixed; stock dividends absorbed by distributing "
        "additional ADSs, ratio preserved.",
        "10 ADSs = 1 common share, fixed (424B4).",
        "Neutral. Both are constant-ratio programmes, so pi is a clean price ratio in "
        "both, which is what makes them comparable at all.",
        "TSMC depositary terms; SK Hynix 424B4; pipeline/ingest/registry.py",
    ),
    (
        "FX regime",
        "TWD, managed float with a central bank that smooths the close.",
        "KRW, free float with deeper offshore forwards.",
        "Against comparability. A smoothed currency mechanically dampens the FX channel, "
        "so TSMC's FX sensitivity is a LOWER bound on the won's.",
        "pipeline/panel/fx_conventions.py; repo",
    ),
    (
        "Foreign-ownership architecture",
        "No issuer-level statutory ceiling on the ordinary shares in the sample period.",
        "20% controlling-shareholder floor under MRFTA holding-company rules, which "
        "constrains the float that can back an issuance, not the ADR itself.",
        "Against the lab. SKHY has a structural constraint on the supply side that TSMC "
        "does not, so persistence should be HIGHER for SKHY.",
        "MRFTA holding-company rules; docs/regime_taxonomy.md",
    ),
    (
        "Index weight / home concentration",
        "Largest TAIEX constituent by a wide margin for most of the sample.",
        "Second-largest KOSPI constituent.",
        "Neutral to mildly against. Both are index-dominant, so both attract the same "
        "passive-flow channel; TSMC's dominance is greater.",
        "repo (D2 index series); README section 2",
    ),
    (
        "ADR share of global liquidity",
        "Large and persistent: the ADR is a primary venue for the name, not a satellite.",
        "New programme; the ADR is a satellite of a much larger local book.",
        "OVERSTATES comparability. A deep ADR makes TSMC's premium easier to arbitrage "
        "and faster to close than a thin one, so the lab's convergence speeds are "
        "OPTIMISTIC for SKHY.",
        "repo (D1/D6 volume); stated as a qualitative ordering, not a measured share",
    ),
    (
        "Listed-derivatives depth",
        "Deep listed options and futures on both the local line and the ADR across the "
        "whole sample.",
        "Local futures and options exist; the ADR has no established surface.",
        "OVERSTATES comparability, and it is why the convexity overlay stays CONTINGENT "
        "on the hedge menu: the lab's own pair could hedge a tail the traded pair cannot.",
        "repo; pipeline/hedging/sheets.py",
    ),
    (
        "LETF presence",
        "None for most of the sample.",
        "Single-stock 2x listings suspended 2026-07-16, deposit requirement accelerated "
        "to 2026-07-31; eligibility admits only two names.",
        "OUT OF SCOPE for the lab. H3's channel is SKHY-new, so the lab is silent on it "
        "rather than reassuring about it.",
        "KRX/FSC notices in the D7 event register",
    ),
    (
        "Short-sale regime",
        "Taiwan has run continuous borrowing with intermittent restriction; the SBL "
        "programme operates across the sample.",
        "Ban imposed 2023-11, fully lifted 2025-03-31; all listed stocks shortable.",
        "Against the lab in one specific way: SKHY's short leg has a REGIME RISK that "
        "recurred within three years, and no TSMC episode is a precedent for it.",
        "D7 event register; docs/data_sources.md",
    ),
    (
        "Cycle exposure",
        "Foundry: capex-cycle levered, customer-concentrated.",
        "Memory: sharper, more volatile amplitude on the same global cycle.",
        "Against comparability on amplitude. Memory's cycle is more violent, so episode "
        "MAGNITUDES from foundry history understate what memory can produce.",
        "qualitative; asserted as a sector ordering, not measured here",
    ),
)

ASYMMETRY = """\
The differences do not cancel, and they do not point in random directions. Read down the
"which way it cuts" column and almost every row leans the same way: TSMC's history should
UNDERSTATE how persistent an SKHY premium can be, and OVERSTATE how comparable the two
trades are on execution.

Understating persistence. TSMC's facility refills, so its premium is pushed from both
sides and mean-reverts. SKHY's issuance needs Company consent, so it is a reflected
process whose upper tail has no arbitrage bound. Add the MRFTA floor on the float that
could back an issuance, and SKHY has a supply-side constraint TSMC never had. Whatever
half-life and whatever resolution rate the lab measures, the reflected case should be
slower and less certain.

Overstating comparability. TSMC's ADR is a primary venue with deep listed derivatives;
SKHY's is a two-week-old satellite with no established option surface. Arbitrage that is
cheap and capacious in the lab is neither in the traded pair. And the TWD is managed while
the won is not, so the lab's FX channel is a smoothed version of the real one.

The consequence for how these numbers may be used. Every figure in this notebook is a
characterisation of a regime FAMILY under its FAVOURABLE variant. A fraction of historical
entries that beat carry is a statement about a revolving facility. Quoting it as the
probability that an SKHY entry beats carry substitutes the easier trade for the real one.
The lab bounds the argument; it does not make it."""


# --------------------------------------------------------------------------------
# Episode and entry rule grids — PROVISIONAL until ratified
# --------------------------------------------------------------------------------
#
# RATIFICATION STATUS: proposed, awaiting the author's ranges (session S25 decision 2).
# Every cell of every grid is reported, so ratifying a RANGE narrows which cells are
# quoted and cannot move a number. That is the point of reporting the full grid: it makes
# the curation auditable instead of invisible.

RULE_GRID_RATIFIED: str | None = None

#: Minimum peak-to-trough move, in premium percentage points, for a swing to be an episode.
#: Spans "barely a move" to "the kind of dislocation the pitch is about".
EPISODE_MIN_MOVE_PP: tuple[float, ...] = (2.0, 3.0, 5.0, 8.0)

#: Minimum episode duration in sessions. Screens out single-print noise.
EPISODE_MIN_DAYS: tuple[int, ...] = (5, 10, 20)

#: Entry trigger: the premium's percentile within its OWN expanding history. Expanding, not
#: full-sample -- a full-sample percentile would let an entry rule see its own future.
ENTRY_PCTILES: tuple[float, ...] = (0.80, 0.90, 0.95, 0.99)

#: Sessions before the expanding percentile is trusted. Two years.
PCTILE_WARMUP_D: int = 504

#: Holding horizons, matched to the trade sheet's sizing horizon.
HORIZONS_D: tuple[int, ...] = (63, 126, 252, 504)

#: Candidate stop distances, in premium percentage points of adverse excursion.
STOP_DISTANCES_PP: tuple[float, ...] = (2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0)

#: The cause-based alternative sample start, for the curation sensitivity. See the registry.
CAUSE_BASED_START = "2002-07-26"


def rule_grid_note() -> str:
    """One line stating whether the grids are ratified, for any figure that uses them."""
    if RULE_GRID_RATIFIED:
        return f"Rule grid ratified {RULE_GRID_RATIFIED}."
    return ("Rule grid PROVISIONAL (author ratification pending). Every grid cell is "
            "reported, so ratifying a range changes which cells are quoted, not any number.")


# --------------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------------


def _spec():
    return next(p for p in PAIRS if p.pair_id == "tsmc")


def legs(sample_start: str | None = None) -> pd.DataFrame:
    """The three raw legs and pi, on the registry sample unless overridden.

    ``sample_start`` exists for :func:`curation_sensitivity` alone and deliberately reaches
    around the registry restriction, which is why it is asserted rather than trusted: the
    only legitimate override is the documented cause-based cut.
    """
    if sample_start is not None:
        assert sample_start == CAUSE_BASED_START, (
            f"the only sanctioned override is the cause-based cut {CAUSE_BASED_START}; "
            f"got {sample_start!r}. Widening the sample any other way re-admits the "
            "stock-dividend artefact the registry excludes."
        )
    spec = _spec()
    start = sample_start or spec.sample_start
    adr = _load_close("d6_comparators", spec.adr)
    loc = _load_close("d6_comparators", spec.local)
    fx = _load_close("d6_comparators", spec.fx)
    adr, loc, fx = (s[s.index >= start] for s in (adr, loc, fx))
    pi = compute_premium(adr, loc, fx, spec.local_shares_per_adr)
    out = pd.DataFrame({"adr": adr, "local": loc, "fx": fx}).join(pi.rename("pi"), how="inner")
    return out.dropna()


def premium(sample_start: str | None = None) -> pd.Series:
    return legs(sample_start)["pi"]


# --------------------------------------------------------------------------------
# 1.1 — episode census
# --------------------------------------------------------------------------------


def episodes(pi: pd.Series, min_move_pp: float = 5.0, min_days: int = 10) -> pd.DataFrame:
    """Peak-to-trough swings exceeding a threshold, by a reversal walk over the whole sample.

    The rule is applied uniformly and forward-only: a running extreme is carried until the
    premium retraces ``min_move_pp`` from it, which confirms the extreme and opens the next
    leg. No smoothing, no centred window, so an episode's endpoints are knowable at the time
    they are dated -- which matters because the census feeds a claim about what an entrant
    would have experienced, not about what a historian can see.
    """
    thr = min_move_pp / 100.0
    if len(pi) < 3:
        return pd.DataFrame(columns=["start", "end", "direction", "move_pp", "days"])

    pivots: list[tuple[pd.Timestamp, float, str]] = []
    ext_i, ext_v = pi.index[0], float(pi.iloc[0])
    direction: str | None = None
    for dt, v in pi.items():
        v = float(v)
        if direction in (None, "up"):
            if v > ext_v:
                ext_i, ext_v = dt, v
            elif ext_v - v >= thr:
                pivots.append((ext_i, ext_v, "peak"))
                direction, ext_i, ext_v = "down", dt, v
                continue
        if direction in (None, "down"):
            if v < ext_v:
                ext_i, ext_v = dt, v
            elif v - ext_v >= thr:
                pivots.append((ext_i, ext_v, "trough"))
                direction, ext_i, ext_v = "up", dt, v

    rows, dropped = [], 0
    for (i0, v0, k0), (i1, v1, _) in zip(pivots, pivots[1:]):
        days = int((pi.index.get_loc(i1) - pi.index.get_loc(i0)))
        if days < min_days:
            dropped += 1
            continue
        rows.append({
            "start": i0, "end": i1,
            "direction": "compression" if k0 == "peak" else "widening",
            "from_pp": round(v0 * 100, 2), "to_pp": round(v1 * 100, 2),
            "move_pp": round(abs(v1 - v0) * 100, 2), "days": days,
        })
    out = pd.DataFrame(rows)
    # min_days filters INDIVIDUAL swings, so dropping a short leg can leave two
    # same-direction rows adjacent. That is a reporting filter, not a merge, and the count
    # is carried so it is visible rather than silently absorbed.
    out.attrs["dropped_short"] = dropped
    out.attrs["n_swings_before_min_days"] = max(len(pivots) - 1, 0)
    return out


def resolution_channel(frame: pd.DataFrame, ep: pd.DataFrame) -> pd.DataFrame:
    """Which leg closed each episode, from the exact log decomposition of pi.

    log(1+pi) = log(P_adr) + log(FX) - log(n * P_local), so over any window

        d log(1+pi) = d log ADR + d log FX - d log LOCAL

    is an identity, not a regression: the three contributions sum to the premium change with
    no residual. The channel is the leg whose contribution is largest in the direction the
    episode actually moved -- "who closed the gap", which is the direct evidence for choosing
    between the short-ADR and long-local expressions on the sheet.
    """
    out = []
    for _, r in ep.iterrows():
        w = frame.loc[r["start"]:r["end"]]
        if len(w) < 2:
            continue
        d_adr = float(np.log(w["adr"].iloc[-1] / w["adr"].iloc[0]))
        d_fx = float(np.log(w["fx"].iloc[-1] / w["fx"].iloc[0]))
        d_loc = float(np.log(w["local"].iloc[-1] / w["local"].iloc[0]))
        contrib = {"adr_leg": d_adr, "fx_leg": d_fx, "local_leg": -d_loc}
        total = float(np.log1p(w["pi"].iloc[-1]) - np.log1p(w["pi"].iloc[0]))
        # The channel is the contribution with the same sign as the move and the largest
        # magnitude. Contributions that push the other way are not candidates.
        same = {k: v for k, v in contrib.items() if np.sign(v) == np.sign(total) and v != 0}
        chan = max(same, key=lambda k: abs(same[k])) if same else "offsetting"
        out.append({**r.to_dict(), **{f"{k}_logpts": round(v * 100, 2) for k, v in contrib.items()},
                    "identity_residual": round(total - sum(contrib.values()), 12),
                    "channel": chan,
                    "channel_share": round(abs(contrib[chan]) / abs(total), 3) if chan != "offsetting" else None})
    return pd.DataFrame(out)


def census(pi: pd.Series | None = None, frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """The full episode grid: one row per (min_move, min_days) cell, every cell reported."""
    frame = legs() if frame is None else frame
    pi = frame["pi"] if pi is None else pi
    rows = []
    for mv in EPISODE_MIN_MOVE_PP:
        for md in EPISODE_MIN_DAYS:
            ep = episodes(pi, mv, md)
            ch = resolution_channel(frame, ep) if len(ep) else ep
            comp = ch[ch["direction"] == "compression"] if len(ch) else ch
            rows.append({
                "min_move_pp": mv, "min_days": md, "n_episodes": len(ep),
                "dropped_short": ep.attrs.get("dropped_short", 0),
                "n_compression": int((ep["direction"] == "compression").sum()) if len(ep) else 0,
                "n_widening": int((ep["direction"] == "widening").sum()) if len(ep) else 0,
                "median_move_pp": round(float(ep["move_pp"].median()), 2) if len(ep) else None,
                "median_days": int(ep["days"].median()) if len(ep) else None,
                "max_move_pp": round(float(ep["move_pp"].max()), 2) if len(ep) else None,
                **{f"compression_via_{k}": (
                    round(float((comp["channel"] == k).mean()), 3) if len(comp) else None)
                   for k in ("adr_leg", "local_leg", "fx_leg")},
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------
# 1.2 / 1.3 — entry outcomes, and what they cost en route
# --------------------------------------------------------------------------------


def expanding_pctile(pi: pd.Series, warmup: int = PCTILE_WARMUP_D) -> pd.Series:
    """Each day's premium as a percentile of its OWN past. No lookahead by construction."""
    r = pi.expanding(min_periods=warmup).apply(
        lambda w: float((w <= w[-1]).mean()), raw=True)
    return r


def entry_outcomes(pi: pd.Series | None = None, pctiles=ENTRY_PCTILES,
                   horizons=HORIZONS_D, brackets=("low", "mid", "high"),
                   margin_frac: float = 0.20) -> pd.DataFrame:
    """Forward outcome distribution for a short-premium entry, per (percentile, horizon).

    P&L convention. The position is short the premium, so the gross gain in premium points
    is ``pi_entry - pi_exit``: the trade makes money when the gap closes. Carry is subtracted
    at the bracketed annual rate for the days held. Return on margin divides by
    ``margin_frac`` of the ADR-leg notional, which is the sheet's illustrative initial
    margin, so the units match the scenario panel.

    Every (percentile, horizon, bracket) cell is reported. The single number the financing
    decision turns on is ``frac_beats_carry``.
    """
    pi = premium() if pi is None else pi
    pct = expanding_pctile(pi)
    idx = pi.index
    rows = []
    for p in pctiles:
        entries = pi.index[(pct >= p).fillna(False)]
        for h in horizons:
            gross, mae = [], []
            for t in entries:
                i = idx.get_loc(t)
                if i + h >= len(pi):
                    continue
                path = pi.iloc[i:i + h + 1]
                gross.append(float(pi.iloc[i] - pi.iloc[i + h]))
                # Adverse for a short-premium position is the premium RISING.
                mae.append(float(path.max() - pi.iloc[i]))
            if not gross:
                continue
            g = np.asarray(gross) * 100.0          # premium points
            m = np.asarray(mae) * 100.0
            for b in brackets:
                cost = carry_bp(b, amortise_conversion_over_days=h) / 1e4 * h / 252.0 * 100.0
                net = g - cost
                rows.append({
                    "entry_pctile": p, "horizon_d": h, "bracket": b,
                    "n_entries": len(g), "carry_cost_pp": round(cost, 3),
                    "median_net_pp": round(float(np.median(net)), 2),
                    "q25_net_pp": round(float(np.percentile(net, 25)), 2),
                    "q75_net_pp": round(float(np.percentile(net, 75)), 2),
                    "p05_net_pp": round(float(np.percentile(net, 5)), 2),
                    "p95_net_pp": round(float(np.percentile(net, 95)), 2),
                    "frac_beats_carry": round(float((net > 0).mean()), 3),
                    "median_rom": round(float(np.median(net) / 100.0 / margin_frac), 3),
                    "median_mae_pp": round(float(np.median(m)), 2),
                    "p95_mae_pp": round(float(np.percentile(m, 95)), 2),
                })
    return pd.DataFrame(rows)


def excursions(pi: pd.Series | None = None, pctile: float = 0.90,
               horizon: int = 252, stops=STOP_DISTANCES_PP) -> pd.DataFrame:
    """Stop survival: what fraction of historical entries a given stop distance would hold.

    Two columns that must not be conflated. ``frac_stopped`` is how often the stop is hit at
    all. ``frac_stopped_but_would_have_won`` is how often it is hit on a path that ended
    profitable anyway -- the cost of the stop, not its benefit. A risk budget is chosen
    against both.
    """
    pi = premium() if pi is None else pi
    pct = expanding_pctile(pi)
    idx = pi.index
    mae, final = [], []
    for t in pi.index[(pct >= pctile).fillna(False)]:
        i = idx.get_loc(t)
        if i + horizon >= len(pi):
            continue
        path = pi.iloc[i:i + horizon + 1]
        mae.append(float(path.max() - pi.iloc[i]) * 100.0)
        final.append(float(pi.iloc[i] - pi.iloc[i + horizon]) * 100.0)
    mae, final = np.asarray(mae), np.asarray(final)
    rows = []
    for s in stops:
        hit = mae >= s
        rows.append({
            "stop_pp": s, "n_entries": len(mae),
            "frac_stopped": round(float(hit.mean()), 3),
            "frac_stopped_but_would_have_won": round(float((hit & (final > 0)).mean()), 3),
        })
    out = pd.DataFrame(rows)
    out.attrs["mae_pp"] = mae
    out.attrs["median_mae_pp"] = float(np.median(mae))
    out.attrs["p95_mae_pp"] = float(np.percentile(mae, 95))
    out.attrs["max_mae_pp"] = float(mae.max())
    return out


def skhy_week_one_excursion() -> dict:
    """SKHY's realised first-week adverse excursion, for the same axis. Repo-measured."""
    from pipeline.measurement.premium import build_all_variants
    s = build_all_variants("skhy")[0].series
    return {"from_pp": round(float(s.iloc[0]) * 100, 2),
            "peak_pp": round(float(s.max()) * 100, 2),
            "excursion_pp": round(float(s.max() - s.iloc[0]) * 100, 2),
            "sessions": int(s.index.get_loc(s.idxmax()) + 1),
            "note": "Realised, in the programme's first sessions. Not a scenario."}


# --------------------------------------------------------------------------------
# 1.4 — the FX case
# --------------------------------------------------------------------------------


def fx_sensitivity_deep(frame: pd.DataFrame | None = None,
                        eras: tuple[tuple[str, str, str], ...] | None = None) -> pd.DataFrame:
    """Regress d(pi) on the proportional FX move, over the full sample and per era.

    The analytic coefficient is (1+pi), a ceteris-paribus derivative. The empirical one
    absorbs both equity legs' own FX betas and is what a hedge would actually face. OLS with
    an HAC-free standard error is adequate here because the regressor is a daily return and
    the residual autocorrelation is small; the CI is reported wide rather than sharpened.
    """
    frame = legs() if frame is None else frame
    d_pi = frame["pi"].diff()
    d_fx = np.log(frame["fx"]).diff()
    eras = eras or (
        ("2005-2009 pre-GFC", "2005-01-03", "2009-12-31"),
        ("2010-2015", "2010-01-01", "2015-12-31"),
        ("2016-2020", "2016-01-01", "2020-12-31"),
        ("2021-2026", "2021-01-01", "2026-12-31"),
    )
    rows = []
    for label, a, b in (("full sample", str(frame.index[0].date()), str(frame.index[-1].date())),) + eras:
        y = d_pi.loc[a:b].dropna()
        x = d_fx.loc[a:b].reindex(y.index).dropna()
        y = y.reindex(x.index)
        if len(y) < 60:
            continue
        X = np.column_stack([np.ones(len(x)), x.values])
        beta, *_ = np.linalg.lstsq(X, y.values, rcond=None)
        resid = y.values - X @ beta
        s2 = float(resid @ resid) / (len(y) - 2)
        se = float(np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1]))
        r2 = 1.0 - float(resid @ resid) / float(((y - y.mean()) ** 2).sum())
        pi_bar = float(frame["pi"].loc[a:b].mean())
        rows.append({
            "era": label, "n": len(y), "mean_pi_pp": round(pi_bar * 100, 2),
            "analytic_coef": round(1.0 + pi_bar, 3),
            "empirical_coef": round(float(beta[1]), 3),
            "ci95_lo": round(float(beta[1] - 1.96 * se), 3),
            "ci95_hi": round(float(beta[1] + 1.96 * se), 3),
            "pp_per_1pct_fx": round(float(beta[1]) * 0.01 * 100, 3),
            "r2": round(r2, 4),
            "theory_inside_ci": bool(beta[1] - 1.96 * se <= 1.0 + pi_bar <= beta[1] + 1.96 * se),
        })
    return pd.DataFrame(rows)


def premium_notional_structure(frame: pd.DataFrame | None = None) -> dict:
    """Does TSMC's history show the same premium-as-currency-notional structure?

    The residual identity is arithmetic and holds in every pair: hedging the local leg
    leaves pi/(1+pi) of the ADR leg's notional FX-exposed. What is NOT arithmetic is how
    big that residual has been, so this reports the distribution of the residual share over
    the deep history against SKHY's current one.
    """
    frame = legs() if frame is None else frame
    pi = frame["pi"]
    resid = pi / (1.0 + pi)
    return {
        "n": int(len(pi)),
        "median_residual_share": round(float(resid.median()), 4),
        "p95_residual_share": round(float(resid.quantile(0.95)), 4),
        "max_residual_share": round(float(resid.max()), 4),
        "identity": "residual / ADR notional = pi / (1 + pi)  -- exact, in any pair",
        "note": ("The structure is identical because it is arithmetic. The MAGNITUDE is not: "
                 "a hedge sized off the local leg leaves a residual proportional to the "
                 "premium, so the same hedge is materially less complete at SKHY's current "
                 "level than at TSMC's typical one."),
    }


# --------------------------------------------------------------------------------
# Sensitivity, and the summary the notebook and the figures both quote
# --------------------------------------------------------------------------------


def curation_sensitivity(pctile: float = 0.90, horizon: int = 252,
                         bracket: str = "mid") -> pd.DataFrame:
    """The headline number under both sample starts, so the exclusion can be checked."""
    rows = []
    for label, start in (("registry (2005-01-03)", None),
                         (f"cause-based ({CAUSE_BASED_START})", CAUSE_BASED_START)):
        pi = premium(start)
        eo = entry_outcomes(pi, pctiles=(pctile,), horizons=(horizon,), brackets=(bracket,))
        r = eo.iloc[0]
        rows.append({"sample": label, "n_obs": len(pi), "first": str(pi.index[0].date()),
                     "n_entries": int(r["n_entries"]),
                     "frac_beats_carry": r["frac_beats_carry"],
                     "median_net_pp": r["median_net_pp"],
                     "p95_mae_pp": r["p95_mae_pp"]})
    return pd.DataFrame(rows)


def lab_summary() -> dict:
    """Every number the notebook and the panels quote, computed once."""
    frame = legs()
    pi = frame["pi"]
    cen = census(frame=frame)
    base = cen[(cen.min_move_pp == 5.0) & (cen.min_days == 10)].iloc[0]
    eo = entry_outcomes(pi)
    ex = excursions(pi)
    fx = fx_sensitivity_deep(frame)
    head = eo[(eo.entry_pctile == 0.90) & (eo.horizon_d == 252)]
    return {
        "sample": {"n_obs": int(len(pi)), "first": str(pi.index[0].date()),
                   "last": str(pi.index[-1].date()),
                   "years": round((pi.index[-1] - pi.index[0]).days / 365.25, 1),
                   "mean_pp": round(float(pi.mean()) * 100, 2),
                   "max_pp": round(float(pi.max()) * 100, 2),
                   "min_pp": round(float(pi.min()) * 100, 2)},
        "census_base": base.to_dict(),
        "beats_carry_by_bracket": {r.bracket: r.frac_beats_carry for r in head.itertuples()},
        "median_net_by_bracket": {r.bracket: r.median_net_pp for r in head.itertuples()},
        "excursion": {"median_pp": round(ex.attrs["median_mae_pp"], 2),
                      "p95_pp": round(ex.attrs["p95_mae_pp"], 2),
                      "max_pp": round(ex.attrs["max_mae_pp"], 2)},
        "skhy_week_one": skhy_week_one_excursion(),
        "fx_full": fx.iloc[0].to_dict(),
        "residual": premium_notional_structure(frame),
        "rule_grid": rule_grid_note(),
    }


if __name__ == "__main__":   # smallest runnable check of the two non-trivial routines
    f = legs()
    ep = episodes(f["pi"], 5.0, 10)
    assert len(ep), "no episodes found at the base rule — the reversal walk is broken"
    ch = resolution_channel(f, ep)
    assert ch["identity_residual"].abs().max() < 1e-9, "log decomposition is not an identity"
    assert set(ch["direction"]) <= {"compression", "widening"}
    # The reversal walk alternates by construction; check it BEFORE the min_days filter,
    # which drops individual swings and can leave two same-direction rows adjacent.
    d = list(episodes(f["pi"], 5.0, 0)["direction"])
    assert all(a != b for a, b in zip(d, d[1:])), "the reversal walk must alternate"
    eo = entry_outcomes(f["pi"], pctiles=(0.90,), horizons=(252,), brackets=("mid",))
    assert 0.0 <= eo.iloc[0]["frac_beats_carry"] <= 1.0
    # Higher carry can never raise the fraction that beats carry.
    m = entry_outcomes(f["pi"], pctiles=(0.90,), horizons=(252,)).set_index("bracket")
    assert m.loc["low", "frac_beats_carry"] >= m.loc["high", "frac_beats_carry"]
    print(f"ok: {len(f)} sessions, {len(ep)} episodes, "
          f"beats carry (90th pctile, 252d, mid) = {eo.iloc[0]['frac_beats_carry']:.1%}")
