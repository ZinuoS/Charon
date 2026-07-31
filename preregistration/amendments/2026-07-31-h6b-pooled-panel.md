# Amendment 003 — H6b, the pooled-panel test of the macro-conditional resolution channel

**Status: STAGED FOR THE AUTHOR**, same as amendment 002. `calls.yaml` is author-reserved and
append-only; this file states the fields and the author pastes them.

**Committed before the pooled test is written or run.** This commit contains the design and no
pooled numbers. The commit carrying results comes after it, and the order is checkable.

---

## Why this needs its own registration rather than riding on 002

H6 was registered on 2026-07-30 and tested on TSM/TWD alone. **The result is already known and
is stated here in full, because an amendment that hides what motivated it is worse than no
amendment:** the local-leg share of compressions was 56.5% in currency-strength states against
40.0% in weakness states — a gap of **+16.5 points in the registered direction** — at
**p = 0.25** on 23 and 25 episodes. The registered threshold required a ≥10-point gap AND
p < 0.05. The gap cleared. The significance did not.

So this is a **second look at a hypothesis that already failed once**, on more data, motivated
by the direction of the first result. That is the single most common way a pre-registration
gets laundered into a finding, and naming it is the only thing that stops it here.

Three consequences, all binding:

1. **The threshold is stricter, not the same.** Bonferroni for two looks at one hypothesis:
   **p < 0.025**, not 0.05. A result between 0.025 and 0.05 is reported as "would have passed
   a single-look threshold it is not entitled to" and nothing more.
2. **The primary test is fixed before it runs** and is the constrained class alone. The
   secondary is all pairs. Whichever reads better afterwards does not become the headline.
3. **Every pair's own table is reported**, including pairs with too few episodes to test. No
   pair is dropped after seeing its numbers.

---

## The fields for `calls.yaml`

```yaml
# ------------------------------------------------------------------------------
# H6b — Pooled-panel test of the macro-conditional resolution channel
#        (registered 2026-07-31, amendment 003; second look at H6)
# ------------------------------------------------------------------------------
h6b_pooled_macro_conditional:
  statement: >-
    The leg through which a premium compression episode resolves is conditional on the
    currency state, tested across the whole D6 comparator panel rather than on TSM alone.
  direction: >-
    UNCHANGED FROM H6 and fixed before this test was written: compressions are
    disproportionately LOCAL-LEG-LED in local-currency-STRENGTH states relative to
    WEAKNESS states. A pooled odds ratio ABOVE 1 is the registered direction.
  design: >-
    Pairs: every D6 comparator pair with at least 1,000 joined sessions and at least 5
    compression episodes at the base rule. SKHY is excluded — it is the forward-test
    instrument and never enters a fit or a test.
    Episodes: the pipeline.lab.tsmc reversal walk at min_move 5pp, min_days 10, unchanged.
    Channel: the exact log decomposition d log(1+pi) = d log ADR + d log FX - d log LOCAL.
    State: the pair's OWN FX leg, 20-day trailing move, terciles computed WITHIN pair, read
    at the episode's FIRST session — never over the episode, because FX is one of the three
    terms that assigns the channel.
    Test: Mantel-Haenszel stratified by pair on the 2x2 of (strength vs weakness) x
    (local-leg vs ADR-leg). Stratification is what handles between-pair heterogeneity in the
    unconditional channel share; pooling episodes without it would let a pair with many
    episodes and an extreme base rate drive the answer.
  threshold: >-
    Pooled Mantel-Haenszel odds ratio > 1 AND p < 0.025 on the CONSTRAINED-CLASS primary.
    The 0.025 is Bonferroni for a second look at a hypothesis that already failed once at
    p = 0.25 on TSM alone; 0.05 is not available to this test and a result between 0.025
    and 0.05 is reported as insufficient.
  resolution_date: "2026-10-31"
  resolution_criterion: >-
    Primary: constrained class (tsmc, umc, ase, cht). Secondary: all qualifying pairs, with
    the regime split reported. Both are computed and both are reported regardless of which
    reads better. Every pair's own 2x2 is shown including pairs below the episode minimum,
    which are listed as excluded WITH their counts rather than silently omitted.
  freeze_class: C
  known_limitations: >-
    The panel's constrained pairs share one regulator and one currency regime (Taiwan/TWD),
    so they are not four independent draws on the RULE — they reduce issuer-idiosyncratic
    noise and do not provide independent variation in the mechanism. A pooled result across
    them is therefore weaker than its episode count suggests, and that is stated wherever
    the number appears. The fungible pairs are a different regime entirely and are why the
    secondary is secondary.
```

## What would make this worth believing

A pooled odds ratio above 1 at p < 0.025, with the effect visible in most pairs individually
rather than carried by one. If the effect lives in a single pair, the pooled p-value is a
statement about that pair and the notebook will say so.

---

## RESULT — added 2026-07-31, after the registration commit

**Verdict: NULL on both, and the informative part is HOW it nulled.**

| scope | pairs | episodes | pooled odds ratio | p |
|---|---|---|---|---|
| constrained class (**primary**) | 4 | 145 | **1.31** | 0.53 |
| all qualifying pairs (secondary) | 10 | 209 | **1.13** | 0.77 |

Registered threshold was OR > 1 **and** p < 0.025. The odds ratio is above 1 in both — the
registered direction — and neither p comes close.

**The effect attenuated toward 1 as the sample grew.** TSM alone gave a 16.5-point gap; four
constrained pairs give an odds ratio of 1.31; all ten give 1.13. That is the shape of a noise
result under replication, and it is a stronger conclusion than "underpowered": the first
result did not survive more data.

**Per-pair local-leg share, strength versus weakness** — every pair, none dropped:

| pair | regime | strength | weakness | direction |
|---|---|---|---|---|
| tsmc | constrained | 0.565 | 0.400 | **+16.5pp** as registered |
| umc | constrained | 0.400 | 0.348 | +5.2pp as registered |
| ase | constrained | 0.500 | 0.636 | **−13.6pp, OPPOSITE** |
| cht | constrained | 0.643 | 0.571 | +7.2pp as registered |
| baba | fungible | 0.545 | 0.222 | +32.3pp as registered |
| vale | fungible | 0.400 | 0.800 | −40.0pp opposite |
| itub | fungible | 0.500 | 0.600 | −10.0pp opposite |
| abev | fungible | 0.333 | 1.000 | −66.7pp opposite |
| pbr | fungible | 0.500 | 0.667 | −16.7pp opposite |
| ggb | fungible | 0.500 | 0.556 | −5.6pp opposite |

No pair was excluded: every one cleared the 1,000-session and 5-episode minimums fixed before
the run.

**The amendment predicted the diagnostic and it fired.** It said: *"A pooled odds ratio above 1
at p < 0.025, with the effect visible in most pairs individually rather than carried by one. If
the effect lives in a single pair, the pooled p-value is a statement about that pair."* Three of
four constrained pairs point the registered way, but only TSM has a gap of any size and ASE
points the other way. The effect lives in TSM.

**What this closes.** H6 is not "awaiting more data" any more. More data arrived, twice, and
the effect shrank both times. The macro chapter states the currency state as a **level** effect
only — 0.86 premium points per 1% won, 1.3% of daily variance — and makes no channel claim. The
pitch does not use the won as a signal, and now has two registered tests behind that restraint
rather than one.
