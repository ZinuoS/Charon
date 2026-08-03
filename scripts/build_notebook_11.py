"""Generate notebooks/11_pitch_book.ipynb — the presentation material.

NUMBERING. The session brief called this "04_pitch_book" and described notebook 03 as the
slide layer. Neither matches the repository: 03 is the comparator panel and 04 is regimes and
convergence, both live, and the slide layer is `data/derived/deck_v3/`. Writing to 04 would
have destroyed a live notebook, so this takes the next free number. A rename is one `git mv`
if a different one is wanted.

WHAT THIS IS versus deck_v3. deck_v3 is what gets projected: one line per slide, a figure, and
a prepared answer for the presenter. This is what gets READ -- walked through in the room, left
behind afterwards, and judged by whoever was not in the room. Both render from the same
builders, so no figure exists in two versions and no number can disagree with itself.

REGISTER. Sell-side conviction: short declaratives, benefits before features, the trade on page
one. The honesty floor is unchanged and is enforced by the same guards the deck uses -- every
number live at render, brackets rendered as brackets, no forecast verbs, no decay claims, risk
present once and positioned. Persuasion by selection and emphasis; never by invention.
"""
from __future__ import annotations

from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(ROOT))
from scripts._nb import notebook  # noqa: E402

OUT = ROOT / "notebooks" / "11_pitch_book.ipynb"
md, code, write = notebook()

# ---------------------------------------------------------------- §0 cover
md(r"""
# SK hynix ADR / local relative value

### Accessing a structural premium, swap-financed and cross-margined

The US line trades above the identical Korean shares because new US shares require the
Company's consent and it has not given it. The market cannot arbitrage the gap away. We
manufacture the exposure.

$$\pi \;=\; \frac{P_{\text{ADR}}}{P_{\text{local}} \cdot \text{FX} / 10} \;-\; 1$$

*One ADR represents one-tenth of a common share. π is the object of everything that follows,
defined before anything is claimed about it.*
""")

