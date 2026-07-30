# M5 — local-leg context feature dictionary

**Status: BUILT, TESTED, CUT.**

## One correction to the spec first

M5 is specified as "000660 deep history". **It cannot be that.** 000660 is SKHY's local leg
and SKHY is forward-test-only (README §8), so a feature computed on it could never enter a
panel fit — exactly one pair would carry it, and that pair is excluded by the validation
layer's own guard.

So M5 is built as the same idea generalised: **each pair's own local leg.** SKHY's version is
computed for scoring and never fitted. That is the only form in which the feature is both
testable and inside the quarantine.

## Built

| feature | definition | source | availability | in model |
|---|---|---|---|---|
| `rv20` | 20-day realized vol of local log returns, annualised | pair's registry `local` series | same-day close, `_STD_LAG` | **no — cut** |
| `dd60` | local close ÷ 60-day rolling max − 1 (drawdown state) | same | same | **no — cut** |

## Dropped from the dictionary before building

| candidate | reason |
|---|---|
| listing-era dummy | **collinear.** Within a pair it is constant over the sample, so the train-only centring in `_oof_predictions` absorbs it entirely. It contributes nothing by construction, not by measurement |
| lending utilization state | **BUILT 2026-07-29, and UN-ABLATABLE.** See below |
| beta / correlation to a Korea proxy | **no index series in-repo.** Logged as a probe; not pulled mid-session |

## Ablation result — cut, and worse than M6

Identical folds, `n` asserted equal on every row (`data/derived/s4/metrics_table.md`):

| | fungible h=60 | constrained h=60 | pooled h=60 |
|---|---|---|---|
| Δr² | **−0.4104** | +0.0039 | −0.0533 |

RMSE worsens and R² falls in almost every cell. M5+M6 together is no better than either
alone, so no interaction is being missed.

## The degenerate-regime case, which M5 actually produced

At h=60 M5 **helps the minority class and hurts the dominant one**: constrained (n≈13,210)
gains Δr² +0.0039 while fungible (n≈23,207) loses 0.41, and the pooled row nets −0.053.

This is the case the design is required to surface rather than bury. Reading only the improved
cell — "M5 helps the constrained regime at the horizon we care about" — would justify keeping a
family that makes the panel measurably worse. It is why the pooled row exists, why it is
labelled, and why the detector that finds this pattern is computed in `scripts/s4_table.py`
rather than left to a reader comparing columns.

## When to revisit

M5 becomes worth rebuilding when there is a question the premium level cannot answer — most
plausibly **when** the barrier binds (a state question) rather than how persistent the premium
is (answered by the table). Utilization states are the strongest candidate and are **no longer gated** — D3 landed
2026-07-29. Building them is the next honest increment, and they go through the same
identical-folds ablation that cut rv20/dd60 and fx_trend20.

## Utilization state — built, and the ablation is vacuous

`pipeline/measurement/utilization.py`. Balance percentile against its own trailing
1,250-session history, terciled, plus net lending flow. Current reading: **16th percentile —
`low`**, net **+1.02m shares** over five sessions.

**It is not an M5 panel feature, and it cannot be one.** D3 covers **000660 only**; 000660 is
SKHY's local leg; SKHY is forward-test-only and never enters a fit. So the family reaches
**zero fitted pairs**.

The ablation was **run rather than skipped**, through the same harness that cut `rv20`/`dd60`
and `fx_trend20`:

| regime | h | Δrmse | Δr² |
|---|---|---|---|
| fungible | 1 | 0.0 | 0.0 |
| fungible | 20 | 0.0 | 0.0 |
| one_way_constrained | 1 | 0.0 | 0.0 |
| one_way_constrained | 20 | 0.0 | 0.0 |
| POOLED | 1 | 0.0 | 0.0 |

**Exactly zero, not approximately.** Toggling a family that reaches no fitted pair cannot move
a metric. That is the finding: not "untested", but "there is no fold structure to test it in".
A non-zero delta would mean the feature was leaking somewhere it should not be, which is why
`tests/test_utilization.py` asserts the zeros rather than the intent.

**Where it earns its place instead.** It is a barrier-state observable, the same kind of thing
H5's headroom monitor is — regime is a rule, binding-ness is a state. Its live consumer is the
financing sheet's `BORROW STATE` line, the public half of a borrow question whose other half
the desk quotes. And the current reading is worth reading carefully: a `low` percentile is
**not reassurance**. It says borrow is plentiful today, on a series that contains no forward
commitment at all — the tenor question against a 220-day holding floor is untouched by it.

## Route to a real ablation — both sources approved, and approval was not the constraint

**Both approved 2026-07-29** (`twse_sbl_available`, `b3_btb_lending`). The ablation still
cannot run, and the reason is worth being exact about because it is not permission:

**TWSE SBL gives the right thing in the wrong shape.**
`https://openapi.twse.com.tw/v1/SBL/TWT96U` returns lendable supply for all four constrained
pairs — 2330 12,248,328 · 2303 61,751,182 · 3711 7,949,964 · 2412 5,885,259 — which is the
*denominator* Korea does not publish, so Taiwanese utilization could be a true ratio rather
than a percentile. But `當日` means today: the payload has four fields and **no date**. It is a
snapshot, so history begins the day capture begins. Capture began **2026-07-30**; one
observation exists.

**59 more sessions to the fold minimum → runnable ≈ 2026-10-26** (business days plus a 6%
allowance for Taiwanese holidays; `lending_readiness()` computes the current count).

**B3 BTB is left unresolved deliberately, and not for budget.** Brazilian utilization without
Taiwanese history would give the feature to the *fungible class alone*, where it is
**confounded with the class label** — an ablation of a variable present in one class and absent
in the other measures the class, not the variable. It is worth landing only once the
constrained side has history.

**What has to happen, in order:** `just snapshot` daily (the capture is perishable — an
uncaptured day is unrecoverable), then when `lending_readiness()["ready"]` includes the
Taiwanese pairs, add them to `_LENDING_COVERAGE` and run `families=("util",)`. A test compares
the hardcoded set against what is landed and fails on divergence, so this does not depend on
anyone remembering.
