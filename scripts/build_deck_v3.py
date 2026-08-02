"""Deck v3 — the pitch book: sell-side write-up, quant appendix, one set of numbers.

WHAT THIS IS. A book a salesperson opens cold: topic on the first line, offer forward,
numbers loaded, and an appendix the client's quant can disappear into. Main body is the
opportunity register. Appendix is the research register, with each slide opening on what the
work buys the client rather than on what it cost us to do.

WHY THE APPENDIX MATTERS MORE THAN IT LOOKS. Every fund has one person who checks. The
appendix is addressed to that person, and it is the reason the main body can be short: the
claims are cashed somewhere the reader can reach, which is what lets the front of the book
make them without hedging adverbs.

BODY-COPY RULES, enforced by :func:`assert_pitch_register`:

*   short declaratives; "we" is the desk, "you" is the client;
*   no hedging adverbs in the main body -- the honesty lives in what is SHOWN and what is
    BRACKETED, not in "arguably" and "potentially";
*   no forecast language, no mechanical-decay claim, no conversion-as-a-trade;
*   every number traceable to a repo builder or a citation; brackets rendered as brackets.

THE BRACKET -> INDICATION SWITCH is :data:`INDICATIVE_ECONOMICS`. It is None today, so the
economics slide renders ranges. Fill it after the two desk conversations and the same slide
renders desk indications; nothing else in the book changes.

NEVER COMMITTED. Output is data/derived/deck_v3/, gitignored with the rest of data/derived.

    uv run python -m scripts.build_deck_v3
"""
from __future__ import annotations

import base64
import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "derived" / "deck_v3"

# --------------------------------------------------------------------------------
# The one config the desk conversations change
# --------------------------------------------------------------------------------
#
# None  -> the economics slide renders the bracket, and every cost reads as a range.
# dict  -> the same slide renders desk indications. One line, one place, nothing else moves.
#
# The four bracketed components are local short borrow, ADR borrow, USD/KRW forward points,
# and the USD-vs-KRW funding differential. The fifth, the conversion fee, is documented.
INDICATIVE_ECONOMICS: dict[str, float] | None = None


def economics_line(brackets: dict) -> tuple[str, str]:
    """(headline number, provenance clause) for the economics slide, both modes.

    The range comes from the FINANCING DECOMPOSITION, not the legacy bundled bracket: two
    components are measured, the obol is documented, and the only thing still spanning a range
    is the ADR borrow spread. Quoting the old bundle here while the appendix showed the stack
    had the book disagreeing with itself about its own cost.
    """
    from pipeline.package import financing as FIN

    if INDICATIVE_ECONOMICS:
        bp = INDICATIVE_ECONOMICS["all_in_bp"]
        return (f"{bp / 12:.0f}bp/mo", f"desk indication as of {INDICATIVE_ECONOMICS['as_of']}")
    lo = FIN.carry_summary("low")["total_bp_per_month"]
    hi = FIN.carry_summary("high")["total_bp_per_month"]
    return (f"{lo:.0f}-{hi:.0f}bp/mo",
            "range, not a quote — it is the ADR borrow spread, and it is the one component "
            "still awaiting the desk")


# --------------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------------


@dataclass
class Slide:
    num: str
    name: str
    headline: str
    body: list[str]
    panels: list[str] = field(default_factory=list)
    callouts: list[tuple[str, str]] = field(default_factory=list)
    footnote: str = ""
    table: str = ""
    opens_with: str = ""          # appendix only: what this buys the client

    @property
    def stem(self) -> str:
        return f"slide_{self.num}_{self.name}"