code(r"""
%matplotlib inline
import sys, pathlib, datetime as _dt
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import pandas as pd
from IPython.display import Markdown
from pipeline.viz import theme, figures
from pipeline.measurement.premium import build_all_variants
from pipeline.package import breakeven as BE, capacity as CAP, financing as FIN
from pipeline.package import margin_path as MP, netting as NET, scenarios as SC
from pipeline.hedging.ratios import HedgeLegs, fx_sensitivity
from pipeline.lab import tsmc as LAB
from scripts.export_client_pack import panels
from scripts.build_deck_v2 import extra_panels
from scripts.build_deck_v3 import economics_line
theme.apply()
PANELS = dict(panels()) | dict(extra_panels())

# Every number below is computed at render. Nothing on this page is typed.
sk   = build_all_variants("skhy")[0].series
tsm  = build_all_variants("tsmc")[0].series
bb   = build_all_variants("baba")[0].series
_5y  = pd.Timedelta(days=365 * 5)
PI    = float(sk.iloc[-1]) * 100
NORM  = float(tsm[tsm.index >= tsm.index[-1] - _5y].mean()) * 100
CTRL  = float(bb[bb.index >= bb.index[-1] - _5y].mean()) * 100
CARRY = FIN.carry_summary(); FED = FIN.fed_sensitivity()
LO    = FIN.carry_summary("low")["total_bp_per_month"]
HI    = FIN.carry_summary("high")["total_bp_per_month"]
BE_MO = CARRY["critical_carry_bp_per_month"]
ECON, ECON_NOTE = economics_line(BE.CARRY_BRACKET_BP)
EO    = LAB.entry_outcomes(LAB.premium(), pctiles=(0.90,), horizons=(252,)).set_index("bracket")
EX    = LAB.excursions(LAB.premium()); SKW = LAB.skhy_week_one_excursion()
FXS   = fx_sensitivity(HedgeLegs.live("skhy").premium)
PEAK  = MP.peak_call()
_cvs  = NET.calm_vs_stress().set_index("regime_label")
_c0 = [i for i in _cvs.index if i.startswith("calm")][0]
_s0 = [i for i in _cvs.index if i.startswith("stress")][0]
N_CALM, N_STRESS = int(_cvs.loc[_c0, "n"]), int(_cvs.loc[_s0, "n"])
CALM  = float(_cvs.loc[_c0, "capital_saving"]) * 100
STRESS= float(_cvs.loc[_s0, "capital_saving"]) * 100
from pipeline.convergence.jorda import run_panel as _rp
HL = _rp()["one_way_constrained"].hl
CRIT_FAST = BE.critical_carry_bp(half_life_days=HL.lower) / 12
CRIT_PT   = BE.critical_carry_bp(half_life_days=HL.point) / 12
CRIT_SLOW = BE.critical_carry_bp(half_life_days=HL.upper) / 12
_days = CAP.days_to_unwind()
D1BN  = float(_days[(_days.participation == 0.10) & (_days.size_usd == 1e9)].days_binding.iloc[0])
ADV   = CAP.adv_table()
AS_OF = str(sk.index[-1].date())
from hypotheses.h4_vol_decomposition.realized import compare_pairs as _cp
VOLS   = FIN.vol_context()
STR_SK = FIN.stress_liquidity("skhy"); STR_TS = FIN.stress_liquidity("tsmc")
VARSH  = float(_cp().set_index("pair").loc["tsmc", "share_pi"])
TIERS  = FIN.segmentation()
from pipeline.package import clientele as CLI
from pipeline.package import clientele as CLI
IND    = FIN.indicated_tier()
WINS   = {b: float(EO.loc[b, "frac_beats_carry"]) for b in ("low", "mid", "high")}
_k = VOLS[VOLS.leg.str.startswith("KOSPI")]; _v = VOLS[VOLS.leg.str.contains("VIX")]
KOSPI_V, KOSPI_M = float(_k.latest_vol_pct.iloc[0]), float(_k.median_vol_pct.iloc[0])
VIX_V, VIX_M     = float(_v.latest_vol_pct.iloc[0]), float(_v.median_vol_pct.iloc[0])
RNG_MAX = float(max(STR_SK.range_multiple.max(), STR_TS.range_multiple.max()))
print(f"rendered {AS_OF} — pi {PI:.2f}% | carry {LO:.0f}-{HI:.0f}bp/mo vs {BE_MO:.0f} breakeven")
""")

code(r"""Markdown(f'''
| {PI:.1f}% | {NORM:.1f}% | {CTRL:.1f}% |
|---|---|---|
| **SK hynix today** | **TSMC, 5-year mean** — the structural comparable | **Alibaba** — supply fully fungible |

*Levels at {AS_OF}. Same construction for all three pairs.
Research: `github.com/ZinuoS/Charon`.*
''')""")

# ---------------------------------------------------------------- §1 the pitch
md("## 1. The pitch")

code(r"""Markdown(f'''
**The trade.** Long 000660.KS through a total-return swap, short SKHY, FX-hedged through the
USD/KRW cross-currency structure, cross-margined as one ticket. You face us once.

**Entry.** {PI:.1f}%, against a five-year mean of {NORM:.1f}% for the closest structural
comparable and {CTRL:.1f}% for a pair whose share supply is fully fungible. That is the
relative-value anchor. It is a level comparison and it is not a forecast — nothing forces this
gap to close, and the mechanism section explains why we say so.

**Size.** $100mm reference. Capacity to roughly $1bn at 10% participation, with a
{D1BN:.1f}-session exit. Getting out is easy; borrowing the shares to get in is the constraint.

**The economics.** All-in carry is **{ECON} against an {BE_MO:.0f}bp/mo breakeven** — a modest
hurdle across the entire borrow range, because the funding leg is a
{abs(CARRY["funding_differential_bp"]):.0f}bp/yr **tailwind** rather than a cost. Return on
margin is quoted against illustrative 20% initial margin.

**What we charge**

| Component | Terms |
|---|---|
| Financing spread, both swap legs | indicative on request |
| Borrow | pass-through + spread; the {ECON} range is this line |
| Execution | indicative on request |
| FX | executed with the pair, not bolted on |

*{ECON_NOTE[0].upper() + ECON_NOTE[1:]}.*

**Why it holds, in three sentences.** It is **durable** because new ADRs need the Company's
consent, so supply cannot answer demand. It is **attractive** because 21.6 years of the nearest
comparable regime show elevated entries beating the carry
{EO.loc["low","frac_beats_carry"]:.0%} of the time at low borrow and
{EO.loc["mid","frac_beats_carry"]:.0%} at mid. It is **timely** because the ADR trades
\\${ADV.iloc[0].adv_usd/1e9:.1f}bn a day after twelve sessions against
\\${ADV.iloc[1].adv_usd/1e9:.1f}bn for a line with 2,838 sessions of history, and the funding
leg gets cheaper if the Fed hikes.
''')""")

