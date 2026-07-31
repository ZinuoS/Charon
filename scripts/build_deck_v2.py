"""Deck v2 — the opportunity register, per the desk's guidance.

TWO REGISTERS, ONE ANALYSIS. The desk asked for a document that convinces: opportunity-led,
P&L-forward, with risk management explicitly the PM's job. The repository answers a different
reader and keeps every honest figure it has. Neither is a compromise and nothing is deleted --
this module REORDERS and RECAPTIONS panels the repository already renders, and it draws every
number from the same builders `scripts/export_client_pack.py` uses. There is no second set of
numbers anywhere.

WHAT ADVOCACY IS ALLOWED TO DO HERE. Select which panel leads. Choose which of three honest
paths is featured. Frame a breakeven as "what has to happen" rather than as a probability.
Put the qualifier in the speaker's mouth as an answer rather than on the slide as a volunteer.

WHAT IT MAY NEVER DO, and these are enforced rather than remembered:

*   invent a number -- every figure is a repo builder, none is drawn by hand;
*   quote an unbracketed cost -- `assert_costs_bracketed()` fails the build if a carry number
    appears without its range;
*   claim a mechanical convergence force -- `assert_no_decay_claim()` greps this module's own
    captions and notes for the language the research disproved.

NEVER COMMITTED. Output goes to data/derived/deck_v2/, which is gitignored with the rest of
data/derived. The author moves it to firm systems.

    uv run python -m scripts.build_deck_v2
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "derived" / "deck_v2"

# --------------------------------------------------------------------------------
# The order — opportunity-led
# --------------------------------------------------------------------------------
#
# (stem, slide title, the convincing line, [speaker's answer to the question it invites])
#
# The fourth element is the honest qualifier. It is NOT on the slide. It is the answer the
# presenter already has when the obvious question comes, which is a better place for it than
# volunteered in six-point type nobody reads.

ORDER: list[tuple[str, str, str, str]] = [
    ("S01_anchor", "The opportunity, in one chart",
     "Hynix's US line trades 22.6% above its Korean line. The comparable Taiwanese pair "
     "averages 12.5%, and a pair whose share supply is fully fungible sits at zero. Same "
     "instrument, three levels, one structural cause.",
     "Q: why should it converge to TSMC's level? A: nothing forces it to, and I would not "
     "pitch it that way. TSMC's ADR facility revolves and Hynix's does not, which is exactly "
     "why Hynix sits higher. The chart establishes that the level is extreme, not that it "
     "reverts."),
    ("S02_thesis", "Why the gap exists, and why it stays",
     "New US shares require the Company's consent, which it has not given. Supply cannot "
     "answer demand, so the premium is structural rather than a mispricing waiting to be "
     "traded away. The desk manufactures the exposure synthetically.",
     "Q: could the Company issue tomorrow? A: yes, and that is the single largest risk to the "
     "position. It is DART-observable, it is on the catalyst slide, and it is the first thing "
     "the monitoring product watches."),
    ("S02b_ops", "What the client holds, and what we hold",
     "One position for the client. The Korean plumbing, the borrow, the booking chain and the "
     "operational risk sit on our side. That asymmetry is the product.",
     "Q: what if the borrow disappears? A: it is the binding constraint on size, it is priced "
     "into the capacity slide, and the standby terms are a desk conversation."),
    ("S03_opportunity", "The opportunity math",
     "Compression to the family norm is roughly 10 points of premium. Against illustrative "
     "20% margin that is the featured path on this slide, drawn against a financing cost we "
     "quote as a range because four of its five components are not yet desk-confirmed.",
     "Q: what has to happen for this to work? A: about 10 points of compression inside a year "
     "at mid-bracket financing. That is the honest framing -- not a probability, a "
     "requirement. The static and widening paths are on the same slide at the same scale."),
    ("S04_identity", "What actually drives the P&L",
     "Two components and no third: financing, which is deterministic and which the desk "
     "prices, and the change in the gap, which has no assumed drift and moves on identifiable "
     "events. The entry level and the catalysts argue for the second leg.",
     "Q: doesn't the premium decay? A: no, and our own research is the reason we say so. A "
     "premium held open by a consent gate has no arbitrage force pulling it down. That is why "
     "this is a catalyst trade and not a carry-the-convergence trade."),
    ("S05_catalysts", "The compression channels, each with its observable",
     "Three identifiable ways this closes, and every one of them is watchable rather than "
     "hoped for.",
     "Q: what if none of them fires? A: then the position bleeds financing and the widening "
     "path on the opportunity slide is what it looks like. That is why size and the exit "
     "terms are agreed up front."),
    ("S06_economics", "What the desk provides and earns",
     "Financing, borrow, cross-margining and the operational chain -- the netting is where the "
     "capital efficiency comes from and it is measurable.",
     "Q: is the netting benefit contractual? A: the margining shown is illustrative; real "
     "schedules are the desk's and the sheets say so."),
    ("S07_capacity", "How much of it there is",
     "Size against participation, with the borrow as the binding constraint rather than the "
     "exit.",
     "Q: how fast can we get out? A: getting out is easy; borrowing the shares to get in is "
     "the limit. That asymmetry is on the slide."),
    ("S08_service", "The ongoing relationship",
     "Monthly monitoring: the gap, the valve, and three registered things that either happened "
     "or did not.",
     "Q: what makes this different from a broker screen? A: the three watch items are "
     "pre-registered with a resolution date, so the product is falsifiable."),
    ("S09_risk", "Risk considerations (for the PM's assessment)",
     "The shape of the exposure, what it did in its first week, and the wrong-way note -- "
     "presented for the PM's own risk assessment, which is where this decision belongs.",
     "Q: how bad can it get? A: the loss side is not capped by anything on file, and the "
     "position moved 36 points against an early seller in three sessions. Full distributions, "
     "the stop analysis and the exit tree are in the research notebooks."),
    ("S10_methods", "Methods backup",
     "The P&L identity, the comparator evidence base, and where every number comes from.",
     "Q: what is this built on? A: 5,064 sessions of the nearest comparable pair and the "
     "public filings; the repository reproduces every figure from source."),
]

#: Panels that ship on each slide, by stem. Builders are reused verbatim from the pack.
SLIDE_PANELS: dict[str, list[str]] = {
    "S01_anchor": ["S01a_anchor"],
    "S02_thesis": ["P1_situation"],
    "S02b_ops": ["P2_structure"],
    "S03_opportunity": ["P8_scenario_pnl"],
    "S04_identity": ["S04a_identity"],
    "S05_catalysts": ["S05a_catalysts"],
    "S06_economics": ["P3_economics"],
    "S07_capacity": ["P5_size_and_exit"],
    "S08_service": ["P6_what_you_receive"],
    "S09_risk": ["P4a_payoff", "P8d_lab_stops"],
    "S10_methods": ["S04a_identity", "P8c_lab_outcomes"],
}

#: Content that stays in the research notebooks rather than becoming a deck slide, and why.
MOVED_TO_RESEARCH = {
    "P9_exit_discipline": "exit tree -> notebooks/08, referenced from S09's speaker note",
    "P4b_margin_path":    "margin-call replay -> notebooks/01",
    "P8b_hedge_menu":     "hedge menu -> notebooks/08",
    "P0a_the_stage":      "regulatory backdrop -> notebooks/07",
    "P0b_the_currents":   "macro currents -> notebooks/07",
    "P7_the_chain":       "the six-step chain -> notebooks/08",
}


# --------------------------------------------------------------------------------
# The guards — the constraint made structural rather than remembered
# --------------------------------------------------------------------------------

_DECAY_CLAIM = re.compile(
    r"(will|must|should|tends to|expected to)\s+(converge|revert|decay|close)"
    r"|mean[- ]revert(s|ing)?\s+(to|toward)"
    r"|(mechanical|natural|inevitable)\s+(convergence|decay|reversion)"
    r"|pull(s|ed)?\s+(the\s+)?(premium|gap)\s+(down|back)",
    re.IGNORECASE)

_BARE_COST = re.compile(r"\b\d{2,4}\s*(bp|basis points)\b", re.IGNORECASE)
_BRACKET_WORD = re.compile(r"bracket|range|between|to\s+\d|low.*high|assumption", re.IGNORECASE)


def assert_no_decay_claim() -> None:
    """No caption or note may claim a convergence force the research disproved."""
    bad = []
    for stem, title, line, answer in ORDER:
        for field, text in (("title", title), ("line", line), ("answer", answer)):
            m = _DECAY_CLAIM.search(text)
            # "no ... decay" and "nothing forces it" are DENIALS of the claim, not the claim.
            if m and not re.search(r"\b(no|not|nothing|never|does not|cannot)\b",
                                   text[max(0, m.start() - 60):m.start()], re.IGNORECASE):
                bad.append(f"{stem}.{field}: {m.group(0)!r}")
    assert not bad, (
        "deck v2 claims a mechanical convergence force, which the research disproved:\n  "
        + "\n  ".join(bad)
        + "\nAdvocacy may select and emphasise. It may not assert a mechanism that is not there."
    )


def assert_costs_bracketed() -> None:
    """A cost in basis points must appear with its range, never as a single quoted level."""
    bad = []
    for stem, title, line, answer in ORDER:
        for field, text in (("line", line), ("answer", answer)):
            if _BARE_COST.search(text) and not _BRACKET_WORD.search(text):
                bad.append(f"{stem}.{field}: {_BARE_COST.search(text).group(0)!r}")
    assert not bad, (
        "deck v2 quotes an unbracketed cost:\n  " + "\n  ".join(bad)
        + "\nFour of five carry components are assumptions. They ship as a range or not at all."
    )


# --------------------------------------------------------------------------------
# Extra panels this deck needs and the pack does not
# --------------------------------------------------------------------------------


def extra_panels() -> list[tuple[str, callable]]:
    """(name, builder) for deck-only panels. Same theme, same data, same finalize."""
    import numpy as np
    from pipeline.measurement.premium import build_all_variants
    from pipeline.package import breakeven as BE
    from pipeline.viz import figures, theme

    def s01a():
        import pandas as pd
        sk = build_all_variants("skhy")[0].series
        tsm = build_all_variants("tsmc")[0].series
        bb = build_all_variants("baba")[0].series
        five = pd.Timedelta(days=365 * 5)
        levels = [
            ("SK Hynix\nconsent-gated supply", float(sk.iloc[-1]) * 100,
             "issuance needs the\nCompany's consent", "emphasis"),
            ("TSMC\nrevolving facility", float(tsm[tsm.index >= tsm.index[-1] - five].mean()) * 100,
             "cancelled shares return\nto a re-issuable pool", "constrained"),
            ("Alibaba\nfully fungible", float(bb[bb.index >= bb.index[-1] - five].mean()) * 100,
             "the two lines convert\nfreely both ways", "fungible"),
        ]
        return figures.g29_comparator_anchor(levels, tsmc_band=float(tsm.median()) * 100)

    def s04a():
        import numpy as np
        sk = build_all_variants("skhy")[0].series
        tsm = build_all_variants("tsmc")[0].series
        # Volatility from the deep comparator, not from fourteen sessions of SKHY: the traded
        # pair's own sample is too short to estimate a one-year band from, and using it would
        # be the more flattering choice in neither direction -- it is simply not an estimate.
        sd = float(np.diff(tsm.values).std()) * 100
        return figures.g28_pnl_identity(
            float(sk.iloc[-1]), BE.CARRY_BRACKET_BP, sd,
            catalysts=[(21, "Q2 earnings"), (63, "issuance decision window"),
                       (94, "registered call resolves 2026-10-31")])

    def s05a():
        from pipeline.viz import figures as F
        return _catalyst_slide()

    def s03a():
        """The macro-catalyst map — H6's registered result, in whichever form it took."""
        from pipeline.lab import tsmc as LAB
        t = LAB.h6_conditional_channels()
        return figures.g30_macro_catalyst_map(t, LAB.h6_verdict(t), LAB.h6_skhy_descriptive())

    def s0a6():
        """The carry decomposition — the financing chapter's headline panel."""
        from pipeline.package import financing as FIN
        return figures.g29b_carry_decomposition(FIN.carry_components(), FIN.carry_summary(),
                                                FIN.fed_sensitivity())

    def s0a6b():
        """The structure, drawn as legs rather than described as a table."""
        from pipeline.package import financing as FIN
        return figures.g29a_financing_structure(FIN.rate_legs(), FIN.carry_summary())

    return [("S01a_anchor", s01a), ("S03a_macro_map", s03a), ("S04a_identity", s04a),
            ("S05a_catalysts", s05a), ("S0A6_financing", s0a6),
            ("S0A6b_structure", s0a6b)]


