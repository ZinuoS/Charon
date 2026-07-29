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
    ax.axhline(fee_pct, color=theme.INK, linewidth=1.8, zorder=2)
    ax.annotate(
        f"OPEN — ADR cancellation, uncapped\nround trip ≈ ${FEE_PER_ADS * 2:.2f}/ADS ≈ {fee_pct:.2%} of price",
        xy=(0.012, fee_pct), xycoords=("axes fraction", "data"), xytext=(0, -6),
        textcoords="offset points", fontsize=theme.NOTE_SIZE, color=theme.INK,
        va="top", ha="left", fontfamily=theme.SERIF_STACK,
    )

    # Upper barrier — long-dashed: discretionary, and with no number on file it has no
    # determinate height. Drawn above the realized max to say "not observed to bind here".
    ax.axhline(top, color=theme.CLAY, linewidth=1.6, linestyle=(0, (9, 5)), zorder=2)
    ax.annotate(
        "DISCRETIONARY — primary ADS issuance at the Company's determination.\n"
        "No numeric deposit cap appears in any SEC filing.",
        xy=(0.012, top), xycoords=("axes fraction", "data"), xytext=(0, 6),
        textcoords="offset points", fontsize=theme.NOTE_SIZE, color=theme.CLAY,
        va="bottom", ha="left", fontfamily=theme.SERIF_STACK,
    )

    ax.plot(pi.index, pi.values, color=theme.INK, linewidth=1.9, marker="o", markersize=3.4, zorder=3)
    theme.pct_axis(ax)
    ax.set_ylim(min(-0.03, float(pi.min()) - 0.04), top * 1.16)

    theme.headline(
        ax,
        "The premium has a floor that works and a ceiling that is somebody's decision",
        "SKHY vs 000660.KS close-to-close. The asymmetry is structural, not incidental: "
        "one direction is a holder's right, the other requires the issuer's consent.",
    )
    theme.label_line_end(ax, pi.index[-1], pi.values[-1], "SKHY / 000660", theme.INK)
    if events:
        theme.annotate_events(ax, events, labels={
            "skhy_adr_listing": "listing", "skhy_conversion_open": "books reopen",
            "skhy_q2_earnings": "Q2 earnings"}, y_frac=0.62)

    # Sits in the empty upper-right quadrant: anywhere lower collides with the floor rule.
    ax.annotate(DEPOSIT_QUOTE, xy=(0.985, 0.88), xycoords="axes fraction",
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
                     facecolor=theme.PAPER, edgecolor=theme.INK, linewidth=1.3))
        ax.text(x + 0.95, 3.22, label, ha="center", va="center", fontsize=9,
                color=theme.TEXT, fontfamily=theme.SERIF_STACK)

    # Open channel: ADR -> local. Wide arrow, solid.
    ax.annotate("", xy=(7.15, 2.32), xytext=(2.95, 2.32),
                arrowprops=dict(arrowstyle="-|>,head_width=0.42,head_length=0.7",
                                color=theme.INK, linewidth=5.5, alpha=0.85))
    ax.text(5.05, 1.94, "CANCELLATION — uncapped, a holder right (17 CFR §239.36(a))",
            ha="center", fontsize=8.2, color=theme.INK, fontfamily=theme.SERIF_STACK)
    ax.text(5.05, 1.60, f"fee ${FEE_PER_ADS:.2f}/ADS · settlement via KSD",
            ha="center", fontsize=7.4, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    # Gated channel: local -> ADR. Thin, dashed, with a gate bar across it.
    ax.annotate("", xy=(2.95, 4.28), xytext=(7.15, 4.28),
                arrowprops=dict(arrowstyle="-|>,head_width=0.24,head_length=0.5",
                                color=theme.CLAY, linewidth=1.7, linestyle=(0, (7, 4))))
    ax.plot([5.05, 5.05], [3.98, 4.58], color=theme.CLAY, linewidth=3.4)
    ax.text(5.05, 4.74, "ISSUANCE — gated", ha="center", fontsize=8.6, color=theme.CLAY,
            fontfamily=theme.SERIF_STACK)
    ax.text(5.05, 5.28,
            "Company determination  ·  board authorization 17,790,000 sh (2.50%)\n"
            "·  SK Square must hold ≥20% (MRFTA) — post-issue 20.0008%",
            ha="center", fontsize=7.6, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    # D5 gauge on the gated channel.
    ax.add_patch(mpatches.Rectangle((4.30, 3.62), 1.5, 0.20, facecolor="#eceae5",
                                    edgecolor=theme.MUTED, linewidth=0.7))
    ax.text(5.05, 3.40, "D5 observable — capped programme headroom: 0",
            ha="center", fontsize=7.4, color=theme.MUTED, fontfamily=theme.SERIF_STACK)

    theme.headline(ax, "One direction is a right; the other is a permission",
                   "Why the classic create-to-arbitrage trade is unavailable here.")
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
          color=[theme.INK if v < 0 else theme.CLAY for v in grouped.values], width=0.62)
    a.axhline(0, color=theme.RULE, linewidth=1.0)
    a.set_title("TSM: next-day premium change by starting level\n(bp, 2,328 days) — "
                "no strong pull toward zero from high levels",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    a.set_xlabel("starting premium quintile", fontsize=8, color=theme.MUTED)

    grid = np.linspace(-0.05, 0.60, 400)
    entry = float(pi_skhy.iloc[0])
    floor = 0.0007
    pnl = np.where(grid <= entry, entry - grid, entry - grid)
    b.fill_between(grid, pnl, 0, where=(grid > entry), color=theme.CLAY, alpha=0.16)
    b.fill_between(grid, pnl, 0, where=(grid <= entry), color=theme.INK, alpha=0.13)
    b.plot(grid, pnl, color=theme.TEXT, linewidth=1.5)
    b.axvline(floor, color=theme.INK, linewidth=1.6)
    b.axhline(0, color=theme.RULE, linewidth=1.0)
    lo, hi = float(pi_skhy.min()), float(pi_skhy.max())
    b.annotate("", xy=(hi, entry - hi), xytext=(lo, entry - lo),
               arrowprops=dict(arrowstyle="-|>", color=theme.CLAY, linewidth=2.0))
    b.annotate(f"realized {lo:.1%} → {hi:.1%}\nin week one", xy=(hi, entry - hi),
               xytext=(-6, -26), textcoords="offset points", fontsize=8, color=theme.CLAY,
               ha="right", fontfamily=theme.SERIF_STACK)
    b.annotate("GAIN BOUNDED\nby the cost floor", xy=(0.03, 0.10), xycoords="axes fraction",
               fontsize=8, color=theme.INK, fontfamily=theme.SERIF_STACK)
    b.annotate("LOSS UNBOUNDED — no ceiling on file", xy=(0.97, 0.90),
               xycoords="axes fraction", fontsize=8.4, color=theme.CLAY, ha="right",
               fontfamily=theme.SERIF_STACK, weight="medium")
    b.set_title("Short-premium payoff: the skew is structural, not bad luck",
                loc="left", fontsize=9.2, color=theme.TEXT, fontfamily=theme.SERIF_STACK, pad=8)
    b.set_xlabel("premium at exit", fontsize=8, color=theme.MUTED)
    theme.pct_axis(b)
    b.xaxis.set_major_formatter(theme.mpl.ticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

    theme.multiples_headline(
        fig, "This is relative value against a one-sided barrier — not arbitrage",
        "Left: whether high premiums revert, shown rather than assumed. "
        "Right: what the convergence expression actually pays.")
    return fig, axes
