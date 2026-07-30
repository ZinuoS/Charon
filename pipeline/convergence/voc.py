"""Track B — Virtue-of-Complexity, per Kelly, Malamud & Zhou (J. Finance 2024).

**EXPERIMENT — deviation-gated.** Runs only under `docs/deviations.md` DEV-004, signed
2026-07-29. It exceeds README §8's capacity rule by construction: random Fourier features with
P >> N. That is the method, not an accident of it.

The comparison isolates MODEL CLASS, not information: identical inputs to Track A, identical
test folds (both consume `jorda.fold_iter`, so they match by construction rather than by two
implementations agreeing), identical target.

Both tracks run at the same capped N_train. A complexity grid c = P/N means nothing without a
window: KMZ work in the hundreds of observations, where P >> N is feasible and is the point.
Our expanding folds reach N ~ 18,000, where c = 20 would want 360,000 features -- infeasible
rather than faithful. Capping N_train makes it a head-to-head at the sample size §8's capacity
rule was actually written for, which is the claim under test.

Ridge is solved in the DUAL, Z'(ZZ' + lambda I)^-1 y. With P >> N that is an N x N solve
instead of P x P -- the numerically sane choice and also the cheap one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .jorda import _regime_series, _score, fold_iter

#: c = P/N, spanning well below 1 to well above, so double descent is observable if present.
COMPLEXITY_GRID = (0.1, 0.25, 0.5, 0.9, 1.1, 2.0, 5.0, 10.0, 20.0, 50.0)
#: Near-ridgeless to heavy. KMZ's headline result lives at high complexity AND high shrinkage.
SHRINKAGE_GRID = (1e-6, 1e-3, 1e-1, 1.0, 10.0)
N_TRAIN = 200
SEED = 20260729
GAMMA = 1.0        # RFF bandwidth on standardised inputs


def _rff(X: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Random Fourier features: cos(XW + b), scaled. Seeded draws, so runs are reproducible."""
    return np.sqrt(2.0 / W.shape[1]) * np.cos(X @ W + b)


def _dual_ridge(Ztr: np.ndarray, ytr: np.ndarray, Zte: np.ndarray, lam: float) -> np.ndarray:
    """Predict via the dual. Cheaper and better-conditioned than the primal when P >> N."""
    K = Ztr @ Ztr.T
    alpha = np.linalg.solve(K + lam * np.eye(K.shape[0]), ytr)
    return Zte @ (Ztr.T @ alpha)


def run(regime: str, h: int = 20, target: str = "change",
        complexity=COMPLEXITY_GRID, shrinkage=SHRINKAGE_GRID,
        n_train: int = N_TRAIN, shuffle_seed: int | None = None) -> pd.DataFrame:
    """OOS metrics across the (complexity, shrinkage) grid for one regime and horizon."""
    series = [s for _, s in _regime_series()[regime]]
    folds = list(fold_iter(series, h, target=target, use_extra=False,
                           shuffle_seed=shuffle_seed, max_train=n_train))
    if not folds:
        return pd.DataFrame()

    rows = []
    for c in complexity:
        P = max(2, int(round(c * n_train)))
        rng = np.random.default_rng(SEED)
        for lam in shrinkage:
            acts, preds, lvls = [], [], []
            for Xtr, ytr, Xte, yte, lvl, _, _ in folds:
                mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12      # train-only standardisation
                W = rng.standard_normal((Xtr.shape[1], P)) * GAMMA
                bb = rng.uniform(0, 2 * np.pi, P)
                Ztr, Zte = _rff((Xtr - mu) / sd, W, bb), _rff((Xte - mu) / sd, W, bb)
                ym = ytr.mean()
                preds.append(_dual_ridge(Ztr, ytr - ym, Zte, lam) + ym)
                acts.append(yte); lvls.append(lvl)
            m = _score(np.concatenate(acts), np.concatenate(preds), np.concatenate(lvls))
            rows.append({"regime": regime, "horizon": h, "c": c, "P": P,
                         "shrinkage": lam, **m})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = run("one_way_constrained", h=20, complexity=(0.5, 2.0, 20.0), shrinkage=(1e-3, 1.0))
    print(df[["c", "P", "shrinkage", "n", "rmse", "r2", "hit_rate"]].round(4).to_string(index=False))


# ================================================================================
# Block C — critique diagnostics. Both tracks face them.
#
# The Nagel objection to KMZ, implemented rather than cited: an apparent edge can be
# mechanical position-scaling with volatility rather than sign-prediction skill. A strategy
# that levers up when vol is low earns a Sharpe premium that looks like forecasting.
#
# So the benchmark is not zero. It is a VOL-MANAGED UNCONDITIONAL strategy on the same folds:
# always short the premium, sized 1/sigma. If a track cannot beat that, its edge is the
# sizing, not the signal.
# ================================================================================

