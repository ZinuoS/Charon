"""Reusable figure modules (G-series). Themed, smoke-tested, deployed in the notebooks.

Design rules, uniform across the suite:

* **Barrier states are drawn, not described.** Solid rule = a binding barrier that
  actually operates; long-dash = a *discretionary* barrier (someone may or may not let
  you through); absent = no barrier. A reader must be able to see which is which without
  the caption.
* **Regime labels sit on the chart**, not only in the caption.
* **The negative-skew warning is a drawn element.** A risk stated only in a footnote is a
  risk the chart is hiding.
* Declarative-sentence headlines; source lines always.

Barrier vocabulary is the post-prospectus one (`docs/research_notes.md` C-A/C-B). The
upper barrier is **not** an exhausted quota — it is primary ADS issuance at the Company's
determination, bounded in practice by the board authorization and the controlling
shareholder's MRFTA position. The deposit agreement's own words are printed on G1 and G2
so the claim travels with its evidence.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from . import theme

# The operative language, quoted so no figure overstates the constraint.
DEPOSIT_QUOTE = ('deposit agreement: shares refused whenever deposit "would cause the\n'
                 'total number of Shares deposited to exceed a level from time to time\n'
                 'determined by the Company"')

FEE_PER_ADS = 0.05  # USD per ADS each way, 424B4 "Fees and Charges"


def g1_barrier_anatomy(pi: pd.Series, events: list[dict] | None = None, fee_pct: float = 0.0007):
    """G1 — the thesis in one frame: an open floor, a discretionary ceiling, and the
    habitat between them.

    The asymmetry is the whole argument, so it is drawn as two visually different rules:
    a **solid** floor (cancellation works, always, for a fee) and a **long-dashed** ceiling
    (issuance works only if the Company decides it does).
    """
    fig, ax = theme.figure(height=5.6)

    top = float(pi.max()) * 1.14
    ax.axhspan(fee_pct, top, color=theme.INK, alpha=0.045, zorder=0)

    # Lower barrier — solid: it operates mechanically.
    ax.axhline(fee_pct, color=theme.BARRIER, linewidth=1.8, zorder=2)
    # Upper barrier — long-dashed: discretionary, and with no number on file it has no
    # determinate height. Drawn above the realized max to say "not observed to bind here".
    ax.axhline(top, color=theme.BARRIER, linewidth=1.6, linestyle=(0, (9, 5)), zorder=2)

    ax.plot(pi.index, pi.values, color=theme.INK, linewidth=1.9, marker="o", markersize=3.4, zorder=3)
    theme.pct_axis(ax)
    ax.set_ylim(min(-0.03, float(pi.min()) - 0.04), top * 1.16)

    # Barrier labels LAST, and via the helper: each one measures itself and expands the
    # limit if it would otherwise hang outside the axes onto the tick labels. Setting ylim
    # afterwards would undo that, which is why the order here is load-bearing.
    theme.annotate_barrier(
        ax, fee_pct,
        f"OPEN — ADR cancellation, uncapped\nround trip ≈ ${FEE_PER_ADS * 2:.2f}/ADS ≈ {fee_pct:.2%} of price",
        side="below")
    theme.annotate_barrier(
        ax, top,
        "DISCRETIONARY — primary ADS issuance at the Company's determination.\n"
        "No numeric deposit cap appears in any SEC filing.",
        side="above")

    theme.finalize(
        fig,
        kicker="barrier structure",
        headline="The premium has a floor that works and a ceiling that is somebody's decision",
        subtitle="SKHY vs 000660.KS close-to-close. The asymmetry is structural, not incidental: "
                 "one direction is a holder's right, the other requires the issuer's consent.",
        source="Nasdaq (SKHY); EODHD (000660.KO); frankfurter/ECB. Barrier language: "
               "SEC 424B4 and Deposit Agreement F-6 Ex. 99(a).",
        footnote="pi = P_ADR * FX / (0.1 * P_local) - 1, raw closes. STALE: KRX closes "
                 "15:30 KST, Nasdaq 16:00 ET - 13.5h apart, so each point pairs "
                 "non-contemporaneous legs.",
    )
    theme.label_line_end(ax, pi.index[-1], pi.values[-1], "SKHY / 000660", theme.INK)
    if events:
        theme.annotate_events(ax, events, labels={
            "skhy_adr_listing": "listing", "skhy_conversion_open": "books reopen",
            "skhy_q2_earnings": "Q2 earnings"}, y_frac=0.62)

    # Sits in the empty upper-right quadrant: anywhere lower collides with the floor rule.
    # Lower-right: the only quadrant free of the path, both barrier rules and the labels.
    ax.annotate(DEPOSIT_QUOTE, xy=(0.985, 0.17), xycoords="axes fraction",
                fontsize=theme.NOTE_SIZE - 0.5, color=theme.MUTED, ha="right", va="top",
                style="italic", fontfamily=theme.SERIF_STACK)
    theme.thin_date_ticks(ax, 6)
    return fig, ax


def g2_plumbing_map():
    """G2 — the plumbing, answering "can this be arbitraged?" before a word is read.

    One channel is drawn wide and open; the other is drawn narrow with a gate across it.
    The gate's label carries the three things that actually govern it.
    """
    fig, ax = theme.figure(height=5.2)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")

    boxes = {"Nasdaq\nADR (SKHY)": 1.0, "Depositary\n(Citibank, N.A.)": 4.1, "KRX common\n(000660)": 7.2}
    for label, x in boxes.items():
        ax.add_patch(mpatches.FancyBboxPatch((x, 2.6), 1.9, 1.25, boxstyle="round,pad=0.10",
                     facecolor=theme.PAPER, edgecolor=theme.SEMANTIC["context"], linewidth=1.3))
        ax.text(x + 0.95, 3.22, label, ha="center", va="center", fontsize=9,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK)

    # Open channel: ADR -> local. Wide arrow, solid.
    ax.annotate("", xy=(7.15, 2.32), xytext=(2.95, 2.32),
                arrowprops=dict(arrowstyle="-|>,head_width=0.42,head_length=0.7",
                                color=theme.BARRIER, linewidth=5.5, alpha=0.85))
    ax.text(5.05, 1.94, "CANCELLATION — uncapped, a holder right (17 CFR §239.36(a))",
            ha="center", fontsize=8.2, color=theme.BARRIER, fontfamily=theme.SERIF_STACK)
    ax.text(5.05, 1.60, f"fee ${FEE_PER_ADS:.2f}/ADS · settlement via KSD",
            ha="center", fontsize=7.4, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    # Gated channel: local -> ADR. Thin, dashed, with a gate bar across it.
    ax.annotate("", xy=(2.95, 4.28), xytext=(7.15, 4.28),
                arrowprops=dict(arrowstyle="-|>,head_width=0.24,head_length=0.5",
                                color=theme.BARRIER, linewidth=1.7, linestyle=(0, (7, 4))))
    ax.plot([5.05, 5.05], [3.98, 4.58], color=theme.BARRIER, linewidth=3.4)
    ax.text(5.05, 4.74, "ISSUANCE — gated", ha="center", fontsize=8.6, color=theme.BARRIER,
            fontfamily=theme.SERIF_STACK)
    ax.text(5.05, 5.28,
            "Company determination  ·  board authorization 17,790,000 sh (2.50%)\n"
            "·  SK Square must hold ≥20% (MRFTA) — post-issue 20.0008%",
            ha="center", fontsize=7.6, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    # D5 gauge on the gated channel.
    ax.add_patch(mpatches.Rectangle((4.30, 3.62), 1.5, 0.20, facecolor=theme.SEMANTIC["inert_fill"],
                                    edgecolor=theme.MUTED, linewidth=0.7))
    ax.text(5.05, 3.40, "D5 observable — capped programme headroom: 0",
            ha="center", fontsize=7.4, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    theme.finalize(
        fig,
        kicker="plumbing",
        headline="One direction is a right; the other is a permission",
        subtitle="Why the classic create-to-arbitrage trade is unavailable here.",
        source="SEC 424B4; Deposit Agreement F-6 Ex. 99(a); 17 CFR 239.36(a); 6-K 2026-07-15.",
        footnote="Solid = barrier that operates mechanically. Long-dash = discretionary.",
    )
    ax.annotate(DEPOSIT_QUOTE, xy=(0.5, 0.02), xycoords="axes fraction",
                fontsize=theme.NOTE_SIZE - 0.5, color=theme.MUTED, ha="center", va="bottom",
                style="italic", fontfamily=theme.SERIF_STACK)
    return fig, ax


def g4_asymmetry(pi_tsm: pd.Series, pi_skhy: pd.Series):
    """G4 — why nobody should call this arbitrage.

    Left: does a high premium mean-revert? Shown by conditioning next-day change on level,
    not asserted. Right: the payoff shape of the short-premium expression, with the
    realized week-one excursion drawn on it.
    """
    fig, axes = theme.small_multiples(2, height=4.8, sharey=False)
    a, b = axes

    lvl = pi_tsm.shift(1).dropna()
    chg = (pi_tsm.diff().dropna()).reindex(lvl.index)
    bins = pd.qcut(lvl, 5, duplicates="drop")
    grouped = chg.groupby(bins, observed=True).mean()
    centres = [iv.mid for iv in grouped.index]
    a.bar([f"{c:.0%}" for c in centres], grouped.values * 1e4,
          color=theme.INK, width=0.62)
    a.axhline(0, color=theme.RULE, linewidth=1.0)
    a.set_title("Mean reversion is asymmetric: the floor reflects\nharder than the ceiling pulls",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    a.set_ylabel("mean next-day change (bp)", fontsize=8, color=theme.MUTED)
    # The asymmetry IS the reflected-process thesis, measured. Bottom quintile pulls up at
    # t=+10.9; the top quintile pulls down at only t=-5.0, and -70bp is small against
    # 249bp daily premium volatility. Stating this precisely rather than claiming "no
    # reversion" -- an earlier caption overstated in the direction that flattered the
    # thesis, and the figure audit caught it.
    a.annotate("bottom quintile t=+10.9   ·   top quintile t=-5.0", xy=(0.30, 0.97),
               xycoords="axes fraction", fontsize=7.4, color=theme.MUTED, ha="left", va="top",
               fontfamily=theme.SERIF_STACK)
    a.set_xlabel("starting premium quintile", fontsize=8, color=theme.MUTED)

    grid = np.linspace(-0.05, 0.60, 400)
    entry = float(pi_skhy.iloc[0])
    floor = 0.0007
    pnl = np.where(grid <= entry, entry - grid, entry - grid)
    b.fill_between(grid, pnl, 0, where=(grid > entry), color=theme.WARNING, alpha=0.16)
    b.fill_between(grid, pnl, 0, where=(grid <= entry), color=theme.INK, alpha=0.13)
    b.plot(grid, pnl, color=theme.TEXT, linewidth=1.5)
    b.axvline(floor, color=theme.BARRIER, linewidth=1.6)
    b.axhline(0, color=theme.RULE, linewidth=1.0)
    lo, hi = float(pi_skhy.min()), float(pi_skhy.max())
    b.annotate("", xy=(hi, entry - hi), xytext=(lo, entry - lo),
               arrowprops=dict(arrowstyle="-|>", color=theme.WARNING, linewidth=2.0))
    b.annotate(f"realized {lo:.1%} → {hi:.1%}\nin week one", xy=(hi, entry - hi),
               xytext=(-4, -32), textcoords="offset points", fontsize=8, color=theme.WARNING,
               ha="right", fontfamily=theme.SERIF_STACK)
    b.annotate("GAIN BOUNDED\nby the cost floor", xy=(0.03, 0.50), xycoords="axes fraction",
               fontsize=8, color=theme.BARRIER, va="top", fontfamily=theme.SERIF_STACK)
    b.annotate("LOSS UNBOUNDED — no ceiling on file", xy=(0.97, 0.90),
               xycoords="axes fraction", fontsize=8.4, color=theme.WARNING, ha="right",
               fontfamily=theme.SERIF_STACK, weight="medium")
    b.set_title("Short-premium payoff: the skew\nis structural, not bad luck",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    b.set_xlabel("premium at exit", fontsize=8, color=theme.MUTED)
    theme.pct_axis(b)
    b.xaxis.set_major_formatter(theme.mpl.ticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

    theme.finalize(
        fig,
        kicker="risk",
        headline="This is relative value against a one-sided barrier - not arbitrage",
        subtitle="Left: conditional next-day change by starting-level quintile, TSM, "
                 "2,328 days. Right: what the convergence expression actually pays.",
        source="Nasdaq; TWSE; EODHD; FRED H.10; frankfurter/ECB. Repo-computed.",
        footnote="The excursion marked on the right is realized, not hypothetical.",
    )
    return fig, axes


def g_convergence(results: dict):
    """Persistence ρ_h by horizon with its 95% HAC band — the open upper tail drawn.

    S17 rewrite. The old version stopped at h=20 and its whole point was that the curve
    never reached ½. Extended to h=400 the crossing IS reached, and the honest content moves
    to the band: the shaded upper edge stays above ½ across the entire estimable window, so
    the chart's subject is now the *unbounded* side of the interval rather than a point.

    PROVISIONAL: regime labels are the proposed taxonomy.
    """
    fig, ax = theme.figure(height=5.0)
    for regime, res in results.items():
        hs = [f.horizon for f in res.horizons]
        rs = [f.rho for f in res.horizons]
        c = theme.regime_color(regime)
        lo = [f.band()[0] for f in res.horizons]
        hi = [f.band()[1] for f in res.horizons]
        ax.fill_between(hs, lo, hi, color=c, alpha=0.13, linewidth=0)
        ax.plot(hs, rs, color=c, linewidth=1.8)
        # Identified stretch drawn solid-marked; underpowered stretch left bare, so the eye
        # can see where the evidence thins without reading a caption.
        idh = [f.horizon for f in res.horizons if f.identified]
        idr = [f.rho for f in res.horizons if f.identified]
        ax.plot(idh, idr, color=c, linewidth=0, marker="o", markersize=2.6)
        theme.label_line_end(ax, hs[-1], rs[-1], regime.replace("_", " "), c)

        hl = getattr(res, "hl", None)
        if hl is not None and hl.support in ("interpolated", "interpolated_underpowered"):
            ax.plot([hl.point], [0.5], marker="v", markersize=6, color=c, zorder=5)
            ax.annotate(f"first passage {hl.point:.0f}d", xy=(hl.point, 0.5),
                        xytext=(4, 12), textcoords="offset points", fontsize=theme.NOTE_SIZE,
                        color=c, fontfamily=theme.SERIF_STACK)
            if hl.lower:
                ax.axvline(hl.lower, color=c, linewidth=0.9, linestyle=":", alpha=0.8)
                # Anchored low, in the empty band below the control line — at y≈0 it
                # overprinted the fungible series.
                ax.annotate(f"95% floor\n{hl.lower:.0f}d", xy=(hl.lower, -0.30),
                            xytext=(5, 0), textcoords="offset points", fontsize=theme.NOTE_SIZE,
                            color=theme.MUTED, fontfamily=theme.SERIF_STACK, linespacing=1.3,
                            va="center")
            if hl.unbounded_above:
                ax.annotate("upper band never crosses ½ →\nno finite upper bound",
                            xy=(0.62, 0.86), xycoords="axes fraction",
                            fontsize=theme.NOTE_SIZE, color=theme.MUTED,
                            fontfamily=theme.SERIF_STACK, linespacing=1.4)

    ax.axhline(0.5, color=theme.RULE, linewidth=1.0, linestyle="--")
    ax.annotate("ρ = ½", xy=(0.015, 0.5), xycoords=("axes fraction", "data"),
                xytext=(0, 4), textcoords="offset points", fontsize=theme.NOTE_SIZE,
                color=theme.MUTED, fontfamily=theme.SERIF_STACK)
    ax.axhline(0.0, color=theme.RULE, linewidth=0.8)
    ax.set_ylim(-0.45, 1.15); ax.set_xlabel("horizon (trading days)", fontsize=8, color=theme.MUTED)
    ax.set_ylabel("premium persistence ρ", fontsize=8, color=theme.MUTED)
    theme.finalize(
        fig, kicker="convergence",
        headline="The premium half-life has a floor, and no ceiling",
        subtitle="Jordà local-projection persistence with 95% Newey–West bands, pooled within "
                 "regime. Markers mark horizons carrying at least 12 independent spans; any "
                 "unmarked stretch is drawn but not supported. The fungible control starts below ½.",
        source="Nasdaq; TWSE; EODHD; frankfurter/ECB; FRED. Repo-computed, HAC errors.",
        footnote="PROVISIONAL — regime labels are the proposed taxonomy, pending ratification. "
                 "SKHY excluded from all fits (forward test).",
    )
    return fig, ax


def g9_cost_and_skew(cost_rows, margin: dict):
    """G9 — the cost stack and the margin-stress excursion, with undocumented legs hatched.

    Two truths on one frame: the documented cost is trivial (the conversion 'obol'), and
    the risk is not (the realized week-one drawdown, with the unbounded-loss note drawn).
    A cost figure that hid the skew would flatter the trade.
    """
    fig, axes = theme.small_multiples(2, height=4.4, sharey=False)
    a, b = axes

    names = [r["segment"] for r in cost_rows]
    docs = [r["documented"] for r in cost_rows]
    vals = [float(r["cost"].rstrip("%")) if d else 0.0 for r, d in zip(cost_rows, docs)]
    y = range(len(names))
    for i, (v, d) in enumerate(zip(vals, docs)):
        a.barh(i, v if d else 0.10, color=theme.INK if d else theme.PAPER,
               edgecolor=theme.MUTED, hatch=None if d else "////", height=0.6)
    a.set_yticks(list(y)); a.set_yticklabels([n[:22] for n in names], fontsize=7.5)
    a.invert_yaxis()
    a.set_xlabel("% of notional", fontsize=8, color=theme.MUTED)
    theme.obol(a, vals[0], 0)
    a.set_title("Documented cost is the 'obol' — trivial.\nHatched legs are quoted live, not zero.",
                loc="left", fontsize=9, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    entry, peak = margin["entry_premium"], margin["peak_premium"]
    b.bar(["entry", "peak (week 1)"], [entry * 100, peak * 100],
          color=[theme.INK, theme.WARNING], width=0.55)
    b.annotate(f"{margin['premium_leg_drawdown_pct_pts']:.0f}pp\nmarked against",
               xy=(0, entry * 100), xytext=(6, 12), textcoords="offset points",
               fontsize=8, color=theme.WARNING, ha="left", fontfamily=theme.SERIF_STACK)
    b.annotate("LOSS UNBOUNDED — no ceiling on file", xy=(0.5, 0.94), xycoords="axes fraction",
               fontsize=8, color=theme.WARNING, ha="center", fontfamily=theme.SERIF_STACK, weight="medium")
    b.set_ylabel("premium (%)", fontsize=8, color=theme.MUTED)
    b.set_title("The risk is not trivial: the realized\nweek-one excursion, marked",
                loc="left", fontsize=9, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    theme.finalize(
        fig, kicker="financing",
        headline="Cheap to cross, dangerous to fade: the two facts a convergence expression must hold together",
        subtitle="Left: cost stack, documented vs quoted-live. Right: the short-premium stress case, realized.",
        source="SK Hynix 424B4 [P]; repo data. Non-advisory — costs and risks, not a recommendation.",
        footnote="Undocumented legs are shown hatched at a placeholder width; a desk quotes them live. "
                 "The negative skew is structural (G4).",
    )
    return fig, axes


def g10_expression_readiness(sheets):
    """G10 — why each expression is or is not constructible, as a dependency matrix.

    The trade sheets render as prose, which is right for a client reading one of them and
    wrong for a client comparing five. A reader asking "what would it take to trade #3?"
    should not have to diff two paragraphs. So: expressions down the side, required inputs
    across the top, and the blocking cells drawn as holes.

    The design decision that matters is that a MISSING input is drawn, not omitted. An
    all-present row and a two-holes row must be distinguishable at a glance, because the
    difference between them is the difference between a trade and a wish.
    """
    inputs = [
        ("premium\nseries", "D1"), ("FX\nspot", "D2"), ("convergence\nhorizon", "M3"),
        ("beta\ncontext", "M5"), ("index\nfutures", "H2"), ("option\nsurfaces", "H1/H4"),
        ("LETF\nAUM", "D4"),
    ]
    # Requirement matrix, keyed to the sheets in pipeline.hedging.sheets.all_sheets order.
    # 2 = landed, 1 = landed but bounded-only, 0 = missing, None = not required.
    REQ = [
        [2, 2, 1, 0, None, None, None],      # 1 convergence RV      (live)
        [2, 2, None, 0, 0, None, None],      # 2 local-access substitute
        [2, 2, 1, None, 0, 0, None],         # 3 term-structure RV
        [2, 2, None, None, None, 0, None],   # 4 volatility RV
        [2, 2, None, None, None, None, 0],   # 5 flow-aware overlay
    ]
    # Sheet names already carry their ordinal; prepending another produced "1. 1. ...".
    # Expressions only. Operational sheets (financing, access) are not ways to take the
    # view, and charting them here would put rows in a matrix whose columns do not apply.
    sheets = [s for s in sheets if getattr(s, "kind", "expression") == "expression"]
    names = [s.name.split("(")[0].strip() for s in sheets]
    live = [s.readiness.strip("[] ").lower().startswith("live") for s in sheets]

    fig, ax = theme.figure(height=4.6)
    nrow, ncol = len(REQ), len(inputs)
    for r, row in enumerate(REQ):
        y = nrow - 1 - r
        for c, v in enumerate(row):
            if v is None:
                ax.plot(c, y, marker=".", color=theme.RULE, markersize=2)
                continue
            if v == 2:
                ax.plot(c, y, marker="o", markersize=11, color=theme.INK,
                        markeredgecolor=theme.INK)
            elif v == 1:
                # bounded-only: half-filled, because "we have a floor" is not "we have it"
                ax.plot(c, y, marker="o", markersize=11, markerfacecolor=theme.PAPER,
                        markeredgecolor=theme.BARRIER, markeredgewidth=2.0)
                ax.plot(c, y, marker="_", markersize=7, color=theme.BARRIER, markeredgewidth=2.4)
            else:
                ax.plot(c, y, marker="o", markersize=11, markerfacecolor=theme.PAPER,
                        markeredgecolor=theme.WARNING, markeredgewidth=1.4)
                ax.plot(c, y, marker="x", markersize=6, color=theme.WARNING, markeredgewidth=1.6)
        label_color = theme.TEXT if live[r] else theme.MUTED
        ax.text(-0.62, y, names[r], ha="right", va="center", fontsize=theme.LABEL_SIZE,
                color=label_color, fontfamily=theme.SERIF_STACK)
        tag = "live" if live[r] else "contingent"
        ax.text(ncol + 0.25, y, tag, ha="left", va="center", fontsize=theme.NOTE_SIZE,
                color=theme.INK if live[r] else theme.WARNING, fontfamily=theme.SERIF_STACK)
        # Rule stops short of the readiness tag — at full width it struck through the text.
        ax.plot([-0.45, ncol - 0.55], [y, y], color=theme.RULE, linewidth=0.6, zorder=0)

    for c, (label, src) in enumerate(inputs):
        ax.text(c, nrow - 0.35, label, ha="center", va="bottom", fontsize=theme.NOTE_SIZE,
                color=theme.MUTED, fontfamily=theme.SERIF_STACK, linespacing=1.3)
        ax.text(c, nrow - 0.62, src, ha="center", va="bottom", fontsize=theme.NOTE_SIZE - 0.8,
                color=theme.RULE, fontfamily=theme.SERIF_STACK)

    ax.set_xlim(-3.0, ncol + 1.9); ax.set_ylim(-1.5, nrow + 0.6)
    ax.axis("off")
    ax.text(-2.9, -1.05,
            "filled = landed     ·     open with bar = bounded only (floor, no ceiling)     ·"
            "     open with cross = missing     ·     dot = not required",
            fontsize=theme.NOTE_SIZE, color=theme.MUTED, fontfamily=theme.SERIF_STACK)
    theme.finalize(
        fig, kicker="expressions",
        headline="One expression is constructible today; four wait on named inputs",
        subtitle="Required inputs per expression. Nothing here is a view on which trade is "
                 "better — only on which can be built from data this programme has landed.",
        source="Repo-computed from pipeline.hedging.sheets and the D-source registry.",
        footnote="The convergence horizon is drawn bounded-only: a 95% floor exists, an upper "
                 "bound does not. Cost accrues against the floor.",
    )
    return fig, ax


def g11_taxonomy_separation(per_pair: list[dict]):
    """G11 — the ratified taxonomy, and the evidence it is not circular.

    One point per pair: mean premium on x (the LEVEL), half-life on y (the DYNAMICS),
    coloured by regime class. Two claims at once, pulling in opposite directions:

    *   The classes **separate vertically, completely.** Constrained half-lives run 161-398
        days; controls run 1-24. No overlap, and the nearest constrained pair is ~7x the
        slowest control. That is the result.
    *   The classes separate far more weakly on the horizontal. That is the alibi, and the
        first draft of this docstring overstated it: the ranges do not literally overlap
        (constrained min |mean pi| 1.96%, control max 0.91%), but the LEVEL gap is ~2.2x
        while the DYNAMICS gap is ~6.7x across ranges that differ by 300x. ASE carries the
        argument on its own — a mean premium roughly twice the largest control's, and a
        half-life roughly seven times it. At comparable levels the dynamics differ by an
        order of magnitude, which is what stops the label from restating the data.

    A NOTE ON THE Y-AXIS, because the first draft of this figure got it wrong. Plotting
    1-day persistence shows NO separation at all — ggb (fungible) is 0.934 against cht
    (constrained) 0.936. The classes are indistinguishable at daily frequency and diverge
    only over weeks, so rho_1 would have made the taxonomy look worthless while the half-life
    shows it separating cleanly. Which horizon you look at decides what you conclude.
    """
    fig, ax = theme.figure(height=5.2)
    for row in per_pair:
        c = theme.regime_color(row["regime"])
        x, y = abs(row["mean"]), row["half_life"]
        ax.plot(x, y, marker="o", markersize=8, color=c, markerfacecolor=c, alpha=0.9, zorder=3)
        ax.annotate(row["pair"], xy=(x, y), xytext=(10, row.get("dy", 0)),
                    textcoords="offset points", fontsize=theme.NOTE_SIZE, color=c,
                    va="center", fontfamily=theme.SERIF_STACK)

    con_hl = [r["half_life"] for r in per_pair if r["regime"] == "one_way_constrained"]
    fun_hl = [r["half_life"] for r in per_pair if r["regime"] == "fungible"]
    # The gap is the finding — draw it rather than describing it.
    ax.axhspan(max(fun_hl), min(con_hl), color=theme.GRAY, alpha=0.09, zorder=0)
    ax.annotate(f"no pair lands here\n{max(fun_hl):.0f}d — {min(con_hl):.0f}d",
                xy=(0.985, (max(fun_hl) * min(con_hl)) ** 0.5), xycoords=("axes fraction", "data"),
                ha="right", va="center", fontsize=theme.NOTE_SIZE, color=theme.MUTED,
                fontfamily=theme.SERIF_STACK, linespacing=1.5)

    # The discriminating case, called out by name. An earlier draft shaded a horizontal
    # "both classes live here" band; the ranges do not actually overlap, so the claim is
    # made where it is true — on the pair that carries it — rather than by drawing a band.
    con_x = [abs(r["mean"]) for r in per_pair if r["regime"] == "one_way_constrained"]
    fun_x = [abs(r["mean"]) for r in per_pair if r["regime"] == "fungible"]
    lo_pair = min((r for r in per_pair if r["regime"] == "one_way_constrained"),
                  key=lambda r: abs(r["mean"]))
    hi_ctrl = max((r for r in per_pair if r["regime"] == "fungible"),
                  key=lambda r: abs(r["mean"]))
    ax.annotate(
        f"{lo_pair['pair']} carries the argument: {abs(lo_pair['mean'])/abs(hi_ctrl['mean']):.1f}x "
        f"{hi_ctrl['pair']}'s premium,\n{lo_pair['half_life']/hi_ctrl['half_life']:.1f}x its "
        "half-life. Similar level, different dynamics.",
        xy=(abs(lo_pair["mean"]), lo_pair["half_life"]), xytext=(-14, 26),
        textcoords="offset points", ha="right", fontsize=theme.NOTE_SIZE,
        color=theme.MUTED, fontfamily=theme.SERIF_STACK, linespacing=1.5,
        arrowprops=dict(arrowstyle="-", color=theme.RULE, linewidth=0.8,
                        connectionstyle="angle,angleA=0,angleB=90,rad=3"))

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("mean premium, absolute value — the LEVEL", fontsize=8, color=theme.MUTED)
    ax.set_ylabel("half-life, trading days — the DYNAMICS", fontsize=8, color=theme.MUTED)
    ax.annotate("one-way constrained", xy=(0.02, 0.95), xycoords="axes fraction",
                fontsize=theme.NOTE_SIZE, color=theme.regime_color("one_way_constrained"),
                fontfamily=theme.SERIF_STACK)
    ax.annotate("fungible control", xy=(0.02, 0.05), xycoords="axes fraction",
                fontsize=theme.NOTE_SIZE, color=theme.regime_color("fungible"),
                fontfamily=theme.SERIF_STACK)

    theme.finalize(
        fig, kicker="taxonomy",
        headline="The regime label predicts how a premium behaves, not how big it is",
        subtitle="One point per cross-listed pair. Classes are assigned from the documented "
                 "issuance rule before any of this was estimated. They separate completely on "
                 "half-life — a 6.7x gap across ranges 300x apart — and only weakly on level, "
                 "a 2.2x gap. The label is about dynamics, not size.",
        source="Repo-computed. Rule, evidence and falsification criteria: docs/regime_taxonomy.md.",
        footnote="At 1-day horizon the classes do NOT separate (ρ₁ ≈ 0.93 in both) — the "
                 "divergence appears over weeks. Taxonomy RATIFIED 2026-07-29; the PANEL is not: "
                 "four constrained issuers share one regulator, five of six controls are Brazilian.",
    )
    return fig, ax

# ================================================================================
# Block 4 — the layman layer.
#
# Every figure must pass a stated TEN-SECOND TEST: a cold reader gets the point from the
# headline plus one drawn annotation alone. The bullets below are the third leg — plain
# English, in the register a salesperson can repeat from memory, with no Greek and no
# estimator names.
#
# They live HERE, in the figure module, rather than in the notebook builders, because the
# same figure ships to a notebook and to a deck export and the two must not drift. Notebook
# text is downstream of this dict, never parallel to it.
# ================================================================================

LAYMAN: dict[str, list[str]] = {
    "g1_barrier_anatomy": [
        "Hynix's US shares have been worth 16-52% more than the identical Korean shares "
        "since July. Normally that gap gets traded away in a day.",
        "It cannot be, because the trade only works one way. You can always turn a US share "
        "back into a Korean one. Going the other way needs the company's permission, and it "
        "has not given it.",
        "So the gap has a floor it cannot fall through and no ceiling it cannot rise above.",
    ],
    "g2_plumbing_map": [
        "Two pipes connect the US listing to the Korean one. The wide one always flows; the "
        "narrow one has a gate on it.",
        "The gate is not a rulebook number — it is a decision the company makes and does not "
        "publish. That is harder to plan around than a quota.",
        "Watch the gauge: it reads zero, meaning nothing is currently allowed through.",
    ],
    "g4_asymmetry": [
        "Betting the gap closes pays a little if you are right and loses a lot if you are "
        "wrong. That is not bad luck, it is the shape of the trade.",
        "The most you can make is the gap you sold. The most you can lose has no limit, "
        "because nothing on file caps how wide it can get.",
        "It already ran from 16% to 52% in one week — about 36 points against that bet, "
        "before any of it came back.",
    ],
    "g9_cost_and_skew": [
        "The paperwork cost of the trade is trivial: about 7 basis points, round trip.",
        "The costs that matter — borrowing the shares, funding the position, hedging the "
        "currency — are not published. The desk quotes them live.",
        "Cost is not what keeps this gap open. Risk is.",
    ],
    "g_convergence": [
        "Gaps like this one close slowly. Ones where the trade works both ways close within "
        "days.",
        "Best case, on the evidence, is about ten and a half months. There is no worst case "
        "we can rule out — the data cannot say the gap ever halves.",
        "Anything you pay per day, you should assume you pay for at least ten months.",
    ],
    "g10_expression_readiness": [
        "Five ways to express this view. One can be built today; four wait on data we have "
        "not yet been able to buy or scrape.",
        "Two of the four need only a single missing input each, and both are purchasing "
        "problems rather than research problems.",
        "Nothing here says which trade is better — only which can be built honestly now.",
    ],
    "g12_variance_shares": [
        "Break the US share's daily moves into three parts: the Korean share, the currency, "
        "and the gap between them.",
        "The gap looks like most of the risk in every case — including the ones where the "
        "trade works both ways. So a big gap-share on its own proves nothing.",
        "The tell is that for a freely tradeable pair the gap almost exactly cancels against "
        "the local share: it opens and closes inside a day, mostly because the two markets "
        "close at different times.",
    ],
    "g11_taxonomy_separation": [
        "Sort cross-listings by whether the trade works both ways, using only the legal "
        "documents. Then look at how their gaps behave.",
        "The one-way ones take months to close. The two-way ones take days. Nothing sits in "
        "between.",
        "That sorting was done before looking at any prices, which is why it is a finding "
        "and not a circular argument.",
    ],
}


def layman(figure_name: str) -> list[str]:
    """Plain-English bullets for a figure. Empty list if none assigned."""
    return LAYMAN.get(figure_name, [])


def layman_block(figure_name: str, width: int = 96) -> str:
    """Render the layman bullets as a markdown block for notebooks and deck exports."""
    import textwrap
    bullets = layman(figure_name)
    if not bullets:
        return ""
    out = ["**In plain terms**", ""]
    for b in bullets:
        wrapped = textwrap.fill(b, width=width, subsequent_indent="  ")
        out.append(f"- {wrapped}")
    return "\n".join(out)


def ten_second_test() -> dict[str, bool]:
    """Which figures carry the full three-legged treatment (headline + annotation + layman).

    Reported in docs/figure_audit.md. A figure with no layman bullets fails by definition --
    the test is about a cold reader, and a cold reader does not read docstrings.
    """
    names = [n for n in globals() if n.startswith(("g1", "g2", "g4", "g9", "g10", "g11", "g_"))
             and callable(globals()[n])]
    return {n: bool(layman(n)) for n in sorted(names)}



def g12_variance_shares(rows):
    """G12 — realized variance shares of the ADR return, per pair.

    NUMBERED 12, not 10/11: those are taken by `g10_expression_readiness` and
    `g11_taxonomy_separation`. Reusing the numbers would collide in the audit doc and in
    every caption that cites one.

    NO REGIME-TIMELINE COMPANION. The session spec paired this with a regime timeline; there
    is nothing to plot. Regime is a per-pair label read off a filing, so a timeline of it is a
    horizontal line. The time-varying quantity is binding-ness (headroom), which the H5
    monitor already reports as text and which has one observation on the capped programme.

    What the figure has to be honest about: the shares do NOT separate the classes. The
    premium's share is high for the fungible control too. The separating structure is the
    COVARIANCE — a fungible pair's premium variance is almost entirely cancelled by negative
    covariance with the local leg, i.e. the two legs move apart and back inside the
    measurement window rather than the premium being an independent risk.
    """
    fig, ax = theme.figure(height=4.6)
    names = [r["pair"] for r in rows]
    y = np.arange(len(names))
    share_pi = [r["share_pi"] for r in rows]
    cov = [r["share_cov_local_pi"] for r in rows]

    ax.barh(y - 0.19, share_pi, height=0.34, color=theme.INK, label="premium variance share")
    ax.barh(y + 0.19, cov, height=0.34, color=theme.WARNING,
            label="covariance(local, premium) share")
    ax.axvline(0, color=theme.RULE, linewidth=1.0)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=theme.LABEL_SIZE)
    ax.invert_yaxis()
    ax.set_xlabel("share of ADR return variance", fontsize=8, color=theme.MUTED)
    ax.legend(fontsize=theme.NOTE_SIZE, frameon=False, loc="lower right")

    # The one takeaway annotation: the cancellation, on the control.
    i = next((k for k, r in enumerate(rows) if r["pair"] == "baba"), None)
    if i is not None:
        # Text into the empty upper-left, arrow down to the bar. Anchored at the bar with a
        # point offset it landed on the x tick labels -- the same defect class as G1's floor
        # label, and the bottom-left corner of a horizontal bar chart is always contested.
        ax.annotate("the control's premium variance is\nalmost exactly cancelled by its\n"
                    "covariance with the local leg",
                    xy=(cov[i] * 0.55, i + 0.19), xytext=(0.03, 0.72),
                    textcoords="axes fraction", ha="left", va="top",
                    fontsize=theme.NOTE_SIZE, color=theme.MUTED,
                    fontfamily=theme.SERIF_STACK, linespacing=1.45,
                    arrowprops=dict(arrowstyle="-|>", color=theme.RULE, linewidth=0.9,
                                    connectionstyle="arc3,rad=-0.15"))

    theme.finalize(
        fig, kicker="variance",
        headline="A large premium-variance share is not evidence of a barrier",
        subtitle="Log-additive decomposition of the ADR return. The premium's share is high "
                 "for the fungible control too — what differs is how completely the local leg "
                 "cancels it.",
        source="Repo-computed from D1/D6 closes. hypotheses/h4_vol_decomposition.",
        footnote="Non-contemporaneous closes inflate premium variance on every pair; the "
                 "negative local-premium covariance is largely that artefact returning. SKHY "
                 "n=11 — far too few to compare against 2,327 and 1,592.",
    )
    return fig, ax
