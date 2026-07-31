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
    DEFAULT_SOURCE,
    PAIR_SOURCE,
    PremiumVariant,
    _load_close,
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


# --------------------------------------------------------------------------------
# Panel description — what the training universe actually covers, and what it costs
# --------------------------------------------------------------------------------
#
# These describe the panel; they do not construct anything. The construction stays shared
# with the SKHY path above, which is the whole point of this module.


def coverage_table() -> pd.DataFrame:
    """One row per registry pair: regime, span, sample restriction, and why.

    Includes pairs that are EXCLUDED and pairs that resolve to nothing, because a panel
    described only by its members overstates itself. A reader needs to see what was
    attempted and dropped, not only what survived.
    """
    from pipeline.convergence.jorda import FORWARD_TEST_PAIRS, REGIME_OF_PAIR

    rows = []
    for p in PAIRS:
        try:
            v = build_all_variants(p.pair_id)[0]
            n, first, last = v.n_obs, v.first, v.last
        except Exception:
            n, first, last = 0, None, None
        regime = ("forward test (never fitted)" if p.pair_id in FORWARD_TEST_PAIRS
                  else "excluded" if getattr(p, "excluded", False)
                  else REGIME_OF_PAIR.get(p.pair_id, "unreachable — no data landed"))
        rows.append({
            "pair": p.pair_id, "regime": regime, "n_obs": n, "first": first, "last": last,
            "ratio": p.local_shares_per_adr, "ratio_confirmed": p.confirmed,
            "sample_start": getattr(p, "sample_start", None),
            "sample_end": getattr(p, "sample_end", None),
            "restriction_reason": (getattr(p, "sample_reason", "") or "").split(".")[0] or None,
        })
    return pd.DataFrame(rows).sort_values(["regime", "pair"]).reset_index(drop=True)


def calendar_cost() -> pd.DataFrame:
    """What the three-calendar join costs, measured inside the span all three legs share.

    ``PremiumVariant.dropped_to_join`` is the wrong number for this question: it compares
    against the LONGEST leg, so a pair whose local line starts fifteen years after its ADR
    reports an enormous "loss" that is really just a short leg. The honest measurement is
    taken INSIDE the overlapping span, where all three legs exist and the only thing
    separating them is which days each market chose to open.
    """
    rows = []
    for p in PAIRS:
        source = PAIR_SOURCE.get(p.pair_id, DEFAULT_SOURCE)
        fx_source = "d1_prices" if p.pair_id == "skhy" else source
        try:
            adr = _load_close(source, p.adr)
            local = _load_close(source, p.local)
            fx = _load_close(fx_source, p.fx)
        except Exception:
            continue
        lo = max(s.index.min() for s in (adr, local, fx))
        hi = min(s.index.max() for s in (adr, local, fx))
        if lo >= hi:
            continue
        a, l, f = ({d for d in s.index if lo <= d <= hi} for s in (adr, local, fx))
        both = a & l
        joined = both & f
        rows.append({
            "pair": p.pair_id,
            "overlap_years": round((hi - lo).days / 365.25, 1),
            "adr_sessions": len(a), "local_sessions": len(l),
            "adr_only": len(a - l), "local_only": len(l - a),
            "both_equity_legs": len(both), "joined_all_three": len(joined),
            "lost_to_fx_calendar": len(both - f),
            "pct_lost_to_equity_calendars": round(
                100 * (1 - len(both) / ((len(a) + len(l)) / 2)), 1),
            "pct_lost_to_fx_calendar": round(100 * len(both - f) / len(both), 1) if both else None,
        })
    return pd.DataFrame(rows)