def _hac_lrv(x: np.ndarray, lag: int) -> float:
    """Newey-West long-run variance of the MEAN of x. Bartlett kernel, bandwidth `lag`.

    Needed because strategy returns at horizon h overlap by h-1 periods, so the plain
    sqrt(var/n) standard error is understated by roughly sqrt(h). The first ledger quoted
    t = -11.5 on h=20 overlapping returns; that is the textbook signature of exactly this
    omission, and correcting it is not optional.
    """
    x = x - x.mean()
    n = len(x)
    g = (x @ x) / n
    for k in range(1, min(lag, n - 1) + 1):
        w = 1.0 - k / (lag + 1)
        g += 2 * w * (x[k:] @ x[:-k]) / n
    return float(max(g, 1e-18))


def _t_stats(x: np.ndarray, h: int) -> dict:
    """t on the mean of x, three ways: naive, HAC, and non-overlapping blocks.

    All three reported rather than the friendliest one. The naive figure stays visible so the
    size of the correction is auditable instead of quietly absorbed.
    """
    n = len(x)
    naive = x.mean() / (x.std(ddof=1) / np.sqrt(n)) if x.std() > 0 else 0.0
    hac = x.mean() / np.sqrt(_hac_lrv(x, max(h - 1, 1)) / n)
    blk = x[::max(h, 1)]                      # every h-th observation: non-overlapping
    nb = blk.mean() / (blk.std(ddof=1) / np.sqrt(len(blk))) if len(blk) > 2 and blk.std() > 0 else 0.0
    return {"t_naive": float(naive), "t_hac": float(hac), "t_nonoverlap": float(nb),
            "n_effective_blocks": int(len(blk))}


def _sharpe(pnl: np.ndarray, h: int) -> float:
    """Annualised, corrected for h-step overlap.

    Overlapping h-day returns are not independent, so scaling by sqrt(252) would inflate this
    by roughly sqrt(h). Scaling by sqrt(252/h) treats the series as its non-overlapping
    equivalent -- conservative, and the honest direction to err in.
    """
    sd = pnl.std(ddof=1)
    return float(pnl.mean() / sd * np.sqrt(252.0 / h)) if sd > 0 else 0.0


def strategy_diagnostics(regime: str, h: int = 20, c: float = 20.0, lam: float = 1.0,
                         n_train: int = N_TRAIN) -> dict:
    """Track A vs Track B vs an unconditional benchmark vs a VOL-MANAGED unconditional one."""
    series = [s for _, s in _regime_series()[regime]]
    folds = list(fold_iter(series, h, target="change", use_extra=False, max_train=n_train))
    P = max(2, int(round(c * n_train)))
    rng = np.random.default_rng(SEED)

    a_pnl, b_pnl, uncond, volman, sigmas, b_sign = [], [], [], [], [], []
    for Xtr, ytr, Xte, yte, _, _, _ in folds:
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
        # Track A: ridge on the raw feature, same fold.
        A = Xtr - Xtr.mean(0)
        beta = np.linalg.solve(A.T @ A + 1e-4 * np.eye(A.shape[1]), A.T @ (ytr - ytr.mean()))
        pa = (Xte - Xtr.mean(0)) @ beta + ytr.mean()
        # Track B: RFF ridge, same fold.
        W = rng.standard_normal((Xtr.shape[1], P)) * GAMMA
        bb = rng.uniform(0, 2 * np.pi, P)
        pb = _dual_ridge(_rff((Xtr - mu) / sd, W, bb), ytr - ytr.mean(),
                         _rff((Xte - mu) / sd, W, bb), lam) + ytr.mean()
        # sigma from the TRAINING block only -- using test-window vol would be the leak the
        # whole diagnostic is meant to detect.
        sig = ytr.std(ddof=1) or 1e-9
        # POSITION FOLLOWS THE FORECAST: long the premium when it is forecast to widen,
        # short when forecast to narrow. pnl = position * realised change = sign(pred) * y.
        #
        # This had the sign inverted (`-np.sign(...)`), which built a strategy that faded its
        # own signal. It was caught by the magnitude-decile table: P&L was negative in EVERY
        # decile including buckets where the hit rate was 67%, which is arithmetically
        # impossible for a strategy that trades WITH its forecast. Every Sharpe and alpha in
        # the first ledger was the exact negative of the truth.
        a_pnl.append(np.sign(pa) * yte)
        b_pnl.append(np.sign(pb) * yte)
        uncond.append(-yte)                      # always short, unit size
        volman.append(-yte / sig)                # always short, sized 1/sigma  <- the benchmark
        sigmas.append(np.full(len(yte), sig))
        b_sign.append(np.sign(pb))

    A_, B_, U_, V_ = (np.concatenate(x) for x in (a_pnl, b_pnl, uncond, volman))
    sig_all, bs = np.concatenate(sigmas), np.concatenate(b_sign)

    # Does Track B survive the vol-managed benchmark? Regress its PnL on it; the intercept is
    # what is left once mechanical sizing is accounted for.
    v = V_ - V_.mean()
    load = float(v @ (B_ - B_.mean()) / (v @ v))
    alpha = float(B_.mean() - load * V_.mean())
    resid = B_ - (alpha + load * V_)
    # alpha = mean(B) - load*mean(V), so its influence function is the residual: the HAC
    # long-run variance of resid IS the HAC variance of alpha.
    ta = _t_stats(resid + alpha, h)

    return {
        "regime": regime, "horizon": h, "c": c, "shrinkage": lam,
        "sharpe_track_a": _sharpe(A_, h),
        "sharpe_track_b": _sharpe(B_, h),
        "sharpe_unconditional": _sharpe(U_, h),
        "sharpe_vol_managed": _sharpe(V_, h),
        "track_b_alpha_vs_volmanaged": alpha,
        "track_b_t_alpha_naive": ta["t_naive"],
        "track_b_t_alpha_hac": ta["t_hac"],
        "track_b_t_alpha_nonoverlap": ta["t_nonoverlap"],
        "n_effective_blocks": ta["n_effective_blocks"],
        # Same correction audit applied to what the Sharpes rest on.
        "t_sharpe_b_hac": _t_stats(B_, h)["t_hac"],
        "t_sharpe_a_hac": _t_stats(A_, h)["t_hac"],
        "scope": f"N_train={n_train} (capped; see DEV-004), h={h}, expanding walk-forward, embargo=h",
        "track_b_load_on_volmanaged": load,
        # If the sign flips with vol, the "forecast" is a vol signal wearing a forecast's coat.
        "corr_track_b_sign_with_vol": float(np.corrcoef(bs, sig_all)[0, 1]),
        "turnover_track_b": float(np.abs(np.diff(bs)).mean() / 2),
        "n": int(len(B_)),
    }


