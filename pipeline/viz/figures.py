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
    "g16_netting": [
        "Run the two legs as one position and the margin is about a third of running them "
        "separately — that is the capital case for doing it through one desk.",
        "But that saving is measured on ordinary days. On the days the gap actually jumps, it "
        "shrinks to roughly a third of what it was.",
        "So the capital relief is real and it is smallest exactly when you need it most.",
    ],
    "g2c_ops_asymmetry": [
        "You get one position, one margin call and one report a month.",
        "Everything else — registering in Korea, borrowing the US shares, rolling the currency "
        "hedge, booking the local leg — sits on our side of the line.",
        "That is what you are paying for. Not a view on the gap.",
    ],
    "g19_monitoring": [
        "Every month you get the gap, the state of the one-way valve, and whether any of three "
        "specific things has happened.",
        "The three things are all visible facts: a company filing, a change in the conversion "
        "headroom, or a shift in the borrow rules.",
        "We are not sending you a forecast, because we tested forecasting and it did not beat "
        "simply watching.",
    ],
    "g23_currents": [
        "Three outside forces move this gap: the Korean market overall, the won, and the gap "
        "between US and Korean interest rates.",
        "None of them are about SK hynix. The rate one matters most to you, because it is what "
        "funding the position costs.",
        "One thing we still cannot show you is what foreign investors are doing month to month — "
        "there is no clean public feed for it, so we say so rather than guess.",
    ],
    "g23_hedge_menu": [
        "Three things you can bolt on. Only one has a price today.",
        "The currency hedge is standard — but be clear what it does not do: about a quarter of "
        "your position is still exposed to the won afterwards, because the gap itself is a "
        "dollar-versus-won number.",
        "The one that would cap your downside needs listed options that do not exist for this "
        "name yet. We will not make up a price for it.",
    ],
    "g24_exit_tree": [
        "We are not telling you when to get out, so we agree the rules up front: five things to "
        "watch, three ways out.",
        "If the borrow gets pulled, the cleanest exit is handing the US shares back for Korean "
        "ones — that kills the borrowing problem outright.",
        "And be honest about stops: this gap jumped 36 points in a week. A stop tells the desk "
        "what you want, it does not promise you get it.",
    ],
    "g20_macro_map": [
        "This gap does not float in space. Korean rules on short selling, a leveraged-ETF curb "
        "landing this month, and the won all move it.",
        "None of those are about whether SK hynix is a good company. They can push the gap "
        "around on their own.",
        "Two dates to know cold: short selling came back in March 2025, and the ETF curb bites "
        "end of July.",
    ],
    "g21_chain": [
        "Walk it in order: you want the gap, you cannot reach the Korean side, so we hold both "
        "legs and you hold one position.",
        "Whether it pays comes down to your funding cost. Whether it survives comes down to "
        "margin and borrow.",
        "And we are not selling you timing — we tested that and it did not hold up, which is why "
        "the triggers are things you can see rather than things we predict.",
    ],
    "g22_scenario_pnl": [
        "Three ways this can go: the gap closes at its normal speed, it sits still while you pay "
        "to hold it, or it widens the way it actually did in July.",
        "Best case here makes you about a fifth to two-fifths of the money you had to post. Worst "
        "case loses more than all of it.",
        "The shaded band is not uncertainty about the market — it is uncertainty about your own "
        "costs, and the desk can remove it.",
    ],
    "g18_margin_path": [
        "In the first week of this thing existing, the gap went from 16% to 52%. That is not a "
        "scenario, it happened.",
        "Carrying the position through that would have needed roughly 44 cents of margin for "
        "every dollar of position — and about 60 if the two legs were margined separately.",
        "Running it as one position helps. It does not make the call small.",
    ],
    "g17_capacity": [
        "Both sides trade around eight billion dollars a day, so getting in and out is not the "
        "problem: a billion-dollar position clears in about a day.",
        "What limits size is borrowing the US shares to sell. We can show what is already on "
        "loan; we cannot show what is still available.",
        "Ask the desk for real borrow depth before sizing — that is the number that binds.",
    ],
    "g15_breakeven": [
        "The gap is 22.6% today. If it closes, you make money; while you wait, you pay to hold "
        "the position.",
        "The arithmetic says: at today's level, the cost of carrying has to stay under about "
        "80 basis points a month, or waiting costs more than closing pays.",
        "We do not know your borrow and funding rates — that is the one number this turns on, "
        "and it is the first thing to ask the desk.",
    ],
    "g14_magnitude_paradox": [
        "Both models call the direction right about six times in ten. That sounds like the "
        "same model twice.",
        "It isn't. Sort the days by how much the gap actually moved: almost all the money is "
        "in the biggest days, and on those the complicated model is barely better than a coin "
        "toss while the simple one holds up.",
        "Being right about small moves is cheap. The simple model is right when the move is "
        "worth something.",
    ],
    "g13_complexity": [
        "We tried the fashionable answer: throw thousands of made-up features at the problem "
        "and let the maths sort it out.",
        "It made no difference. Going from 20 features to 10,000 moved the result almost not "
        "at all — what mattered was how hard we reined the model in.",
        "So the boring model was the right model here, and now we can say that because we "
        "tested it, not because we preferred it.",
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


def g13_complexity(grid, regime="one_way_constrained", horizon=20):
    """G13 — the double-descent curve, drawn on our problem, where it does not appear.

    The paper's signature is OOS performance improving as complexity passes the interpolation
    threshold c = P/N = 1. On this panel there is no such curve: R² is flat in c and ordered
    almost entirely by SHRINKAGE. Drawn as flat, because a negative result massaged into a
    shape is the one thing this figure must not do.

    Left panel is log-scaled because near-ridgeless R² reaches −1,300 — on a linear axis every
    other line collapses onto zero and the shrinkage ordering, which is the actual finding,
    becomes invisible.
    """
    g = grid[(grid.regime == regime) & (grid.horizon == horizon)]
    fig, (a, b) = theme.figure(ncols=2, height=4.8)
    lams = sorted(g.shrinkage.unique())
    ramp = [theme._ramp(theme.SEMANTIC["emphasis"], 0.62 - 0.72 * i / max(1, len(lams) - 1))
            for i in range(len(lams))]

    for lam, col in zip(lams, ramp):
        s = g[g.shrinkage == lam].sort_values("c")
        a.plot(s.c, -s.r2, color=col, linewidth=1.7, marker="o", markersize=3)
        theme.label_line_end(a, s.c.iloc[-1], -s.r2.iloc[-1], f"λ={lam:g}", col)
        b.plot(s.c, s.hit_rate, color=col, linewidth=1.7, marker="o", markersize=3)

    for ax in (a, b):
        ax.axvline(1.0, color=theme.BARRIER, linewidth=1.2, linestyle=(0, (6, 4)))
        ax.set_xscale("log")
        ax.set_xlabel("complexity  c = P / N", fontsize=8, color=theme.MUTED)
    a.set_yscale("log")
    a.set_ylabel("out-of-sample loss  (−R², log)", fontsize=8, color=theme.MUTED)
    b.set_ylabel("sign hit rate", fontsize=8, color=theme.MUTED)
    b.axhline(0.5, color=theme.RULE, linewidth=1.0)

    a.annotate("interpolation\nthreshold", xy=(1.0, a.get_ylim()[1] * 0.45),
               xytext=(6, 0), textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.BARRIER, fontfamily=theme.SERIF_STACK, linespacing=1.4)
    a.set_title("Loss is ordered by shrinkage, not by complexity",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    b.set_title("Hit rate is flat in complexity —\neven 20 features get it",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    # The one takeaway annotation: flatness is the finding.
    s10 = g[g.shrinkage == max(lams)].sort_values("c")
    b.annotate(f"flat across a 500× range in P\n({s10.hit_rate.min():.1%}–{s10.hit_rate.max():.1%})",
               xy=(s10.c.iloc[len(s10) // 2], s10.hit_rate.iloc[len(s10) // 2]),
               # Into the empty lower half of the panel; at -34pt it landed on the lines.
               xytext=(0.5, 0.16), textcoords="axes fraction", ha="center", va="bottom",
               fontsize=theme.NOTE_SIZE, color=theme.MUTED, fontfamily=theme.SERIF_STACK,
               linespacing=1.4, arrowprops=dict(arrowstyle="-|>", color=theme.RULE, linewidth=0.9,
                                                connectionstyle="arc3,rad=0.12"))

    theme.finalize(
        fig, kicker="experiment — deviation-gated",
        headline="The virtue here is shrinkage, not complexity",
        subtitle=f"Random-Fourier ridge on Δln(1+π), {regime.replace('_', ' ')}, h={horizon}. "
                 "Complexity spans a 500× range in feature count; the curve barely moves. "
                 "Regularisation moves it by three orders of magnitude.",
        source="Repo-computed. Method: Kelly, Malamud & Zhou (J. Finance 2024). Identical folds "
               "to Track A by construction.",
        footnote="EXPERIMENT under docs/deviations.md DEV-004, signed 2026-07-29. Exceeds the "
                 "README §8 capacity rule by design; quarantined to data/derived/voc_experiment/.",
    )
    return fig, (a, b)


def g14_magnitude_paradox(dec):
    """G14 — where the money is, and where complexity stops being right.

    The question this answers: two tracks with near-identical hit rates (62.1% vs 62.2% at the
    same N) have Sharpes of +0.54 and +0.36. Where does the difference come from?

    Sorting by realised |Δπ| answers it. P&L is monotone in magnitude — the largest decile
    carries most of the result — and it is exactly there that the complex model's accuracy
    collapses: 60.6% for the shallow track against 52.6% for the random-features one. Being
    right on small moves is cheap; the decile that pays is the one complexity gets wrong.
    """
    fig, (a, b) = theme.figure(ncols=2, height=4.8)
    cols = {"A": theme.SEMANTIC["emphasis"], "B": theme.SEMANTIC["warning"]}
    names = {"A": "shallow", "B": "random feat."}   # short: the long forms clipped at the axis

    for t, col in cols.items():
        s = dec[dec.track == t].sort_values("decile")
        a.plot(s.decile, s.hit_rate, color=col, linewidth=1.8, marker="o", markersize=4)
        b.plot(s.decile, s.pnl_mean * 1e4, color=col, linewidth=1.8, marker="o", markersize=4)
        theme.label_line_end(a, s.decile.iloc[-1], s.hit_rate.iloc[-1], names[t], col)

    a.axhline(0.5, color=theme.RULE, linewidth=1.0)
    a.set_ylabel("sign hit rate", fontsize=8, color=theme.MUTED)
    b.axhline(0, color=theme.RULE, linewidth=1.0)
    b.set_ylabel("mean P&L per observation (bp)", fontsize=8, color=theme.MUTED)
    for ax in (a, b):
        ax.set_xlabel("realised |Δπ| decile  (10 = largest moves)", fontsize=8, color=theme.MUTED)
        ax.set_xticks(range(1, 11))

    # The one takeaway: the gap opens in decile 10, and decile 10 is where the money is.
    top = dec[dec.decile == dec.decile.max()].set_index("track")
    a.axvspan(9.5, 10.5, color=theme.SEMANTIC["context"], alpha=0.12, zorder=0)
    b.axvspan(9.5, 10.5, color=theme.SEMANTIC["context"], alpha=0.12, zorder=0)
    a.annotate(f"the whole difference is here:\n{top.loc['A','hit_rate']:.1%} vs "
               f"{top.loc['B','hit_rate']:.1%} on the largest moves",
               xy=(10, top.loc["B", "hit_rate"]), xytext=(0.03, 0.06),
               textcoords="axes fraction", ha="left", va="bottom",
               fontsize=theme.NOTE_SIZE, color=theme.MUTED, fontfamily=theme.SERIF_STACK,
               linespacing=1.45, arrowprops=dict(arrowstyle="-|>", color=theme.RULE,
                                                 linewidth=0.9, connectionstyle="arc3,rad=-0.2"))
    a.set_title("Accuracy rises with move size — until the top decile,\nwhere complexity gives it back",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    b.set_title("P&L is monotone in move size:\nthe largest decile is the result",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    theme.finalize(
        fig, kicker="experiment — deviation-gated",
        headline="Both models are right equally often; only one is right when it matters",
        subtitle="Out-of-fold outcomes sorted by realised move size, identical folds, "
                 "N_train=200, h=20. Hit rates are near-identical overall (62.1% vs 62.2%) — "
                 "the Sharpe gap is built entirely in the top decile.",
        source="Repo-computed. Track B method: Kelly, Malamud & Zhou (J. Finance 2024).",
        footnote="EXPERIMENT under DEV-004. GROSS of transaction costs, on the comparator "
                 "panel only — SKHY is never fitted. Not a claim about the live trade.",
    )
    return fig, (a, b)


def g15_breakeven(surf, verdict, critical_bp, critical_bp_floor):
    """G15 — how fast convergence must arrive to beat the carry.

    The pitch's central number, drawn as a BRACKET because four of five cost components are
    undocumented. Point estimates would be the dishonest version: the whole finding is that
    the bracket straddles the answer, so whether this trade works is determined by numbers the
    desk holds and this repository does not.
    """
    fig, (a, b) = theme.figure(ncols=2, height=5.0)
    ramp = {"low": theme._ramp(theme.SEMANTIC["emphasis"], 0.45),
            "mid": theme.SEMANTIC["emphasis"],
            "high": theme.SEMANTIC["warning"]}

    # LEFT: breakeven half-life vs entry premium, one line per cost bracket, at 252d.
    s252 = surf[surf.horizon_days == 252]
    for br, col in ramp.items():
        d = s252[s252.bracket == br].sort_values("entry_premium")
        a.plot(d.entry_premium, d.breakeven_half_life_days, color=col, linewidth=1.9,
               marker="o", markersize=4)
        theme.label_line_end(a, d.entry_premium.iloc[-1], d.breakeven_half_life_days.iloc[-1],
                             f"{br} carry", col)

    est, flo = verdict["estimated_half_life_days"], verdict["estimated_floor_days"]
    a.axhspan(flo, est, color=theme.SEMANTIC["context"], alpha=0.16, zorder=0)
    a.axhline(est, color=theme.BARRIER, linewidth=1.6)
    a.annotate(f"estimated base rate {est:.0f}d\n(95% floor {flo:.0f}d, no ceiling)",
               xy=(0.02, est), xycoords=("axes fraction", "data"), xytext=(0, 7),
               textcoords="offset points", fontsize=theme.NOTE_SIZE, color=theme.BARRIER,
               fontfamily=theme.SERIF_STACK, linespacing=1.4)
    a.axvline(verdict["entry_premium"], color=theme.RULE, linewidth=1.1, linestyle=(0, (4, 3)))
    a.annotate("SKHY today", xy=(verdict["entry_premium"], a.get_ylim()[1]),
               xytext=(4, -12), textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.MUTED, fontfamily=theme.SERIF_STACK)
    theme.pct_axis(a)
    a.set_yscale("log")
    a.set_xlabel("entry premium", fontsize=8, color=theme.MUTED)
    a.set_ylabel("breakeven half-life (days, log)", fontsize=8, color=theme.MUTED)
    a.set_title("Above the black line the base rate pays;\nbelow it, it does not",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    # RIGHT: the single number the desk conversation must fill.
    brs = list(ramp)
    vals = [verdict[f"carry_bp_{k}"] for k in brs]
    b.barh(range(len(brs)), vals, color=[ramp[k] for k in brs], height=0.55)
    b.set_yticks(range(len(brs))); b.set_yticklabels([f"{k} bracket" for k in brs], fontsize=8)
    b.invert_yaxis()
    b.axvline(critical_bp, color=theme.BARRIER, linewidth=2.0)
    # Anchored in axes fraction: at (critical_bp, len(brs)-0.55) it fell below the inverted
    # y-range and rendered off-panel entirely -- the takeaway was invisible.
    b.annotate(f"CRITICAL CARRY {critical_bp:.0f}bp/yr\n({critical_bp/12:.0f}bp/month)\n"
               "above this, the linear trade is\nnegative-carry to the base rate",
               xy=(critical_bp, 1.0), xytext=(0.03, 0.06), textcoords="axes fraction",
               ha="left", va="bottom", fontsize=theme.NOTE_SIZE, color=theme.BARRIER,
               fontfamily=theme.SERIF_STACK, linespacing=1.45,
               arrowprops=dict(arrowstyle="-|>", color=theme.BARRIER, linewidth=1.0,
                               connectionstyle="arc3,rad=-0.15"))
    b.axvline(critical_bp_floor, color=theme.BARRIER, linewidth=1.1, linestyle=(0, (5, 4)))
    b.set_xlabel("all-in carry (bp per year)", fontsize=8, color=theme.MUTED)
    b.set_title("The brackets straddle it — which is the finding",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    theme.finalize(
        fig, kicker="economics",
        headline=f"At today's premium the carry has to stay under ~{critical_bp/12:.0f}bp a month",
        subtitle=f"Breakeven half-life against entry level, one line per cost bracket, 252-day "
                 f"horizon. Estimated base rate {est:.0f}d. Dashed line on the right is the "
                 f"critical carry at the 95% FLOOR half-life ({critical_bp_floor:.0f}bp/yr).",
        source="Conversion fee 0.07% documented [424B4]. FOUR of five components are BRACKETED "
               "assumptions, not quotes: local borrow, ADR borrow, FX forward points, funding.",
        footnote="Brackets exist to be replaced by the desk, not quoted. Whether this trade "
                 "pays is determined by numbers this repository does not hold.",
    )
    return fig, (a, b)


def g16_netting(calm_stress, wrong_way: str):
    """G16 — the netting case and its erosion, on one frame.

    Two panels because the sell and the warning are the same measurement in two states, and
    splitting them across figures is how the second one gets left out of a deck.

    Stress is the top quintile of |Δπ| on the pair's OWN move distribution, not a date range:
    the first version used SKHY's excursion dates for every pair, which gave TSMC four
    arbitrary days and a ratio computed on n=4.
    """
    fig, (a, b) = theme.figure(ncols=2, height=4.8)
    d = calm_stress.dropna(subset=["ratio"])
    labels = list(d.regime_label)
    cols = [theme.SEMANTIC["emphasis"], theme.SEMANTIC["warning"]][:len(d)]

    a.bar(range(len(d)), d.ratio, color=cols, width=0.55)
    for i, (r, n) in enumerate(zip(d.ratio, d.n)):
        a.annotate(f"{1 - r:.0%}\nsaving", xy=(i, r), xytext=(0, 6), textcoords="offset points",
                   ha="center", fontsize=theme.NOTE_SIZE + 1.5, color=theme.TEXT,
                   fontfamily=theme.SERIF_STACK, linespacing=1.3)
        a.annotate(f"n={n:,}", xy=(i, 0.02), ha="center", fontsize=theme.NOTE_SIZE,
                   color=theme.PAPER, fontfamily=theme.SERIF_STACK)
    a.axhline(1.0, color=theme.BARRIER, linewidth=1.4, linestyle=(0, (6, 4)))
    a.annotate("no netting benefit", xy=(0.02, 1.0), xycoords=("axes fraction", "data"),
               xytext=(0, 5), textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.BARRIER, fontfamily=theme.SERIF_STACK)
    a.set_xticks(range(len(d)))
    a.set_xticklabels([l.split("(")[0].strip() for l in labels], fontsize=8)
    a.set_ylim(0, 1.2)
    a.set_ylabel("pair risk ÷ sum of standalone risks", fontsize=8, color=theme.MUTED)
    a.set_title("The benefit roughly halves when the premium moves",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    # RIGHT: the vols the ratio is built from, so it is auditable rather than asserted.
    x = np.arange(len(d))
    for k, (lab, col) in enumerate((("vol_adr", theme.SEMANTIC["context"]),
                                    ("vol_local_usd", theme.SEMANTIC["barrier"]),
                                    ("vol_pair", theme.SEMANTIC["emphasis"]))):
        b.bar(x + (k - 1) * 0.26, d[lab], width=0.24, color=col,
              label=lab.replace("vol_", "").replace("_", " "))
    b.set_xticks(x); b.set_xticklabels([l.split("(")[0].strip() for l in labels], fontsize=8)
    b.set_ylabel("annualised vol", fontsize=8, color=theme.MUTED)
    b.legend(fontsize=theme.NOTE_SIZE, frameon=False)
    b.set_title("What the ratio is built from",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    theme.finalize(
        fig, kicker="capital",
        headline="Cross-margining the pair saves most of the capital — until it is needed",
        subtitle="Pair risk against two standalone tickets, on the deep comparator history. "
                 "Stress is the top quintile of the pair's own premium moves, so both bars "
                 "carry real sample size.",
        source="Repo-computed from landed closes. VaR sketch is ILLUSTRATIVE at 95% one-tailed; "
               "margin methodology is the desk's and the desk quotes actual schedules.",
        # Short form, not a slice: wrong_way[:300] cut the sentence mid-word.
        footnote="WRONG-WAY RISK: when the premium widens the short leg loses AND its borrow "
                 "tightens, so recall risk peaks exactly when the position most needs holding. "
                 "The netting benefit is smallest in that same state.",
    )
    return fig, (a, b)


def g17_capacity(days, adv, borrow):
    """G17 — how big, and how fast out.

    The honest headline is a negative: at any plausible size, screen liquidity is not the
    binding constraint. Both legs turn over roughly $8bn a day, so a $1bn position clears in
    about a session. What binds is the short leg's borrow, and that is drawn as a separate
    ceiling rather than folded into the same axis.
    """
    fig, ax = theme.figure(height=5.0)
    ramp = [theme._ramp(theme.SEMANTIC["emphasis"], 0.55 - 0.55 * i / 2) for i in range(3)]

    for p, col in zip(sorted(days.participation.unique()), ramp):
        d = days[days.participation == p].sort_values("size_usd")
        ax.plot(d.size_usd / 1e9, d.days_binding, color=col, linewidth=1.9, marker="o",
                markersize=4)
        theme.label_line_end(ax, d.size_usd.iloc[-1] / 1e9, d.days_binding.iloc[-1],
                             f"{p:.0%} of ADV", col)

    ax.axhline(1.0, color=theme.RULE, linewidth=1.0)
    ax.annotate("one session", xy=(0.02, 1.0), xycoords=("axes fraction", "data"),
                xytext=(0, 4), textcoords="offset points", fontsize=theme.NOTE_SIZE,
                color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    if borrow.get("on_loan_usd"):
        bn = borrow["on_loan_usd"] / 1e9
        ax.axvline(bn, color=theme.SEMANTIC["warning"], linewidth=1.6, linestyle=(0, (7, 4)))
        # Anchored low-right: at 0.55 of the y-range it sat on the participation line labels.
        ax.annotate(f"on-loan book USD {bn:.0f}bn\n(indicator, NOT lendable depth —\n"
                    "the desk quotes real depth)",
                    xy=(bn, 1.0), xytext=(0.97, 0.06), textcoords="axes fraction",
                    ha="right", va="bottom", fontsize=theme.NOTE_SIZE,
                    color=theme.SEMANTIC["warning"], fontfamily=theme.SERIF_STACK,
                    linespacing=1.4,
                    arrowprops=dict(arrowstyle="-|>", color=theme.SEMANTIC["warning"],
                                    linewidth=0.9, connectionstyle="arc3,rad=0.2"))

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("position size (US$bn, log)", fontsize=8, color=theme.MUTED)
    ax.set_ylabel("sessions to unwind, binding leg (log)", fontsize=8, color=theme.MUTED)

    row = days[(days.participation == 0.10)].sort_values("size_usd")
    one_bn = row[np.isclose(row.size_usd, 1e9)]
    if len(one_bn):
        ax.annotate(f"a USD 1bn position unwinds in ~{one_bn.days_binding.iloc[0]:.1f} sessions "
                    "at 10% of ADV",
                    xy=(1.0, one_bn.days_binding.iloc[0]), xytext=(0.04, 0.90),
                    textcoords="axes fraction", fontsize=theme.NOTE_SIZE, color=theme.MUTED,
                    fontfamily=theme.SERIF_STACK,
                    arrowprops=dict(arrowstyle="-|>", color=theme.RULE, linewidth=0.9,
                                    connectionstyle="arc3,rad=0.15"))

    # NEVER two "$" in one chrome string: matplotlib treats the pair as a mathtext delimiter
    # and renders the span as italic maths. This subtitle came out as "8.8bnADV·0006608.3bn".
    adv_txt = " · ".join(f"{r.leg.split()[0]} USD {r.adv_usd/1e9:.1f}bn ADV" for _, r in adv.iterrows())
    theme.finalize(
        fig, kicker="capacity",
        headline="Screen liquidity is not the constraint here — borrow is",
        subtitle=f"Sessions to exit at conventional participation rates. {adv_txt}. "
                 "Participation bands are a quoting convention, not advice.",
        source="Landed daily volume x close, both legs. KOFIA on-loan balance for the borrow line.",
        footnote="SKHY ADV rests on 12 sessions — regime-fresh, not a cycle average. The "
                 "borrow line is an ON-LOAN BALANCE, which is what is already out, not what "
                 "can be sourced.",
    )
    return fig, ax


def g18_margin_path(path, peak):
    """G18 — the realised excursion replayed as a margin call.

    The chart that carries the stress honesty and the netting sell at once: the pair calls for
    less than two standalone tickets, and it still calls for a great deal. A client trusts the
    desk that shows this before being asked.

    The price path is real. The margining is a parametric sketch and says so — but the sketch
    is applied to sigmas measured INSIDE the window, because the question is what margin does
    when vol is high, not what a calm-period model would have asked for.
    """
    fig, (a, b) = theme.figure(ncols=2, height=4.8)

    a.plot(path.index, path.premium, color=theme.INK, linewidth=2.0, marker="o", markersize=3.5)
    theme.pct_axis(a)
    a.set_ylabel("premium", fontsize=8, color=theme.MUTED)
    a.set_title("The move that did happen", loc="left", fontsize=9.2, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK, pad=8)
    a.annotate(f"{peak['premium_start']:.1%} → {peak['premium_peak']:.1%}\n"
               f"in {peak['sessions']} sessions",
               xy=(path.premium.idxmax(), path.premium.max()), xytext=(-10, -30),
               textcoords="offset points", ha="right", fontsize=theme.NOTE_SIZE,
               color=theme.MUTED, fontfamily=theme.SERIF_STACK, linespacing=1.4)
    theme.thin_date_ticks(a, 4)

    b.fill_between(path.index, path.total_standalone_pct * 100, color=theme.SEMANTIC["warning"],
                   alpha=0.22, linewidth=0)
    b.plot(path.index, path.total_standalone_pct * 100, color=theme.SEMANTIC["warning"],
           linewidth=1.9)
    b.plot(path.index, path.total_pair_pct * 100, color=theme.INK, linewidth=2.1)
    theme.label_line_end(b, path.index[-1], path.total_standalone_pct.iloc[-1] * 100,
                         "two tickets", theme.SEMANTIC["warning"])
    theme.label_line_end(b, path.index[-1], path.total_pair_pct.iloc[-1] * 100,
                         "one netted pair", theme.INK)
    b.set_ylabel("margin required (% of notional)", fontsize=8, color=theme.MUTED)
    b.set_title("What it called for, both ways", loc="left", fontsize=9.2, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK, pad=8)
    b.annotate(f"peak call {peak['peak_total_pair_pct']:.0%} of notional\n"
               f"USD {peak['peak_total_pair_usd']/1e6:.0f}m on a USD "
               f"{peak['notional_usd']/1e6:.0f}m position\n"
               f"vs {peak['peak_total_standalone_pct']:.0%} unnetted",
               xy=(path.total_pair_pct.idxmax(), path.total_pair_pct.max() * 100),
               xytext=(0.04, 0.06), textcoords="axes fraction", ha="left", va="bottom",
               fontsize=theme.NOTE_SIZE, color=theme.TEXT, fontfamily=theme.SERIF_STACK,
               linespacing=1.5, arrowprops=dict(arrowstyle="-|>", color=theme.RULE,
                                                linewidth=0.9, connectionstyle="arc3,rad=0.2"))
    theme.thin_date_ticks(b, 4)

    theme.finalize(
        fig, kicker="stress",
        # "first five sessions" over-specified: the peak lands on session 4 of a 12-session
        # window, so the claim is about the RUN, not a session count.
        headline=f"A move that already happened called for {peak['peak_total_pair_pct']:.0%} of notional",
        subtitle="The realised 16%→52% run, replayed as a margin path. Netting cuts the peak "
                 f"call to {peak['pair_vs_standalone']:.0%} of the unnetted version — real "
                 "relief, and still a large number.",
        source="Price path is realised, from landed closes. Margining is an ILLUSTRATIVE "
               "parametric sketch; the desk quotes actual schedules.",
        footnote="WRONG-WAY RISK: borrow on the short leg tends to tighten as the premium widens, "
                 "so the call and the recall risk arrive together.",
    )
    return fig, (a, b)


def g2c_ops_asymmetry(pkg):
    """G2c — the plumbing map rewritten from the client's chair.

    G2 answers "can this be arbitraged?" for a researcher. A PM asks a different question:
    *what do I have to do, and what do you do?* Same mechanism, opposite framing — so this is a
    separate render rather than a variant of G2, because a figure that tries to answer both
    questions answers neither at a glance.

    Left column is what the client faces. Right column is what the desk absorbs. The asymmetry
    between the two column heights IS the product.
    """
    fig, ax = theme.figure(height=5.4)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    you = ["one ticket", "one margin call", "one monthly report"]
    weabsorb = ["KRX investment registration + standing proxy",
                "local leg booked via total-return swap",
                "ADR borrow sourced and rolled",
                "FX hedge struck and rolled at ≥12m",
                "two legs cross-margined as one position",
                "daily barrier + borrow monitoring"]

    for x0, title, items, col in ((0.4, "YOU FACE", you, theme.SEMANTIC["emphasis"]),
                                  (5.2, "WE ABSORB", weabsorb, theme.SEMANTIC["context"])):
        ax.text(x0, 9.4, title, fontsize=10.5, color=col, fontfamily=theme.SERIF_STACK)
        ax.plot([x0, x0 + 4.4], [9.15, 9.15], color=col, linewidth=1.4)
        for i, it in enumerate(items):
            y = 8.5 - i * 1.32
            ax.add_patch(mpatches.FancyBboxPatch(
                (x0, y - 0.42), 4.4, 0.86, boxstyle="round,pad=0.06",
                facecolor=theme.PAPER, edgecolor=col, linewidth=1.1))
            ax.text(x0 + 0.22, y, it, fontsize=8.4, va="center", color=theme.TEXT,
                    fontfamily=theme.SERIF_STACK)

    # The count asymmetry, in the empty space under the shorter column. A zero-length arrow
    # between the columns rendered as a stray dash, and the label at x=4.95 sat on the last
    # right-hand box.
    ax.text(2.6, 3.4, f"{len(you)} things on your side.\n{len(weabsorb)} on ours.",
            ha="center", va="center", fontsize=10.5, color=theme.MUTED,
            fontfamily=theme.SERIF_STACK, linespacing=1.6)

    theme.finalize(
        fig, kicker="what you do, what we do",
        headline="You hold one position; the operational chain sits on our side",
        subtitle="The same plumbing as the research map, from the client's chair. Everything in "
                 "the right column is a prerequisite to holding the trade at all.",
        source="Mechanics from SEC 424B4, Deposit Agreement F-6 Ex. 99(a), and Korean "
               "registration requirements. Repo-computed figures elsewhere in this pack.",
        footnote="Booking-entity and standby terms are desk matters and are not quoted here.",
        stats=[(f"{pkg['calm_saving']:.0%}", "capital saved vs two tickets\n(calm conditions)"),
               (f"{pkg['peak']['peak_total_pair_pct']:.0%}", "peak margin call on the\nrealised excursion"),
               (f"{pkg['crit_bp']/12:.0f}bp", "carry ceiling per month\nfor the base rate to pay")],
    )
    return fig, ax


def g19_monitoring(ledger_text: str, triggers: list[str], call: dict):
    """G19 — the monitoring pack as a preview of the actual client report.

    P6 exists so the client sees what arrives monthly before they sign anything. It is a
    deliberately plain figure: a state strip, the trigger list, and the registered call with its
    resolution date. Nothing here forecasts; every line is a state reading.
    """
    fig, (a, b) = theme.figure(nrows=2, height=5.6)

    # Top: the barrier-state strip. One bar per programme, so "sealed" is visible not asserted.
    from pipeline.measurement.premium import build_all_variants
    pi = build_all_variants("skhy")[0].series
    a.plot(pi.index, pi.values, color=theme.INK, linewidth=1.8)
    a.fill_between(pi.index, pi.values, color=theme.INK, alpha=0.08)
    theme.pct_axis(a); theme.thin_date_ticks(a, 4)
    a.set_ylabel("premium", fontsize=8, color=theme.MUTED)
    a.set_title("What you receive: the premium, the barrier state, and the trigger list",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=6)

    b.axis("off")
    b.text(0.0, 0.95, "TRIGGERS — mechanism-observables, not forecasts", fontsize=9,
           color=theme.SEMANTIC["barrier"], va="top", fontfamily=theme.SERIF_STACK)
    for i, t in enumerate(triggers):
        b.text(0.02, 0.76 - i * 0.17, f"·  {t}", fontsize=8.2, va="top", color=theme.TEXT,
               fontfamily=theme.SERIF_STACK, wrap=True)
    b.text(0.0, 0.16, f"REGISTERED CALL  H5, Class C, frozen {call['frozen']}, "
                      f"resolves {call['resolution']} — four branches incl. INDETERMINATE. "
                      "Not resolved in this pack.",
           fontsize=8, va="top", color=theme.MUTED, fontfamily=theme.SERIF_STACK)
    b.text(0.0, 0.02, ledger_text, fontsize=7.6, va="top", color=theme.MUTED,
           fontfamily=theme.SERIF_STACK)

    theme.finalize(
        fig, kicker="monitoring",
        headline="The service is a state report, because the timing test came back a draw",
        subtitle="Directional model timing was tested head-to-head (notebook 06) and the shallow "
                 "model's edge is gross, pre-cost and panel-only. Triggers are therefore "
                 "observables whose reading does not depend on that.",
        source="D5 KSD/SEIBro headroom; KOFIA 000660 lending; DART disclosures; event register.",
        footnote="Nothing on this panel is a forecast. A state change is visible only once it "
                 "has happened, which is the honest limit of a trigger.",
    )
    return fig, (a, b)


def g22_scenario_pnl(lv, pl, summ, crit_bp):
    """G22 — three paths, net of bracketed carry, in multiples of initial margin.

    Return-on-margin is the axis, because that is the number a book is run on. The static path
    is drawn as a FAN across the cost bracket rather than a line: four of five carry components
    are undocumented, and a single line would imply a precision that does not exist.

    The honest shape of this figure is that the best path pays a fraction of margin and the
    realised-widening path costs more than all of it.
    """
    fig, (a, b) = theme.figure(ncols=2, height=5.0)
    im = float(summ.initial_margin_pct.iloc[0])
    style = {"compression": (theme.SEMANTIC["emphasis"], "-"),
             "static": (theme.SEMANTIC["context"], (0, (5, 3))),
             "widening": (theme.SEMANTIC["warning"], "-")}

    for path, (col, ls) in style.items():
        a.plot(lv.index, lv[path] * 100, color=col, linewidth=1.9, linestyle=ls)
        theme.label_line_end(a, lv.index[-1], lv[path].iloc[-1] * 100, path, col)
    a.axhline(0.07, color=theme.BARRIER, linewidth=1.5)
    a.annotate("cost floor 0.07%", xy=(0.02, 0.07), xycoords=("axes fraction", "data"),
               xytext=(0, 6), textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.BARRIER, fontfamily=theme.SERIF_STACK)
    a.set_xlabel("sessions held", fontsize=8, color=theme.MUTED)
    a.set_ylabel("premium (%)", fontsize=8, color=theme.MUTED)
    a.set_title("Three paths, one of them realised", loc="left", fontsize=9.2,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    for path, (col, ls) in style.items():
        lo = pl[f"{path}__low"] / im
        hi = pl[f"{path}__high"] / im
        b.fill_between(pl.index, lo, hi, color=col, alpha=0.16, linewidth=0)
        b.plot(pl.index, pl[f"{path}__mid"] / im, color=col, linewidth=1.9, linestyle=ls)
        theme.label_line_end(b, pl.index[-1], pl[f"{path}__mid"].iloc[-1] / im, path, col)
    b.axhline(0, color=theme.BARRIER, linewidth=1.5)
    b.axhline(-1.0, color=theme.SEMANTIC["warning"], linewidth=1.2, linestyle=(0, (4, 3)))
    b.annotate("−1× : the whole initial margin", xy=(0.35, -1.0),
               xycoords=("axes fraction", "data"), xytext=(0, 5),
               textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.SEMANTIC["warning"], fontfamily=theme.SERIF_STACK)
    b.set_xlabel("sessions held", fontsize=8, color=theme.MUTED)
    # labelpad: the left panel's end-labels overhang into this axis's default label position.
    b.set_ylabel("P&L ÷ initial margin", fontsize=8, color=theme.MUTED, labelpad=10)
    b.set_title("Shaded band = the cost bracket, not a confidence interval",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    best = summ[(summ.path == "compression") & (summ.bracket == "low")].iloc[0]
    worst = summ[(summ.path == "widening") & (summ.bracket == "high")].iloc[0]
    theme.finalize(
        fig, kicker="scenario P&L",
        headline="The best path pays a fraction of the margin; the realised one cost more than all of it",
        subtitle=f"Short-premium pair over 252 sessions, net of carry. Compression decays to the "
                 f"cost floor at the estimated base-rate half-life; widening applies the "
                 f"realised move ADDITIVELY from today's level. Breakeven carry {crit_bp:.0f}bp/yr.",
        source="Premium path and realised excursion from landed closes; half-life from the S4 "
               "metrics table. Initial margin is an ILLUSTRATIVE sketch.",
        footnote="Carry is BRACKETED, not quoted — the band is the bracket. Four of five cost "
                 "components are undocumented, so no path here has a single number.",
        stats=[(f"{best.pnl_x_initial_margin:+.2f}×", "compression, low carry\n(best drawn path)"),
               (f"{summ[(summ.path=='static')&(summ.bracket=='mid')].pnl_x_initial_margin.iloc[0]:+.2f}×",
                "static, mid carry\n(the bleed)"),
               (f"{worst.pnl_x_initial_margin:+.2f}×", "realised widening, high carry\n(worse than total margin)"),
               (f"{im:.0%}", "initial margin\n(illustrative)")],
    )
    return fig, (a, b)


def g20_macro_map(pi, fx, events):
    """G20 — the premium inside its policy-and-flow environment.

    WHAT THIS PANEL CANNOT SHOW, stated because the absence is the honest part: KOSPI level,
    the US-Korea rate differential, and foreign-investor flows are NOT landed in this
    repository. A macro strip built from unsourced levels would be the one kind of slide this
    project has spent every session refusing. What is landed is the won and the event register,
    so that is what is drawn.
    """
    fig, (a, b) = theme.figure(nrows=2, height=5.6)

    a.plot(pi.index, pi.values, color=theme.INK, linewidth=2.0, marker="o", markersize=3)
    theme.pct_axis(a); a.set_ylabel("premium", fontsize=8, color=theme.MUTED)
    a.set_title("Regulatory and market-structure events sit above the price",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    if events:
        theme.annotate_events(a, events, labels={
            "skhy_adr_listing": "ADR listing", "skhy_conversion_open": "books reopen",
            "skhy_q2_earnings": "Q2 earnings"}, y_frac=0.55)
    theme.thin_date_ticks(a, 5)

    win = fx.loc[pi.index[0]:] if len(fx.loc[pi.index[0]:]) > 2 else fx.tail(30)
    b.plot(win.index, win.values, color=theme.SEMANTIC["barrier"], linewidth=1.8)
    b.set_ylabel("USD/KRW", fontsize=8, color=theme.MUTED)
    b.set_title("The won — a full leg of the premium and of the hedge cost",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    b.annotate("KOSPI level, US–KR rate differential and foreign-flow series are NOT landed;\n"
               "they are named as gaps rather than drawn from unsourced numbers.",
               xy=(0.01, 0.06), xycoords="axes fraction", fontsize=theme.NOTE_SIZE,
               color=theme.MUTED, fontfamily=theme.SERIF_STACK, linespacing=1.4)
    theme.thin_date_ticks(b, 5)

    theme.finalize(
        fig, kicker="the environment",
        headline="The premium lives inside a policy environment that can move it for non-fundamental reasons",
        subtitle="Event register above, the won below. This panel describes the stage; it does "
                 "not call it.",
        source="Event register (repo, hand-maintained, checksummed); USD/KRW from frankfurter/ECB.",
        footnote="Short selling resumed 2025-03-31. Single-stock 2x ETF listings suspended "
                 "2026-07-16 with the deposit requirement raised, accelerated to 2026-07-31. "
                 "Eurex–KRX link terminated 2025-06-06; KRX night session from 2025-06-09.",
        stats=[("2025-03-31", "short selling resumed\n— the short leg is possible"),
               ("2026-07-31", "2x ETF curb effective\n— concentrated in this name"),
               (f"{float(fx.iloc[-1]):.0f}", "USD/KRW today\n— a full leg of π")],
    )
    return fig, (a, b)


def g21_chain():
    """G21 — the argument, drawn as six nodes.

    A salesperson walks a client left to right. Each node answers the objection the previous one
    raises, which is why it is a chain and not a list.
    """
    fig, ax = theme.figure(height=5.0)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")

    nodes = [
        ("THE PROBLEM", "you want the premium,\nbut cannot reach the\nlocal market", theme.SEMANTIC["context"]),
        ("THE STRUCTURE", "one pair booked\nthrough the desk,\ncross-margined", theme.SEMANTIC["emphasis"]),
        ("IS IT VIABLE?", "carry under ~79bp/mo\nand the base rate pays.\nAbove, it is your view", theme.SEMANTIC["emphasis"]),
        ("CAN IT SURVIVE?", "64% capital saved,\nexits in ~1 session,\nbarrier monitored daily", theme.SEMANTIC["emphasis"]),
        ("WHAT HURTS", "44% peak margin call,\nloss unbounded above,\nborrow tightens into it", theme.SEMANTIC["warning"]),
        ("WHY TRUST IT", "we tested timing and\nit came back a draw.\nTriggers are observables", theme.SEMANTIC["barrier"]),
    ]
    w, gap = 1.72, 0.28
    for i, (title, body, col) in enumerate(nodes):
        x = 0.25 + i * (w + gap)
        ax.add_patch(mpatches.FancyBboxPatch((x, 2.1), w, 2.5, boxstyle="round,pad=0.08",
                     facecolor=theme.PAPER, edgecolor=col, linewidth=1.4))
        ax.text(x + w / 2, 4.28, title, ha="center", fontsize=7.6, color=col,
                fontfamily=theme.SERIF_STACK)
        ax.text(x + w / 2, 3.25, body, ha="center", va="center", fontsize=7.4,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK, linespacing=1.55)
        if i < len(nodes) - 1:
            ax.annotate("", xy=(x + w + gap - 0.03, 3.35), xytext=(x + w + 0.03, 3.35),
                        arrowprops=dict(arrowstyle="-|>", color=theme.RULE, linewidth=1.4))

    theme.finalize(
        fig, kicker="the argument",
        headline="Six steps, and the last one is why the other five are worth hearing",
        subtitle="Each node answers the objection the previous one raises. Every number on this "
                 "panel is derived elsewhere in the pack.",
        source="Repo-computed throughout; carry is bracketed and the desk fills it.",
        footnote="No forecast is sold at any node. The viability step names the client's view as "
                 "the client's.",
    )
    return fig, ax


def g24_exit_tree(days_to_exit: float, stop_points: float = 8.0,
                  excursion_points: float = 35.6, call: dict | None = None):
    """G24 — the exit decision tree. Unifies the rules scattered across P4, P5 and P6.

    Since no timing signal is sold, exits are RULES, and rules are a tree. Each monitor node
    carries the observable that fires it and points at the route that answers it — recall points
    to cancellation because the borrow problem lives on the leg cancellation extinguishes.

    The honesty note is drawn, not footnoted: a stop on a gapping spread limits INTENT, not
    loss. The realised excursion is marked against the stop to show by how much.
    """
    call = call or {"resolution": "2026-10-31"}
    fig, ax = theme.figure(height=6.0)
    ax.set_xlim(0, 25); ax.set_ylim(0, 15); ax.axis("off")
    ax.set_aspect("equal")

    def box(x, y, w, h, title, body, col, lw=1.3):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10",
                     facecolor=theme.PAPER, edgecolor=col, linewidth=lw))
        ax.text(x + w / 2, y + h - 0.55, title, ha="center", fontsize=7.4, color=col,
                fontfamily=theme.SERIF_STACK)
        ax.text(x + w / 2, y + h / 2 - 0.35, body, ha="center", va="center", fontsize=6.6,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK, linespacing=1.5)

    EM, WA, BA, CX = (theme.SEMANTIC["emphasis"], theme.SEMANTIC["warning"],
                      theme.SEMANTIC["barrier"], theme.SEMANTIC["context"])

    box(9.0, 12.6, 7.0, 2.0, "POSITION ON", "the pair, cross-margined", EM, lw=1.8)

    # Monitor layer — five nodes, each with its observable and the route it points at.
    mons = [
        (0.2, "DRAWDOWN", f"stop at {stop_points:.0f} premium pts\n(realised move was "
                          f"{excursion_points:.0f})", WA, 2),
        (5.2, "BORROW", "recall, or a cost step\non the short leg", WA, 1),
        (10.2, "ISSUANCE", "DART disclosure —\nthe upper-barrier class", BA, 0),
        (15.2, "HEADROOM", f"D5 print on the capped\nprogramme · H5 {call['resolution']}", BA, 0),
        (20.2, "CARRY SPENT", "the bleed fan crosses\nyour tolerance", CX, 2),
    ]
    for x, title, body, col, route in mons:
        box(x, 7.8, 4.2, 3.0, title, body, col)
        ax.annotate("", xy=(x + 2.1, 10.95), xytext=(12.5, 12.55),
                    arrowprops=dict(arrowstyle="-", color=theme.RULE, linewidth=0.8,
                                    connectionstyle="arc3,rad=0.06"))

    # Exit-route layer — three terminals, each with cost and timeline.
    routes = [
        (0.2, "MARKET UNWIND", f"sell both legs\n~{days_to_exit:.1f} sessions at 10% ADV\n"
                               "cost: spread + fees", EM),
        (9.0, "CANCEL THROUGH\nTHE OPEN BARRIER", "surrender ADRs, take local\n0.07% round trip, "
                                                  "KSD settle\nextinguishes the borrow", BA),
        (17.8, "DE-RISK / REVERT\nTO STANDBY", "cut size, or never having\ninitiated: zero cost\n"
                                               "(event-conditional variant)", CX),
    ]
    for x, title, body, col in routes:
        box(x, 2.2, 7.0, 3.0, title, body, col, lw=1.5)

    # Edges: monitor -> route. Arrowheads land ON the top edge (5.2), below which the two-line
    # route titles sit -- at 5.9 they crossed the titles they were pointing at.
    targets = {0: 3.7, 1: 12.5, 2: 21.3}
    for x, _, _, _, route in mons:
        ax.annotate("", xy=(targets[route], 5.25), xytext=(x + 2.1, 7.7),
                    arrowprops=dict(arrowstyle="-|>", color=theme.RULE, linewidth=1.0,
                                    connectionstyle="arc3,rad=0.10"))

    ax.text(12.5, 1.05, "recall points at cancellation because the borrow problem lives on the "
                        "very leg cancellation extinguishes.\nA stop on a gapping spread limits "
                        "INTENT, not loss — the realised move gapped through any level set here.",
            ha="center", va="center", fontsize=7.0, color=theme.MUTED,
            fontfamily=theme.SERIF_STACK, linespacing=1.6)

    theme.finalize(
        fig, kicker="exit discipline",
        headline="No timing is sold, so exits are rules — and rules are a tree",
        subtitle="Five observables, three routes. Each monitor points at the route that actually "
                 "answers it.",
        source="Cancellation mechanics and fee from SEC 424B4 and F-6 Ex. 99(a); unwind sessions "
               "from the capacity panel; H5 from the frozen ledger.",
        footnote="A stop is an instruction, not a guarantee: this spread has gapped 36 points in "
                 "five sessions. Sizing, not stops, is what bounds loss here.",
    )
    return fig, ax


def g23_currents(kospi, fx, kr_rate, us_rate):
    """P0b — the currents: the three macro series that were gaps until they landed.

    Three panels because three different frequencies. The rate differential is drawn at the
    Korea leg's NATIVE MONTHLY frequency: interpolating a monthly OECD series to daily for a
    context panel would manufacture twenty observations a month that nobody published.

    Foreign-investor flows remain a gap and are named as one. No route exists without a
    registration this repo does not hold, and an unsourced flow direction on a client panel is
    exactly the claim this project has spent every session refusing.
    """
    fig, (a, b, c) = theme.figure(ncols=3, height=4.4)

    k = kospi.tail(750)
    a.plot(k.index, k.values, color=theme.INK, linewidth=1.8)
    a.set_title("KOSPI", loc="left", fontsize=9, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK, pad=6)
    theme.thin_date_ticks(a, 3)

    f = fx.tail(750)
    b.plot(f.index, f.values, color=theme.SEMANTIC["barrier"], linewidth=1.8)
    b.set_title("USD/KRW", loc="left", fontsize=9, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK, pad=6)
    theme.thin_date_ticks(b, 3)

    diff = (us_rate.resample("MS").mean() - kr_rate).dropna().tail(60)
    c.fill_between(diff.index, diff.values, color=theme.SEMANTIC["emphasis"], alpha=0.18,
                   linewidth=0)
    c.plot(diff.index, diff.values, color=theme.SEMANTIC["emphasis"], linewidth=1.8)
    c.axhline(0, color=theme.RULE, linewidth=1.0)
    c.set_title("US − KR short rate (monthly)", loc="left", fontsize=9, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK, pad=6)
    theme.thin_date_ticks(c, 3)

    theme.finalize(
        fig, kicker="the currents",
        headline="Three things move this gap that have nothing to do with the company",
        subtitle="Index level, the won, and the funding differential. The rate panel is monthly "
                 "because its Korea leg is — not interpolated to look daily.",
        source="KOSPI via EODHD (KS11.INDX); USD/KRW frankfurter/ECB; both rate legs FRED "
               "(EFFR; OECD-sourced Korea 3-month interbank), public domain.",
        footnote="FOREIGN-INVESTOR FLOWS REMAIN A GAP: no sanctioned route without a "
                 "registration this repository does not hold. Named rather than estimated.",
        stats=[(f"{float(kospi.iloc[-1]):,.0f}", "KOSPI today"),
               (f"{float(fx.iloc[-1]):.0f}", "USD/KRW"),
               (f"{float(diff.iloc[-1]):+.2f}pp", "US minus KR short rate\n(funding-leg relevant)"),
               ("gap", "foreign flows\n— no sanctioned route")],
    )
    return fig, (a, b, c)


def g23_hedge_menu(fxh, fxs, beta, carry_bracket_bp):
    """G23 — the hedge menu: what bolts on, what it removes, what it costs.

    THIS PANEL WAS WRONGLY DEFERRED once. It was dropped because one of its three rows -- the
    convexity overlay -- cannot be priced without a listed-option surface. That reasoning
    dropped two rows that are presentable, including the FX one, which carries the project's
    most substantive hedge result: a premium position is NOT FX-neutral even with the local leg
    fully hedged, because the premium is itself a currency-exposed notional.

    Three rows, three honest states: LANDED, PENDING, CONTINGENT. A menu that shows only the
    priced row implies the others do not exist.
    """
    fig, (a, b) = theme.figure(ncols=2, height=4.6)
    lo, hi = carry_bracket_bp["low"], carry_bracket_bp["high"]

    rows = [
        ("FX hedge\nsell KRW fwd vs the local leg", "LANDED",
         f"removes the local leg's FX\nLEAVES {fxh['residual_as_pct_of_adr_leg']:.0%} of the ADR "
         f"leg exposed\n(the premium is itself FX-exposed)",
         f"in the {lo:.0f}–{hi:.0f}bp bracket", theme.SEMANTIC["emphasis"]),
        ("Beta overlay\nvs a Korea market proxy", "PENDING",
         "would remove residual market beta\nratio and interval need M5", "not quotable yet",
         theme.SEMANTIC["barrier"]),
        ("Convexity overlay\nlong straddle vs the short leg", "CONTINGENT",
         "would cap the unbounded side\n— the one thing no other hedge does",
         "no listed surface landed;\nthis repo will not price a synthetic one",
         theme.SEMANTIC["warning"]),
    ]
    a.set_xlim(0, 10); a.set_ylim(0, 9.6); a.axis("off")
    for i, (name, state, removes, cost, col) in enumerate(rows):
        y = 6.4 - i * 3.1
        a.add_patch(mpatches.FancyBboxPatch((0.15, y), 9.7, 2.7, boxstyle="round,pad=0.08",
                    facecolor=theme.PAPER, edgecolor=col, linewidth=1.3))
        a.text(0.45, y + 2.2, name, fontsize=7.8, color=theme.TEXT, va="top",
               fontfamily=theme.SERIF_STACK, linespacing=1.4)
        a.text(9.55, y + 2.25, state, fontsize=7.4, color=col, ha="right",
               fontfamily=theme.SERIF_STACK)
        a.text(0.45, y + 1.55, removes, fontsize=6.8, color=theme.MUTED, va="top",
               fontfamily=theme.SERIF_STACK, linespacing=1.5)
        a.text(0.45, y + 0.42, f"cost: {cost}", fontsize=6.6, color=col, va="bottom",
               fontfamily=theme.SERIF_STACK, linespacing=1.4)
    a.set_title("Three bolt-ons, three honest states", loc="left", fontsize=9.2,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    # RIGHT: the FX finding, because it is the one a client gets wrong by default.
    parts = [("ADR leg", fxh["adr_leg_usd_notional"], theme.SEMANTIC["context"]),
             ("local, hedged", fxh["local_leg_usd_equivalent"], theme.SEMANTIC["emphasis"]),
             ("residual", fxh["residual_premium_notional_usd"], theme.SEMANTIC["warning"])]
    b.barh([2, 1, 0], [p[1] for p in parts], color=[p[2] for p in parts], height=0.55)
    b.set_yticks([2, 1, 0]); b.set_yticklabels([p[0] for p in parts], fontsize=7.6)
    b.annotate("still FX-exposed after the local-leg hedge", xy=(0, 0), xytext=(6, -22),
               textcoords="offset points", fontsize=theme.NOTE_SIZE,
               color=theme.SEMANTIC["warning"], fontfamily=theme.SERIF_STACK)
    for i, (_, v, _) in zip([2, 1, 0], parts):
        b.annotate(f"USD {v:,.0f}", xy=(v, i), xytext=(5, 0), textcoords="offset points",
                   va="center", fontsize=7.4, color=theme.TEXT, fontfamily=theme.SERIF_STACK)
    b.set_xlabel("per ADR-equivalent", fontsize=8, color=theme.MUTED)
    b.set_title("Hedging the local leg does not make the pair FX-neutral",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)

    theme.finalize(
        fig, kicker="the hedge menu",
        headline="One hedge is standard, one waits on a model, one waits on a market",
        subtitle="What each bolt-on removes and what it costs. The FX row is the one clients "
                 "assume is complete and is not.",
        source="FX identity repo-derived and checked to −0.0; empirical sensitivity on 2,300+ "
               "observations; carry bracket from the cost stack.",
        footnote="FX explains only ~1.2% of daily premium variance — hedging it removes a real "
                 "but secondary risk, not the position's main one.",
        stats=[(f"{fxh['residual_as_pct_of_adr_leg']:.0%}", "of the ADR leg still\nFX-exposed after hedging"),
               (f"{fxs['empirical_central_pct_pts']}pp", "premium move per 1% KRW\n(95% CI "
                f"{fxs['empirical_range_pct_pts'][0]:.2f}–{fxs['empirical_range_pct_pts'][1]:.2f})"),
               (f"{fxs['fx_share_of_daily_premium_variance']:.1%}", "of daily premium variance\nis FX"),
               ("1 of 3", "hedges quotable today")],
    )
    return fig, (a, b)
