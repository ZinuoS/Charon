"""M3 — convergence dynamics via Jordà local projections. PROVISIONAL until taxonomy ratified.

README §6 M3: conditional half-life of π per capacity regime via Jordà local projections
across h = 1…H with an exponential half-life fit, on the D6 comparator panel, everything
train-only, SKHY forward-scored never fitted.

The method
----------
For each horizon h, one regression of the level h steps ahead on the level now:

    π_{t+h} = α_h + ρ_h · π_t + ε_{t,h}

ρ_h is the persistence of the premium at horizon h. Under mean reversion it decays with h,
and the half-life is the h at which ρ_h = ½.

**The half-life is reported as an interval, not a point** (S17). Through S15 the window
stopped at h=20, ρ_h never approached ½ inside it, and the half-life came from extrapolating
ρ_h ≈ exp(−h/τ) — a number with no support under it. Extending the window to h=400 was
expected to fix that by making the crossing observable. It did, and the observable crossing
said something the extrapolation had hidden:

*   The extrapolated figure (227d) was **too fast**. First passage of ρ below ½ happens at
    h ≈ 331, about 46% later.
*   The 95% HAC band's **upper edge never crosses ½ at any estimable horizon.** So there is
    no finite upper bound: the data do not reject a premium that never halves.
*   The band's lower edge crosses at h ≈ 143, where coefficients are still identified. That
    is the defensible number — the fastest convergence consistent with the evidence.

Extending the horizon therefore did not convert an extrapolation into a point estimate. It
converted a false point estimate into a **floor with an open tail**, which is what the data
actually support and what anything linear in holding horizon must be quoted against.

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
#
# S18: the constrained class goes from one pair to four. Membership is assigned from the
# DOCUMENTED RE-ISSUANCE RULE, before any persistence is estimated — never from how the
# resulting premium series behaves, which would be selecting on the outcome.
#
# The rule for all four is ROC law, and it is a REVOLVING facility rather than SKHY's
# discretionary consent: 華僑及外國人投資證券管理辦法 Art. 31 permits domestic purchase for
# re-issuance only "within the scope of the originally cancelled share count", and
# Regulations Governing the Offering and Issuance of Overseas Securities by Issuers Art. 14
# requires FSC effective registration for any follow-on issue outside that. TSMC's FY2024
# 20-F Ex. 2(a)(1) states it directly; Chunghwa Telecom's FY2025 20-F goes further and draws
# the price conclusion itself, which is why CHT is the citation of record for the mechanism.
#
# ⚠️ THE LIMITATION, STATED WHEREVER THE POOLED ESTIMATE IS: these four share a REGULATOR.
# Four pairs reduce ISSUER-idiosyncratic noise; they do not provide independent variation in
# the RULE. A second jurisdiction remains the binding gap (see docs/gate_reports/S18.md).
REGIME_OF_PAIR = {
    "tsmc": "one_way_constrained",
    "umc": "one_way_constrained",
    "ase": "one_way_constrained",
    "cht": "one_way_constrained",
    # auo is the same rule but EXCLUDED: it delisted its ADSs from the NYSE in 2019 and
    # moved to an OTC programme. See PairSpec.sample_reason.
    "baba": "fungible",
    # skhy is one_way_constrained too, but is FORWARD-TEST ONLY and never fitted.
}
FORWARD_TEST_PAIRS = {"skhy"}

RIDGE_LAMBDA = 1e-4     # ridge penalty; near-OLS, stabilises small-sample folds. TODO(ash: ratify)

# ---------------------------------------------------------------- horizon window
#
# MAX_HORIZON was 20 through S15, which put the half-life OUTSIDE the fitting window and
# forced an exponential extrapolation. S17 extends it, and the extension is what makes the
# half-life honest rather than what makes it precise — see `_half_life_interval`.
#
# The binding constraint on H is NOT the row count. Local projections at horizon h use
# overlapping windows, so 2,328 daily observations at h=300 are 2,028 rows carrying roughly
# 2028/300 ≈ 7 independent spans. That ratio, not n, is what the standard error should be
# read against, so it is computed and reported as `n_eff` on every fit.
#
# H is capped where n_eff falls below MIN_EFF_SPANS. Past that the ρ_h path stops being
# monotone (it wanders and even turns back up — an artefact of a handful of overlapping
# spans, not a sign the premium re-diverges), so fits beyond the cap would be noise wearing
# a coefficient's clothes.
MAX_HORIZON = 400        # trading days ≈ 19 months
MIN_EFF_SPANS = 5.0      # cap H where n/h drops below this
IDENTIFIED_EFF_SPANS = 12.0   # below this a crossing is in-window but statistically unidentified


def horizon_grid(max_h: int = MAX_HORIZON) -> list[int]:
    """Dense at the short end, sparse at the long end.

    Fitting every integer h to 400 costs O(n·h) per HAC estimate for no resolution gain: the
    crossing interval is hundreds of days wide, so 10-day steps out there are far finer than
    anything the data can distinguish. The short end stays dense because that is where the
    coefficients are actually identified.
    """
    grid = list(range(1, min(21, max_h + 1)))
    grid += [h for h in range(25, min(101, max_h + 1), 5)]
    grid += [h for h in range(110, max_h + 1, 10)]
    return sorted(set(h for h in grid if h <= max_h))


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

    @property
    def n_eff(self) -> float:
        """Independent spans, not rows. n rows at horizon h overlap into about n/h of them."""
        return self.n / self.horizon if self.horizon else float("nan")

    @property
    def identified(self) -> bool:
        return self.n_eff >= IDENTIFIED_EFF_SPANS

    def band(self, z: float = 1.96) -> tuple[float, float]:
        if np.isnan(self.se_hac):
            return (float("nan"), float("nan"))
        return (self.rho - z * self.se_hac, self.rho + z * self.se_hac)


@dataclass
class HalfLife:
    """A half-life as an interval with a support classification, not a point.

    The point estimate is the first h at which ρ_h falls below ½. The bounds come from the
    same first-passage rule applied to the 95% HAC band: the LOWER bound is where the lower
    edge of the band crosses (the fastest convergence the data are consistent with) and the
    UPPER bound is where the upper edge crosses (the slowest). If the upper edge never
    crosses inside the estimable window, there is no finite upper bound — the data do not
    reject a premium that never halves.
    """

    point: float | None
    lower: float | None
    upper: float | None          # None means UNBOUNDED, not missing
    method: str
    support: str                 # interpolated | interpolated_underpowered | extrapolated | none
    n_eff_at_point: float | None = None

    @property
    def unbounded_above(self) -> bool:
        return self.upper is None and self.point is not None

    def describe(self) -> str:
        if self.point is None:
            return f"no half-life ({self.method})"
        # Asymmetric on purpose: a missing UPPER bound means the slow tail is unbounded,
        # a missing LOWER bound means the fast end is simply below what daily data resolve.
        hi = "unbounded" if self.upper is None else f"{self.upper:.0f}d"
        lo = "unresolved" if self.lower is None else f"{self.lower:.0f}d"
        return f"{self.point:.0f}d  [95% {lo} .. {hi}]  {self.support}"


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
    hl: HalfLife | None = None          # the interval form; `half_life` is its point

    def metrics_at(self, h: int = 1) -> dict:
        hf = next((x for x in self.horizons if x.horizon == h), None)
        return {} if hf is None else {
            "regime": self.regime, "n_pairs": self.n_pairs, "n_obs": self.n_obs,
            "horizon": h, "rho": round(hf.rho, 4), "t_HAC": round(hf.t_hac, 2),
            "r2": round(hf.r2, 4), "n_eff": round(hf.n_eff, 1),
            "half_life_days": (round(self.half_life, 1) if self.half_life else None),
            "half_life_lo": (round(self.hl.lower, 1) if self.hl and self.hl.lower else None),
            "half_life_hi": ("unbounded" if self.hl and self.hl.unbounded_above
                             else (round(self.hl.upper, 1) if self.hl and self.hl.upper else None)),
            "half_life_support": self.hl.support if self.hl else None,
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

    # WITHIN transformation before pooling (S18). Stacking raw LEVELS across pairs with
    # different long-run means would let the between-pair dispersion masquerade as
    # persistence: a constant offset is perfectly autocorrelated at every horizon, so the
    # more pairs you add the more persistent the pooled premium looks, regardless of
    # dynamics. Demeaning per pair removes that channel. It costs a small downward (Nickell)
    # bias of order 1/T, negligible at T = 2,000-6,000.
    #
    # Measured on the S18 panel: pooling raw levels gave rho_1 = 0.9816 against 0.9798
    # demeaned — small here because the four means are close, but the correction is not
    # optional, since its size is a property of the panel and not of the estimator.
    pi_series = [s - s.mean() for s in pi_series]

    for h in horizon_grid(max_h):
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
        fit = HorizonFit(h, rho, _newey_west_se(x, resid, h), len(x), r2)
        if fit.n_eff < MIN_EFF_SPANS:
            break                      # past here the ρ path is overlap artefact, not decay
        fits.append(fit)

    hl = _half_life_interval(fits)
    notes = _half_life_notes(hl, fits)
    return ConvergenceResult(regime, len(pi_series), total_obs, fits,
                             hl.point, hl.method, notes=notes, hl=hl)


def _first_crossing(hs: np.ndarray, vals: np.ndarray, level: float = 0.5) -> float | None:
    """First h at which `vals` falls below `level`, linearly interpolated within the step.

    FIRST passage, deliberately. The ρ_h path is not monotone at long horizons — with a
    handful of independent spans it wanders — so "the crossing" is not well defined and the
    first one is the only rule that does not require choosing among several.
    """
    for (h0, v0), (h1, v1) in zip(zip(hs, vals), zip(hs[1:], vals[1:])):
        if v0 >= level > v1:
            frac = (v0 - level) / (v0 - v1) if v0 != v1 else 0.0
            return float(h0 + frac * (h1 - h0))
    return None


def _half_life_interval(fits: list[HorizonFit]) -> HalfLife:
    """First-passage half-life with a 95% band, classified by whether it is in support."""
    if len(fits) < 3:
        return HalfLife(None, None, None, "insufficient fits", "none")

    hs = np.array([f.horizon for f in fits], float)
    rho = np.array([f.rho for f in fits], float)
    lo = np.array([f.band()[0] for f in fits], float)
    hi = np.array([f.band()[1] for f in fits], float)

    # Already below ½ at the shortest horizon: the premium halves faster than we can resolve.
    # This is the fungible-control case, and it must NOT fall through to the "does not decay"
    # branch below — that phrase means "never converges", which is the exact opposite.
    if rho[0] < 0.5:
        h0 = float(hs[0])
        return HalfLife(h0, 0.0, (h0 if hi[0] < 0.5 else None),
                        f"ρ is below ½ at the shortest horizon (h={h0:.0f}) — half-life is under "
                        "one step and is not resolvable at daily frequency",
                        "sub_resolution", fits[0].n_eff)

    point = _first_crossing(hs, rho)
    # Lower band crossing first => the FASTEST convergence consistent with the data.
    hl_lower = _first_crossing(hs, lo)
    hl_upper = _first_crossing(hs, hi)
    h_max = float(hs[-1])

    if point is not None:
        n_eff_at = float(np.interp(point, hs, [f.n_eff for f in fits]))
        support = "interpolated" if n_eff_at >= IDENTIFIED_EFF_SPANS else "interpolated_underpowered"
        return HalfLife(point, hl_lower, hl_upper, "first passage of ρ below ½ (in window)",
                        support, n_eff_at)

    # ρ never falls below ½ inside the estimable window. Fall back to the exponential fit,
    # but say plainly that it is an extrapolation.
    m = rho > 1e-6
    if m.sum() < 3:
        return HalfLife(None, hl_lower, hl_upper, "insufficient positive ρ", "none")
    slope = np.polyfit(hs[m], np.log(rho[m]), 1)[0]
    if slope >= 0:
        return HalfLife(None, hl_lower, None, "ρ does not decay — no finite half-life", "none")
    tau = -1.0 / slope
    return HalfLife(float(tau * np.log(2)), hl_lower, hl_upper,
                    f"exponential fit extrapolated beyond h={h_max:.0f}", "extrapolated")


def _half_life_notes(hl: HalfLife, fits: list[HorizonFit]) -> list[str]:
    notes: list[str] = []
    if not fits:
        return notes
    h_max = fits[-1].horizon
    if hl.support == "extrapolated":
        notes.append(
            f"HALF-LIFE ({hl.point:.0f}d) EXCEEDS THE FITTING WINDOW (h={h_max}). ρ does not "
            "cross ½ in range, so this is an EXTRAPOLATION, not an observed half-life.")
    elif hl.support == "interpolated_underpowered":
        notes.append(
            f"Half-life {hl.point:.0f}d is INSIDE the fitting window (h={h_max}) — no longer an "
            f"extrapolation — but it sits where only ~{hl.n_eff_at_point:.0f} independent spans "
            f"support it (threshold {IDENTIFIED_EFF_SPANS:.0f}). The crossing is observed; it is "
            "not precisely located.")
    if hl.unbounded_above:
        notes.append(
            f"NO FINITE UPPER BOUND. The upper 95% edge of ρ_h stays above ½ across every "
            f"estimable horizon (to h={h_max}), so the data do not reject a premium that never "
            "halves. Any quantity linear in holding horizon — financing cost above all — "
            "inherits an unbounded upper tail and must be quoted as a floor, never a point.")
    if hl.lower is not None:
        notes.append(
            f"Lower bound {hl.lower:.0f}d is the FASTEST convergence consistent with the data at "
            "95%, and it is the defensible number: it sits where the coefficients are still "
            "identified.")
    return notes


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
