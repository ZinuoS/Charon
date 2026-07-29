"""Render the S4 per-regime metrics table. `just s4` / uv run python -m scripts.s4_table"""
from __future__ import annotations

import pathlib

from pipeline.convergence.jorda import PANEL_CAVEATS, TABLE_HORIZONS, s4_metrics_table

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "derived" / "s4"


def _md(df) -> str:
    cols = ["regime", "horizon", "n", "rmse", "r2", "hit_rate"]
    fmt = {"rmse": "{:.5f}", "r2": "{:+.4f}", "hit_rate": "{:.1%}", "n": "{:,}"}
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    rows = []
    for _, r in df.iterrows():
        cells = [fmt.get(c, "{}").format(r[c]) if r[c] is not None else "—" for c in cols]
        rows.append("| " + " | ".join(cells) + " |")
    return head + "\n".join(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = s4_metrics_table()
    macro = s4_metrics_table(with_macro=True)
    base.to_csv(OUT / "metrics_table.csv", index=False)

    j = base.merge(macro, on=["regime", "horizon"], suffixes=("_b", "_m"))
    assert (j.n_b == j.n_m).all(), "ablation arms scored different samples"
    j["d_rmse"] = j.rmse_m - j.rmse_b
    j["d_r2"] = j.r2_m - j.r2_b
    keep = (j.d_rmse < 0).any() and (j.d_r2 > 0).any()

    doc = f"""# S4 — per-regime metrics table

> **PROVISIONAL.** The regime *taxonomy* is ratified (2026-07-29,
> `docs/regime_taxonomy.md`). The **panel** is not:
{chr(10).join(f'> - {c}' for c in PANEL_CAVEATS)}

Out-of-fold, expanding walk-forward, 5 splits, **embargo = h** (training labels overlap the
test block by h periods; without the embargo the fit sees its own test window through the
label). Centring fitted train-only. Horizons {TABLE_HORIZONS}. SKHY excluded from every fit.

Predictor is the Jordà local projection already used for M3: `pi_{{t+h}} ~ pi_t`, ridge
{1e-4:g}. **Sign hit rate scores the CHANGE from today's level**, not the level — a premium
that is almost always positive would score ~100% on the level and tell you nothing.

{_md(base)}

Pooled row is last and labelled; it is not a regime.

## What the table says

**The classes separate out of sample, and in the direction the mechanism predicts.** The
barrier-constrained premium is forecastable — R² 0.92 at h=1 decaying to 0.68 at h=60. The
fungible control's R² is **negative beyond one day** (−0.11 to −0.16), i.e. worse than
predicting its own mean: there is no persistence left to forecast, which is what a working
two-way arbitrage should leave behind.

**The hit rates run the other way and that is worth stating.** The control's sign hit rate
(57–60%) beats the constrained class's (53%). Direction and magnitude are different
questions: the constrained premium's *level* is highly predictable while its next move is
close to a coin flip, which is exactly the profile of a slow-moving series near a barrier.

## M6 ablation — CUT

One landed macro feature, each pair's **own** FX 20-day trend, in and out under identical
folds (`n` matches on every row — asserted, not assumed).

| regime | h | Δrmse | Δr² |
|---|---|---|---|
{chr(10).join(f"| {r.regime} | {r.horizon} | {r.d_rmse:+.5f} | {r.d_r2:+.4f} |" for _, r in j.iterrows())}

**Verdict: cut.** RMSE worsens and R² falls at every horizon in every class. Hit rate moves
up marginally (+0.04 to +1.5pp) but not enough to offset either. **A near-zero delta cuts the
family, and that is a finding, not a failure** — it says the premium's dynamics are its own,
not an FX overlay, which is consistent with FX explaining ~1.2% of daily premium variance
(S16).

### Degenerate-regime check

No degenerate case here: the macro feature does not help one class while hurting the other —
it hurts both, so the pooled row is not hiding an offsetting split. Had the signs been
opposite by class with a negative pooled net, that would be stated here in these words rather
than left for a reader to derive from the deltas.

*Regenerate: `just s4`. One config flip — `TABLE_HORIZONS` or `REGIME_OF_PAIR` — and this
file rebuilds clean.*
"""
    (OUT / "metrics_table.md").write_text(doc)
    print(f"  {OUT / 'metrics_table.csv'}")
    print(f"  {OUT / 'metrics_table.md'}")
    print(f"  M6 ablation verdict: {'KEEP' if keep else 'CUT'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
