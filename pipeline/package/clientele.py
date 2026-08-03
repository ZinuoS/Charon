"""Who has run this trade family, and who survives this repository's own filters.

TWO HARD RULES, and the second is the one that needs enforcing.

**Archetypes only.** No live fund appears here as a presumed or current client, and no
inference about any specific counterparty appears anywhere in this repository. Historical
episodes and publicly listed vehicles may be named AS HISTORY — that is what a citation is —
but nothing is named as the client. `tests/test_clientele_boundary.py` greps for it.

**Citation confidence is stated, not implied.** Every entry carries a `confidence` field. The
brief that commissioned this asked for "cite what exists; where thin, say thin", and the way
to honour that is a field that can say `thin` rather than prose that quietly omits the
difference. `verified_this_session` records whether the source was actually opened while
writing, because "I know this" and "I checked this" are different claims and only one of them
survives a reader who checks.

THE FUNNEL IS CURATION AND IS MARKED AS SUCH. Six gates, each citing a finding this repository
actually produced. Where a gate rests on a desk convention rather than on a measurement, it
says so — a filter that looks empirical but is not is worse than an admitted heuristic.
"""

from __future__ import annotations

#: RATIFICATION STATUS: RATIFIED 2026-08-03 by the author, all six gates and their
#: thresholds. What was signed is the PLACEMENT, not the evidence: four gates cite
#: measurements this repository produced and those stand on their own, and two are desk
#: conventions that stand on the author's judgement. Signing does not convert the second kind
#: into the first, and the figure keeps drawing them apart.
FUNNEL_RATIFIED: str | None = "2026-08-03"


