"""H4 — realized variance decomposition. The runnable half of the hypothesis.

README §5 H4 states the identity

    Var(ADR) ~ Var(local) + Var(FX) + Var(pi) + covariances

The *implied* side of H4 — whether US options price SKHY vol off local history or Micron
comps — needs an options surface this repository has not sourced. That half is gated and
absent, not approximated. What is computable today is the realized side, and it is
informative on its own: it says how much of the ADR's variance is premium variance rather
than fundamental or currency variance.

Exact, not approximate
----------------------
Working in logs makes the decomposition an identity rather than a first-order
approximation:

    ln(1+pi) = ln P_adr + ln FX - ln n - ln P_local     =>     r_pi = r_adr + r_fx - r_local

so, rearranged,

    r_adr = r_local - r_fx + r_pi        (exactly, per observation)

and taking variances of both sides:

    Var(r_adr) = Var(r_local) + Var(r_fx) + Var(r_pi)
                 - 2Cov(r_local, r_fx) + 2Cov(r_local, r_pi) - 2Cov(r_fx, r_pi)

**Sign discipline matters here and is not cosmetic.** Defining r_pi as
(r_adr - r_local - r_fx) instead would make the variance identity close to floating point
*by construction* while measuring the wrong quantity entirely — a residual of 1e-18 would
certify nothing. The locked-pair fixture in the tests is what distinguishes the two.

Every term is measurable and the residual is zero to floating point — asserted in tests.
The covariance terms are the interesting ones: a large negative Cov(local, pi) is the
signature of the premium absorbing local moves rather than transmitting them.

Scope
-----
SKHY's sample is ~12 observations. Any variance statistic on it is reported with n
attached and is descriptive only — README §8 is explicit that n≈12 is not validation.
TSM's 2,328 observations carry the weight. **The contrast between the pairs is the
evidence, not the SKHY level.**
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class VarianceDecomposition:
    pair_id: str
    n_obs: int
    components: dict[str, float]
    covariances: dict[str, float]
    shares: dict[str, float]
    total_var: float
    residual: float
    notes: list[str] = field(default_factory=list)

    @property
    def premium_share(self) -> float:
        """Fraction of ADR variance attributable to premium variance alone."""
        return self.shares.get("pi", float("nan"))

    def summary(self) -> dict:
        out = {"pair": self.pair_id, "n": self.n_obs,
               "ann_vol_adr_pct": round(float(np.sqrt(self.total_var * 252)) * 100, 2),
               "residual": self.residual}
        out |= {f"var_{k}": round(v, 12) for k, v in self.components.items()}
        out |= {f"share_{k}": round(v, 4) for k, v in self.shares.items()}
        out |= {f"cov_{k}": round(v, 12) for k, v in self.covariances.items()}
        return out


def decompose_variance(
    adr_close: pd.Series,
    local_close: pd.Series,
    fx_local_per_usd: pd.Series,
    local_shares_per_adr: float,
    pair_id: str = "pair",
) -> VarianceDecomposition:
    """Decompose realized ADR return variance into local, FX and premium components.

    Returns shares that sum to 1 across components *and* covariances — the covariance
    terms are reported rather than folded away, because folding them hides the case where
    a small premium-variance share coexists with a large negative covariance (the premium
    damping local moves).
    """
    frame = pd.concat(
        {"adr": adr_close, "local": local_close, "fx": fx_local_per_usd},
        axis=1, join="inner",
    ).dropna()
    ln = np.log(frame)
    r = pd.DataFrame({
        "adr": ln["adr"].diff(),
        "local": ln["local"].diff(),
        "fx": ln["fx"].diff(),
    }).dropna()
    # Premium return follows from the identity; it is not independently estimated.
    r["pi"] = r["adr"] + r["fx"] - r["local"]

    n = len(r)
    notes: list[str] = []
    if n < 30:
        notes.append(
            f"n={n}: descriptive only. README §8 — a sample this size is not validation, "
            "and no inference is drawn from it."
        )

    comp = {k: float(r[k].var(ddof=1)) for k in ("local", "fx", "pi")}
    cov = {
        "local_fx": float(r["local"].cov(r["fx"])),
        "local_pi": float(r["local"].cov(r["pi"])),
        "fx_pi": float(r["fx"].cov(r["pi"])),
    }
    total = float(r["adr"].var(ddof=1))
    rebuilt = (comp["local"] + comp["fx"] + comp["pi"]
               - 2 * cov["local_fx"] + 2 * cov["local_pi"] - 2 * cov["fx_pi"])
    residual = float(abs(total - rebuilt))

    denom = total if total else float("nan")
    shares = {k: v / denom for k, v in comp.items()}
    _sign = {"local_fx": -2.0, "local_pi": +2.0, "fx_pi": -2.0}
    shares |= {f"cov_{k}": _sign[k] * v / denom for k, v in cov.items()}

    if cov["local_pi"] < -0.25 * comp["pi"]:
        notes.append(
            "Cov(local, pi) is materially negative: the premium is absorbing local moves "
            "rather than transmitting them — consistent with two participant pools "
            "repricing on different information."
        )
    return VarianceDecomposition(pair_id, n, comp, cov, shares, total, residual, notes)


def compare_pairs(pair_ids: tuple[str, ...] = ("skhy", "tsmc", "baba")) -> pd.DataFrame:
    """Run the decomposition across the panel. The CONTRAST is the evidence (README §5 H4)."""
    from pipeline.ingest.registry import pair_by_id
    from pipeline.measurement.premium import PAIR_SOURCE, DEFAULT_SOURCE, _load_close

    rows = []
    for pid in pair_ids:
        pair = pair_by_id(pid)
        src = PAIR_SOURCE.get(pid, DEFAULT_SOURCE)
        try:
            d = decompose_variance(
                _load_close(src, pair.adr), _load_close(src, pair.local),
                _load_close("d1_prices" if pid == "skhy" else src, pair.fx),
                pair.local_shares_per_adr, pid,
            )
        except Exception:
            continue
        rows.append(d.summary())
    return pd.DataFrame(rows)