def build_slides(n) -> tuple[list[Slide], list[Slide]]:
    """Main body and appendix. ``n`` is the numbers bundle -- nothing is typed by hand."""
    econ_head, econ_note = economics_line(n["brackets"])

    main = [
        Slide("01", "title",
              f"SK hynix ADR / local relative value: accessing a {n['pi']:.1f}% premium "
              f"against a {n['norm']:.1f}% structural norm, swap-financed and cross-margined",
              [f"The US line trades {n['pi']:.1f}% above the Korean line.",
               f"The closest structural comparable has averaged {n['norm']:.1f}% over five "
               f"years. A pair whose share supply is fully fungible trades at "
               f"{n['fungible']:.1f}%.",
               "The difference is plumbing, not fundamentals.",
               "We finance the pair, source the borrow, and cross-margin it as one risk."],
              ["S01a_anchor"],
              [(f"{n['pi']:.1f}%", "SK hynix today"),
               (f"{n['norm']:.1f}%", "TSMC, 5-year mean"),
               (f"{n['fungible']:.1f}%", "Alibaba, fungible supply")],
              "Levels from exchange closes, same construction for all three pairs. "
              "Repo-computed; see appendix A7."),

        Slide("02", "executive_summary",
              "The idea, the offer, and where the risk slide is",
              [f"**The dislocation.** SK hynix's ADR trades {n['pi']:.1f}% above its Korean "
               f"shares — {n['gap']:.0f} points wide of the structural comparable.",
               "**Why it persists.** New ADRs require the Company's consent. Supply cannot "
               "answer demand, so the market cannot arbitrage this gap away.",
               "**What we build you.** One cross-margined position: synthetic local access "
               "through our booking chain, ADR borrow sourced, FX executed, monitored monthly.",
               f"**Indicative economics.** All-in carry {econ_head}. The trade bears "
               f"{n['crit_slow_mo']:.0f}–{n['crit_fast_mo']:.0f}bp/mo depending on how fast "
               f"the gap closes, so it clears at every borrow level except one corner: slow "
               f"convergence and expensive borrow together. "
               f"Cross-margining saves {n['capital_saved']:.0f}% of capital on ordinary days "
               f"(n={n['n_calm']}) and {n['peak_saving']:.0f}% at the peak of the worst week "
               f"this pair has seen. Capacity is roughly {n['days_1bn']:.1f} sessions for "
               f"$1bn at 10% participation.",
               "Risk considerations are slide 08, sized for the PM's own assessment."],
              ["S01a_anchor"],
              [(econ_head, "all-in carry"),
               (f"{n['crit_slow_mo']:.0f}–{n['crit_fast_mo']:.0f}bp", "what it can bear,\nacross the interval"),
               (f"{n['days_1bn']:.1f}", "sessions to build\n$1bn at 10% ADV"),
               (f"{n['gap']:.0f}pts", "wide of the\nstructural norm")],
              f"Carry is a {econ_note}. Margining is illustrative; real schedules are ours "
              f"to quote. The netting figures rest on {n['n_calm']} ordinary and "
              f"{n['n_stress']} stressed sessions — this programme is three weeks old and "
              f"the sample says so."),

        Slide("03", "why_now",
              "Why now: the bid, the cost, the channel, the access",
              [f"**The bid.** The ADR is three weeks old and trades "
               f"${n['adr_adv_usd'] / 1e9:.1f}bn a day — more than the Korean line's "
               f"${n['local_adv_usd'] / 1e9:.1f}bn, which has 2,838 sessions of history. "
               f"US demand has nowhere to go: new ADRs need the Company's consent.",
               f"**The cost.** The funding leg is long the front end. You earn the USD rate "
               f"on collateral and short proceeds and pay the Korean rate on the local long, "
               f"so a 25bp hike makes this "
               f"{n['fed_bp_per_month_per_25bp']:.1f}bp per month CHEAPER to hold, not "
               f"dearer.",
               f"**The channel.** The won moves the premium's level — "
               f"{n['fx_coef']:.2f} points per 1% — and explains {n['fx_r2']:.1%} of its "
               f"daily variation. We registered the stronger claim, that won strength "
               f"selects which leg closes the gap, and tested it: {n['h6_gap_pp']:+.1f} points "
               f"in the predicted direction at p = {n['h6_p']:.2f}. It did not clear. We are "
               f"not pitching the won as a signal.",
               "**The access.** Short selling resumed 2025-03-31, so the short leg exists. "
               "The 2x-ETF eligibility change lands 2026-07-31 and this name is in scope. "
               "The Eurex-KRX link terminated 2025-06-06 and KRX runs its own night session, "
               "which is what the overnight hedge routes through."],
              ["S05a_catalysts", "S03a_macro_map"],
              [(f"${n['adr_adv_usd'] / 1e9:.1f}bn", "ADR daily volume,\n12 sessions in"),
               (f"{n['fed_bp_per_month_per_25bp']:.1f}bp", "per month,\nper 25bp of Fed"),
               (f"{n['fx_coef']:.2f}pts", "premium move,\nper 1% won"),
               ("tested", "and the channel claim\ndid not clear")],
              "Volumes from measured ADV on both legs; the twelve-session caveat travels with "
              "the number. Fed sensitivity from pipeline.package.financing. The channel claim "
              "was registered 2026-07-30 in a commit containing no results — appendix A2 and "
              "the public repository have the order."),

        Slide("04", "the_opportunity",
              "The market cannot arbitrage this premium. We can manufacture the exposure.",
              ["Cancelling an ADR into local shares is a holder right and always works.",
               "Creating an ADR requires the Company to consent to a larger deposit. It has "
               "not.",
               "So the gap has a floor that functions and a ceiling that is somebody's "
               "decision. That is why it is still here.",
               "You cannot close it by converting. You can hold the spread — and that is "
               "what we build."],
              ["P1_situation", "P2_structure"],
              [(f"{n['pi']:.1f}%", "premium today"),
               ("0.07%", "cost floor —\ncancellation round trip"),
               ("one-way", "the arbitrage\nthat works")],
              "Mechanism from the F-6 Ex. 99(a) undertaking and 17 CFR 239.36(a). "
              "Cancellation appears in this book only as an unwind mechanic."),

        Slide("05", "catalysts",
              "Three ways this compresses, each with the thing you watch",
              ["**Issuance decision.** The Company moves its deposit level and supply finally "
               "answers demand. DART-observable; headroom on the ISIN has printed zero to "
               "date, so any print is information.",
               "**Demand normalisation.** The US bid that opened the gap is a flow. The 2x-ETF "
               "eligibility change effective 2026-07-31 is the dated part of it.",
               f"**Local-leg outperformance.** The gap closes from below. In {n['lab_years']} "
               f"years of the nearest comparable pair, {n['via_local']:.0f}% of compressions "
               f"closed this way and {n['via_adr']:.0f}% closed by the US leg falling.",
               "Each of these is watchable. We monitor all three monthly."],
              ["S05a_catalysts"],
              [(f"{n['via_local']:.0f}%", "historical compressions\nvia the local leg"),
               (f"{n['via_adr']:.0f}%", "via the US\nleg falling"),
               ("0", "headroom prints\nto date"),
               ("2026-10-31", "our registered\ncall resolves")],
              "Channel split computed on the comparator pair, whose facility revolves. It "
              "records which leg did the work in that family. Appendix A2."),

        Slide("06", "what_we_offer",
              "One position for you. The Korean plumbing on our side.",
              ["**Synthetic local access.** You face us. The local leg, the booking chain and "
               "the operational risk sit with us.",
               "**Borrow sourcing.** The ADR borrow is the binding constraint on size, and "
               "sourcing it is the part of this that is a desk capability rather than a view.",
               "**FX execution.** The won leg is executed and hedged with the pair, not "
               "bolted on afterwards.",
               f"**Cross-margining.** One netted ticket instead of two: "
               f"{n['capital_saved']:.0f}% less capital than two standalone tickets on "
               f"ordinary days, and {n['peak_saving']:.0f}% less through the worst week this "
               f"pair has actually seen — {n['peak_call']:.0f} cents on the dollar against "
               f"{n['peak_standalone']:.0f}. Appendix A4 has the day-by-day and the "
               f"conditions under which the offset thins.",
               f"**Capacity.** Roughly {n['days_1bn']:.1f} sessions to build $1bn at 10% "
               f"participation.",
               "**Entry.** We build the pair over multiple sessions at agreed participation, "
               "and the borrow is arranged before the first ticket rather than after it.",
               "**Financing.** Two legs: the local leg through the booking chain, the ADR leg "
               "borrowed. Both reprice on the agreed schedule.",
               "**Monitoring.** Monthly: the gap, the valve, and three registered items that "
               "either happened or did not."],
              ["P4b_margin_path", "P5_size_and_exit"],
              [(f"{n['capital_saved']:.0f}%", "capital saved,\nordinary days"),
               (f"{n['peak_saving']:.0f}%", "capital saved through\nthe worst week"),
               (f"{n['peak_call']:.0f}c", "peak call per dollar,\nnetted"),
               (f"{n['days_1bn']:.1f}", "sessions for $1bn\nat 10% ADV")],
              "Margining illustrative; the realised week is not — that path happened. "
              "Capacity from measured ADV on both legs. Appendix A4."),

        Slide("07", "indicative_economics",
              "What has to happen, what it costs, and the one case where it does not work",
              [f"**The featured path.** Compression to the structural norm is {n['gap']:.0f} "
               f"points of premium.",
               f"**What that requires.** Roughly {n['gap']:.0f} points inside twelve months at "
               f"mid-bracket financing. That is a requirement, not a probability.",
               f"**The known cost.** All-in carry of {econ_head}, drawn against the path "
               f"rather than netted out of it. Two of its components are measured from "
               f"landed series; the range is the ADR borrow spread alone.",
               f"**What the trade can bear.** Convergence is an interval, not a point — "
               f"{n['hl_lower']:.0f} to {n['hl_upper']:.0f} sessions at 95% — so the "
               f"breakeven is a boundary rather than a number: "
               f"{n['crit_fast_mo']:.0f}bp/mo at the fast end, "
               f"{n['crit_point_mo']:.0f} at the point, {n['crit_slow_mo']:.0f} at the slow "
               f"end. It clears at every borrow level except one corner — slow convergence "
               f"AND expensive borrow together — and that corner is exactly the client we "
               f"route to a different expression on slide 1b.",
               "**The other two paths are on the same slide at the same scale.** Static "
               "bleeds the carry. The realised widening is what it looks like when the gap "
               "goes the other way.",
               "We do not forecast which path happens. We price the financing and show you "
               "all three."],
              ["S07a_breakeven", "P8_scenario_pnl"],
              [(econ_head, "all-in carry"),
               (f"{n['gap']:.0f}pts", "compression to\nthe norm"),
               (f"{n['crit_slow_mo']:.0f}–{n['crit_fast_mo']:.0f}bp", "bearable, across\nthe interval"),
               ("1", "corner where it\ndoes not clear")],
              f"Carry is a {econ_note}. The breakeven surface is appendix A6."),

        Slide("08", "risk_considerations",
              "Risk considerations — for the PM's assessment",
              ["**The payoff is asymmetric.** Gain is capped by the cost floor. Loss is not "
               "capped by anything on file, because the ceiling is the Company's decision.",
               f"**It has already moved hard.** The premium went {n['excursion']:.0f} points "
               f"against an early seller in {n['excursion_sessions']} sessions. That is "
               f"realised, not modelled.",
               "**Wrong-way risk.** The event that closes the gap — an issuance — is also the "
               "event that would mark the position against you on the way there.",
               "**Sizing, not stops.** A stop tight enough to bound loss fires on most "
               "winners. We size the position instead, and the appendix shows the work.",
               "**Three ways out, agreed at entry.** Trade the spread out in the market, the "
               "usual path. Deliver the ADR and sell the local shares, slower and it always "
               "works. If the borrow is recalled we route to cancellation, because that is "
               "the leg cancellation extinguishes.",
               "This slide is here because the analysis exists, and the position sizing is "
               "yours to set."],
              ["P4a_payoff", "P8d_lab_stops"],
              [(f"{n['excursion']:.0f}pts", f"realised move against,\nin {n['excursion_sessions']} sessions"),
               (f"{n['max_mae']:.0f}pts", f"worst in {n['lab_years']} years\nof the comparable"),
               ("uncapped", "the loss side"),
               ("3", "unwind routes,\nagreed at entry")],
              "Excursion from exchange closes. Distributions, stop analysis and the exit "
              "tree are appendices A2 and A5. Booking-entity and standby terms are ours "
              "to quote."),
    ]

    appendix = [
        Slide("A1", "measurement_discipline",
              "Why the marks in this book are trustworthy",
              ["Every premium in this book is a price ratio, and a price ratio is only as "
               "good as the two prices and the currency between them.",
               "We build the premium under every combination of FX source and close "
               "definition, and we report the spread between them rather than picking one.",
               "The two FX sources disagree by 23bp on average — because they are fixed "
               "hours apart, which is a fact about observation timing, not an error.",
               "The close definition changes nothing at all. That is worth knowing before "
               "anyone quotes a level to two decimal places.",
               "All three legs are taken on their last SHARED observation date. Taking each "
               "leg's own newest close mixes moments and is not a price ratio."],
              [],
              [(f"{n['f6_variants']}", "measurement\nvariants built"),
               (f"{n['f6_fx_bp']:.0f}bp", "FX-source spread,\nmean"),
               ("0bp", "close-definition\nspread"),
               ("identity", "the asynchrony\ndecomposition residual")],
              "pipeline/measurement/premium.py and asynchrony.py. Variant table below.",
              table=n["f6_table"],
              opens_with="You get a level you can quote, and the size of the disagreement "
                         "behind it."),

        Slide("A2", "the_comparator_lab",
              "21.6 years of the nearest comparable regime",
              [f"SK hynix's ADR programme is {n['skhy_sessions']} sessions old. Every question "
               f"about a distribution needs a longer one, so we built it on TSMC: "
               f"{n['lab_obs']:,} sessions from {n['lab_first']}.",
               f"The gap moved in {n['episodes']} episodes at the base rule — median "
               f"{n['median_move']:.1f} points over {n['median_days']} sessions.",
               f"Entering at the 90th percentile of the premium's own history and holding a "
               f"year beat the carry {n['beats_low']:.0%} of the time at low cost, "
               f"{n['beats_mid']:.0%} at mid, and {n['beats_high']:.0%} at high.",
               "We report that because it is the honest answer and because it is the "
               "argument for the financing conversation: the cost bracket decides this "
               "trade, not the timing.",
               "The entry rule is triggered on an expanding percentile, so it never sees its "
               "own future. Every grid cell is reported; nothing is selected."],
              ["P8c_lab_outcomes", "P8d_lab_stops"],
              [(f"{n['beats_low']:.0%}", "beat LOW carry"),
               (f"{n['beats_mid']:.0%}", "beat MID carry"),
               (f"{n['beats_high']:.0%}", "beat HIGH carry"),
               (f"{n['episodes']}", "episodes in\n21.6 years")],
              "TSMC's facility revolves and SK hynix's does not, so this is the FAVOURABLE "
              "variant of the family. It bounds the argument; it does not make it.",
              opens_with="You get a distribution instead of an anecdote, and you get the "
                         "number that argues against us alongside the ones that argue for."),

        Slide("A3", "we_tested_the_timing",
              "We checked whether this is a signal trade. It is not.",
              ["Before pitching this as carry plus catalysts, we tested the alternative: a "
               "high-complexity forecasting model of the kind that wins when there is a "
               "signal to find.",
               "We ran a parsimonious model against a heavily overparameterised one on the "
               "comparator panel, at matched sample size, with the traded instrument never "
               "fitted.",
               "The shallow model won. Both beat the naive benchmarks gross, and the "
               "t-statistic falls from 11.5 to 5.3 once the overlapping-horizon correction "
               "is applied.",
               "So there is no model behind this pitch, and that is deliberate. What we sell "
               "is access, financing and capital efficiency at an extreme entry level.",
               "You are not wondering what we are hiding, because the answer is nothing."],
              [],
              [("parsimony", "won the\nhead-to-head"),
               ("5.3", "t-stat after the\noverlap correction"),
               ("0", "SK hynix observations\nin any fit"),
               ("no model", "behind this\npitch")],
              "Kelly-Malamud-Zhou random Fourier features against the shallow specification; "
              "Nagel critique diagnostics applied. Notebook 06 in the public repository.",
              opens_with="You get to skip the question every quant asks third: what model is "
                         "this really, and why am I not seeing it."),

        Slide("A4", "netting_under_stress",
              "The capital saving, measured on the week it mattered",
              ["Cross-margining is only worth quoting if it holds when the position moves. "
               "Ours does not hold uniformly, and this slide is where we show that.",
               f"On ordinary days the netted ticket saves {n['capital_saved']:.0f}% of the "
               f"capital. On the top 20% of move days that saving is "
               f"{n['capital_saved_stress']:.0f}%: the two legs stop offsetting precisely "
               f"when the gap jumps, which is when the offset would be worth most.",
               "We replayed the worst week this pair has actually seen through both "
               "structures: one netted ticket, and two standalone tickets on the same legs.",
               f"The netted structure peaked at {n['peak_call']:.0f} cents on the dollar "
               f"against {n['peak_standalone']:.0f} standalone — {n['peak_saving']:.0f}% less "
               f"capital through the stress itself.",
               "Both numbers belong on the same slide. A netting benefit quoted without its "
               "peak call is a marketing number."],
              ["P4b_margin_path"],
              [(f"{n['capital_saved']:.0f}%", "saved on\nordinary days"),
               (f"{n['capital_saved_stress']:.0f}%", "saved on the\ntop 20% of days"),
               (f"{n['peak_saving']:.0f}%", "saved through\nthe worst week"),
               (f"{n['peak_call']:.0f}c", "peak call,\nnetted")],
              "Initial margin is a parametric sketch and is illustrative. The price path is "
              "not: it happened.",
              opens_with="You get the capital number with its own stress test attached."),

        Slide("A5", "the_exit_tree",
              "Five things watched, three ways out, decided in advance",
              ["Because we sell no timing signal, the exits are rules — and rules are a tree.",
               "Each monitor points at the route that answers it. A borrow recall points at "
               "cancellation, because the borrow problem lives on the leg cancellation "
               "extinguishes.",
               "A stop on a gapping spread limits intent, not loss. This spread moved 36 "
               "points in five sessions.",
               "So sizing bounds the loss and the stop expresses preference. We say which is "
               "which."],
              ["P9_exit_discipline"],
              [("5", "monitors"), ("3", "routes"),
               ("agreed at entry", "not improvised\nat the exit")],
              "Exit discipline is a term of the trade, not a slide.",
              opens_with="You get the unwind decided while everyone is calm."),

        Slide("A6", "the_financing_stack",
              "The carry, opened into components — and the funding leg pays you",
              [f"Two of the four carry components are measured from landed series, one is a "
               f"desk quote, and one cannot be measured at all with the data we hold. They "
               f"are drawn as three different kinds of bar so the chart cannot pass an "
               f"assumption off as a measurement.",
               f"USD rates sit above Korean rates and you are long the Korean asset funded "
               f"from dollars, so the funding differential is a TAILWIND. All-in carry is "
               f"{n['carry_bp_per_month']:.0f}bp per month against a "
               f"an {n['critical_bp'] / 12:.0f}bp breakeven.",
               "The cross-currency basis is drawn hatched at zero. Measuring it needs a "
               "USD/KRW forward curve we do not hold, and a negative won basis — the usual "
               "sign — eats directly into that tailwind.",
               f"The breakeven is the carry at which the estimated base rate exactly pays "
               f"for itself: {n['critical_bp']:.0f}bp per year at today's entry over one "
               f"year. Above it, a client is expressing a faster-than-base-rate view, and "
               f"this book says so in those words."],
              ["S0A6_financing", "P3_economics"],
              [(f"{n['carry_bp_per_month']:.0f}bp", "all-in carry,\nper month"),
               (f"{n['critical_bp'] / 12:.0f}bp", "breakeven,\nper month"),
               (f"{n['fed_bp_per_month_per_25bp']:.1f}bp", "per month, per\n25bp of Fed"),
               ("1 of 5", "components still\nunmeasurable")],
              "pipeline/package/breakeven.py. The estimated half-life is an interval with a "
              "support classification, not a point estimate.",
              opens_with="You get the cost broken into parts you can negotiate, and the "
                         "exact level at which our own argument stops working."),

        Slide("A7", "methodology_and_sources",
              "Where every number in this book comes from",
              ["Prices are exchange closes from the listing venue or a corroborated "
               "aggregator; the comparator's deep history is bit-identical to the listing "
               "venue over 2,513 overlapping sessions.",
               "Raw data is immutable and checksummed. Every pull writes a payload, a "
               "provenance sidecar, a log line and a checksum entry.",
               "Analysis code touches no network. Every figure in this book is rendered by a "
               "builder in the repository from source data.",
               "Registered calls are frozen with a resolution date before the outcome is "
               "known, and they resolve in public whichever way they go.",
               "The research is public. Nothing in this book is a number the appendix cannot "
               "reach."],
              [],
              [(f"{n['lab_obs']:,}", "comparator sessions"),
               ("0", "network calls in\nanalysis code"),
               ("2026-10-31", "next registered\ncall resolves")],
              "Public repository: github.com/ZinuoS/Charon",
              opens_with="You get to check any of it without asking us."),
    ]
    return main, appendix


