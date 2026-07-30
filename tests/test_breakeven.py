"""Breakeven arithmetic. The pitch's central number, so its identities are pinned."""
from __future__ import annotations

import pytest

from pipeline.package import breakeven as B


def test_breakeven_and_critical_carry_are_mutual_inverses():
    """The two entry points answer the same question from opposite ends. If they disagree, one
    of them is wrong and the sheet quotes whichever it happened to call."""
    pi, T = 0.226, 252.0
    cc = B.critical_carry_bp(pi, T, half_life_days=300.0)
    B.CARRY_BRACKET_BP["_probe"] = cc - B.CONVERSION_FEE_BP * 252.0 / T
    try:
        assert B.breakeven_half_life(pi, T, "_probe") == pytest.approx(300.0, rel=0.02)
    finally:
        del B.CARRY_BRACKET_BP["_probe"]


def test_carry_exceeding_the_distance_to_the_floor_is_unreachable_not_negative():
    """A carry larger than the entire premium cannot have a finite breakeven. Returning a
    number here would put a plausible-looking figure on a sheet for a trade that cannot pay."""
    assert B.breakeven_half_life(0.005, 252, "high") is None


def test_higher_carry_demands_faster_convergence():
    hs = [B.breakeven_half_life(0.226, 252, b) for b in ("low", "mid", "high")]
    assert hs == sorted(hs, reverse=True), f"breakeven should tighten as carry rises: {hs}"


def test_the_brackets_straddle_the_estimated_half_life():
    """The session's finding: whether this trade pays is decided by numbers the repo does not
    hold. If a future cost landing collapses the bracket to one side, this fails and the sheet's
    tone has to be rewritten — which is the correct trigger for doing so."""
    v = B.verdict()
    pays = [v[f"pays_at_{b}"] for b in ("low", "mid", "high")]
    assert True in pays and False in pays, f"bracket no longer straddles: {pays}"


def test_hatched_components_are_named_not_counted():
    v = B.verdict()
    assert len(v["hatched_components"]) == 4
    assert all(isinstance(c, str) and c for c in v["hatched_components"])
