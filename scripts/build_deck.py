"""Assemble the ordered deck from the exported panel files.

    uv run python -m scripts.build_deck

Copies the panels into presentation order under data/derived/deck/ with numeric prefixes, and
writes one speaker note per slide to a SEPARATE file -- notes belong in the presenter's hand,
not on the slide.

No re-rendering: the panels are already correct, and re-deriving them here would be a second
place that has to agree with the exporter about what a panel is.
"""

from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "derived" / "client_pack"
OUT = ROOT / "data" / "derived" / "deck"

#: (panel stem, one-line speaker note in the approved layman register)
ORDER = [
    ("P0a_the_stage", "Set the stage: Korean rules and the won move this gap on their own."),
    ("P1_situation", "The gap is 22.6% and the trade that normally closes it runs one way."),
    ("P2_structure", "You hold one position; the Korean plumbing sits on our side."),
    ("P3_economics", "It pays if your carry stays under about 79 basis points a month."),
    ("P7_the_chain", "Walk the six steps — the last one is why the first five matter."),
    ("P8_scenario_pnl", "Best case pays a fraction of your margin; the realised case cost all of it."),
    ("P4a_payoff", "Gain is capped by the floor. Loss is not capped by anything on file."),
    ("P4b_margin_path", "A move that already happened called for 44 cents per dollar."),
    ("P5_size_and_exit", "Getting out is easy. Borrowing the shares to sell is the limit."),
    ("P6_what_you_receive", "Monthly: the gap, the valve, and three things that either happened or did not."),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    notes, missing = [], []
    for i, (stem, note) in enumerate(ORDER, 1):
        found = False
        for ext in ("png", "pdf"):
            src = SRC / f"{stem}.{ext}"
            if src.is_file():
                shutil.copyfile(src, OUT / f"{i:02d}_{stem}.{ext}")
                found = True
        if not found:
            missing.append(stem)
            continue
        notes.append(f"{i:02d}. {stem}\n    {note}\n")
    (OUT / "speaker_notes.txt").write_text(
        "SPEAKER NOTES — one line per slide. Not on the slides.\n"
        "Brackets: four of five cost components are assumptions, not quotes. Say so.\n\n"
        + "\n".join(notes))
    print(f"  {len(notes)} slides -> {OUT}")
    if missing:
        print(f"  MISSING (not exported yet): {missing}")
    print(f"  speaker notes -> {OUT / 'speaker_notes.txt'}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
