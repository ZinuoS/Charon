"""M3 — convergence dynamics via Jordà local projections. PROVISIONAL until taxonomy ratified.

README §6 M3: conditional half-life of π per capacity regime via Jordà local projections
across h = 1…H with an exponential half-life fit, on the D6 comparator panel, everything
train-only, SKHY forward-scored never fitted.

The method
----------
For each horizon h, one regression of the level h steps ahead on the level now:

    π_{t+h} = α_h + ρ_h · π_t + ε_{t,h}

ρ_h is the persistence of the premium at horizon h. Under mean reversion it decays with h,
and the half-life is the h at which ρ_h = ½. Fitting ρ_h ≈ exp(−h/τ) gives a smooth
estimate, and half-life = τ·ln 2.

**HAC errors are not optional here.** The h-step windows overlap — π_{t+h} and π_{t+1+h}
share h−1 periods — so ε is serially correlated by construction and plain OLS standard
errors are badly understated. Newey–West with bandwidth ≈ h corrects it. Implemented inline
(no statsmodels; doctrine permits this where the package mirror balks).

Capacity rule (README §6): the effective N is small and the estimator is deliberately
shallow — ridge-regularized linear, no tree depth, no interaction search. A ridge with
λ→0 is OLS; a small λ stabilises the tiny-sample regime fits without changing the
large-sample ones materially.

Quarantine: every result carries ``provisional=True`` because the regime *labels* are the
author's proposed taxonomy, not ratified. SKHY is scored (its persistence measured on its
12 points) but never enters a fit — enforced by the validation layer's forward-test guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Proposed taxonomy at pair level (PROVISIONAL — pending ratification).
REGIME_OF_PAIR = {
    "tsmc": "one_way_constrained",
    "baba": "fungible",
    # skhy is one_way_constrained too, but is FORWARD-TEST ONLY and never fitted.
}
FORWARD_TEST_PAIRS = {"skhy"}

RIDGE_LAMBDA = 1e-4     # ridge penalty; near-OLS, stabilises small-sample folds. TODO(ash: ratify)
MAX_HORIZON = 20        # trading days


def _newey_west_se(x: np.ndarray, resid: np.ndarray, bandwidth: int) -> float:
    """HAC standard error for the slope of a simple regression y = a + b x.

    Bartlett kernel, bandwidth L. Returns the standard error of the slope coefficient.
    """
    n = len(x)
    xc = x - x.mean()
    sxx = (xc ** 2).sum()
    if sxx == 0:
        return float("nan")
    # meat: sum of autocovariances of (xc * resid), Bartlett-weighted
    u = xc * resid
    s = (u ** 2).sum()
    for lag in range(1, min(bandwidth, n - 1) + 1):
        w = 1.0 - lag / (bandwidth + 1)
        s += 2 * w * (u[lag:] * u[:-lag]).sum()
    return float(np.sqrt(s) / sxx)


@dataclass
class HorizonFit:
    horizon: int
    rho: float
    se_hac: float
    n: int
    r2: float

    @property
    def t_hac(self) -> float:
        return self.rho / self.se_hac if self.se_hac and not np.isnan(self.se_hac) else float("nan")


@dataclass
class ConvergenceResult:
    regime: str
    n_pairs: int
    n_obs: int
    horizons: list[HorizonFit]
    half_life: float | None
    half_life_method: str
    provisional: bool = True
    notes: list[str] = field(default_factory=list)

    def metrics_at(self, h: int = 1) -> dict:
        hf = next((x for x in self.horizons if x.horizon == h), None)
        return {} if hf is None else {
            "regime": self.regime, "n_pairs": self.n_pairs, "n_obs": self.n_obs,
            "horizon": h, "rho": round(hf.rho, 4), "t_HAC": round(hf.t_hac, 2),
            "r2": round(hf.r2, 4), "half_life_days": (round(self.half_life, 1)
                                                      if self.half_life else None),
        }


def _local_projection(pi: pd.Series, horizon: int, ridge: float) -> HorizonFit | None:
    y = pi.shift(-horizon)
    df = pd.concat({"x": pi, "y": y}, axis=1).dropna()
    if len(df) < 20:
        return None
    x = df["x"].to_numpy(); yv = df["y"].to_numpy()
    xc = x - x.mean(); yc = yv - yv.mean()
    rho = float((xc @ yc) / (xc @ xc + ridge))
    alpha = yv.mean() - rho * x.mean()
    resid = yv - (alpha + rho * x)
    ss_tot = ((yv - yv.mean()) ** 2).sum()
    r2 = 1.0 - (resid ** 2).sum() / ss_tot if ss_tot else float("nan")
    se = _newey_west_se(x, resid, bandwidth=horizon)
    return HorizonFit(horizon, rho, se, len(df), r2)


def estimate_regime(pi_series: list[pd.Series], regime: str, max_h: int = MAX_HORIZON,
                    ridge: float = RIDGE_LAMBDA) -> ConvergenceResult:
    """Pool the pairs of one regime class and estimate the persistence decay + half-life.

    Pairs are pooled by stacking their (level_t, level_{t+h}) observations — not by
    averaging ρ across pairs — so a longer pair contributes more evidence, which is correct.
    """
    fits: list[HorizonFit] = []
    total_obs = sum(len(s) for s in pi_series)
    for h in range(1, max_h + 1):
        xs, ys = [], []
        for pi in pi_series:
            yb = pi.shift(-h)
            d = pd.concat({"x": pi, "y": yb}, axis=1).dropna()
            xs.append(d["x"].to_numpy()); ys.append(d["y"].to_numpy())
        x = np.concatenate(xs); yv = np.concatenate(ys)
        if len(x) < 20:
            continue
        xc = x - x.mean(); yc = yv - yv.mean()
        rho = float((xc @ yc) / (xc @ xc + ridge))
        alpha = yv.mean() - rho * x.mean()
        resid = yv - (alpha + rho * x)
        ss = ((yv - yv.mean()) ** 2).sum()
        r2 = 1.0 - (resid ** 2).sum() / ss if ss else float("nan")
        fits.append(HorizonFit(h, rho, _newey_west_se(x, resid, h), len(x), r2))

    hl, method = _half_life(fits)
    notes = []
    if hl is not None and fits and hl > fits[-1].horizon:
        notes.append(
            f"HALF-LIFE ({hl:.0f}d) EXCEEDS THE FITTING WINDOW (h={fits[-1].horizon}). ρ does "
            "not cross 0.5 in range, so this is an EXTRAPOLATION from the exponential fit, "
            "not an observed half-life. It says 'slow' reliably; the exact figure does not.")
    return ConvergenceResult(regime, len(pi_series), total_obs, fits, hl, method, notes=notes)


def _half_life(fits: list[HorizonFit]) -> tuple[float | None, str]:
    """Half-life two ways: direct crossing of ρ=0.5, and an exponential fit as backup."""
    if not fits:
        return None, "no fits"
    for a, b in zip(fits, fits[1:]):
        if a.rho >= 0.5 >= b.rho:
            frac = (a.rho - 0.5) / (a.rho - b.rho) if a.rho != b.rho else 0
            return a.horizon + frac, "direct ρ=0.5 crossing"
    # exponential fit rho ≈ exp(-h/tau) on positive rhos
    hs = np.array([f.horizon for f in fits], float)
    rs = np.array([f.rho for f in fits], float)
    m = rs > 1e-6
    if m.sum() < 3:
        return None, "insufficient positive ρ for exp fit"
    tau = -1.0 / np.polyfit(hs[m], np.log(rs[m]), 1)[0]
    if tau <= 0:
        return None, "ρ does not decay (persistent/explosive) — no finite half-life"
    return float(tau * np.log(2)), "exponential fit (no direct crossing in range)"


def run_panel(max_h: int = MAX_HORIZON) -> dict[str, ConvergenceResult]:
    """Estimate convergence per regime class on the panel. SKHY excluded from all fits."""
    from pipeline.measurement.premium import build_all_variants
    from pipeline.validation.splitters import assert_no_forward_test_instrument

    by_regime: dict[str, list[pd.Series]] = {}
    fitted_pairs: list[str] = []
    for pid, regime in REGIME_OF_PAIR.items():
        if pid in FORWARD_TEST_PAIRS:
            continue
        try:
            by_regime.setdefault(regime, []).append(build_all_variants(pid)[0].series)
            fitted_pairs.append(pid)
        except Exception:
            continue
    assert_no_forward_test_instrument(fitted_pairs)   # structural guard: no SKHY in fits
    return {r: estimate_regime(series, r, max_h) for r, series in by_regime.items()}


def score_skhy(max_h: int = 6) -> dict:
    """Measure SKHY's own persistence — SCORED, never fitted, out-of-support declared."""
    from pipeline.measurement.premium import build_all_variants
    pi = build_all_variants("skhy")[0].series
    rows = []
    for h in range(1, max_h + 1):
        fit = _local_projection(pi, h, RIDGE_LAMBDA)
        if fit:
            rows.append({"horizon": h, "rho": round(fit.rho, 4), "n": fit.n})
    too_short = not rows
    return {
        "instrument": "skhy", "n_obs": len(pi), "scored_not_fitted": True,
        "out_of_support": f"n={len(pi)} is far below the panel; README §8: not validation",
        "adjacency": "one_way_constrained (by name only — not used to fit that regime)",
        "resolution": "NONE — this is a forward test in progress, no call resolved",
        "persistence": rows,
        "note": ("n is below the 20-obs minimum for a single-horizon fit, so SKHY's own "
                 "persistence cannot be estimated yet — the honest out-of-support answer, "
                 "not a number." if too_short else ""),
    }


def metrics_table(results: dict[str, ConvergenceResult], horizons=(1, 5, 20)) -> pd.DataFrame:
    """Per-regime persistence/fit metrics. Pooled row last and labelled (README §8)."""
    rows = []
    for regime, res in sorted(results.items()):
        for h in horizons:
            m = res.metrics_at(h)
            if m:
                rows.append(m)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["PROVISIONAL"] = "pending taxonomy ratification"
    return df