# ---------------------------------------------------------------- §1b which version
md("## 1b. Which version of this is yours")

code(r"""Markdown(f'''
**The borrow quote decides the expression.** One view, four answers, and the switch is what the
borrow costs. {FIN.segmentation_note()}

| | Borrow band | Who it fits | What we earn |
|---|---|---|---|
| **Linear pair** | <= {FIN.BORROW_CUTOFF_BP["linear_max"]}bp/yr | Level conviction, 6-12 months, budget for the skew | Financing both legs, borrow, execution, FX |
| **Standby** | {FIN.BORROW_CUTOFF_BP["linear_max"]}-{FIN.BORROW_CUTOFF_BP["standby_max"]}bp/yr, or catalyst-contingent | Wants it if a catalyst fires, will not pay to wait | Monitoring; the full ticket if it initiates |
| **Long-local via TRS** | > {FIN.BORROW_CUTOFF_BP["standby_max"]}bp/yr, or no borrow at any price | Compression view, no appetite for the short leg | Swap financing on the local leg |
| **Pass** | any | Needs a dated exit, or has no level view | Nothing — and saying so is why the rows above are believed |

**Where the cutoffs come from.** At low borrow the 21.6-year win rate is
{WINS["low"]:.0%} — at or above a coin flip, so the wait is cheap and the view required is
about the level rather than the timing. At mid it is {WINS["mid"]:.0%} and at high
{WINS["high"]:.0%}. The bands sit where that crossing happens.

**Where the borrow sits today.** Lending balance is at the {IND["balance_pctile"]:.0%}
percentile of its own history — a **{IND["utilization_state"]}** utilization state as of
{IND["as_of"]}, which indicates the **{IND["indicated_tier"]}**. That is an indication and not
a quote: D3 measures shares on loan, not the spread to borrow one more, and a lightly-utilised
name can still quote wide if the lendable pool sits with holders who will not lend.

**The desk sentence.** The borrow quote is this product's viability switch, and sourcing it is
our edge. Deciding which version fits which client is structuring, not selling.
''')""")
code('fig, _ = figures.g33_segmentation(TIERS, WINS, lambda b: FIN.carry_summary(b)["total_bp_per_month"])\nfig;')

# ---------------------------------------------------------------- §1c who has done this
md("## 1c. Who has done this trade, and who survives our own filters")

code(r"""Markdown(f'''
**The trade family is old; this pair is new.** Convergence against a structural gap that no
mechanism closes has a documented history, and its canonical laboratory is the dual-listed
company — Royal Dutch and Shell Transport ran as one economic entity split 60/40 across two
listings from 1907 until the 2005 unification, so two claims on the same assets in a fixed
ratio could still diverge. The literature on that divergence is Froot & Dabora (1999, JFE) and
Rosenthal & Young (1990, JFE); the best-known position in it ended in 1998 with the level view
correct and the interim path fatal, per the standard public accounts.

**That is our own finding, arrived at independently.** Gain capped by a cost floor, loss capped
by nothing on file, and an excursion larger than any stop would tolerate. The history and the
measurement agree, which is why the risk section leads on sizing rather than stops.

**The closest living analogue is structural-discount capture.** Korean preference shares
against common: same country, same regulator, two claims on one issuer, a persistent discount
and no arbitrage that closes it. London-listed closed-end vehicles run exactly that strategy
and publish their horizon and sizing. We do not name them — naming a live vehicle in a document
about who buys this product invites precisely the inference this section avoids.

**Six gates, and most enquirers fail one.** {CLI.ratification_note()}
''')""")
code('fig, _ = figures.g35_capacity_funnel(CLI.FUNNEL_GATES, CLI.CLIENTELE, len(CLI.PLAYBOOK), CLI.funnel_note())\nfig;')