#: The documented record. `confidence` is one of: canonical | documented | thin.
#: `verified_this_session` is True only where the source was opened while writing this.
CLIENTELE: tuple[dict, ...] = (
    {
        "archetype": "Convergence arbitrage, classical",
        "what_they_did": (
            "Took offsetting positions in two claims on the same cash flows that traded at "
            "persistently different prices, and held for the level rather than the timing. "
            "The canonical laboratory is the dual-listed company: Royal Dutch / Shell "
            "Transport operated as one economic entity split 60/40 between two separately "
            "listed holding companies from 1907 until the 2005 unification, so the two lines "
            "were claims on the same assets in a fixed ratio and could still diverge."
        ),
        "why_it_ended": (
            "The level view was right and the interim path killed the position. This is the "
            "same lesson this repository re-derives on its own pair: gain capped by a cost "
            "floor, loss capped by nothing on file, and an excursion that can exceed anything "
            "a stop would tolerate."
        ),
        "sources": (
            "Froot & Dabora (1999), 'How are stock prices affected by the location of "
            "trade?', Journal of Financial Economics — the standard reference for DLC "
            "mispricing; Rosenthal & Young (1990), JFE, on Royal Dutch/Shell and Unilever; "
            "Lowenstein, 'When Genius Failed' (2000), for the LTCM position and its unwind."
        ),
        "confidence": "canonical",
        "verified_this_session": (
            "PARTIAL. The 60/40 dual-listed structure and its 2005 termination were confirmed "
            "against a public encyclopaedia entry while writing. The price-divergence "
            "literature and the LTCM position were NOT re-read this session and are cited "
            "from the standard public accounts above."
        ),
        "our_evidence": "G4 (payoff asymmetry), G26b (excursion vs stop distances)",
    },
    {
        "archetype": "Structural-discount specialists",
        "what_they_did": (
            "Bought the cheap line of a two-line capital structure where no mechanism forces "
            "the lines together, and held it as a yield-and-discount position rather than as "
            "a convergence bet. Korean preference shares against common are the closest "
            "living analogue to this pair: same country, same regulator, two claims on one "
            "issuer, a persistent discount, and no arbitrage that closes it."
        ),
        "why_it_fits": (
            "This is the revealed preference that matters most, because the shape is "
            "identical to ours: a structural gap that persists precisely because it cannot be "
            "arbitraged, held by someone whose mandate permits owning a discount without a "
            "convergence date."
        ),
        "sources": (
            "London-listed closed-end vehicles specialising in Korean preference shares "
            "publish prospectuses and factsheets describing exactly this strategy. Named "
            "examples are deliberately omitted here: naming a live vehicle in a document "
            "about who buys our product invites the inference this section exists to "
            "prevent."
        ),
        "confidence": "documented",
        "verified_this_session": (
            "NO. The vehicle's own site was unreachable while writing. The archetype is "
            "described from the strategy class rather than from a document opened today, and "
            "that distinction is why this row reads 'documented' and not 'canonical'."
        ),
        "our_evidence": "G1 (the barrier), G29 (the anchor: three levels, one structural cause)",
    },
    {
        "archetype": "Multi-strategy platform pods",
        "what_they_did": (
            "Run tight per-pod drawdown limits with monthly or intra-quarter risk reviews, "
            "and size to a stop rather than to a horizon."
        ),
        "why_it_ends": (
            "Mechanically incompatible, in two sentences. Our own excursion evidence says the "
            "premium moved 36 points against an early seller in three sessions — worse than "
            "the worst 252-day excursion in 21.6 years of the comparator — so a pod-scale "
            "drawdown limit is breached before the thesis has had time to be right or wrong. "
            "And there is no timing edge to shorten the hold: the complexity ledger tested a "
            "forecasting model against a parsimonious one and the shallow model won, so "
            "nothing in this product lets a pod exit early on signal."
        ),
        "sources": "Our own figures; no external citation is needed for a negative fit.",
        "confidence": "documented",
        "verified_this_session": "N/A — the claim rests on this repository's own measurements.",
        "our_evidence": "G26b (excursion), notebook 06 (parsimony beat complexity)",
    },
    {
        "archetype": "EM / macro level-view funds",
        "what_they_did": (
            "Express country- and structure-normalisation views over multi-quarter horizons, "
            "and tolerate mark-to-market paths that a stop-driven book cannot."
        ),
        "why_it_fits": (
            "The horizon matches, and the resolution-channel evidence points at the "
            "expression they can hold without a borrow: a large minority of historical "
            "compressions in the comparator family closed through the LOCAL leg rising rather "
            "than the ADR falling, which is precisely the long-local TRS variant."
        ),
        "sources": "Strategy class described generically; no vehicle named.",
        "confidence": "documented",
        "verified_this_session": "N/A — archetype description, not a factual claim about a firm.",
        "our_evidence": "G25 (resolution channel), the long-local tier of the segmentation",
    },
    {
        "archetype": "Passive / index-adjacent and quant RV",
        "what_they_did": (
            "Hold the ADR because an index does, or trade the spread in small size as one "
            "signal among hundreds."
        ),
        "why_it_ends": (
            "They are price-takers in this name rather than buyers of this product. The "
            "ticket is too small to justify a bespoke booking chain, and the position is a "
            "by-product of a mandate rather than a view on the gap."
        ),
        "sources": "Strategy class described generically.",
        "confidence": "thin",
        "verified_this_session": "NO. Asserted as a market-structure generality, not measured.",
        "our_evidence": "capacity math (a bespoke chain needs a ticket to amortise it)",
    },
    {
        "archetype": "Academic and public work on THIS family",
        "what_they_did": (
            "The A/H premium — mainland versus Hong Kong listings of the same Chinese issuer "
            "— is the most-studied restricted-fungibility premium and the closest large "
            "literature to our object."
        ),
        "why_it_matters": (
            "It establishes that a premium can persist for years under capital controls "
            "without an arbitrage that closes it. What it does NOT do is tell us who held it "
            "in size, which is the question this section is actually asking."
        ),
        "sources": (
            "A substantial A/H premium literature exists. Work specifically on who HOLDS "
            "ADR-versus-local premia in size is thin to absent in public sources."
        ),
        "confidence": "thin",
        "verified_this_session": (
            "NO. No paper was opened while writing this. The row is included because the "
            "brief asked what exists, and the honest answer for the holder question is 'very "
            "little in public' rather than a padded list."
        ),
        "our_evidence": "notebook 09 (our own 21.6-year characterisation stands in for it)",
    },
)


