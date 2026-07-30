"""Render the six client-pack panels as standalone slides.

    uv run python -m scripts.export_client_pack

Each panel is ONE figure, so a panel is one file. `theme.finalize(stats=...)` puts the callout
row in the chrome band, which is why no assembler exists here — a composition layer would be a
second thing that has to agree with finalize about spacing.

PNG for the deck, PDF for print. Both palettes when PRESENTATION_PALETTE is set; the public
palette alone otherwise, with no error.
"""

from __future__ import annotations

import pathlib

from execution.costs import margin_stress, summary_table
from hypotheses.h4_vol_decomposition.realized import compare_pairs
from hypotheses.h5_quota_ledger.monitor import status_report
from pipeline.convergence.jorda import run_panel
from pipeline.hedging.sheets import _pkg_numbers
from pipeline.measurement.premium import build_all_variants
from pipeline.package import breakeven as BE, capacity as CAP, margin_path as MP, netting as NET
from pipeline.viz import figures, theme

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "derived" / "client_pack"

#: THE PACK, in presentation order, with the one-line note for each. Single source of truth:
#: `build_deck` copies in this order, `build_client_note` renders in this order, and the note
#: doubles as the notebook's plain-English line. Three separate lists had already drifted.
ORDER = [
    ("P0a_the_stage", "Set the stage: Korean rules and the won move this gap on their own."),
    ("P0b_the_currents", "Three outside forces: the index, the won, and the funding differential."),
    ("P1_situation", "The gap is 22.6% and the trade that normally closes it runs one way."),
    ("P2_structure", "You hold one position; the Korean plumbing sits on our side."),
    ("P3_economics", "It pays if your carry stays under about 79 basis points a month."),
    ("P7_the_chain", "Walk the six steps — the last one is why the first five matter."),
    ("P8_scenario_pnl", "Best case pays a fraction of your margin; the realised case cost all of it."),
    ("P4a_payoff", "Gain is capped by the floor. Loss is not capped by anything on file."),
    ("P4b_margin_path", "A move that already happened called for 44 cents per dollar."),
    ("P9_exit_discipline", "We agree the exit rules up front: five things to watch, three ways out."),
    ("P5_size_and_exit", "Getting out is easy. Borrowing the shares to sell is the limit."),
    ("P6_what_you_receive", "Monthly: the gap, the valve, and three things that either happened or did not."),
]

TRIGGERS = [
    "DART issuance disclosure indicating the Company has moved its deposit level",
    "D5 headroom CREATION on ISIN US78392B2060 — pinned at 0, so any print is information",
    "Korean borrow-regime shift (short-sale rule change, or a step in lending balances)",
]
CALL = {"frozen": "2026-07-29", "resolution": "2026-10-31"}