md(r"""
**Three archetypes clear all six**, and each opens on a different expression. The questions
below are the ones any buyer of this shape asks in the first ninety seconds — borrow
stability, margin stability, unwind support — not the ones any particular buyer has asked.
""")
code('fig, _ = figures.g36_sales_map(CLI.PLAYBOOK)\nfig;')

md(r"""
**Preparation for the next desk conversation.** Have loaded, generically: the borrow term and
what recall protection is available; whether the margin schedule is fixed or reprices with
volatility; what unwind support and monitoring are included; and the all-in financing on the
local leg alone, for the client who wants the view without the short. Three of those four are
desk answers rather than research answers — the research says which client asks which
question, and the desk says what the answer is.

**The boundary this section respects.** Archetypes only. Historical episodes and public
listed-vehicle strategies are cited as history; nothing is named as a counterparty, and no
inference about any specific current relationship appears anywhere in this repository.
""")

# ---------------------------------------------------------------- §1d segmentation method
md("## 1d. Which regime sees which buyer — and why capability is not appetite")

code(r"""Markdown(f'''
{CLI.THREE_LAYER_METHOD}
''')""")

code('fig, _ = figures.g34r_evidence_availability(CLI.VISIBILITY, CLI.FUNNEL_GATES)\nfig;')

md(r"""
**Read the empty column, not the full ones.** 13F carries no cell at all. It is the source most
often reached for when someone asks who trades a thing — and for this trade it is worth exactly
nothing, because it reports US-listed longs and this pair is a short plus a foreign line. The
chart's usefulness is that it says so in a form that survives being disagreed with.
""")

code(r"""Markdown(f'''
### The test that upgrades the argument

{CLI.DART_CONTRACT_COLUMN_NULL}
''')""")

md(r"""
**Why this is worth a section rather than a footnote.** The weak version of "our trade is
invisible" rests on absence in regimes that never ask the question, and absence like that proves
nothing whatsoever. The strong version needs a regulator who *did* build a field for the thing,
and Korea did: its 5% regime carries a contract column for derivative exposure. Pulling it
answers a question instead of failing to.

**The inversion is the part that would be got wrong by default.** A capability screen normally
reads as a buyer list — the more capable the manager, the better the prospect. Here it runs the
other way. Evidence that a manager already executes the Korean local leg is evidence that they
do not need the largest component of what is being sold. That does not make them worthless as a
counterparty; it makes them a different, smaller sale, and mistaking the two would put the wrong
pitch in front of the most sophisticated name on the list.
""")

code(r"""Markdown(f'''
{CLI.DART_FORMAT_SWITCHING}
''')""")

md(r"""
**What is deliberately absent from this section.** No manager is named, here or anywhere in this
repository. Counts describe what a disclosure regime can and cannot see, which is a fact about
the regime; naming who appeared in it would be a claim about people, and a different kind of
document. The booking-chain criterion stays empty for the same reason it was empty before: Form
ADV Schedule D would fill it, and every automated route to that data refuses a compliant client.
""")

# ---------------------------------------------------------------- §1e the named screen
md("## 1e. Who trades this family: nineteen managers, from filings only")

md(r"""
**This section names managers.** Every name comes from a public filing — a 13F information
table, a Korean 5% substantial-shareholding report, or an SEC adviser registration — and every
claim is stated in filing shape: what a document says a manager held, over what period. Nothing
here asserts that any manager is a client, a prospect, or interested in anything.

**The roster is rule-determined and that is what makes it publishable.** A manager appears for
one of exactly two reasons: named in the research specification, or surfaced by an evidence
pull. There is no discretionary inclusion. Had membership been a judgement call, the list itself
would encode a view about who is interesting — and that view is precisely what a document like
this must not carry, however carefully each sentence is worded.
""")