#: The six gates. Each names the finding it rests on, and says when it is a convention.
FUNNEL_GATES: tuple[dict, ...] = (
    {"gate": "Multi-quarter horizon",
     "test": "no redemption fragility inside 6–12 months",
     "cites": "the convergence interval is 211–391 sessions at 95% — the position needs to be "
              "holdable across it",
     "basis": "measured (pipeline.convergence.jorda)",
     "drops": "monthly-liquidity vehicles, pods on quarterly review"},
    {"gate": "Negative-skew tolerance",
     "test": "risk budget at least the size of the realised excursion",
     "cites": "36 points against an early seller in 3 sessions, worse than the worst 252-day "
              "excursion in 21.6 years of the comparator",
     "basis": "measured (pipeline.lab.tsmc.excursions)",
     "drops": "stop-driven books, pod-scale drawdown limits"},
    {"gate": "Booking-chain access",
     "test": "ISDA in place and prime relationship deep enough for a bespoke TRS",
     "cites": "the product IS the booking chain; without it there is no synthetic local leg",
     "basis": "convention — a desk requirement, not a measurement",
     "drops": "long-only without swap documentation, smaller vehicles"},
    {"gate": "Borrow economics",
     "test": "sourced cheap, or willing to drop the short leg entirely",
     "cites": "the trade clears at every borrow level except slow convergence AND expensive "
              "borrow together; above ~600bp/yr the same view is better expressed long-local",
     "basis": "measured (pipeline.package.financing + the ratified segmentation cutoffs)",
     "drops": "anyone needing the linear pair at a borrow they cannot source"},
    {"gate": "Ticket size",
     "test": "USD 100mm ticket; capacity ~USD 1bn at 10% participation",
     "cites": "a bespoke chain has to be amortised over a ticket that justifies it",
     "basis": "convention on the floor, measured on the ceiling (pipeline.package.capacity)",
     "drops": "quant RV in small size, index-adjacent holders"},
    {"gate": "Mandate permits a discount without a date",
     "test": "discount capture allowed, no stop-loss guarantee",
     "cites": "no timing edge is sold — the complexity ledger found the shallow model won, so "
              "there is nothing to promise an exit date on",
     "basis": "measured (notebook 06) plus a mandate convention",
     "drops": "anyone who needs this resolved by a date"},
)


#: Archetypes that clear all six, and how to open with each.
PLAYBOOK: tuple[dict, ...] = (
    {"archetype": "Structural-discount specialist",
     "lead_with": "linear pair, with borrow term and recall protection agreed up front",
     "first_questions": ("How stable is the borrow term, and what happens on recall?",
                         "Is the margin schedule fixed or does it reprice with vol?",
                         "What unwind support and monitoring come with it?"),
     "desk_earns": "financing both legs, borrow spread, execution, FX",
     "why_them": "the only archetype whose mandate is built for holding a discount without a "
                 "convergence date — the shape matches before the pitch starts"},
    {"archetype": "EM / macro level-view fund",
     "lead_with": "long-local TRS — the compression view without paying for the short leg",
     "first_questions": ("What is the all-in financing on the local leg alone?",
                         "How does this sit against my existing Korea exposure?",
                         "What does the unwind look like if the won moves against me?"),
     "desk_earns": "swap financing on the local leg; no borrow, no short",
     "why_them": "horizon fits and the resolution-channel evidence points at their expression"},
    {"archetype": "Borrow-advantaged RV",
     "lead_with": "standby, converting to the linear pair when a catalyst fires",
     "first_questions": ("What exactly triggers initiation, and who decides?",
                         "What does the monitoring cost while I am not in the trade?",
                         "Can I pre-agree the borrow so it is there when I want it?"),
     "desk_earns": "monitoring fee, then the full ticket on initiation",
     "why_them": "they hold the one input the desk cannot manufacture — their own borrow"},
)


def funnel_note() -> str:
    if FUNNEL_RATIFIED:
        return ratification_note()
    return ("Funnel gates PROVISIONAL — four of six rest on measurements in this repository, "
            "two are desk conventions and say so, and where to set each threshold is the "
            "author's judgement to sign.")


