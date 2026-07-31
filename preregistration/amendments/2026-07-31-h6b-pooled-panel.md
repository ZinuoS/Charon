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
