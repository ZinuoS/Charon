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
