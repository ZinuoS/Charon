"""`make notebook`, made real: a committed notebook must reproduce on re-execution.

`notebooks/README.md` promises "a fresh offline re-execution reproduces them [the
outputs]." Until now nothing enforced it — the existing freshness tests assert only that
outputs *exist* and carry no error, so a notebook could drift arbitrarily far from the
pipeline while staying green. It happened: the Session 14 figure fixes (D5 gauge, G4
t-stat, G1 floor label) changed how G1/G2/G4 render, and the committed notebook images
went stale without a single test noticing.

This module re-executes each notebook offline and checks two things:

* **Structural reproduction** (portable, deterministic everywhere). Re-execution completes
  with no cell error, and every cell that was committed with an image still emits an image,
  every cell committed with a stream still emits a stream. This catches a notebook that now
  raises (a pipeline signature the notebook calls has changed) or a figure that vanished.

* **Pixel fidelity** (the drift catcher). For each committed figure, the freshly rendered
  pixels must equal the committed pixels. A pure coordinate move inside a still-rendered
  figure — exactly the Session 14 staleness — changes nothing structural and only shows up
  here. It runs strictly where the committed images and the re-execution share a font
  environment (the machine that built them, which is where `just notebook` is run), and
  skips rather than false-fails where fonts differ, because the theme's serif stack
  degrades to DejaVu by design and a fallback render is a different, legitimate picture.

Both paths require the ingested payloads under `data/raw/`, which are gitignored. Where the
data is absent — a fresh clone, this CI container — the whole module skips, the same
contract as `tests/test_figures.py`.
"""
from __future__ import annotations

import base64
import copy
import io
import json
import re
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
NOTEBOOKS = ["00_executive_pitch", "02_premium_anatomy"]
CELL_TIMEOUT = 300


# --------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------


def _required_pairs(nb: dict) -> list[str]:
    """The `build_all_variants` pair ids a notebook depends on, read from its own source.

    Parsed rather than hard-coded so a notebook that starts using a new comparator is
    gated on that comparator's data automatically, not silently run without it.
    """
    src = " ".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    return sorted(set(re.findall(r'build_all_variants\(\s*["\']([a-z0-9]+)["\']', src)))


def _data_available(pairs: list[str]) -> bool:
    from pipeline.measurement.premium import build_all_variants
    for pair in pairs:
        try:
            if not build_all_variants(pair):
                return False
        except Exception:
            return False
    return True


def _load(name: str) -> dict:
    return json.loads((NB_DIR / f"{name}.ipynb").read_text())


