"""Lint: figure chrome goes through `finalize`, or it does not exist.

Every collision in the Session 11 and 13 audits had one root cause — chrome placed by
whoever wrote the figure, each choosing coordinates independently. `finalize` owns the
placement; this test owns the rule, so the fix is structural rather than remembered.
"""
from __future__ import annotations
import ast, json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"suptitle", "tight_layout"}
THEME = ROOT / "pipeline" / "viz" / "theme.py"


def _notebook_sources() -> list[tuple[str, str]]:
    out = []
    for nb in sorted((ROOT / "notebooks").glob("*.ipynb")):
        doc = json.loads(nb.read_text())
        for i, c in enumerate(doc.get("cells", [])):
            if c.get("cell_type") == "code":
                out.append((f"{nb.name}:cell{i}", "".join(c["source"])))
    return out


def _calls(src: str) -> set[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            found.add(node.func.attr)
    return found


@pytest.mark.parametrize("name,src", _notebook_sources(), ids=lambda x: x if isinstance(x, str) else "")
def test_notebooks_do_not_place_chrome_directly(name, src):
    if not isinstance(src, str):
        pytest.skip("parametrize placeholder")
    offending = _calls(src) & FORBIDDEN
    assert not offending, (
        f"{name} calls {sorted(offending)}. Figure chrome is placed by "
        "pipeline.viz.theme.finalize(), which reserves its own space; a direct call "
        "does not know what other chrome has claimed and is how collisions return."
    )


def test_finalize_exists_and_owns_the_full_chrome_set():
    from pipeline.viz import theme
    import inspect
    params = set(inspect.signature(theme.finalize).parameters)
    assert {"fig", "headline", "subtitle", "source", "footnote", "kicker"} <= params


def test_finalize_places_every_element_it_is_given():
    import matplotlib; matplotlib.use("Agg")
    from pipeline.viz import theme
    theme.apply()
    fig, ax = theme.figure()
    ax.plot([0, 1], [0, 1])
    theme.finalize(fig, headline="H", subtitle="S", source="Src", footnote="F", kicker="k")
    texts = [t.get_text() for t in fig.texts]
    assert "H" in texts and "S" in texts and "F" in texts
    assert any(t.startswith("Source: ") for t in texts)
    assert any("K" in t for t in texts), "kicker rendered as tracked caps"


def test_chrome_stack_orders_kicker_above_headline_above_subtitle():
    """The ordering bug that shipped once: laying the stack out downward makes each
    element's position depend on what follows, and the kicker overprinted the subtitle."""
    import matplotlib; matplotlib.use("Agg")
    from pipeline.viz import theme
    theme.apply()
    fig, ax = theme.figure()
    ax.plot([0, 1], [0, 1])
    theme.finalize(fig, headline="HEAD", subtitle="SUB", kicker="kick")
    pos = {t.get_text(): t.get_position()[1] for t in fig.texts}
    kicker_y = max(y for t, y in pos.items() if "K" in t and t not in ("HEAD", "SUB"))
    assert kicker_y > pos["HEAD"] > pos["SUB"]


def test_obol_is_drawn_not_an_image_asset():
    import matplotlib; matplotlib.use("Agg")
    from pipeline.viz import theme
    theme.apply()
    fig, ax = theme.figure()
    before = len(ax.collections)
    theme.obol(ax, 0.5, 0.5)
    assert len(ax.collections) == before + 2, "coin glyph is two drawn scatters, no asset"


class TestPaletteIsolation:
    """The public repo must be structurally incapable of rendering brand colours."""

    def test_public_palette_contains_no_env_derived_values(self, monkeypatch):
        from pipeline.viz import theme
        monkeypatch.delenv("PRESENTATION_PALETTE", raising=False)
        monkeypatch.delenv("CHARON_PALETTE", raising=False)
        name, pal = theme.active_palette()
        assert name == "public"
        assert pal == theme.PALETTES["public"]

    def test_requesting_presentation_without_an_anchor_falls_back(self, monkeypatch):
        """Not an error — a silent, safe fallback. A public checkout has no anchor."""
        from pipeline.viz import theme
        monkeypatch.delenv("PRESENTATION_PALETTE", raising=False)
        monkeypatch.setenv("CHARON_PALETTE", "presentation")
        assert theme.active_palette()[0] == "public"

    def test_anchor_yields_a_derived_family_not_a_hand_picked_set(self, monkeypatch):
        from pipeline.viz import theme
        monkeypatch.setenv("PRESENTATION_PALETTE", "#a4243b")
        monkeypatch.setenv("CHARON_PALETTE", "presentation")
        name, pal = theme.active_palette()
        assert name == "presentation"
        assert pal["clay"] == "#a4243b"
        assert pal["moss"] != pal["clay"], "third series derives from the anchor"
        assert pal["ink"] == theme.PALETTES["public"]["text"], \
            "the field stays neutral — emphasis only, never full-chart colour"

    def test_no_brand_hex_is_committed_anywhere(self):
        """A committed anchor would defeat the whole mechanism."""
        import subprocess, re
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout
        for f in out.splitlines():
            p = root / f
            if p.suffix in {".py", ".md", ".toml"} and p.is_file():
                for line in p.read_text(errors="replace").splitlines():
                    if "PRESENTATION_PALETTE=" in line:
                        val = line.split("PRESENTATION_PALETTE=", 1)[1].strip()
                        assert not re.match(r"^#?[0-9a-fA-F]{6}", val), \
                            f"{f}: a brand hex is committed"
