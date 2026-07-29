"""M1 — comparator-pair premium construction (README §4 D6, §8).

There is deliberately almost no code here. The comparator premium is built by calling
:func:`pipeline.measurement.premium.build_all_variants` with a different ``pair_id`` —
the *same* function, the *same* join semantics, the *same* ratio handling that the SKHY
pair uses.

That is the point. README §8 makes the D6 panel the training universe and SKHY a forward
test, which is only a valid design if the two are measured identically. A separate
comparator implementation, however faithful, would be an untested assumption that the
constructions match; a shared code path makes it a fact, and
``tests/test_comparators.py`` asserts the paths are literally the same object.

No network. Reads only what ingestion wrote.
"""

from __future__ import annotations

import pandas as pd

from pipeline.ingest.registry import PAIRS
from pipeline.measurement.premium import (
    PremiumVariant,
    build_all_variants,
    compute_premium,  # re-exported: identical construction, not a copy
)

#: Pairs whose legs are all present on disk are the panel; the rest are coverage gaps.
COMPARATOR_PAIRS = tuple(p.pair_id for p in PAIRS if p.pair_id != "skhy")


def build_comparator(pair_id: str, start: str | None = None) -> list[PremiumVariant]:
    """π variants for one comparator pair, via the shared SKHY code path."""
    if pair_id == "skhy":
        raise ValueError("skhy is the forward-test instrument, not a comparator (README §8)")
    return build_all_variants(pair_id, start=start)


def available_comparators() -> list[str]:
    """Comparator pairs whose legs are actually on disk right now."""
    out = []
    for pair_id in COMPARATOR_PAIRS:
        try:
            if build_all_variants(pair_id):
                out.append(pair_id)
        except Exception:
            continue
    return out


def panel_summary(start: str | None = None) -> pd.DataFrame:
    """One row per available comparator variant — the S3 coverage view, read-only here."""
    rows = []
    for pair_id in available_comparators():
        for v in build_comparator(pair_id, start=start):
            rows.append(v.describe())
    return pd.DataFrame(rows)
