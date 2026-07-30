"""Every committed notebook must carry its outputs.

The repository IS the delivery medium — a reader opens the notebooks on GitHub and sees the
figures, or sees nothing. So an unexecuted notebook is not a cosmetic problem, it is a blank
deliverable, and it is silent: the file is valid, the tests pass, the push succeeds.

It happened on 2026-07-30. `scripts.build_client_note` REGENERATES 01 from scratch, and it was
run after the execute pass, wiping fifteen figures. `scripts/pitch_refresh.py` sequences build
-> execute correctly; the mistake was hand-sequencing instead of using it. This test is the
reason that mistake cannot ship twice.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

NOTEBOOKS = sorted((Path(__file__).resolve().parents[1] / "notebooks").glob("*.ipynb"))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_every_code_cell_ran(path):
    nb = json.loads(path.read_text())
    code = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    unrun = [i for i, c in enumerate(code) if not c.get("execution_count")]
    assert not unrun, (
        f"{path.name}: {len(unrun)}/{len(code)} code cells have no execution_count, so the "
        "notebook renders blank on GitHub. Run `uv run python -m scripts.pitch_refresh`, "
        "which sequences build-then-execute — do not hand-run the build scripts after "
        "executing, because they regenerate the notebook and discard its outputs."
    )


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebooks_that_draw_have_figures(path):
    """A notebook that calls a figure builder must actually carry rendered images."""
    nb = json.loads(path.read_text())
    src = "".join("".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code")
    if "figures." not in src and "PANELS[" not in src:
        pytest.skip(f"{path.name} draws nothing")
    images = sum("image/png" in o.get("data", {})
                 for c in nb["cells"] for o in c.get("outputs", []))
    assert images, f"{path.name} builds figures but carries none — see the message above."