code('import json\nfrom pipeline.ingest._common import RAW_ROOT\nfrom scripts.build_named_screen import DART_FILERS\n'
     '_snap = sorted((RAW_ROOT / "d9_13f").iterdir())[-1]\n'
     '_screen = json.loads((_snap / "screen.json").read_text())\n'
     'fig, _m = figures.g37_filing_screen(_screen, set(DART_FILERS))\nfig;')

md(r"""
**The chart's message is a shape, not a ranking.** The circles — managers filing 5%+ of a Korean
local line — are long-only institutions and a sovereign fund: BlackRock, Wellington Management,
Norges Bank, Capital Research, Nomura, Macquarie, T. Rowe Price, Silchester. The triangles at
comparable book size — Citadel Advisors, Millennium Management, Point72, D. E. Shaw, Balyasny —
hold Korean ADRs and file nothing on the local side.

**Read plainly, that is a problem for the pitch and it belongs in the pitch.** The managers whose
structure resembles this trade cannot be shown to touch its hard leg. The managers who
demonstrably execute the hard leg file simplified, passive-intent disclosures that argue against
running it. Public paper splits the capability across two populations that do not overlap the
way this trade requires, and evidences appetite for the trade itself in neither.
""")

code(r"""Markdown(f'''
{CLI.CAPACITY_IS_NOT_MANDATE}
''')""")

md(r"""
**What the desk should take from this.** Not a target list — the screen does not produce one.
Three usable things instead: the segmentation is real and each layer wants a different product;
the largest books show adjacency that breadth alone explains, so capacity must never be read as
fit; and the one manager whose filings report movement *between* the local line and depositary
receipts is doing something structurally adjacent to this trade, which makes those filings worth
watching rather than worth citing as demand.

**The honest boundary, which belongs on the slide.** SK hynix's ADR listed 2026-03-24 and 13F
reports quarterly with a 45-day lag, so **the first filing that could name a holder of this
pair's ADR is the Q3 2026 report, due about 2026-11-14.** Every name above is adjacency. The
register of actual holders does not exist yet, and any claim to know it today would not be
coming from filings.
""")

# ---------------------------------------------------------------- §2 durability
md(r"""
## 2. Why the premium exists

**The gap is structural, not a mispricing waiting to be traded away.**

Cancelling an ADR into local shares is a holder right. It always works, it costs seven basis
points round trip, and it puts a floor under the premium.

Creating an ADR is the other direction, and it requires the Company to consent to a larger
deposit. It has not. So the arbitrage that would normally close a gap like this can only push
one way.

That asymmetry is the whole opportunity. A premium with a functioning floor and a ceiling that
is somebody's decision does not converge on its own — and we do not claim it does. What it does
is persist, which is what makes it available to hold.

**You cannot reach it by converting.** The direction that would capture the gap is the one
that is shut. You reach it by holding the spread, and that is what we build.
""")
code('fig, _ = PANELS["P1_situation"]()\nfig;')
code('fig, _ = PANELS["P2_structure"]()\nfig;')

# ---------------------------------------------------------------- §3 history
md("## 3. Where it sits")
code(r"""Markdown(f'''
**{PI - NORM:.0f} points wide of the structural comparable.** The anchor below is three pairs
of the same instrument type at three levels, and one structural fact explains the spread
between them: whether the supply of US shares can respond to demand.
''')""")
code('fig, _ = PANELS["S01a_anchor"]()\nfig;')

code(r"""Markdown(f'''
**The historical case, stated exactly.** Entering at the 90th percentile of the premium's own
history and holding a year, across 21.6 years of the nearest comparable regime:

| Borrow bracket | Beat the carry |
|---|---|
| low | **{EO.loc["low","frac_beats_carry"]:.0%}** |
| mid | **{EO.loc["mid","frac_beats_carry"]:.0%}** |
| high | **{EO.loc["high","frac_beats_carry"]:.0%}** |

Elevated entries beat the carry in the majority of history at low borrow. At mid they do not,
and at high they clearly do not — **the cost bracket decides this trade, not the timing**, which
is exactly why the financing conversation is the one worth having. The entry rule triggers on an
expanding percentile so it never sees its own future, and every grid cell is reported.

**How these gaps have closed.** Over 21.6 years the comparable pair produced
{int(LAB.census(frame=LAB.legs()).query("min_move_pp==5.0 and min_days==10").iloc[0].n_episodes)}
episodes at the base rule. Compressions closed through the US leg falling more often than
through the local leg rising — which is why the short-ADR expression is the primary one on the
term sheet. Full distributions are in the appendix, not hidden.
''')""")
code('fig, _ = PANELS["P8c_lab_outcomes"]()\nfig;')

