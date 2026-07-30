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
| lending utilization state | **UNBLOCKED 2026-07-29** — D3 landed (`skhynix_lending_daily`, 4,095 rows from 2010). Not yet built into M5, and the M6/M5 ablation result is the prior: it must earn its place under identical folds like everything else |
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
