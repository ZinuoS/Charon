"""Scenario P&L for the convergence pair — the three paths, net of bracketed carry.

A PM asks two questions the panels so far do not answer together: what do I make, and against
what capital. So every figure here reports P&L in notional AND in units of initial margin,
because return-on-margin is the number a book is run on.

Three paths, all sourced rather than invented:

* **compression** — decay to the cost floor at the estimated base-rate half-life (M3).
* **static** — the premium simply sits there and the carry bleeds, drawn as a FAN across the
  cost bracket, since four of five components are undocumented.
* **widening** — the realised 15.98 -> 51.60 run, replayed, then held.

The breakeven carry (~954bp/yr) is the line the whole trade argues with, so it is drawn.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.package.breakeven import CARRY_BRACKET_BP, FLOOR, carry_bp, critical_carry_bp


def paths(pi_0: float = 0.226, horizon_days: int = 252, half_life: float | None = None
          ) -> pd.DataFrame:
    """Premium level under each path, one row per session."""
    from pipeline.convergence.jorda import run_panel
    from pipeline.measurement.premium import build_all_variants
    H = half_life or run_panel()["one_way_constrained"].hl.point
    t = np.arange(horizon_days + 1)

    compression = FLOOR + (pi_0 - FLOOR) * 2.0 ** (-t / H)
    static = np.full_like(t, pi_0, dtype=float)

    # Realised widening: the ADDITIVE move applied from today's level, then held.
    #
    # A multiplicative rebase (real * pi_0/real[0]) was tried first and is wrong: entry at 22.6%
    # against a start of 15.98% scales by 1.41, so the realised 51.6% peak was drawn at 73% --
    # higher than anything ever observed, from a chart claiming to replay what happened. Additive
    # replay preserves the move that occurred (+35.6 points, peak to trough) without inventing
    # magnitude.
    real = build_all_variants("skhy")[0].series.to_numpy(float)
    widening = pi_0 + (real - real[0])
    widening = np.concatenate([widening,
                               np.full(max(0, len(t) - len(widening)), widening[-1])])[:len(t)]

    return pd.DataFrame({"t": t, "compression": compression, "static": static,
                         "widening": widening}).set_index("t")


def pnl(pi_0: float = 0.226, horizon_days: int = 252) -> pd.DataFrame:
    """Net P&L per unit notional for a SHORT-premium position, per path, per cost bracket."""
    lv = paths(pi_0, horizon_days)
    out = {}
    for path in lv.columns:
        gross = pi_0 - lv[path]                     # premium narrows -> short profits
        for br in CARRY_BRACKET_BP:
            c = carry_bp(br, horizon_days) / 1e4
            out[f"{path}__{br}"] = gross - c * lv.index / 252.0
    return pd.DataFrame(out, index=lv.index)


def summary(pi_0: float = 0.226, horizon_days: int = 252) -> pd.DataFrame:
    """Path-end P&L in notional and in units of initial margin."""
    from pipeline.package.margin_path import margin_path
    im = float(margin_path().im_pair_pct.iloc[0])   # illustrative IM, netted pair
    p = pnl(pi_0, horizon_days).iloc[-1]
    rows = []
    for key, v in p.items():
        path, br = key.split("__")
        rows.append({"path": path, "bracket": br, "pnl_pct_notional": float(v),
                     "pnl_x_initial_margin": float(v / im) if im else None,
                     "initial_margin_pct": im})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    s = summary()
    print(f"illustrative initial margin (netted pair): {s.initial_margin_pct.iloc[0]:.2%} of notional")
    print(f"critical carry: {critical_carry_bp():.0f}bp/yr\n")
    print(s.pivot(index="path", columns="bracket",
                  values="pnl_x_initial_margin").round(2).to_string())
    print("\n(units = multiples of initial margin, at 252 days)")