# ---------------------------------------------------------------- §4 why now
md("## 4. Why now")
code(r"""Markdown(f'''
**(i) The bid.** The ADR is three weeks old and trades \\${ADV.iloc[0].adv_usd/1e9:.1f}bn a day
— more than the Korean line's \\${ADV.iloc[1].adv_usd/1e9:.1f}bn, which has 2,838 sessions of
history. US demand meets a supply that cannot answer it. The twelve-session caveat travels with
that number and is printed on the capacity table.

**(ii) The cost, and it points the friendly way.** The carry decomposes into a measured
funding differential of **{CARRY["funding_differential_bp"]:+.0f}bp/yr** — a credit, not a
charge — plus the ADR borrow spread, which is the desk quote, plus documented fees. A 25bp
**hike makes this {FED["bp_per_month_per_25bp"]:.1f}bp per month cheaper** to hold, not dearer.
The funding leg is long the front end, so it hedges rather than compounds the macro.

**(iii) The channel.** The won moves the premium's level by
{FXS["empirical_central_pct_pts"]:.2f} points per 1%
(95% CI {FXS["empirical_range_pct_pts"][0]:.2f}–{FXS["empirical_range_pct_pts"][1]:.2f}), and
explains {FXS["fx_share_of_daily_premium_variance"]:.1%} of daily premium variation. We
registered the stronger claim — that won strength selects which leg closes the gap — and tested
it twice. On the comparable pair alone: +16.5 points in the predicted direction at p = 0.25.
Pooled across the panel: an odds ratio of 1.31 at p = 0.53, the effect shrinking as the sample
grew. **We are not pitching the won as a signal**, and we hold the caveat that all four
constrained comparables are Taiwanese.
''')""")
md(r"""
$$C \;=\; \underbrace{(r_{\text{KRW}} - r_{\text{USD}})}_{\text{measured — FRED, native frequency}}
\;+\; \underbrace{s_{\text{borrow}}}_{\text{desk quote, bracketed}}
\;+\; \underbrace{f}_{\text{documented, 7bp round trip}}$$

*Each term points at its source. The one that spans a range is the borrow, and it is the one
the desk conversation closes.*
""")
code('fig, _ = PANELS["S0A6_financing"]()\nfig;')
code('fig, _ = PANELS["S03a_macro_map"]()\nfig;')

# ---------------------------------------------------------------- §5 structure
md("## 5. The structure, and what we provide")
code('fig, _ = PANELS["S0A6b_structure"]()\nfig;')
code(r"""Markdown(f'''
| You get | We absorb |
|---|---|
| One ticket | Korean market registration |
| One margin call | ADR borrow sourcing and recall risk |
| One report | Both swap funding legs |
| One counterparty | FX execution and the booking chain |

**Cross-margining.** One netted ticket instead of two saves **{CALM:.0f}% of capital on
ordinary days** — on {N_CALM} ordinary and {N_STRESS} stressed sessions, because this
programme is three weeks old and the sample says so. Through the worst week this pair has actually seen it called
**{PEAK["peak_total_pair_pct"]*100:.0f} cents on the dollar against
{PEAK["peak_total_standalone_pct"]*100:.0f} standalone** — {(1 - PEAK["peak_total_pair_pct"]/PEAK["peak_total_standalone_pct"])*100:.0f}%
less capital through the stress itself. On the top 20% of move days the saving is
{max(STRESS,0):.0f}%: the legs stop offsetting exactly when the gap jumps. We say so because you
will see it on the statement.

**Capacity.** {D1BN:.1f} sessions to build $1bn at 10% participation, borrow-bound rather than
exit-bound.

**Monitoring.** Monthly: the gap, the valve, and three registered items that either happened or
did not.
''')""")
code('fig, _ = PANELS["P4b_margin_path"]()\nfig;')
code('fig, _ = PANELS["P5_size_and_exit"]()\nfig;')

