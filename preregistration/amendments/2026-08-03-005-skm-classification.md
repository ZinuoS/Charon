# Amendment 005 — SK Telecom is `one_way_constrained` on the filing

**Status: SIGNED BY THE AUTHOR 2026-08-03 on instruction.** Applied: `skm` is added to
`REGIME_OF_PAIR` with subtype `consent`.

Amendment 004 withheld this classification because SKM's own deposit-agreement clause had not
been located — only the statute. The statute is necessary and the deposit agreement is what
makes the channel one-way, so withholding was correct at the time. The clause has now been
read.

## The evidence, from SK Telecom's Form 20-F for FY2025 (filed 2026-04-29)

**The risk-factor heading is the same sentence KT and SK Hynix carry:**

> "If an investor surrenders his or her ADSs to withdraw the underlying shares, **he or she
> may not be allowed to deposit the shares again to obtain ADSs**."

**The consent requirement, from the deposit agreement:**

> "under the terms of the deposit agreement, as amended, **the depositary bank is required to
> obtain our prior consent** to any such deposit if, after giving effect to such deposit, the
> total number of our common shares represented by ADSs **exceeds a specified maximum**,
> subject to adjustment under certain circumstances."

**The Korean-law overlay, which names the reference level:**

> "Under current Korean laws and regulations, the depositary is required to obtain our prior
> consent for any proposed deposit of common shares **if the number of shares to be deposited
> in such proposed deposit exceeds the number of common shares initially deposited by us** for
> the issuance of ADSs (including deposits in connection with the initial and all subsequent
> issuances of ADSs by us or with our consent...)."

**And the sentence that settles it — the Company stating its own discretion:**

> "**It is possible that we may not give the consent.** Consequently, an investor who has
> surrendered his or her ADSs and withdrawn the underlying shares may not be allowed to deposit
> the shares again to obtain ADSs."

Two further blocking conditions are disclosed: the depositary may refuse a deposit where the
Company has determined it should be blocked to prevent a violation, or where the depositor is
identified as holding **at least 4.0%** of the common shares.

**This is more explicit than KT's.** KT's filing establishes the consent gate; SK Telecom's
adds an unhedged statement that consent may be withheld. Withdrawal always works; re-deposit
requires the Company. That is `one_way_constrained`, subtype `consent`.

## What is established, and what is not

**Established: the RULE.** The classification rests on it and on nothing else — no price
behaviour entered this decision, as required by the taxonomy.

**Not established: the STATE.** KT's filing gave a utilisation figure — 49.0% foreign-held
against a 49.0% cap, so its ceiling demonstrably binds. **No equivalent utilisation figure was
located for SK Telecom.** Regime is a rule and binding-ness is a state; this amendment
classifies the regime and leaves the state unknown, which is a weaker position than KT's and
is recorded as such rather than assumed across.

## The sample restriction is NOT lifted, and it is a different object

`skm` keeps `sample_start = 2022-01-01`. That restriction has nothing to do with
classification: the implied ADR ratio steps from 0.04 to 0.55 across 2021–22, a roughly
thirteen-fold change consistent with the share split plus a depositary ratio change. Carrying a
constant ratio across that step would put a 13x error into every pre-2022 observation — the
ASE failure mode, and a measurement error rather than a policy choice. Lifting it would not
add history; it would add wrong history. It stays until both effective dates are sourced.

Post-restriction the pair has **1,073 sessions from 2022-01-03**.

## H6c is NOT re-run, and its spec does not cover this

H6c's registered primary is "the four Taiwanese pairs **plus `kt`**". Adding a sixth pair
changes membership, exactly as adding KT changed H6b's. Re-running H6c with SKM in it would be
improvising against a signed spec, which the standing instruction forbids. A fourth look would
need its own registration and its own threshold — and would be the fourth look at a hypothesis
that has now nulled three times with the effect reversing under the one independent regulator,
so the case for running it at all is weak and is not made here.