# --------------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------------

_FORECAST = re.compile(
    r"\b(we (expect|forecast|project|anticipate)|will (converge|close|revert|narrow)"
    r"|should (converge|close|revert|narrow)|is likely to (converge|close|revert)"
    r"|guarantee\w*|risk[- ]free)\b", re.IGNORECASE)
_DECAY = re.compile(
    r"(mechanical|natural|inevitable)\s+(convergence|decay|reversion)"
    r"|mean[- ]revert(s|ing)\s+(to|toward)"
    r"|pull(s|ed)?\s+(the\s+)?(premium|gap)\s+(down|back)", re.IGNORECASE)
_CONVERSION = re.compile(
    r"conversion\s+(trade|arb\w*|play)|convert\s+(to|and)\s+capture"
    r"|arb(itrage)?\s+the\s+(gap|premium)", re.IGNORECASE)
# "rather THAN" is a contrast, not a hedge -- "a desk capability rather than a view" is the
# most decisive sentence on that slide. Only bare "rather" is the qualifier being banned.
_HEDGE_ADVERB = re.compile(
    r"\b(arguably|potentially|possibly|perhaps|somewhat|fairly|quite|maybe"
    r"|hopefully|presumably)\b|\brather\b(?!\s+than)", re.IGNORECASE)
