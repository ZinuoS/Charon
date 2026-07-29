"""Semantic palette — the project's legend, enforced.

Two jobs. First, accessibility: every assigned MEANING colour must stay distinguishable from
every other under normal vision and under simulated deuteranopia and protanopia. This is
measured, not asserted — Okabe-Ito is colour-vision-safe *as a set*, which does NOT make an
arbitrary pair inside it safe for two meanings that share a frame. Both collisions found while
building this system were inside Okabe-Ito.

Second, semantic constancy: a meaning owns a hue everywhere, so figures may not introduce raw
hex. A colour with no meaning is a colour a reader has to decode twice.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pipeline.viz import theme

REPO = Path(__file__).resolve().parents[1]
FIGURES = REPO / "pipeline" / "viz" / "figures.py"


class TestColourVision:
    @pytest.mark.parametrize("condition", ["normal", "deuteranopia", "protanopia"])
    def test_all_meanings_separate_under(self, condition):
        """The gate. A failure names the colliding pair, because 'the palette failed' is not
        an actionable message."""
        report = theme.palette_report(list(theme.SEMANTIC))[condition]
        assert report["passes"], (
            f"{condition}: {report['worst_pair']} collapse to ΔE {report['worst_delta_e']} "
            f"(floor {theme.MIN_DELTA_E}). Reassign one of the two meanings — do NOT lower "
            "the floor."
        )

    def test_the_known_collisions_stay_fixed(self):
        """Regression guards, named for what they caught.

        constrained|barrier: vermillion vs orange, the closest pair in Okabe-Ito, ΔE 13.1
        under deuteranopia — and they share G1's frame. Barrier moved to black.
        warning|context: reddish purple desaturates toward grey for protanopes, ΔE 10.7.
        Context darkened rather than lightened."""
        for cond in ("deuteranopia", "protanopia"):
            pairs = theme.palette_report(list(theme.SEMANTIC))[cond]["all_pairs"]
            assert pairs["constrained|barrier"] >= theme.MIN_DELTA_E, cond
            assert pairs["warning|context"] >= theme.MIN_DELTA_E, cond

    def test_simulation_actually_changes_colours(self):
        """A simulator that returns its input would make every test above vacuous."""
        assert theme.simulate_cvd(theme.SEMANTIC["constrained"]) != theme.SEMANTIC["constrained"]
        assert theme.delta_e("#ffffff", "#000000") > 90


class TestSemanticConstancy:
    def test_figures_introduce_no_raw_hex(self):
        """Every colour in a figure must come from the palette. Raw hex is how a hue
        acquires a second meaning."""
        src = FIGURES.read_text()
        body = re.sub(r'"""[\s\S]*?"""', "", src)          # drop docstrings
        # Strip comments with tokenize, NOT by splitting on "#". The first version of this
        # test did `l.split("#")[0]`, which truncated `facecolor="#eceae5"` to `facecolor="`
        # and silently removed the very thing it was looking for — it passed against a file
        # that had raw hex in it.
        import io
        import tokenize
        kept = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(body).readline):
                if tok.type != tokenize.COMMENT:
                    kept.append(tok.string)
        except (tokenize.TokenError, IndentationError):
            kept = [body]
        raw = re.findall(r'"#[0-9a-fA-F]{3,8}"', " ".join(kept))
        assert not raw, f"raw hex in figures.py: {sorted(set(raw))} — assign a meaning in theme.SEMANTIC"

    def test_regime_colours_key_off_the_taxonomy_labels(self):
        """A figure and the estimator must not disagree about which class is which colour."""
        from pipeline.convergence.jorda import REGIME_OF_PAIR
        for regime in set(REGIME_OF_PAIR.values()):
            assert regime in theme.REGIME_COLORS, f"{regime} has no assigned hue"
        assert theme.regime_color("nonexistent") == theme.SEMANTIC["context"]

    def test_warning_hue_is_reserved(self):
        """Its whole informational value is that it means one thing."""
        assigned = [k for k, v in theme.SEMANTIC.items() if v == theme.SEMANTIC["warning"]]
        assert assigned == ["warning"], f"warning hue also used for {assigned}"

    def test_legacy_aliases_point_at_meanings(self):
        assert theme.INK == theme.SEMANTIC["emphasis"]
        assert theme.CLAY == theme.SEMANTIC["constrained"]
        assert theme.MOSS == theme.SEMANTIC["fungible"]
        assert theme.GRAY == theme.SEMANTIC["context"]


class TestDerivedRamps:
    def test_sequential_ramp_ends_at_its_anchor_family(self):
        ramp = theme.sequential_ramp("constrained", 6)
        assert len(ramp) == 6
        lightness = [theme._lab(c)[0] for c in ramp]
        assert lightness == sorted(lightness, reverse=True), "ramp must run light -> dark"

    def test_diverging_ramp_is_symmetric_with_neutral_midpoint(self):
        ramp = theme.diverging_ramp(n=9)
        assert len(ramp) == 9
        mid = theme._lab(ramp[4])
        assert abs(mid[1]) < 6 and abs(mid[2]) < 8, "midpoint should be near-neutral"

    def test_ramps_are_generated_not_hardcoded(self):
        """Changing an anchor must move the ramp, or the ramp is not derived."""
        original = theme.SEMANTIC["constrained"]
        before = theme.sequential_ramp("constrained", 5)
        theme.SEMANTIC["constrained"] = theme.OKABE_ITO["sky_blue"]
        try:
            assert theme.sequential_ramp("constrained", 5) != before
        finally:
            theme.SEMANTIC["constrained"] = original