def ratification_note() -> str:
    """What the signature covers, which is narrower than what the funnel asserts."""
    if not FUNNEL_RATIFIED:
        return funnel_note()
    n_meas = sum(1 for g in FUNNEL_GATES if g["basis"].startswith("measured"))
    return (f"Gates ratified {FUNNEL_RATIFIED}. The signature covers the PLACEMENT of the "
            f"thresholds. {n_meas} of {len(FUNNEL_GATES)} gates rest on measurements that "
            f"stand without it; {len(FUNNEL_GATES) - n_meas} are desk conventions that rest "
            f"on it. Ratifying a convention does not make it a measurement.")


def survivors() -> list[str]:
    return [p["archetype"] for p in PLAYBOOK]


if __name__ == "__main__":   # the boundary is the thing worth checking
    import re

    blob = " ".join(str(v) for row in (*CLIENTELE, *FUNNEL_GATES, *PLAYBOOK)
                    for v in row.values())
    # No entry may present a named vehicle as a current or presumed counterparty. History is
    # allowed; "our client" is not.
    for pat in (r"\bour client\b", r"\bthe client is\b", r"\bcurrent(ly)? (a )?client\b",
                r"\bprospect(ive)? client\b"):
        assert not re.search(pat, blob, re.I), f"client-identifying language: {pat}"
    assert all(r.get("confidence") in ("canonical", "documented", "thin") for r in CLIENTELE)
    assert all("basis" in g for g in FUNNEL_GATES), "every gate must say what it rests on"
    assert len(FUNNEL_GATES) == 6 and len(PLAYBOOK) == 3
    print(f"ok: {len(CLIENTELE)} archetypes, {len(FUNNEL_GATES)} gates, "
          f"{len(PLAYBOOK)} survivors — {funnel_note()}")


# --------------------------------------------------------------------------------
# The visibility method — what each open source can and cannot see
# --------------------------------------------------------------------------------
#
# ADDED 2026-08-03 after an evidence pass that mostly FAILED, which is why it is worth
# writing down. The failure was structural rather than a matter of effort, and the structure
# is the same fact that makes the product commercially defensible: a swap-financed pair leaves
# no public trace. A competitor cannot copy it from filings, and a buyer cannot be found in
# them either.

#: (source, what it CAN see, what it CANNOT, strength for identifying this trade)
VISIBILITY: tuple[dict, ...] = (
    {"source": "13F", "class": "holdings",
     "sees": "US-listed LONG positions above the reporting threshold, quarterly, 45-day lag",
     "blind": "every short leg, and every non-US-listed line — so both legs of this pair",
     "strength": "none for the pair; useful only as strategy DNA where BOTH legs of some "
                 "other discount trade happen to be US-listed"},
    {"source": "13D / 13G", "class": "beneficial ownership",
     "sees": "5%+ stakes in SEC-registered classes, with intent",
     "blind": "Korean preference shares and KRX lines — not SEC-registered, so the regime "
              "does not reach them",
     "strength": "none here. A full-text screen returned 730 hits on 'Korea' and every one "
                 "was a US-listed issuer"},
    {"source": "N-CSR / N-PORT", "class": "audited portfolio",
     "sees": "the complete book of a US-registered fund, audited, including foreign lines",
     "blind": "anything held outside a registered vehicle — i.e. most of the buyer universe",
     "strength": "STRONGEST where it applies. An audited holdings table is worth more than "
                 "any amount of inference. It found one real instance of the instrument"},
    {"source": "DART 5% filings", "class": "local-leg capacity",
     "sees": "substantial shareholdings in Korean listed names, including by foreign managers; "
             "uniquely, a CONTRACT column that captures contract-based (derivative) holdings, "
             "and stated reasons that distinguish local shares from depositary receipts",
     "blind": "sub-5% positions, and every short leg",
     "strength": "PULLED 2026-08-02, 71 filings across four issuers. It resolved the local-leg "
                 "capability question and, more importantly, returned the decisive negative — "
                 "see DART_CONTRACT_COLUMN_NULL below"},
    {"source": "Form ADV Schedule D", "class": "infrastructure",
     "sees": "regulatory AUM and prime-broker relationships per adviser",
     "blind": "positions of any kind",
     "strength": "the booking-chain criterion from filings rather than assumption. Not pulled"},
    {"source": "prospectus / mandate", "class": "permission",
     "sees": "what a vehicle is ALLOWED to hold, and its redemption terms",
     "blind": "what it actually holds",
     "strength": "strongest for the horizon and mandate criteria, which are permissions "
                 "rather than positions"},
)