_NEGATED = re.compile(r"\b(no|not|nothing|never|cannot|does not|do not|without)\b",
                      re.IGNORECASE)


def _scan(text: str, pattern: re.Pattern) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    # A DENIAL of the claim is not the claim. "the market cannot arbitrage the premium" is
    # the thesis; "arb the premium" as an offer is the thing being banned.
    if _NEGATED.search(text[max(0, m.start() - 70):m.start()]):
        return None
    return m.group(0)


def assert_pitch_register(main: list[Slide], appendix: list[Slide]) -> None:
    """Language rules, checked on the copy itself rather than remembered by the writer."""
    bad: list[str] = []
    for slides, is_main in ((main, True), (appendix, False)):
        for s in slides:
            blob = " ".join([s.headline, *s.body, s.footnote, s.opens_with])
            for label, pat in (("forecast", _FORECAST), ("decay", _DECAY),
                               ("conversion-as-trade", _CONVERSION)):
                hit = _scan(blob, pat)
                if hit:
                    bad.append(f"{s.stem}: {label} — {hit!r}")
            if is_main:
                hit = _HEDGE_ADVERB.search(blob)
                if hit:
                    bad.append(f"{s.stem}: hedging adverb in main body — {hit.group(0)!r}")
    assert not bad, (
        "deck v3 copy breaks the pitch register:\n  " + "\n  ".join(bad)
        + "\nThe honesty in this book lives in what is SHOWN and what is BRACKETED. "
          "Qualifier adverbs are not honesty, they are the absence of a decision."
    )