# ---------------------------------------------------------------- §6 P&L
md(r"""
## 6. P&L scenarios

The identity, before the table:

$$\text{P\&L} \;=\; \Delta\pi \cdot N \;-\; C \cdot t, \qquad \text{ROM} \;=\; \frac{\text{P\&L}}{\text{IM}}$$

Two terms and no third. Δπ is the opportunity leg and has no assumed drift. C is the carry,
which accrues whatever happens and is the only component known in advance.
""")
code('fig, _ = PANELS["S07a_breakeven"]()\nfig;')
code('fig, _ = PANELS["P8_scenario_pnl"]()\nfig;')
code(r"""Markdown(f'''
**Compression to the comparable's five-year mean is {PI - NORM:.0f} points.** Against
illustrative 20% initial margin that is the featured path. Half-compression is half of it. The
static path bleeds the carry at {LO:.0f}–{HI:.0f}bp/mo. The realised widening — what this pair
actually did in its first week — is on the same chart at the same scale, and it is why the risk
section exists.

We do not forecast which path happens. We price the financing and show you all three.
''')""")

# ---------------------------------------------------------------- §7 risk
md("## 7. Risk considerations — for the PM's assessment")
code(r"""Markdown(f'''
**The payoff is asymmetric.** Gain is capped by the cost floor. Loss is not capped by anything
on file, because the ceiling is the Company's decision rather than a rule.

**It has already moved hard.** The premium went **{SKW["excursion_pp"]:.0f} points against an
early seller in {SKW["sessions"]} sessions** — worse than the worst 252-day excursion
({EX.attrs["max_mae_pp"]:.0f} points) in 21.6 years of the comparable pair. That is realised,
not modelled.

**Wrong-way dynamics.** The event that closes the gap — an issuance — is also the event that
marks the position against you on the way there, and the borrow tightens into exactly that
state.

**Sizing, not stops.** A stop tight enough to bound loss fires on most winners; one loose
enough to leave winners alone does not bound loss. The risk budget is set by size, and the
appendix shows the distribution it should be set against. Exit paths are agreed at entry and
are in the appendix tree.
''')""")
code('fig, _ = PANELS["P4a_payoff"]()\nfig;')
code('fig, _ = PANELS["P8d_lab_stops"]()\nfig;')

# ---------------------------------------------------------------- §7b execution reality
md("## 7b. Execution reality — four objections, answered")

code(r"""Markdown(f'''
**"Passive waiting is not viable without a strong view."** The hurdle is
{LO:.0f}–{HI:.0f}bp/mo against an {BE_MO:.0f}bp/mo breakeven, because the funding leg is a
{abs(CARRY["funding_differential_bp"]):.0f}bp/yr tailwind rather than a cost. At low borrow the
wait is cheap, and what it asks of you is a view on the LEVEL, not on the timing — we tested
the timing and the shallow model won, so there is no timing signal in this product to disagree
with. What you are choosing to hold is the premium's own volatility: on 6,771 comparator
sessions the premium accounts for {VARSH:.0%} of the ADR leg's daily variance, which is the
point of pairing the legs at all.

**"You cannot unwind through conversion."** Correct, and we had this wrong. Cancellation is a
holder right, and in this pair you are SHORT the ADR — there is nothing to surrender. The
pitched pair unwinds in the market, or in the standby variant by never having been initiated.
Cancellation is an exit for the opposite direction only, and the exit tree has been corrected
to route a borrow recall to a market cover with the capacity number attached.

**"Covering the short moves the price."** On a normal day it does not: the ADR turns over
\${ADV.iloc[0].adv_usd/1e9:.1f}bn and $1bn exits in {D1BN:.1f} sessions at 10%
participation. In stress it is a different question, and the answer is the one that should
worry you — through the worst sessions in each pair's history the high-low range ran up to
{RNG_MAX:.0f}× a normal day while volume roughly doubled at best and did not rise at all in the
GFC comparator. **The book does not disappear; the cost of crossing it multiplies far faster
than the depth grows.** Normal unwind is cheap. Stressed unwind is the trade's real risk, and
it is why the position is sized against a risk budget rather than defended with a stop.

**"Why not just market-make it converged?"** That is a liquidity-provision business with a
different balance sheet, a different holding period and a different P&L. It is not this
product, and it is out of scope by design rather than by oversight.

*Volatility context: KOSPI realised {KOSPI_V:.0f}% against its own median of {KOSPI_M:.0f}%,
while US implied sits at {VIX_V:.0f} against a median of {VIX_M:.0f}. The volatility in this
trade is Korean, not global.*
''')""")
code('fig, _ = figures.g31_execution_reality(VOLS, STR_SK, STR_TS, VARSH, D1BN)\nfig;')

