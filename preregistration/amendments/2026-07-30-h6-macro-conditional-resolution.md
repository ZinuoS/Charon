# Amendment 002 — H6, the macro-conditional resolution channel

**Status: STAGED FOR THE AUTHOR.** `preregistration/calls.yaml` is author-reserved and
append-only after the 2026-07-29 freeze. This file states the amendment; the author pastes
the three fields into `calls.yaml`. It is committed **before any H6 result exists**, and the
git history is the evidence for that claim: this commit contains the direction and no
numbers, and the commit that carries results comes after it. Direction frozen first, checked
second, in that order and verifiably.

**Date:** 2026-07-30
**Freeze class:** C (registered call)
**What was already observed at the time of this amendment**, stated because the amendment
rule requires it: the TSMC lab has run and its unconditional resolution-channel split is
known — 43.7% of compressions closed via the local leg and 56.3% via the ADR leg falling, at
the 5pp/10d base rule over 5,064 sessions. The FX **level** sensitivity is known (0.856
premium points per 1% currency move, 95% CI 0.653–1.058, R² 1.3%). What is **not** observed,
and what H6 is about, is whether that channel split **conditions on the currency state**. No
conditional split has been computed, on any pair, at the time of this commit.

---

## The three fields for `calls.yaml`

```yaml
# ------------------------------------------------------------------------------
# H6 — Macro-conditional resolution channel (registered 2026-07-30, amendment 002)
# ------------------------------------------------------------------------------
h6_macro_conditional_resolution:
  statement: >-
    The LEG through which a premium compression episode resolves is conditional on the
    currency state. Episodes are identified by the pipeline.lab.tsmc reversal walk; the
    resolving leg is assigned by the exact log decomposition
    d log(1+pi) = d log ADR + d log FX - d log LOCAL; the currency state is classified
    from the M6 trend features on the pair's own FX leg over the episode window.
  direction: >-
    In LOCAL-CURRENCY-STRENGTH states, compression episodes are disproportionately
    LOCAL-LEG-LED relative to the unconditional 43.7% base rate. In
    LOCAL-CURRENCY-WEAKNESS states, episodes are disproportionately ADR-LED or
    NON-RESOLVING relative to their base rates. Direction fixed 2026-07-30 before any
    conditional split was computed.
  threshold: >-
    The local-leg share of compressions in strength states exceeds the local-leg share in
    weakness states by at least 10 percentage points, with the difference surviving a
    two-proportion test at the 5% level on the TSM/TWD deep sample.
  resolution_date: "2026-10-31"
  resolution_criterion: >-
    Computed on the D6 comparator panel, TSM/TWD deep history first (2005-01-03 onward).
    SKHY is scored DESCRIPTIVELY alongside and never enters the test — it is the forward
    test instrument. Every FX state is reported including states with too few episodes to
    test, and a null is a deliverable: if the conditional split does not separate, the
    figure becomes the states-tested-no-pattern chart and says so in its headline.
  freeze_class: C
  data_requirements:
    - D6   # comparator panel premium series and their FX legs
    - D2   # FX series for the state classification
  known_limitations: >-
    TSMC's conversion facility REVOLVES and SK Hynix's does not, so a conditional pattern
    measured on TSM describes the two-sided variant of the family. The TWD is a managed
    float and the won is not, which should DAMPEN any currency-conditional effect in the
    lab relative to the traded pair — so a null on TSM is weaker evidence against the
    conditional than a positive is for it, and that asymmetry is reported wherever the
    result is.
```

## Why this is registered rather than exploratory

H6 is the hypothesis that turns the catalysts slide from a list into an argument: it would
say not merely that the local leg sometimes closes the gap, but *when*. A finding of that
shape is exactly the kind that a reader is right to suspect was chosen after the fact. The
only answer to that suspicion is a timestamp that precedes the result, which is what this
file is.

---

## RESULT — added 2026-07-30, after the registration commit

**Verdict: NULL.** The registered threshold required BOTH a gap of at least 10 points AND
p < 0.05. One cleared and one did not.

| currency state at episode start | compressions | closed by local leg | closed by US leg |
|---|---|---|---|
| local currency STRENGTH | 23 | **56.5%** | 43.5% |
| flat | 23 | 34.8% | 65.2% |
| local currency WEAKNESS | 25 | **40.0%** | 60.0% |

Unconditional local-leg share across all 137 episodes: 43.7%.

**Gap: +16.5 points, in the registered direction.** Threshold on the gap was 10 points, so
that leg cleared. **p = 0.25** on the two-proportion test, z = 1.14. Threshold on
significance was 0.05, so that leg did not. The call is NULL.

**This is what the registration was for.** Unregistered, this result reads as "57% versus
40% — the currency state predicts which leg closes the gap", and it would have been the
headline of the macro chapter. It is a coin-flip-grade separation on 23 and 25 observations
wearing a conclusion's clothes. The direction was frozen in a commit that contains no
numbers, and the commit carrying these numbers comes after it; anyone can check the order.

**What it does not license.** The pitch does not use the currency state as a signal, and G30
says so on its face. SK Hynix currently sits in a local-currency-strength state (KRW +5.9%
over 20 sessions to 2026-07-28). That is DESCRIPTIVE placement on a map the test could not
draw, and quoting it as support would be exactly the error the registration exists to
prevent.

**What would settle it.** More episodes, which means more constrained pairs in the panel
rather than a longer TSM history — the 21.6 years is already spent. The three landed Taiwan
comparators (UMC, ASE, CHT) and the five Brazilian ones are candidates; pooling them needs a
within-pair demeaning step and a decision about whether the currency state is pair-specific
or regional, neither of which is registered. That is a next session, not a footnote.