def assert_costs_bracketed(main: list[Slide]) -> None:
    """No main-body cost may be quoted as a single level while the bracket stands."""
    if INDICATIVE_ECONOMICS:
        return
    bare = re.compile(r"\b\d{2,4}\s*bp\b", re.IGNORECASE)
    # A POLICY SHIFT in basis points is not a cost quote. "2.1bp per month per 25bp of Fed"
    # is a sensitivity, and banning it would push the copy into vaguer language in the name
    # of a rule about precision.
    ok = re.compile(r"\d+\s*-\s*\d+\s*bp|bracket|range|breaks? even|critical"
                    r"|per\s+\d+\s*bp|\d+\s*bp\s+(hike|cut|shift|move)"
                    r"|hike|cut\b", re.IGNORECASE)
    bad = [f"{s.stem}: {bare.search(t).group(0)!r}"
           for s in main for t in [" ".join([s.headline, *s.body])]
           if bare.search(t) and not ok.search(t)]
    assert not bad, ("deck v3 quotes an unbracketed cost while INDICATIVE_ECONOMICS is "
                     "None:\n  " + "\n  ".join(bad))


# --------------------------------------------------------------------------------
# Numbers — computed once, never typed
# --------------------------------------------------------------------------------


def numbers() -> dict:
    import numpy as np
    import pandas as pd

    from pipeline.hedging.ratios import HedgeLegs
    from pipeline.lab import tsmc as LAB
    from pipeline.measurement.premium import build_all_variants, variant_spread
    from pipeline.convergence.jorda import run_panel
    from pipeline.package import (breakeven as BE, capacity as CAP, financing as FIN,
                                  margin_path as MP, netting as NET)
    HL = run_panel()["one_way_constrained"].hl

    sk = build_all_variants("skhy")[0].series
    tsm = build_all_variants("tsmc")[0].series
    bb = build_all_variants("baba")[0].series
    five = pd.Timedelta(days=365 * 5)

    f = LAB.legs()
    cen = LAB.census(frame=f)
    base = cen[(cen.min_move_pp == 5.0) & (cen.min_days == 10)].iloc[0]
    ch = LAB.resolution_channel(f, LAB.episodes(f["pi"], 5.0, 10))
    comp = ch[ch.direction == "compression"]
    eo = LAB.entry_outcomes(f["pi"], pctiles=(0.90,), horizons=(252,))
    ex = LAB.excursions(f["pi"])
    skw = LAB.skhy_week_one_excursion()

    peak = MP.peak_call()
    vs = variant_spread(build_all_variants("skhy"))
    fx_rows = vs[vs.mean_bp > 0]
    days = CAP.days_to_unwind()
    d1bn = float(days[(days.participation == 0.10) & (days.size_usd == 1e9)].days_binding.iloc[0])

    # No fallbacks. A default here is a fabrication machine: the first version of this
    # function shipped 64% and 44% as hardcoded defaults because the real keys did not
    # match, and both looked plausible enough to survive a read-through.
    cvs = NET.calm_vs_stress().set_index("regime_label")
    calm = next(i for i in cvs.index if i.startswith("calm"))
    stress = next(i for i in cvs.index if i.startswith("stress"))
    capital_saved = float(cvs.loc[calm, "capital_saving"]) * 100
    capital_saved_stress = float(cvs.loc[stress, "capital_saving"]) * 100
    peak_pair = float(peak["peak_total_pair_pct"]) * 100
    peak_standalone = float(peak["peak_total_standalone_pct"]) * 100

    table = ["| measurement variant pair | shared days | mean | p95 | max |",
             "|---|---|---|---|---|"]
    for r in vs.itertuples():
        table.append(f"| {r.a} vs {r.b} | {r.n_shared} | {r.mean_bp:.1f}bp | "
                     f"{r.p95_bp:.1f}bp | {r.max_bp:.1f}bp |")

    return {
        "pi": float(sk.iloc[-1]) * 100,
        "norm": float(tsm[tsm.index >= tsm.index[-1] - five].mean()) * 100,
        "fungible": float(bb[bb.index >= bb.index[-1] - five].mean()) * 100,
        "brackets": BE.CARRY_BRACKET_BP,
        "critical_bp": BE.critical_carry_bp(),
        "hl_lower": HL.lower, "hl_point": HL.point, "hl_upper": HL.upper,
        "crit_fast_mo": BE.critical_carry_bp(half_life_days=HL.lower) / 12,
        "crit_point_mo": BE.critical_carry_bp(half_life_days=HL.point) / 12,
        "crit_slow_mo": BE.critical_carry_bp(half_life_days=HL.upper) / 12,
        "adr_adv_usd": float(CAP.adv_table().iloc[0].adv_usd),
        "local_adv_usd": float(CAP.adv_table().iloc[1].adv_usd),
        "fed_bp_per_month_per_25bp": FIN.fed_sensitivity()["bp_per_month_per_25bp"],
        "carry_bp_per_month": FIN.carry_summary()["total_bp_per_month"],
        "fx_coef": float(LAB.fx_sensitivity_deep(f).iloc[0].empirical_coef),
        "fx_r2": float(LAB.fx_sensitivity_deep(f).iloc[0].r2),
        "h6_gap_pp": LAB.h6_verdict()["gap_pp"],
        "h6_p": LAB.h6_verdict()["p_value"],
        "gap": float(sk.iloc[-1]) * 100 - float(tsm[tsm.index >= tsm.index[-1] - five].mean()) * 100,
        "skhy_sessions": int(len(sk)),
        "lab_obs": int(len(f)), "lab_first": str(f.index[0].date()),
        "lab_years": round((f.index[-1] - f.index[0]).days / 365.25, 1),
        "episodes": int(base.n_episodes),
        "median_move": float(base.median_move_pp), "median_days": int(base.median_days),
        "via_local": float((comp.channel == "local_leg").mean()) * 100,
        "via_adr": float((comp.channel == "adr_leg").mean()) * 100,
        "beats_low": float(eo[eo.bracket == "low"].frac_beats_carry.iloc[0]),
        "beats_mid": float(eo[eo.bracket == "mid"].frac_beats_carry.iloc[0]),
        "beats_high": float(eo[eo.bracket == "high"].frac_beats_carry.iloc[0]),
        "max_mae": float(ex.attrs["max_mae_pp"]),
        "excursion": float(skw["excursion_pp"]), "excursion_sessions": int(skw["sessions"]),
        "peak_call": peak_pair,
        "peak_standalone": peak_standalone,
        "peak_saving": (1.0 - peak_pair / peak_standalone) * 100,
        "capital_saved": capital_saved,
        "n_calm": int(cvs.loc[calm, "n"]), "n_stress": int(cvs.loc[stress, "n"]),
        "capital_saved_stress": max(capital_saved_stress, 0.0),
        "days_1bn": d1bn,
        "f6_variants": int(len(build_all_variants("skhy"))),
        "f6_fx_bp": float(fx_rows.mean_bp.mean()) if len(fx_rows) else 0.0,
        "f6_table": "\n".join(table),
    }