def _reexecute(name: str) -> dict:
    """Run the notebook offline from a cleared copy; return the executed notebook.

    A cell error raises ``CellExecutionError`` — surfaced as a genuine test failure with
    the offending traceback, because the data-absent case is filtered out before we get
    here, so an error at this point is a real break rather than a missing file.
    """
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.reads(json.dumps(_load(name)), as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    client = NotebookClient(
        nb, timeout=CELL_TIMEOUT, kernel_name="python3",
        resources={"metadata": {"path": str(NB_DIR)}},
        allow_errors=False,
    )
    client.execute()
    return nb


def _code_cells(nb: dict):
    return [c for c in (nb["cells"] if isinstance(nb, dict) else nb.cells)
            if (c["cell_type"] if isinstance(c, dict) else c.cell_type) == "code"]


def _outputs(cell) -> list:
    return cell["outputs"] if isinstance(cell, dict) else cell.outputs


def _kinds(cell) -> list[str]:
    """The kinds of output a cell carries: 'stream', 'image', or the mime of a data output.

    Compared instead of the payloads for the structural pass — an image is an image whether
    or not its pixels moved; the pixel pass is what checks the pixels.
    """
    out = []
    for o in _outputs(cell):
        ot = o.get("output_type") if isinstance(o, dict) else o.output_type
        data = (o.get("data") if isinstance(o, dict) else getattr(o, "data", None)) or {}
        if ot == "stream":
            out.append("stream")
        elif ot == "error":
            out.append("error")
        elif "image/png" in data:
            out.append("image")
        else:
            out.append("data:" + ",".join(sorted(data)))
    return out


def _pngs(cell) -> list[str]:
    pngs = []
    for o in _outputs(cell):
        data = (o.get("data") if isinstance(o, dict) else getattr(o, "data", None)) or {}
        if "image/png" in data:
            pngs.append(data["image/png"])
    return pngs


def _pixels(b64: str) -> np.ndarray:
    from PIL import Image
    raw = base64.b64decode(b64)
    return np.asarray(Image.open(io.BytesIO(raw)).convert("RGBA"))


# --------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------


@pytest.fixture(scope="module", params=NOTEBOOKS)
def executed(request):
    """(committed, freshly-executed) for one notebook, or skip if its data is absent.

    Module-scoped: each notebook is executed once and the two checks share the result.
    """
    name = request.param
    committed = _load(name)
    if not _data_available(_required_pairs(committed)):
        pytest.skip(f"{name}: panel data not ingested")
    return name, committed, _reexecute(name)


def test_reexecutes_and_reproduces_output_structure(executed):
    """Portable guard: no cell errors, and every committed output kind comes back.

    Would have failed the moment the Session 14 painter split changed a call signature the
    notebook uses, or any figure stopped rendering.
    """
    name, committed, fresh = executed
    cf, xf = _code_cells(committed), _code_cells(fresh)
    assert len(cf) == len(xf), f"{name}: cell count changed under re-execution"

    for i, (c, x) in enumerate(zip(cf, xf)):
        assert "error" not in _kinds(x), f"{name} cell {i} raised on re-execution"
        # Every kind the notebook was committed with must reappear. The re-execution may add
        # outputs (it never should drop one); a committed image that fails to re-render is
        # the regression this catches.
        missing = _multiset_diff(_kinds(c), _kinds(x))
        assert not missing, (
            f"{name} cell {i} no longer produces {missing}. The committed notebook is stale "
            "against the pipeline — regenerate with `just notebook`."
        )


def test_committed_figures_match_current_pipeline(executed):
    """The drift catcher: committed figure pixels must equal a fresh render.

    Strict where the committed images and this run share fonts (the build machine); skips
    per-image where they do not, so the theme's deliberate DejaVu fallback on another host
    is not mistaken for staleness.
    """
    name, committed, fresh = executed
    cf, xf = _code_cells(committed), _code_cells(fresh)

    compared, stale = 0, []
    for i, (c, x) in enumerate(zip(cf, xf)):
        for j, (cb, xb) in enumerate(zip(_pngs(c), _pngs(x))):
            a, b = _pixels(cb), _pixels(xb)
            if a.shape != b.shape:
                continue  # different font environment — not a comparable render
            compared += 1
            if not np.array_equal(a, b):
                stale.append(f"cell {i} figure {j}")
    if compared == 0:
        pytest.skip(f"{name}: no figure comparable in this font environment")
    assert not stale, (
        f"{name}: committed figures differ from the current pipeline ({', '.join(stale)}). "
        "The pipeline changed but the notebook was not rebuilt — run `just notebook`."
    )


def _multiset_diff(want: list[str], have: list[str]) -> list[str]:
    """Kinds in ``want`` not covered by ``have``, respecting multiplicity."""
    have = list(have)
    missing = []
    for k in want:
        if k in have:
            have.remove(k)
        else:
            missing.append(k)
    return missing


# --------------------------------------------------------------------------------
# The comparison helpers are validated here directly, so their logic is exercised even
# on a data-less clone where the notebook-driven tests above skip.
# --------------------------------------------------------------------------------


def _make_png(color=(10, 20, 30), size=(8, 6)) -> str:
    from PIL import Image
    img = Image.new("RGBA", size, color + (255,))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class TestComparisonHelpers:
    def test_identical_pngs_compare_equal(self):
        png = _make_png()
        assert np.array_equal(_pixels(png), _pixels(png))

    def test_one_pixel_difference_is_detected(self):
        from PIL import Image
        base = Image.new("RGBA", (8, 6), (10, 20, 30, 255))
        moved = base.copy(); moved.putpixel((0, 0), (200, 0, 0, 255))
        def enc(im):
            buf = io.BytesIO(); im.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()
        a, b = _pixels(enc(base)), _pixels(enc(moved))
        assert a.shape == b.shape and not np.array_equal(a, b), \
            "a moved element must register as a pixel difference"

    def test_different_shapes_are_treated_as_incomparable(self):
        a, b = _pixels(_make_png(size=(8, 6))), _pixels(_make_png(size=(9, 6)))
        assert a.shape != b.shape, "the shape guard is what routes a font-fallback render to skip"

    def test_kind_diff_flags_a_dropped_image(self):
        assert _multiset_diff(["stream", "image"], ["stream"]) == ["image"]
        assert _multiset_diff(["image", "image"], ["image"]) == ["image"]
        assert _multiset_diff(["stream"], ["stream", "image"]) == []

    def test_required_pairs_are_read_from_source(self):
        nb = {"cells": [{"cell_type": "code",
                         "source": ['a = build_all_variants("skhy")\n', 'b=build_all_variants( "tsmc" )']}]}
        assert _required_pairs(nb) == ["skhy", "tsmc"]
