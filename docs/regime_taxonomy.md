# Regime taxonomy — ratified

**Status:** RATIFIED 2026-07-29 (S19). Supersedes the PROVISIONAL labels carried since M3.
**Scope:** governs `REGIME_OF_PAIR` in `pipeline/convergence/jorda.py` and every pooled estimate.

---

## 0. Why this needed ratifying

Every M3 result carried `provisional=True` on one honest ground: the regime labels were a
proposal, not a rule. With one pair per class that was unfixable — a "taxonomy" over two
elements is a pair of names, not a classification. S18 and S19 put four pairs in the
constrained class and six in the fungible class, which is the minimum at which a rule can be
stated, applied, and *disagreed with*.

## 1. The classification rule

Applied to a candidate pair, in order. **Every step reads a filing or a regulation. No step
reads a price.**

**Step 1 — Is DR→local cancellation free at holder option?**
If no, the pair is out of scope: this study is about *one-sided* barriers, and a two-sided
block (China A/H, where the lines are expressly not interchangeable) is a different object.

**Step 2 — Can local→DR issuance be effected by an unaffiliated holder at will?**

- **Yes → `fungible`.** Both directions open. Requires an affirmative statement of
  convertibility in the deposit agreement or 20-F, not merely the absence of a prohibition.
- **No → `one_way_constrained`.** Issuance is capped, revolving, or consent-gated.

**Step 3 — Record the sub-type** (documentation, not a separate class):

| sub-type | mechanism | example |
|---|---|---|
| `revolving` | re-issuance permitted only up to prior cancellations | Taiwan (ROC Art. 31); Korea programme caps |
| `consent` | issuance requires the issuer's discretionary permission against an undisclosed level | SK Hynix (F-6 Ex. 99(a)) |
| `hard_cap` | a numeric ceiling in law or regulator permission | Russia pre-2021; Thailand foreign board |

**Step 4 — Exclusions**, on documented corporate actions only, never on how a series looks:
delisting of the DR programme, a share exchange breaking leg comparability, or a ratio change
whose price step does not match the ratio step.

## 2. THE CORRECTION THIS RATIFICATION MAKES

The original taxonomy conflated two different things, and the evidence separates them.

**An exhausted *ownership* limit does not produce a premium. An exhausted *programme* cap
does.** Korea is the natural experiment: KT reports foreign ownership at **49.0% against a
49% statutory ceiling — fully exhausted — and its ADR trades at roughly +1%.** KEPCO's own
20-F lists depositary issuance among the circumstances in which the 40% ceiling may be
*exceeded*. The statutory limit constrains who may hold the shares; it does not constrain the
depositary's ability to issue against them.

So the regime label attaches to the **DR issuance mechanism**, never to a foreign-ownership
cap. A pair whose FOL is exhausted but whose programme cap is slack is `fungible` for the
purposes of this study, whatever its headline ownership figure says.

## 3. Regime is a rule; binding-ness is a state

The second correction, and the reason the constrained class contains pairs at parity.

`one_way_constrained` says the valve is one-directional. It does **not** say the valve is
currently shut. A one-way barrier only binds when demand presses against it — a reflected
process sits at its barrier only when pushed there. Chunghwa Telecom, Ambev's mirror image,
carries the same ROC rule as TSMC and has spent most of its life near parity.

Accordingly:

- **The label** (`REGIME_OF_PAIR`) is the rule. Stable, filing-verifiable, assigned before
  estimation.
- **Binding-ness** is a state variable, observed as `shares on deposit ÷ programme cap`. That
  is what H5 monitors on SKHY, and it is a *quantity*, not a class.

**This ordering is what keeps the design honest.** Classifying on binding-ness would mean
selecting on the premium and then measuring the premium's persistence — a circle. The rule is
observable independently of the outcome, so it can be assigned first and be wrong.

## 4. The ratified assignment

**`one_way_constrained` — 4 pairs, 15,853 obs.** All ROC `revolving`. Primary sources: ROC
華僑及外國人投資證券管理辦法 Art. 31; Regulations Governing the Offering and Issuance of
Overseas Securities by Issuers Art. 14/17; TSMC FY2024 20-F Ex. 2(a)(1); **Chunghwa Telecom
FY2025 20-F**, which states the constraint *and* draws the price conclusion itself.

`tsmc` · `umc` · `ase` (from 2018-05-02) · `cht`
*excluded:* `auo` — NYSE ADS delisting, Form 25 filed 2019-09-20.

**`fungible` — 6 pairs.** Brazil: Resolução Conjunta BCB/CVM nº 13/2024 imposes no quantity
cap on DR issuance. Alibaba: FY2026 20-F states holders "are able to convert these Shares
into ADSs, and vice versa."

`baba` · `vale` · `itub` · `abev` · `pbr` · `ggb`

**Forward-test, never fitted:** `skhy` — `one_way_constrained` / `consent`.

## 5. What would falsify a label

Stated so the taxonomy is refutable rather than merely asserted.

- **A `fungible` pair is misclassified** if its deposit agreement or 20-F is found to gate
  issuance on issuer consent or a quantity cap. *Alibaba carries a latent version of this:*
  its 20-F notes the depositary's books "may from time to time be closed to ADS issuances" —
  universal boilerplate, but the control is not perfectly clean and saying so is cheaper than
  being caught by it.
- **A `one_way_constrained` pair is misclassified** if an unaffiliated holder is documented to
  have deposited local shares and received new DRs without issuer involvement or headroom.