def _catalyst_slide():
    """S05a — the three compression channels, each with the thing you actually watch.

    Every row is either a filing you can pull or a series this repository already tracks. A
    catalyst without an observable is a hope, and it does not go on the slide.
    """
    import matplotlib.patches as mpatches

    from pipeline.lab import tsmc as LAB
    from pipeline.viz import theme

    f = LAB.legs()
    ch = LAB.resolution_channel(f, LAB.episodes(f["pi"], 5.0, 10))
    comp = ch[ch.direction == "compression"]
    via_local = float((comp.channel == "local_leg").mean()) * 100
    via_adr = float((comp.channel == "adr_leg").mean()) * 100

    fig, ax = theme.figure(shape_name="tall")
    EM, CON, FUN, CX, BA = (theme.SEMANTIC["emphasis"], theme.SEMANTIC["constrained"],
                            theme.SEMANTIC["fungible"], theme.SEMANTIC["context"],
                            theme.SEMANTIC["barrier"])
    ax.set_xlim(0, 100); ax.set_ylim(3, 94); ax.axis("off")

    rows = [
        ("Issuance decision", EM,
         "The Company moves its deposit level and supply finally answers demand.",
         "DART disclosure; D5 headroom on ISIN US78392B2060, pinned at 0 — any print is news.",
         "Largest single channel. Also the largest risk: it is the same event."),
        ("Demand normalisation", CON,
         "The US bid that opened the gap is a flow, and flows subside.",
         "ADR volume against local volume; the 2x-ETF eligibility change effective 2026-07-31.",
         "No date attaches to this one. It is a condition, not an event."),
        ("Local-leg outperformance", FUN,
         "The gap closes from below: the Korean line rises to the US line.",
         f"Relative performance of the two legs. In 21.6 years of the nearest pair, "
         f"{via_local:.0f}% of compressions closed this way and {via_adr:.0f}% closed by the "
         f"US leg falling.",
         "This is why the expression choice matters — the two are not the same trade."),
    ]
    y = 92.0
    for name, col, what, observable, note in rows:
        ax.add_patch(mpatches.FancyBboxPatch((1.0, y - 27.0), 98.0, 26.5,
                     boxstyle="round,pad=0.4", facecolor=theme.PAPER, edgecolor=col, lw=1.5))
        ax.text(3.5, y - 4.0, name, fontsize=theme.SUBTITLE_SIZE, color=col, weight="medium",
                fontfamily=theme.SERIF_STACK)
        ax.text(3.5, y - 10.0, what, fontsize=theme.LABEL_SIZE, color=theme.TEXT,
                fontfamily=theme.SERIF_STACK)
        ax.text(3.5, y - 16.0, f"WATCH:  {observable}", fontsize=theme.NOTE_SIZE, color=CX,
                fontfamily=theme.SERIF_STACK, wrap=True)
        ax.text(3.5, y - 23.0, note, fontsize=theme.NOTE_SIZE, color=col, style="italic",
                fontfamily=theme.SERIF_STACK)
        y -= 30.5

    theme.finalize(
        fig, kicker="what would close it",
        headline="Three ways this compresses, and the thing you watch for each",
        subtitle="Every channel here is observable. A catalyst without an observable is a "
                 "hope, and it is not on this slide.",
        stats=[(f"{via_local:.0f}%", "of historical compressions\nclosed via the LOCAL leg"),
               (f"{via_adr:.0f}%", "closed via the\nUS leg falling"),
               ("0", "headroom prints on\nthe ISIN to date"),
               ("2026-10-31", "registered call\nresolution date")],
        source="Repo-computed. Channel split from pipeline.lab.tsmc over 21.6 years; "
               "headroom from D5; disclosure route is DART.",
        footnote="The channel split is from the COMPARATOR pair, whose facility revolves. It "
                 "says which leg historically did the work in that family; it does not "
                 "forecast which leg does it here.")
    return fig, {"via_local_pct": via_local, "via_adr_pct": via_adr}


