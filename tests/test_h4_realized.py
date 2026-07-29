"""H4 realized variance decomposition — the identity, and the small-sample guard."""
from __future__ import annotations
import numpy as np, pandas as pd, pytest
from hypotheses.h4_vol_decomposition.realized import decompose_variance, compare_pairs


def _series(vals, start="2026-01-01"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="D"))


@pytest.fixture
def synthetic():
    rng = np.random.default_rng(20260729)
    n = 500
    local = _series(1_000_000 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))
    fx = _series(1400 * np.exp(np.cumsum(rng.normal(0, 0.004, n))))
    pi = np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    adr = (local.values * pi) / (10 * fx.values) * 10
    return _series(adr), local, fx


def test_identity_is_exact(synthetic):
    adr, local, fx = synthetic
    d = decompose_variance(adr, local, fx, 0.1, "synthetic")
    assert d.residual < 1e-12, "the log decomposition is an identity, not an approximation"


def test_shares_reconstruct_unity(synthetic):
    adr, local, fx = synthetic
    d = decompose_variance(adr, local, fx, 0.1)
    assert abs(sum(d.shares.values()) - 1.0) < 1e-9


def test_covariances_are_reported_not_folded_away(synthetic):
    """Folding covariances into the components would hide the case that matters: a small
    premium-variance share coexisting with a large negative covariance."""
    adr, local, fx = synthetic
    d = decompose_variance(adr, local, fx, 0.1)
    assert set(d.covariances) == {"local_fx", "local_pi", "fx_pi"}
    assert any(k.startswith("cov_") for k in d.shares)


def test_small_sample_is_flagged_not_silently_reported(synthetic):
    adr, local, fx = synthetic
    d = decompose_variance(adr.iloc[:12], local.iloc[:12], fx.iloc[:12], 0.1, "short")
    assert any("not validation" in n for n in d.notes), \
        "README §8: a sample this size must announce itself"


def test_zero_premium_variance_when_pair_is_locked(synthetic):
    """A perfectly fungible pair (pi identically constant) must show zero premium variance."""
    _, local, fx = synthetic
    adr = _series((local.values / (10 * fx.values)) * 10)
    d = decompose_variance(adr, local, fx, 0.1, "locked")
    assert d.components["pi"] < 1e-24


class TestLivePanel:
    def test_panel_identity_holds_on_real_data(self):
        df = compare_pairs()
        if df.empty:
            pytest.skip("panel not ingested")
        assert (df["residual"] < 1e-12).all(), "identity must hold on every real pair"

    def test_fungible_control_shows_offsetting_covariance(self):
        """BABA is the panel's control: its premium is noise around parity, so premium
        variance should be largely cancelled by negative covariance with the local leg."""
        df = compare_pairs()
        if df.empty or "baba" not in set(df["pair"]):
            pytest.skip("baba not ingested")
        row = df[df.pair == "baba"].iloc[0]
        assert row["share_cov_local_pi"] < -0.5, "expected strong offsetting covariance"
        assert row["share_local"] > 0.8, "a fungible pair's ADR variance is mostly local"
