"""Cross-provider reconciliation: two sources for one series must agree, or say why.

Once a series has more than one provider, disagreement between them is *observable*
rather than hypothetical — and disagreement is the signature of a whole class of silent
corruption that no single-provider pipeline can detect: a mis-parsed date convention (the
TWSE ROC calendar), an adjusted-vs-raw close mix-up, a stale bar, an off-by-one timezone
filing, or a symbol collision.

This module is deliberately **not** an averaging or repair step. It reports; it never
reconciles by picking a winner or splitting a difference. A repaired series hides the
defect it repaired, and README §8 wants the diagnosis, not a rescued number.

The output feeds two places: the notebook's provenance table (so a reader can see the
series was independently corroborated) and the golden tests (so a future parser change
that breaks a convention fails loudly).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# Default tolerance for close-price agreement between two providers, in relative terms.
# 10bp is deliberately loose: two venues' official closes for the same instrument can
# differ legitimately (consolidated tape vs. primary-listing print, or an FX reference
# fix vs. a spot snapshot). The point is to catch structural breaks — wrong year, wrong
# scale, wrong instrument — not to police the last basis point.
DEFAULT_RTOL = 0.001

# FX *fixes* are a different problem from equity closes. Two fixes of the same pair taken
# hours apart are both correct and will differ persistently — that difference is signal
# about observation timing, not error. Measured 2026-07-29 on 2,850 overlapping days of
# USD/KRW, ECB (~16:00 CET) vs FRED H.10 (noon New York, ~2h later):
#
#     mean +0.055%   median +0.053%   sd 0.263%   p95 0.511%   max 2.95%
#
# So ~50bp covers 95% of days. The tolerance below is set above that so a reconciliation
# flags a STRUCTURAL break (wrong scale, wrong pair, inverted quote) rather than the
# ordinary fix-time gap. Using DEFAULT_RTOL here would flag 62% of days and train the
# reader to ignore the check.
FX_FIX_RTOL = 0.01


@dataclass
class ReconciliationReport:
    series_id: str
    provider_a: str
    provider_b: str
    rtol: float
    overlap_days: int = 0
    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)
    mismatches: list[dict] = field(default_factory=list)
    max_rel_diff: float = 0.0

    @property
    def agrees(self) -> bool:
        return self.overlap_days > 0 and not self.mismatches

    def summary(self) -> str:
        if self.overlap_days == 0:
            return (
                f"{self.series_id}: NO OVERLAP between {self.provider_a} and "
                f"{self.provider_b} — nothing was actually cross-checked."
            )
        verdict = "agree" if self.agrees else f"DISAGREE on {len(self.mismatches)} day(s)"
        return (
            f"{self.series_id}: {self.provider_a} vs {self.provider_b} {verdict} "
            f"over {self.overlap_days} overlapping days "
            f"(max relative diff {self.max_rel_diff:.2%}, tolerance {self.rtol:.2%}); "
            f"{len(self.only_in_a)} days only in {self.provider_a}, "
            f"{len(self.only_in_b)} only in {self.provider_b}"
        )


def reconcile(
    frame_a: pd.DataFrame,
    frame_b: pd.DataFrame,
    series_id: str = "series",
    provider_a: str = "a",
    provider_b: str = "b",
    rtol: float = DEFAULT_RTOL,
    column: str = "close",
) -> ReconciliationReport:
    """Compare two providers' versions of one series on their overlapping dates.

    Dates present in only one provider are reported separately rather than counted as
    mismatches: a provider with a shorter history or a different holiday calendar is a
    coverage fact, not a correctness failure. Only *disagreement on a shared date* is a
    defect.
    """
    report = ReconciliationReport(series_id, provider_a, provider_b, rtol)

    a = frame_a.set_index("date")[column].astype(float)
    b = frame_b.set_index("date")[column].astype(float)

    shared = a.index.intersection(b.index)
    report.overlap_days = len(shared)
    report.only_in_a = sorted(set(a.index) - set(b.index))
    report.only_in_b = sorted(set(b.index) - set(a.index))

    if not len(shared):
        return report

    va, vb = a.loc[shared], b.loc[shared]
    denom = vb.abs().where(vb.abs() > 0, other=1.0)
    rel = (va - vb).abs() / denom
    report.max_rel_diff = float(rel.max())

    for day in sorted(shared[rel > rtol]):
        report.mismatches.append({
            "date": str(day),
            provider_a: float(va.loc[day]),
            provider_b: float(vb.loc[day]),
            "rel_diff": float(rel.loc[day]),
        })
    return report


def diagnose(report: ReconciliationReport) -> list[str]:
    """Turn a disagreement into candidate causes, ordered by how often they are the cause.

    Mirrors README §8's failure-diagnosis discipline: name the likely mechanism rather
    than reporting an undifferentiated delta. Each entry is a hypothesis to check, not a
    conclusion.
    """
    if report.agrees or not report.mismatches:
        return []

    hints: list[str] = []
    ratios = [m["rel_diff"] for m in report.mismatches]
    worst = max(ratios)
    frac = len(report.mismatches) / max(report.overlap_days, 1)

    if frac > 0.9:
        hints.append(
            "Nearly every shared day disagrees, so this is systematic, not sporadic: "
            "suspect a scale/unit difference (e.g. cents vs dollars, or a 100x FX "
            "convention), an adjusted-vs-raw close mix-up, or two different instruments "
            "under one symbol."
        )
    else:
        hints.append(
            f"{len(report.mismatches)} of {report.overlap_days} days disagree "
            f"({frac:.0%}), so this is episodic: suspect stale bars on one side, a "
            "halt/auction print, or a corporate action applied on different dates."
        )

    if worst > 0.5:
        hints.append(
            "Worst difference exceeds 50% — too large for market microstructure. Check "
            "the date convention first (the TWSE adapter converts ROC years by adding "
            "1911; a missed conversion misaligns the whole series)."
        )
    if 0.001 < worst < 0.05:
        hints.append(
            "Differences are small but above tolerance, which is the signature of two "
            "legitimately different prints — consolidated tape vs primary-listing close, "
            "or an FX reference fix vs a spot snapshot. Record which print each provider "
            "serves in the sidecar rather than treating one as wrong."
        )
    return hints