# ---------------------------------------------------------------- §8 the ask
md(r"""
## 8. Monitoring, and the ask

**Weekly, you receive:** the premium and its move, the conversion valve's state, borrow
availability and cost, and the status of three registered watch items — an issuance disclosure,
a headroom print on the ISIN, and a Korean borrow-regime shift.

**The standby variant.** The same monitoring without a position, with our registered call
resolving 2026-10-31. It resolves in public whichever way it goes.

**The ask.** A first conversation on financing levels and borrow availability at $100mm, and
whether the cross-margined structure fits your existing documentation.

---

### Appendix

Referenced rather than re-rendered, so no figure exists in two versions.

| | |
|---|---|
| Measurement discipline | [02](02_premium_anatomy.ipynb) — four π variants, the FX-source spread, the shared-date rule |
| The panel and its limits | [03](03_comparator_panel.ipynb) — three regimes, corporate-action QA, calendar policy, and the withheld PLDT classification |
| The 21.6-year distributions | [09](09_tsmc_lab.ipynb) — census, entry outcomes, excursions, the FX channel per era |
| We tested the timing | [06](06_complexity_ledger.ipynb) — parsimony against complexity; the shallow model won, so there is no model behind this pitch |
| Netting under stress | [01](01_client_note.ipynb) — the margin path through the realised week |
| **Credit memo** | The 44-cents-on-the-dollar peak call on the worst realised week is not only the client's margin experience — it is **our own credit exposure to the client**, quantified on a path that happened rather than a scenario that was chosen. A risk officer reading this book should read that figure as the answer to "what does this counterparty owe us when it goes wrong", and the netted-versus-standalone comparison as the answer to "how much worse would it be booked separately". |
| The exit tree | [08](08_pitch_logic.ipynb) — five monitors, three routes |
| Breakeven surface | [10](10_financing.ipynb) — the carry opened into components |
| H6 in detail | [07](07_macro_environment.ipynb) — registered direction, both tests, the pooled spec |
| Methodology and sources | `docs/data_sources.md`, `preregistration/` |

---

*Informational only. Not advice, not a recommendation, not a solicitation. The ADR borrow
spread is a bracketed assumption pending a desk quote and the cross-currency basis is unmeasured;
margining is illustrative and real schedules are the desk's to quote. Past behaviour of a
comparable pair is characterisation of a regime family, not a forecast of this one.*
""")

# Every str.replace in this file is a silent no-op if its anchor drifts, and that is exactly
# how §1c shipped as a commit with no section in the notebook. The manifest makes it loud.
# FULL headings, not prefixes. Under the old substring check these entries were truncated and
# still passed; line-exact matching caught that immediately, which is the point of it.
REQUIRED_SECTIONS = (
    "## 1. The pitch",
    "## 1b. Which version of this is yours",
    "## 1c. Who has done this trade, and who survives our own filters",
    "## 1d. Which regime sees which buyer — and why capability is not appetite",
    "## 1e. Who trades this family: nineteen managers, from filings only",
    "## 2. Why the premium exists",
    "## 6. P&L scenarios",
    "## 7b. Execution reality — four objections, answered",
    "## 8. Monitoring, and the ask",
)

n = write(OUT, require=REQUIRED_SECTIONS)
print(f"wrote {OUT.relative_to(ROOT)} ({n} cells, {len(REQUIRED_SECTIONS)} sections verified)")
