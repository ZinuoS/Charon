"""Breakeven convergence arithmetic — the pitch's central number.

The question a client actually asks: **how fast must the premium converge to beat the carry?**

Four of the five cost components are undocumented (`execution/costs.py`), so this returns a
BRACKET, not a point. That is the honest answer until the desk conversation fills the numbers,
and a bracket the client can see beats a single figure they cannot audit.

The arithmetic, deliberately simple:

    convergence gain over T  =  (pi_0 - floor) * (1 - 2^(-T/H))     # exponential decay to floor
    carry over T             =  c_annual * T / 252
    breakeven                =  the H at which those are equal

`ponytail: exponential decay to a fixed floor is the same functional form M3 fits, so the
breakeven H is directly comparable to the estimated H. A reflected-process simulation would be
the upgrade if the floor ever stops being flat.`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: Annual carry brackets, in basis points, for the FOUR HATCHED components combined.
#: These are ASSUMPTIONS, labelled as such, and they exist to be replaced by the desk
#: conversation -- not to be quoted. Anchored on published Korean securities-lending fee
#: ranges and USD/KRW funding differentials being of the same order; the spread between low
#: and high is the point, not the midpoint.
CARRY_BRACKET_BP = {"low": 250, "mid": 600, "high": 1200}

#: The one documented component (SK Hynix 424B4 "Fees and Charges"), round trip.
CONVERSION_FEE_BP = 7.0

FLOOR = 0.0007          # the cost-determined lower barrier: cancellation round trip
HATCHED = ("local short borrow", "ADR borrow", "USD/KRW hedge (forward points)",
           "USD vs KRW funding differential")


def carry_bp(bracket: str = "mid", amortise_conversion_over_days: float | None = None) -> float:
    """Annual all-in carry in bp for one bracket. Conversion fee amortised if the unwind
    path assumes cancellation through the open barrier."""
    c = float(CARRY_BRACKET_BP[bracket])
    if amortise_conversion_over_days:
        c += CONVERSION_FEE_BP * 252.0 / amortise_conversion_over_days
    return c


def breakeven_half_life(pi_0: float, horizon_days: float, bracket: str = "mid",
                        floor: float = FLOOR) -> float | None:
    """The half-life at which convergence gain exactly pays the carry. None if unreachable.

    Solve (pi_0 - floor)(1 - 2^(-T/H)) = c*T/252 for H. Rearranged:
        H = -T / log2(1 - carry / (pi_0 - floor))
    """
    T = float(horizon_days)
    gain_needed = carry_bp(bracket, amortise_conversion_over_days=T) / 1e4 * T / 252.0
    room = pi_0 - floor
    if room <= 0 or gain_needed >= room:
        return None                     # carry exceeds the entire distance to the floor
    return float(-T / np.log2(1.0 - gain_needed / room))


def surface(pi_levels=(0.10, 0.15, 0.226, 0.30, 0.40), horizons=(63, 126, 252, 504),
            brackets=("low", "mid", "high")) -> pd.DataFrame:
    """Breakeven half-life over (entry level x horizon x cost bracket)."""
    rows = []
    for b in brackets:
        for pi in pi_levels:
            for T in horizons:
                h = breakeven_half_life(pi, T, b)
                rows.append({"bracket": b, "carry_bp": carry_bp(b, T), "entry_premium": pi,
                             "horizon_days": T, "breakeven_half_life_days": h,
                             "unreachable": h is None})
    return pd.DataFrame(rows)


def verdict(pi_0: float = 0.226, horizon_days: float = 252) -> dict:
    """Compare breakeven against the ESTIMATED half-life. Decides the sheet's tone.

    No thumb on the scale: whichever way it reads, it reads. If the estimated half-life is
    slower than breakeven, a client entering the linear trade is expressing a
    faster-than-base-rate view, and the sheet says so in those words.
    """
    from pipeline.convergence.jorda import run_panel
    hl = run_panel()["one_way_constrained"].hl
    out = {"entry_premium": pi_0, "horizon_days": horizon_days,
           "estimated_half_life_days": hl.point,
           "estimated_floor_days": hl.lower, "estimated_ceiling": hl.upper,
           "hatched_components": list(HATCHED)}
    for b in CARRY_BRACKET_BP:
        be = breakeven_half_life(pi_0, horizon_days, b)
        out[f"breakeven_{b}"] = be
        out[f"carry_bp_{b}"] = carry_bp(b, horizon_days)
        # "Faster than breakeven" = the premium halves SOONER than the carry requires.
        out[f"pays_at_{b}"] = None if be is None else bool(hl.point <= be)
    return out


def critical_carry_bp(pi_0: float = 0.226, horizon_days: float = 252,
                      half_life_days: float | None = None) -> float:
    """The carry at which the ESTIMATED half-life exactly breaks even.

    This is the one number the desk conversation has to fill. Above it the linear trade is
    negative-carry to the base rate and a client entering is expressing a faster-than-base-rate
    view; below it the base rate alone pays. Inverting the gain identity:

        carry_bp = 1e4 * (pi_0 - floor) * (1 - 2^(-T/H)) * 252 / T
    """
    from pipeline.convergence.jorda import run_panel
    H = half_life_days or run_panel()["one_way_constrained"].hl.point
    T = float(horizon_days)
    gain = (pi_0 - FLOOR) * (1.0 - 2.0 ** (-T / H))
    return float(1e4 * gain * 252.0 / T - CONVERSION_FEE_BP * 252.0 / T)


if __name__ == "__main__":
    v = verdict()
    print(f"entry pi={v['entry_premium']:.1%}  horizon={v['horizon_days']:.0f}d")
    print(f"estimated half-life {v['estimated_half_life_days']:.0f}d "
          f"[floor {v['estimated_floor_days']:.0f}d, ceiling unbounded]")
    for b in CARRY_BRACKET_BP:
        be, pays = v[f"breakeven_{b}"], v[f"pays_at_{b}"]
        print(f"  {b:5s} carry {v[f'carry_bp_{b}']:6.0f}bp/yr -> breakeven H = "
              f"{'unreachable' if be is None else f'{be:6.0f}d'}   pays: {pays}")
    cc = critical_carry_bp()
    print(f"\nCRITICAL CARRY at the estimated half-life: {cc:.0f} bp/yr "
          f"({cc/12:.0f} bp/month). Above this the linear trade is negative-carry to base rate.")
    from pipeline.convergence.jorda import run_panel as _rp
    floor_H = _rp()["one_way_constrained"].hl.lower
    print(f"At the 95% FLOOR half-life ({floor_H:.0f}d, i.e. fastest consistent with the "
          f"evidence): {critical_carry_bp(half_life_days=floor_H):.0f} bp/yr")