def panels():
    """(name, builder) per panel. Builders return (fig, axes)."""
    pkg = _pkg_numbers()
    sk = build_all_variants("skhy")[0].series
    tsm = build_all_variants("tsmc")[0].series
    surf, v = BE.surface(), BE.verdict()
    cc = BE.critical_carry_bp()
    ccf = BE.critical_carry_bp(half_life_days=run_panel()["one_way_constrained"].hl.lower)
    mpath, peak = MP.margin_path(), MP.peak_call()

    def p1():
        fig, ax = figures.g1_barrier_anatomy(sk, theme.events_for(markets=["US", "KR"]))
        theme.finalize(
            fig, kicker="the situation",
            headline="The premium has a floor that works and a ceiling that is somebody's decision",
            subtitle="SKHY against 000660.KS, close to close, since listing.",
            source="Nasdaq; EODHD; frankfurter/ECB. Barrier language: SEC 424B4 and F-6 Ex. 99(a).",
            footnote="Non-contemporaneous closes: KRX 15:30 KST against Nasdaq 16:00 ET.",
            stats=[(f"{sk.iloc[-1]:.1%}", "premium today"),
                   ("0.07%", "structural floor\n(cancellation round trip)"),
                   (f"{tsm.mean():.1%}", "base-rate anchor\n(comparator, 2,328 days)")])
        return fig, ax

    def p3():
        fig, axes = figures.g15_breakeven(surf, v, cc, ccf)
        theme.finalize(
            fig, kicker="the economics",
            headline=f"At today's premium the carry has to stay under ~{cc/12:.0f}bp a month",
            subtitle="Breakeven half-life against entry level, one line per cost bracket.",
            source="Conversion fee documented; four of five components are BRACKETED assumptions.",
            footnote="Brackets exist to be replaced by the desk, not quoted.",
            stats=[("250–1200bp", "all-in carry, per year\nBRACKETED"),
                   (f"{cc/12:.0f}bp/mo", "breakeven carry ceiling"),
                   (f"{v['estimated_floor_days']:.0f}–{v['estimated_half_life_days']:.0f}d",
                    "base-rate half-life band\n(no upper bound)"),
                   (f"{1 - pkg['calm_saving']:.2f}×", "pair vs standalone margin")])
        return fig, axes

    def p4b():
        fig, axes = figures.g18_margin_path(mpath, peak)
        theme.finalize(
            fig, kicker="how it hurts",
            headline=f"A move that already happened called for "
                     f"{peak['peak_total_pair_pct']:.0%} of notional",
            subtitle="The realised 16%→52% run, replayed as a margin path.",
            source="Price path realised; margining is an ILLUSTRATIVE sketch.",
            footnote="WRONG-WAY RISK: borrow tightens as the premium widens, so the call and the "
                     "recall risk arrive together.",
            stats=[(f"{peak['peak_total_pair_pct']:.0%}", "peak call, netted"),
                   (f"{peak['peak_total_standalone_pct']:.0%}", "peak call, two tickets"),
                   ("unbounded", "loss above\n(no cap on file)")])
        return fig, axes

    def p5():
        days, adv, borrow = CAP.days_to_unwind(), CAP.adv_table(), CAP.borrow_ceiling()
        fig, ax = figures.g17_capacity(days, adv, borrow)
        one = days[(days.participation == 0.10) & (days.size_usd == 1e9)].days_binding.iloc[0]
        theme.finalize(
            fig, kicker="size and exit",
            headline="Screen liquidity is not the constraint here — borrow is",
            subtitle="Sessions to exit at conventional participation rates.",
            source="Landed daily volume × close, both legs; KOFIA on-loan balance.",
            footnote="SKHY ADV rests on 12 sessions. The borrow line is what is already out, "
                     "not what can be sourced.",
            stats=[(f"~{one:.1f}", "sessions to exit USD 1bn\nat 10% of ADV"),
                   ("USD 8bn", "daily turnover, each leg"),
                   ("desk", "quotes real borrow depth")])
        return fig, ax

    def p0a():
        from pipeline.measurement.premium import _load_close
        fx = _load_close("d1_prices", "usdkrw_spot_daily")
        return figures.g20_macro_map(sk, fx, theme.events_for(markets=["US", "KR", "GLOBAL"]))

    def p0b():
        from pipeline.measurement.premium import _load_close
        return figures.g23_currents(
            _load_close("d2_macro", "kospi_index_daily"),
            _load_close("d1_prices", "usdkrw_spot_daily"),
            _load_close("d2_macro", "kr_rate_3m_monthly"),
            _load_close("d2_macro", "us_rate_effr_daily"))

    def p9():
        days = CAP.days_to_unwind()
        one = float(days[(days.participation == 0.10) & (days.size_usd == 1e9)].days_binding.iloc[0])
        return figures.g24_exit_tree(one)

    def p8():
        from pipeline.package import scenarios as SC
        su = SC.summary()
        return figures.g22_scenario_pnl(SC.paths(), SC.pnl(), su, cc)

    return [
        ("P0a_the_stage", p0a),
        ("P0b_the_currents", p0b),
        ("P1_situation", p1),
        ("P2_structure", lambda: figures.g2c_ops_asymmetry(pkg)),
        ("P3_economics", p3),
        ("P4a_payoff", lambda: figures.g4_asymmetry(tsm, sk)),
        ("P4b_margin_path", p4b),
        ("P5_size_and_exit", p5),
        ("P6_what_you_receive",
         lambda: figures.g19_monitoring(status_report()[:400], TRIGGERS, CALL)),
        ("P7_the_chain", figures.g21_chain),
        ("P8_scenario_pnl", p8),
        ("P9_exit_discipline", p9),
    ]


def main() -> int:
    # Backend switch belongs HERE, not at import. Setting Agg at module scope hijacked the
    # notebook's inline backend when it imported `panels`, so every panel rendered to a file
    # and displayed nothing -- a pack with no figures in it and no error to show why.
    import matplotlib
    matplotlib.use("Agg")
    theme.apply()
    used, _ = theme.active_palette()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in panels():
        fig, _ = build()
        for ext in ("png", "pdf"):
            fig.savefig(OUT / f"{name}.{ext}", dpi=200, bbox_inches="tight")
        print(f"  {name}  ({used} palette)")
    n = len(panels())
    print(f"\n{n} panels -> {OUT}  ({n * 2} files, PNG + PDF). P4 is a pair: payoff + margin path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