# --------------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------------


def _slide_md(s: Slide, images: list[str]) -> str:
    out = [f"# {s.headline}", ""]
    if s.opens_with:
        out += [f"> **What this buys you.** {s.opens_with}", ""]
    out += [*s.body, ""]
    for img in images:
        out += [f"![{s.name}]({img})", ""]
    if s.table:
        out += [s.table, ""]
    if s.callouts:
        out += ["| " + " | ".join(v for v, _ in s.callouts) + " |",
                "|" + "---|" * len(s.callouts),
                "| " + " | ".join(k.replace("\n", " ") for _, k in s.callouts) + " |", ""]
    if s.footnote:
        out += [f"*{s.footnote}*", ""]
    return "\n".join(out)


def _html(main: list[Slide], appendix: list[Slide], imgs: dict[str, list[Path]],
          title: str) -> str:
    def page(s: Slide) -> str:
        blocks = [f"<h1>{html.escape(s.headline)}</h1>"]
        if s.opens_with:
            blocks.append(f'<p class="buys"><b>What this buys you.</b> '
                          f'{html.escape(s.opens_with)}</p>')
        for line in s.body:
            # **bold** -> <b>bold</b>, after escaping, so the copy can carry emphasis
            # without the markdown source leaking into the rendered page.
            txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\\1</b>", html.escape(line))
            blocks.append(f"<p>{txt}</p>")
        for p in imgs.get(s.stem, []):
            b64 = base64.b64encode(p.read_bytes()).decode()
            blocks.append(f'<img src="data:image/png;base64,{b64}" alt="">')
        if s.table:
            rows = [r for r in s.table.splitlines() if r.strip()]
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = "".join(
                "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>"
                for i, row in enumerate(cells) if i != 1)
            blocks.append(f"<table>{body}</table>")
        if s.callouts:
            items = "".join(
                f'<div class="stat"><span class="v">{html.escape(v)}</span>'
                f'<span class="k">{html.escape(k)}</span></div>' for v, k in s.callouts)
            blocks.append(f'<div class="stats">{items}</div>')
        if s.footnote:
            blocks.append(f'<p class="foot">{html.escape(s.footnote)}</p>')
        return (f'<section><div class="num">{html.escape(s.num)}</div>'
                + "".join(blocks) + "</section>")

    css = """
    :root{--ink:#1c1c1a;--mut:#6e6e68;--rule:#d8d5cf;--paper:#fbfaf7;--em:#0072b2}
    *{box-sizing:border-box}
    body{margin:0;background:#eceae5;color:var(--ink);
         font-family:Arial,Helvetica,"Liberation Sans",sans-serif;line-height:1.55}
    section{background:var(--paper);max-width:1120px;margin:26px auto;padding:52px 60px 44px;
            position:relative;box-shadow:0 1px 3px rgba(0,0,0,.10);page-break-after:always}
    .num{position:absolute;top:22px;right:28px;color:var(--mut);font-size:12px;
         letter-spacing:.16em}
    h1{font-size:26px;line-height:1.28;margin:0 0 22px;font-weight:400;max-width:56ch}
    p{margin:0 0 12px;font-size:15px;max-width:74ch}
    .buys{border-left:3px solid var(--em);padding-left:14px;color:var(--mut);font-size:14px}
    img{width:100%;height:auto;margin:22px 0;display:block}
    .foot{color:var(--mut);font-size:12.5px;border-top:1px solid var(--rule);
          padding-top:12px;margin-top:24px;max-width:none}
    .stats{display:flex;gap:34px;flex-wrap:wrap;margin:26px 0 8px;
           border-top:1px solid var(--rule);padding-top:20px}
    .stat{display:flex;flex-direction:column;gap:5px}
    .stat .v{font-size:30px;color:var(--em);line-height:1}
    .stat .k{font-size:12px;color:var(--mut);white-space:pre-line}
    table{border-collapse:collapse;margin:18px 0;font-size:12.5px;width:100%}
    td{border-bottom:1px solid var(--rule);padding:7px 10px;color:var(--mut)}
    tr:first-child td{color:var(--ink);border-bottom:1.5px solid var(--ink)}
    .divider{background:none;box-shadow:none;text-align:center;color:var(--mut);
             letter-spacing:.3em;font-size:13px;padding:14px}
    @media print{body{background:#fff}section{margin:0;box-shadow:none;max-width:none}}
    """
    divider = ('<section class="divider">APPENDIX — THE WORK BEHIND THE NUMBERS</section>')
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title><style>{css}</style></head><body>"
            + "".join(page(s) for s in main) + divider
            + "".join(page(s) for s in appendix) + "</body></html>")


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    from pipeline.viz import theme
    from scripts.build_deck_v2 import extra_panels
    from scripts.export_client_pack import panels

    n = numbers()
    body, appendix = build_slides(n)
    assert_pitch_register(body, appendix)
    assert_costs_bracketed(body)

    theme.apply()
    builders = dict(panels()) | dict(extra_panels())

    if OUT.exists():
        for stale in OUT.iterdir():
            if stale.is_file():
                stale.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    rendered: dict[str, list[Path]] = {}
    for s in body + appendix:
        paths = []
        for j, panel in enumerate(s.panels):
            fig, _ = builders[panel]()
            p = OUT / f"{s.stem}_{j + 1}.png"
            fig.savefig(p, dpi=theme.DPI, bbox_inches="tight")
            fig.clear()
            paths.append(p)
        rendered[s.stem] = paths
        (OUT / f"{s.stem}.md").write_text(_slide_md(s, [p.name for p in paths]))

    title = body[0].headline
    (OUT / "pitch_book.html").write_text(_html(body, appendix, rendered, title))

    mode = "INDICATIONS" if INDICATIVE_ECONOMICS else "BRACKETS"
    print(f"  {len(body)} main + {len(appendix)} appendix slides -> {OUT}")
    print(f"  figures: {sum(len(v) for v in rendered.values())}   economics mode: {mode}")
    print(f"  assembled: {OUT / 'pitch_book.html'}  (print to PDF from a browser)")
    print("  NOT COMMITTED — data/derived is gitignored.")
    print(f"\n  TITLE: {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