- **The taxonomy as a whole fails** if the two classes do not separate on persistence. They do,
  by a wide margin — but that is a *test result*, not a definition, and it is reported as one.

## 6. What remains provisional after this

Ratifying the labels does not ratify the panel. Both of these stay flagged wherever the pooled
estimate appears:

1. **One regulator on the constrained side.** Four pairs, one ROC rule. They reduce
   *issuer*-idiosyncratic noise and give no independent variation in the *rule*.
2. **One country on the control side.** Five of six fungible pairs are Brazilian.

Neither is fixed by relabelling; both need a pair from another jurisdiction. India was the
obvious candidate on both counts and is ruled out twice over — every NSE/BSE symbol 404s on
this entitlement, and its headroom regime was repealed effective 2014-12-15, so the modern
series is not the regime under study. The strongest remaining candidates are **Russia/MTS**
(2003–Feb 2022, with a pre-announced cap abolition on 2021-11-28 as a within-name experiment)
and the **Thai foreign/local board**, which is structurally the cleanest one-way regime found
anywhere but has no US DR.

---

## 2026-08-02 — `kt` (KT Corporation) added to `one_way_constrained` (amendment 004)

**Subtype: `consent`** — a statutory foreign-ownership ceiling with a depositary-consent
gate, and the consent gate is what makes it one-way. Distinct from
the Taiwanese pairs, whose constraint is a revolving-facility ratio, and closer in kind to SK
Hynix's own discretionary-consent structure.

Classified from KT's Form 20-F for FY2025 (filed 2026-04-29), on three findings and none of
them a price:

1. The Telecommunications Business Act caps aggregate foreign shareholding at **49.0%**
   *"including equivalent securities with voting rights, e.g., depositary certificates"* — ADRs
   count against the ceiling.
2. **49.0% was foreign-held at 2025-12-31.** The ceiling is fully utilised: it binds now.
3. The deposit agreement: the depositary *"cannot accept deposits of shares and deliver ADSs
   ... unless (1) we have consented"*. Withdrawal always works; re-deposit requires consent.

**What its arrival changed, and it is not small.** The pooled constrained-class half-life had an
OPEN upper tail on four Taiwanese pairs: point 310 days, lower bound 217, no finite upper. With
KT the interval closes — **point 302 days, 95% interval 211–391**. The open tail was a property
of a four-pair, single-jurisdiction panel, and one pair from a different regulator bounded it.

**The caveat that belongs with it.** KT's ceiling is *fully utilised* while SK Hynix's is a
discretionary consent with no published level. They are the same SHAPE of rule in different
STATES, and pooling across that difference is what closed the interval. A reader who cares
about the open tail should read the four-pair estimate as the SKHY-relevant one and this
five-pair estimate as the better-identified one; they answer slightly different questions.

**SK Telecom is NOT classified.** Its filing confirms the same statute, but its own
deposit-agreement consent clause and utilisation were not located. The statute is necessary and
the deposit agreement is what makes the channel one-way.

---

## 2026-08-03 — `skm` (SK Telecom) added to `one_way_constrained` (amendment 005)

**Subtype: `consent`.** Amendment 004 withheld this pair because only the statute had been
located, not SK Telecom's own deposit-agreement clause — the statute is necessary and the
deposit agreement is what makes the channel one-way. The clause has now been read and it is
**more explicit than KT's**:

> "under the terms of the deposit agreement, as amended, **the depositary bank is required to
> obtain our prior consent** to any such deposit if, after giving effect to such deposit, the
> total number of our common shares represented by ADSs exceeds a specified maximum"

> "**It is possible that we may not give the consent.** Consequently, an investor who has
> surrendered his or her ADSs and withdrawn the underlying shares may not be allowed to
> deposit the shares again to obtain ADSs."

Two further blocking conditions are disclosed: a Company determination to block a deposit to
prevent a violation, and any depositor identified as holding at least **4.0%** of the common
shares.

**Weaker than KT in one specific respect, and it is recorded rather than smoothed over.** KT's
filing states 49.0% foreign-held against a 49.0% cap, so its ceiling demonstrably BINDS. No
equivalent utilisation figure was located for SK Telecom. The regime is classified on the
rule; the state is unknown.

**The sample restriction stands and is a different object.** `sample_start = 2022-01-01`
because the implied ADR ratio steps ~13x across 2021–22. Lifting it would not add history, it
would add wrong history.

**And it behaves like a control on its own sample, which is coherent rather than alarming.**
SK Telecom's individual half-life comes back `sub_resolution` — rho_1 already below one half at
the first horizon, so the series does not persist at daily resolution and the estimator returns
a floor rather than a finding. `baba` carries the same flag in the fungible class.

That is what the rule/state distinction predicts. SKM is constrained by RULE and its ceiling is
**not known to bind**; a non-binding constraint should produce control-like dynamics. The
taxonomy classifies the regime and does not promise that every member is currently constrained.
It also means SKM contributes nothing to the dynamics claim, and the non-circularity test now
excludes sub-resolution pairs from that comparison symmetrically in both classes — an
unresolvable half-life is not a fast one.

**Effect on the pooled estimate: negligible.** Six pairs give a half-life point of 302.3d
(211–392) against five pairs at 302.4d (211–391). SKM contributes 1,073 post-restriction
sessions against the class's ~25,000, so it changes the classification of the pair without
changing what the class measures.