def magnitude_deciles(regime: str, h: int = 20, c: float = 20.0, lam: float = 1.0,
                      n_train: int = N_TRAIN) -> pd.DataFrame:
    """Hit rate and P&L contribution by |Δπ| decile, both tracks, same folds.

    This is where the paradox lives. A 62% hit rate and a negative Sharpe are only compatible
    if the accuracy sits on small moves while the losses arrive on large ones — so the test is
    to sort outcomes by realised magnitude and look.
    """
    series = [s for _, s in _regime_series()[regime]]
    folds = list(fold_iter(series, h, target="change", use_extra=False, max_train=n_train))
    P = max(2, int(round(c * n_train)))
    rng = np.random.default_rng(SEED)
    acts, pa_all, pb_all = [], [], []
    for Xtr, ytr, Xte, yte, _, _, _ in folds:
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
        A = Xtr - Xtr.mean(0)
        beta = np.linalg.solve(A.T @ A + 1e-4 * np.eye(A.shape[1]), A.T @ (ytr - ytr.mean()))
        pa_all.append((Xte - Xtr.mean(0)) @ beta + ytr.mean())
        W = rng.standard_normal((Xtr.shape[1], P)) * GAMMA
        bb = rng.uniform(0, 2 * np.pi, P)
        pb_all.append(_dual_ridge(_rff((Xtr - mu) / sd, W, bb), ytr - ytr.mean(),
                                  _rff((Xte - mu) / sd, W, bb), lam) + ytr.mean())
        acts.append(yte)
    y = np.concatenate(acts)
    pa, pb = np.concatenate(pa_all), np.concatenate(pb_all)

    dec = pd.qcut(np.abs(y), 10, labels=False, duplicates="drop")
    rows = []
    for d in sorted(pd.unique(dec[~pd.isna(dec)])):
        m = dec == d
        for name, pred in (("A", pa), ("B", pb)):
            pnl = np.sign(pred[m]) * y[m]
            rows.append({
                "track": name, "decile": int(d) + 1,
                "mean_abs_move": float(np.abs(y[m]).mean()),
                "hit_rate": float((np.sign(pred[m]) == np.sign(y[m])).mean()),
                # Share of total P&L this decile contributes -- signed, so a decile that
                # destroys the result shows as a negative bar rather than a small one.
                "pnl_share": float(pnl.sum() / np.abs(np.sign(pred) * y).sum()),
                "pnl_mean": float(pnl.mean()),
                "n": int(m.sum()),
            })
    return pd.DataFrame(rows)
