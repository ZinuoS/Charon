# M6 — macro overlay feature dictionary

**Status: BUILT, TESTED, CUT.** One feature was built, ablated, and dropped. The dictionary
records it because a cut with evidence is worth more than an untried feature list.

| feature | definition | source | availability | in model |
|---|---|---|---|---|
| `fx_trend_20d` | pair's own FX, 20-day return: `fx_t / fx_{t-20} − 1` | the pair's registry `fx` series (`usdtwd`/`usdbrl`/`usdhkd`/`usdkrw`) | same-day close, `_STD_LAG` | **no — cut by ablation** |

**Ablation verdict (`data/derived/s4/metrics_table.md`): cut.** RMSE worsens and R² falls at
every horizon in every class, under identical folds. Consistent with S16's finding that FX
explains ~1.2% of daily premium variance.

**Each pair uses its OWN currency.** The first implementation handed USDKRW to every pair in
the panel including the Brazilian ones — a modelling error, not an approximation.

## Not built, and why

| candidate | reason |
|---|---|
| SGX USDKRW forward slope | not landed. Deferred months are `exchange_marked`, not executable, so the slope would be part quote and part mark |
| US–Korea rate differential | FRED series not landed. Would need a mid-session pull, which the session rule forbids |
| semis proxy | not present in-repo |

These are roadmap items, not blockers. **And the ablation is the reason to be sceptical of
adding them:** the one macro feature that was landed and testable made every metric worse.
The capacity rule (README §6) says a small effective N wants shallow models; the evidence now
agrees with the rule.
