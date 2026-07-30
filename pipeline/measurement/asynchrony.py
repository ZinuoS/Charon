"""M1 — decomposition of measured close-to-close premium changes (README §4 D1, §6).

The problem
-----------
D1(a) π pairs legs that were never observed together. The KRX close (15:30 KST) and the
Nasdaq close (16:00 ET) are **13.5 hours** apart, and the FX leg has a *third* instant of
its own. So a measured change in π between two consecutive dates mixes:

1. a genuine change in the economic premium;
2. an artifact from the FX fix being struck at a different instant than either equity
   close — **reducible**, because a fix contemporaneous with the KRX close exists
   (ECOS ``731Y003.0000003``, 15:30 KST) even if access is pending;
3. an artifact from the 13.5h equity-close gap — **irreducible** at daily resolution,
   because no daily bar can observe both legs at one instant.

Identity
--------
Writing π in logs makes the decomposition exact and additive rather than approximate::

    ln(1 + pi_t) = ln P_adr,t + ln FX_t - ln n - ln P_local,t

so

.. math::

   \\Delta \\ln(1+\\pi_t) = \\underbrace{\\Delta \\ln P^{ADR}}_{\\text{ADR leg}}
                          + \\underbrace{\\Delta \\ln FX}_{\\text{FX leg}}
                          - \\underbrace{\\Delta \\ln P^{local}}_{\\text{local leg}}

Every term is observable, so the identity **holds to floating-point exactly** and is
asserted as such in the tests. It is a decomposition, not a model: nothing is estimated.

Calibrating the reducible part
------------------------------
The FX-instant component is no longer assumed. Session 5 measured it directly by holding
two differently-timed fixes of the same pair over **2,850 overlapping days** — ECB
(~16:00 CET) against FRED H.10 (noon New York):

===============  ==========
statistic        value
===============  ==========
mean              +0.0550%
median            +0.0526%
sd                 0.2632%
p95                0.5106%
max                2.95%
===============  ==========

:func:`fx_instant_band` returns that calibration so a chart or a table can state the
reducible component's size instead of hand-waving at it. When two FX variants are
actually present for a pair, :func:`decompose` measures the term per-observation rather
than using the constant.

Honest scope
------------
This is a **daily-bar** decomposition. It attributes a measured π change across three
observable legs; it cannot resolve the intraday *path*, so it cannot show that (say) the
local leg traded a result for a full session while the ADR sat frozen. That requires
intraday data. If the intraday capture for the 2026-07-28→29 window did not survive
provider retention, the worked example runs at daily resolution and says so — the
identity is unchanged, the resolution is coarser.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Measured 2026-07-29, ECB vs FRED H.10 on USD/KRW, 2,850 overlapping days. Empirical,
# not assumed — see the module docstring and docs/gate_reports/S1.md.
FX_FIX_CALIBRATION = {
    # LEVEL gap: how far apart the two fixes are on a given day.
    "mean": 0.000550,
    "median": 0.000526,
    "sd": 0.002632,
    "p95": 0.005106,
    "max": 0.029500,
    # CHANGE gap: how much the day-over-day CHANGE differs between the two fixes.
    # This is the number that matters for this module, because the decomposition
    # operates on changes, not levels — and differencing two independently-noisy fixes
    # AMPLIFIES the discrepancy rather than cancelling it. Measured on 2,849 changes:
    "change_mean_abs": 0.002656,
    "change_p95_abs": 0.007056,
    "change_max_abs": 0.028380,
    "n_days": 2850,
    "fix_a": "frankfurter (ECB ~16:00 CET)",
    "fix_b": "fred (H.10 noon New York)",
}

# For scale: TSM's mean |Δln(1+π)| over the comparator sample is ~162bp (measured on 2,327
# days before the ADR leg was recovered to 1997; the order of magnitude is unchanged). So a 26.6bp mean FX-instant
# artifact is on the order of **16% of a typical daily premium change** — not a rounding
# term, and the single strongest argument for adopting a fix contemporaneous with the
# local close (ECOS 731Y003.0000003, 15:30 KST) once access exists.
TYPICAL_DAILY_PREMIUM_CHANGE_BP_TSM = 162.0

#: The 13.5h equity-close gap, asserted as a number in tests/test_ingest_contracts.py.
EQUITY_CLOSE_GAP_HOURS = 13.5


def fx_instant_band(stat: str = "p95") -> float:
    """Calibrated size of the reducible FX-instant component, as a fraction."""
    if stat not in FX_FIX_CALIBRATION:
        raise KeyError(f"unknown stat {stat!r}; known: {sorted(FX_FIX_CALIBRATION)}")
    return float(FX_FIX_CALIBRATION[stat])


@dataclass
class Decomposition:
    """Per-date attribution of Δln(1+π) across its three observable legs."""

    frame: pd.DataFrame
    fx_variant_a: str
    fx_variant_b: str | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def identity_max_error(self) -> float:
        """Largest absolute residual of the additive identity. Should be ~1e-15."""
        if self.frame.empty:
            return 0.0
        resid = self.frame["d_ln_premium"] - (
            self.frame["adr_leg"] + self.frame["fx_leg"] - self.frame["local_leg"]
        )
        return float(resid.abs().max())

    def summary(self) -> dict:
        f = self.frame
        out = {
            "n_obs": len(f),
            "identity_max_error": self.identity_max_error,
            "fx_variant_a": self.fx_variant_a,
            "fx_variant_b": self.fx_variant_b,
            "mean_abs_d_ln_premium_bp": round(float(f["d_ln_premium"].abs().mean()) * 1e4, 2) if len(f) else None,
            "mean_abs_adr_leg_bp": round(float(f["adr_leg"].abs().mean()) * 1e4, 2) if len(f) else None,
            "mean_abs_local_leg_bp": round(float(f["local_leg"].abs().mean()) * 1e4, 2) if len(f) else None,
            "mean_abs_fx_leg_bp": round(float(f["fx_leg"].abs().mean()) * 1e4, 2) if len(f) else None,
        }
        if "fx_instant_artifact" in f:
            out["mean_abs_fx_instant_artifact_bp"] = round(
                float(f["fx_instant_artifact"].abs().mean()) * 1e4, 2
            )
        else:
            out["fx_instant_artifact_bp_calibrated_change_p95"] = round(
                fx_instant_band("change_p95_abs") * 1e4, 2
            )
        return out


def decompose(
    adr_close: pd.Series,
    local_close: pd.Series,
    fx_a: pd.Series,
    fx_b: pd.Series | None = None,
    fx_variant_a: str = "fx_a",
    fx_variant_b: str | None = None,
) -> Decomposition:
    """Decompose Δln(1+π) into ADR, FX and local legs.

    When ``fx_b`` is supplied, the difference between the two fixes' contributions is
    reported per-observation as ``fx_instant_artifact`` — the *measured* reducible
    component rather than the calibrated constant. That column is the empirical answer to
    confound C2's "how much of this is the FX clock?".
    """
    cols = {"adr": adr_close, "local": local_close, "fx_a": fx_a}
    if fx_b is not None:
        cols["fx_b"] = fx_b
    joined = pd.concat(cols, axis=1, join="inner").dropna()

    if joined.empty:
        return Decomposition(
            pd.DataFrame(columns=["d_ln_premium", "adr_leg", "fx_leg", "local_leg"]),
            fx_variant_a, fx_variant_b, ["no overlapping observations"],
        )

    ln = np.log(joined)
    out = pd.DataFrame(index=joined.index)
    out["adr_leg"] = ln["adr"].diff()
    out["local_leg"] = ln["local"].diff()
    out["fx_leg"] = ln["fx_a"].diff()
    out["d_ln_premium"] = out["adr_leg"] + out["fx_leg"] - out["local_leg"]

    notes: list[str] = []
    if fx_b is not None:
        out["fx_leg_b"] = ln["fx_b"].diff()
        # Reducible: the part of the measured change that flips when you change ONLY the
        # FX observation instant. Everything else is held fixed by construction.
        out["fx_instant_artifact"] = out["fx_leg"] - out["fx_leg_b"]
        # Irreducible at daily resolution: the equity-close gap cannot be differenced
        # away, because no daily bar observes both legs at one instant.
        out["irreducible_close_gap_hours"] = EQUITY_CLOSE_GAP_HOURS
        notes.append(
            f"FX-instant artifact measured per-observation from {fx_variant_a} vs {fx_variant_b}."
        )
    else:
        notes.append(
            "Only one FX variant present; the reducible FX-instant component is not "
            "measured here. Calibrated on CHANGES (the relevant basis for a decomposition "
            f"of changes): mean |.| = {fx_instant_band('change_mean_abs') * 1e4:.1f}bp, "
            f"p95 = {fx_instant_band('change_p95_abs') * 1e4:.1f}bp over "
            f"{FX_FIX_CALIBRATION['n_days']} days "
            f"({FX_FIX_CALIBRATION['fix_a']} vs {FX_FIX_CALIBRATION['fix_b']})."
        )
    notes.append(
        f"The {EQUITY_CLOSE_GAP_HOURS}h equity-close gap is IRREDUCIBLE at daily "
        "resolution: no daily bar observes both legs at one instant."
    )
    return Decomposition(out.dropna(subset=["d_ln_premium"]), fx_variant_a, fx_variant_b, notes)


def event_window(decomp: Decomposition, day: str, before: int = 1, after: int = 1) -> pd.DataFrame:
    """Rows around ``day`` — the worked example helper for the 07-28→07-29 window."""
    idx = pd.to_datetime(decomp.frame.index)
    target = pd.Timestamp(day)
    pos = int(np.searchsorted(idx.values, target.to_datetime64()))
    lo, hi = max(0, pos - before), min(len(idx), pos + after + 1)
    return decomp.frame.iloc[lo:hi]


def attribution_shares(decomp: Decomposition) -> dict:
    """Share of mean absolute Δln(1+π) attributable to each leg.

    Shares are computed on absolute contributions and therefore need not sum to 1 — the
    legs offset. Reported as a rough magnitude guide, and labelled as such rather than
    dressed up as a variance decomposition it is not.
    """
    f = decomp.frame
    if f.empty:
        return {}
    total = float(f["d_ln_premium"].abs().mean())
    if total == 0:
        return {}
    return {
        "adr_leg_share": round(float(f["adr_leg"].abs().mean()) / total, 3),
        "local_leg_share": round(float(f["local_leg"].abs().mean()) / total, 3),
        "fx_leg_share": round(float(f["fx_leg"].abs().mean()) / total, 3),
        "note": "absolute-contribution shares; legs offset so these need not sum to 1",
    }
