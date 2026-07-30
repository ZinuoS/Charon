"""Everything the pitch reads, refreshed in dependency order.

    uv run python -m scripts.pitch_refresh

A Python script rather than a justfile recipe because **`just` is not installed here**, so the
recipe was documentation pretending to be a command — and the one thing that has to work on
the morning should not be the thing nobody has run. The justfile target now calls this, so
both paths execute the same sequence.

Fails loudly and stops at the first broken step: a refresh that half-succeeds and reports
success is worse than one that does not run, because the notebooks would then be a mix of
fresh and stale.

Deliberately NOT scheduled. It is one command on one morning; a launchd job for that is more
moving parts than the thing it automates. TWSE SBL is also deliberately absent — it feeds only
the utilization row-counter, and the cross-pair ablation it exists for needs ~60 sessions
against the four trading days before the pitch.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ("00_executive_pitch", "01_client_note", "02_premium_anatomy",
             "04_regimes_convergence", "05_hypothesis_engines", "06_complexity_ledger")

# Order matters: borrow state feeds the sheets, the table feeds notebook 04, the builders
# write the notebooks that then get executed. Anything out of order silently ships stale text.
STEPS = [
    ("fresh borrow state (D3)", [sys.executable, "-m", "pipeline.ingest.d3_lending"]),
    ("S4 metrics table", [sys.executable, "-m", "scripts.s4_table"]),
    ("build 00 pitch", [sys.executable, "-m", "scripts.build_pitch"]),
    ("build 01 client note", [sys.executable, "-m", "scripts.build_client_note"]),
    ("build 02 anatomy", [sys.executable, "-m", "scripts.build_notebook_01"]),
    ("build 04 regimes", [sys.executable, "-m", "scripts.build_notebook_04"]),
    ("build 05 engines", [sys.executable, "-m", "scripts.build_notebook_05"]),
    ("build 06 complexity ledger", [sys.executable, "-m", "scripts.build_notebook_06"]),
]


def _run(label: str, cmd: list[str]) -> None:
    print(f"\n>>> {label}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"\nFAILED at: {label}. Nothing after this ran; fix it and re-run.")


def main() -> int:
    for label, cmd in STEPS:
        _run(label, cmd)

    for nb in NOTEBOOKS:
        _run(f"execute {nb}", [
            sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
            "--execute", "--inplace", "--ExecutePreprocessor.timeout=3000",
            f"notebooks/{nb}.ipynb"])

    _run("client pack panels", [sys.executable, "-m", "scripts.export_client_pack"])
    _run("social card", [sys.executable, "-m", "scripts.make_social_card"])

    # Cell-level errors do not fail nbconvert, so they are checked explicitly. A notebook that
    # renders a traceback where a figure should be is the failure mode that reaches a reader.
    import json
    figs = errs = 0
    for nb in NOTEBOOKS:
        doc = json.loads((ROOT / "notebooks" / f"{nb}.ipynb").read_text())
        for cell in doc["cells"]:
            for out in cell.get("outputs", []):
                if out["output_type"] == "error":
                    errs += 1
                    print(f"  ERROR in {nb}: {out['ename']}")
                if "image/png" in out.get("data", {}):
                    figs += 1
    if errs:
        sys.exit(f"\n{errs} cell error(s) in the executed notebooks. Do not present these.")

    _run("test suite", [sys.executable, "-m", "pytest", "-q"])
    _run("validation gate", [sys.executable, "-m", "scripts.validate"])
    print(f"\nREADY — {len(NOTEBOOKS)} notebooks, {figs} figures, 0 cell errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