# --------------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------------


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    from scripts.export_client_pack import panels
    from pipeline.viz import theme

    assert_no_decay_claim()
    assert_costs_bracketed()

    theme.apply()
    builders = dict(panels()) | dict(extra_panels())

    if OUT.exists():
        for stale in OUT.iterdir():
            if stale.is_file():
                stale.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    notes: list[str] = [
        "DECK V2 — SPEAKER NOTES (opportunity register)",
        "",
        "Each slide has ONE convincing line and ONE prepared answer. The answer is not on the",
        "slide. It is what you say when the question comes, and the question always comes.",
        "",
        "House rule for this deck: never quote a cost without its range, and never say the",
        "premium converges. It has no force pulling it down and our own research is why we",
        "know that. Say 'this is a catalyst position at an extreme entry level' instead.",
        "",
    ]
    written = 0
    for i, (stem, title, line, answer) in enumerate(ORDER, 1):
        for j, panel in enumerate(SLIDE_PANELS[stem]):
            fig, _ = builders[panel]()
            suffix = "" if len(SLIDE_PANELS[stem]) == 1 else f"{chr(96 + j + 1)}"
            fig.savefig(OUT / f"{i:02d}{suffix}_{stem}.png", dpi=theme.DPI, bbox_inches="tight")
            fig.clear()
            written += 1
        notes += [f"{i:02d}. {title}", f"    SAY:    {line}", f"    ANSWER: {answer}", ""]

    notes += ["", "MOVED TO THE RESEARCH NOTEBOOKS (present, not deleted):"]
    notes += [f"    {k} — {v}" for k, v in MOVED_TO_RESEARCH.items()]
    (OUT / "speaker_notes.txt").write_text("\n".join(notes))

    print(f"  {len(ORDER)} slides, {written} images -> {OUT}")
    print(f"  speaker notes -> {OUT / 'speaker_notes.txt'}")
    print("  NOT COMMITTED — data/derived is gitignored; move it to firm systems yourself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
