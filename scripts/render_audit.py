"""Render every G-figure to data/derived/audit/ for the viewing pass (docs/figure_audit.md).

Deliberately separate from the notebooks: an audit render must be reproducible without
executing a notebook, so a defect can be re-checked in one command.
"""
from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")

from execution.costs import margin_stress, summary_table
from pipeline.convergence.jorda import REGIME_OF_PAIR, estimate_regime, run_panel
from pipeline.hedging.sheets import all_sheets
from pipeline.measurement.premium import build_all_variants
from pipeline.viz import figures, theme

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "derived" / "audit"


def main() -> int:
    theme.apply()
    OUT.mkdir(parents=True, exist_ok=True)
    sk = build_all_variants("skhy")[0]
    tsm = build_all_variants("tsmc")[0]
    res = run_panel()
    rows = [{"pair": p, "regime": r,
             "mean": float(build_all_variants(p)[0].series.mean()),
             "half_life": estimate_regime([build_all_variants(p)[0].series], r).hl.point}
            for p, r in REGIME_OF_PAIR.items()]
    jobs = {
        "g1_barrier_anatomy": lambda: figures.g1_barrier_anatomy(
            sk.series, theme.events_for(markets=["US", "KR"])),
        "g2_plumbing_map": figures.g2_plumbing_map,
        "g4_asymmetry": lambda: figures.g4_asymmetry(tsm.series, sk.series),
        "g9_cost_and_skew": lambda: figures.g9_cost_and_skew(
            summary_table().to_dict("records"), margin_stress()),
        "g_convergence": lambda: figures.g_convergence(res),
        "g10_expression_readiness": lambda: figures.g10_expression_readiness(
            all_sheets(sk.series.iloc[-1], "headroom 0")),
        "g11_taxonomy_separation": lambda: figures.g11_taxonomy_separation(rows),
    }
    for name, fn in jobs.items():
        fig, _ = fn()
        fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight")
        print(f"  {name}")
    print(f"\n{len(jobs)} figures -> {OUT}")
    verdicts = figures.ten_second_test()
    print(f"ten-second test: {sum(verdicts.values())}/{len(verdicts)} carry layman bullets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
