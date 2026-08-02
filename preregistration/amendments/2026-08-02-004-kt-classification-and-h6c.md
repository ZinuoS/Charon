# Amendment 004 — KT's classification, and the H6c third look it would license

**Status: DRAFTED FOR THE AUTHOR'S SIGNATURE. Nothing in it has been applied.** `kt` is not in
`REGIME_OF_PAIR`, enters no fit or test, and the H6c spec below has not been run. Two separate
things need signing and they can be signed separately.

---

## Part A — KT Corporation is `one_way_constrained` on the rule

Read from KT's Form 20-F for FY2025, filed 2026-04-29
(`sec.gov/Archives/edgar/data/892450/000162828026028096/kt-20251231.htm`). Three findings, and
the third is the one that matters.

**1. The ceiling exists, is statutory, and counts ADRs.**

> "The Telecommunications Business Act limits the maximum aggregate foreign shareholding in us
> to 49.0% of our total issued and outstanding Shares with voting rights (**including
> equivalent securities with voting rights, e.g., depositary certificates** and certain other
> equity interests)."

Depositary certificates are inside the cap. An ADR is not a way around this ceiling; it is
counted against it.

**2. The ceiling is fully utilised. This is a state, and the state is BINDING.**

> "As of December 31, 2025, **49.0% of our common shares were owned by foreign investors**."

49.0 against a 49.0 limit. Not "approaching", not "could bind" — at it, as of the last fiscal
year end.

**3. The conversion channel is one-way, and it is the same contractual clause as SK Hynix's.**

Risk-factor heading, verbatim:

> "**If an investor surrenders his American Depositary Shares ('ADSs') to withdraw the
> underlying shares, he may not be allowed to deposit the shares again to obtain ADSs.**"

And the mechanism:

> "under our deposit agreement, **the depositary bank cannot accept deposits of shares and
> deliver ADSs** representing those shares **unless (1) we have consented** to such deposit or
> (2) Korean counsel has advised the depositary bank that the consent required under (1) is no
> longer required under Korean laws and regulations."

> "the depositary bank is **required to obtain our prior consent** for the number of shares to
> be deposited in any given proposed deposit which exceeds the difference between (1) the
> aggregate number of shares deposited by us or with our consent..."

**Withdrawal always works. Re-deposit requires the Company's consent.** That is the definition
this repository uses for `one_way_constrained`, and it is the same clause family as SK Hynix's
F-6 Ex. 99(a) undertaking — not an analogy to it.

**Proposed:** add `"kt": "one_way_constrained"` to `REGIME_OF_PAIR`. 6,449 joined sessions,
1999-05-26 to 2026-07-31, ratio 0.5 empirically stable (median 0.504, no annual median outside
0.50–0.58).

**Why this is worth signing.** It is the first constrained pair outside Taiwan. The four
existing ones share one regulator, one currency and one market structure, so they are not four
independent draws on the RULE — a limitation stated on G31 and inherited by every pooled
constrained-class estimate in the repository. KT is a different regulator under a different
statute, and it carries the same currency and supervisor as the traded instrument.

**What is NOT claimed.** The premium's behaviour played no part in this classification and is
not offered as evidence for it. KT's premium averages +3.01% over 27 years with episodes to
+30%; that is consistent with the classification and would have been the wrong reason for it.
Regime is a rule; binding-ness is a state; the filing establishes both independently of price.

### SK Telecom is NOT proposed, and the distinction is deliberate

SKM's 20-F confirms the same statutory ceiling —

> "The Telecommunications Business Act currently sets a 49.0% limit on the aggregate foreign
> ownership of our issued shares."

— but the searches did **not** locate SKM's own deposit-agreement consent clause or its
current foreign-ownership utilisation in the sections read. The taxonomy classifies on the
ISSUER's conversion mechanics, not on the statute alone: the statute is necessary and the
deposit agreement is what makes the channel one-way. **SKM stays withheld** until its clause is
read. Its sample is also restricted to 1,073 post-2022 sessions by a ratio-regime break, so it
would add little even if classified.

---

## Part B — H6c, the third look, IF Part A is signed

**The already-signed H6b spec does not cover this and must not be stretched to.** H6b fixed its
primary as "constrained class (**tsmc, umc, ase, cht**)" — an explicit list, frozen before the
run. Adding a fifth pair changes the primary's membership, so re-running H6b with KT in it
would be improvising against a signed spec. Hence a separate registration.

**This would be the THIRD look at one hypothesis.** H6 nulled on TSM alone (+16.5pp, p=0.25).
H6b nulled pooled (OR 1.31, p=0.53 primary), and the effect ATTENUATED toward 1 as the sample
grew — the shape of a noise result under replication. A third look needs a reason better than
"more data arrived", and it has exactly one: **KT is the first observation of this hypothesis
under a different regulator.** H6 and H6b were, in effect, one jurisdiction asked twice.

```yaml
h6c_kt_extended_pooled:
  statement: >-
    The leg through which a premium compression episode resolves is conditional on the
    currency state, tested across the constrained class WITH a non-Taiwanese member.
  direction: >-
    UNCHANGED from H6 and H6b, and fixed before this test is written: compressions are
    disproportionately LOCAL-LEG-LED in local-currency-STRENGTH states relative to WEAKNESS
    states. A pooled odds ratio ABOVE 1 is the registered direction.
  design: >-
    Identical to H6b in every respect except membership: same reversal walk (5pp, 10d), same
    log-decomposition channel assignment, same within-pair FX-state terciles read at the
    episode's first session, same Mantel-Haenszel stratification by pair. Primary adds `kt` to
    the four Taiwanese pairs. A SECOND primary is reported alongside and is the one that
    carries the interest: KT ALONE, since it is the only independent draw on the rule.
  threshold: >-
    Pooled MH odds ratio > 1 AND p < 0.0167 on the extended primary. The 0.0167 is Bonferroni
    for THREE looks at one hypothesis; 0.05 and 0.025 are both spent. A result between 0.0167
    and 0.05 is reported as insufficient and is not described as suggestive.
  resolution_date: "2026-10-31"
  resolution_criterion: >-
    Both the extended-primary and the KT-alone results are computed and reported regardless of
    which reads better, with every pair's own 2x2 shown. If KT alone points opposite to the
    Taiwanese pairs, that is the finding and it is reported as the headline rather than
    diluted by pooling.
  freeze_class: C
  known_limitations: >-
    One non-Taiwanese pair is one, not many. KT breaks the jurisdiction monopoly; it does not
    make the class well-identified. And KT's ceiling is fully utilised while SK Hynix's
    constraint is a discretionary consent with no published level, so the two are the same
    SHAPE of rule in different states.
```

**If Part A is signed and Part B is not, nothing runs** — KT simply joins the class for
description, and the H6 line in the macro chapter stands as it is today.