#: The 2026-08-02 DART pull, as an aggregate. No holder is named: this module states what the
#: DISCLOSURE REGIME can and cannot see, which is a fact about the regime, not about anyone.
DART_PULL_2026_08_02: dict = {
    "issuers": 4,                    # SK hynix, KT, SK Telecom, Samsung Electronics
    "filings": 71,
    "distinct_reporters": 8,
    "foreign_managers": 5,           # non-domestic institutions holding ≥5% of a KRX line
    "filings_citing_depositary_receipts": 6,
    "reporters_citing_depositary_receipts": 1,
    "reporters_using_the_contract_column": 1,       # a strategic affiliate, not a manager
    "foreign_managers_using_the_contract_column": 0,
    "snapshot": "data/raw/d8_dart/2026-08-02/",
}

#: THE RESULT THAT MATTERS, and it is a negative.
DART_CONTRACT_COLUMN_NULL = (
    "Korea's 5% substantial-shareholding regime has a CONTRACT column (`ctr_stkqy`/`ctr_stkrt`) "
    "that captures contract-based holdings — precisely where swap and derivative exposure would "
    "surface. The column is demonstrably live: one strategic affiliate populates it in all 40 of "
    "its filings, and the contract portion moves visibly across two years. Zero foreign managers "
    "populate it, in any of the four issuers pulled.\n\n"
    "So the swap-financed structure is invisible EVEN IN THE ONE REGIME THAT HAS A FIELD BUILT "
    "TO SEE IT. The earlier version of this argument inferred invisibility from the absence of "
    "US filings, which is weak: absence in a regime that never asks the question proves nothing. "
    "This is the stronger form — a regime that does ask, asked, and got nothing back.\n\n"
    "That single fact carries both halves of the commercial case. A trade a regulator's "
    "purpose-built field cannot see is a trade a competitor cannot reverse-engineer from paper; "
    "it is also a trade whose buyers cannot be found from paper. The moat and the research "
    "obstacle are the same property, observed from opposite sides."
)

#: A second, weaker aggregate finding, recorded because it is testable rather than because it
#: is conclusive.
DART_FORMAT_SWITCHING = (
    "Six of the 71 filings state a reason that mentions depositary receipts (`증권예탁증권`) "
    "alongside local common — and all six fall on the two pairs this repository classifies as "
    "one-way-constrained by Company consent. One of them reports a local sale on-exchange and a "
    "DR purchase off-exchange in the same filing: a format switch between the two legs.\n\n"
    "Read conservatively. Korea's regime aggregates DRs with the underlying shares into a "
    "SINGLE stake, because a DR represents deposited local shares — so dual-format presentation "
    "is what an ordinary long looks like when it sits in both formats, not a long/short. Every "
    "one of these filings is also a simplified report declaring passive investment intent, which "
    "cuts against an arbitrage reading. What the filings establish is CAPABILITY — that managers "
    "operate both formats on the constrained pairs, off-exchange — not that the pair trade is "
    "being run."
)


def visibility_note() -> str:
    """The one-sentence version, for a caption."""
    return ("A swap-financed pair leaves no public trace: 13F sees US-listed longs only, Korean "
            "lines are not SEC-registered so no beneficial-ownership regime reaches them, and "
            "Korea's own 5% regime — which HAS a contract column for derivative exposure — was "
            "pulled and returned zero foreign managers using it. The trade is unobservable to a "
            "competitor and to us alike, and that is one property, not two.")
