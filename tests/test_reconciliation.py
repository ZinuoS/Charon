"""Cross-provider reconciliation, on synthetic fixtures reproducing real failure modes.

Each test encodes a way two providers can disagree that a single-provider pipeline would
never notice. The ROC-calendar case is not hypothetical — the TWSE adapter has to add
1911 to every year, and getting it wrong shifts an entire series without producing a
single obviously-wrong price.
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.ingest.reconcile import DEFAULT_RTOL, FX_FIX_RTOL, diagnose, reconcile


def _f(pairs: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame({"date": list(pairs), "close": list(pairs.values())})


BASE = {"2026-07-10": 168.01, "2026-07-13": 152.35, "2026-07-14": 193.92}


class TestAgreement:
    def test_identical_series_agree(self):
        r = reconcile(_f(BASE), _f(BASE), "skhy", "nasdaq", "yahoo")
        assert r.agrees
        assert r.overlap_days == 3
        assert r.max_rel_diff == 0.0

    def test_differences_inside_tolerance_agree(self):
        """Two venues' official closes can differ legitimately by a basis point or two."""
        b = {k: v * 1.0005 for k, v in BASE.items()}
        assert reconcile(_f(BASE), _f(b)).agrees

    def test_differences_outside_tolerance_disagree(self):
        b = dict(BASE, **{"2026-07-13": 152.35 * 1.02})
        r = reconcile(_f(BASE), _f(b))
        assert not r.agrees
        assert [m["date"] for m in r.mismatches] == ["2026-07-13"]


class TestCoverageIsNotCorrectness:
    def test_nonoverlapping_dates_are_reported_not_counted_as_mismatch(self):
        """A shorter history or a different holiday calendar is a coverage fact."""
        a = _f({**BASE, "2026-07-15": 176.46})
        b = _f(BASE)
        r = reconcile(a, b, provider_a="nasdaq", provider_b="frankfurter")
        assert r.agrees
        assert r.only_in_a == ["2026-07-15"]
        assert r.only_in_b == []

    def test_zero_overlap_is_never_reported_as_agreement(self):
        """The dangerous vacuous pass: two series that never overlap have not been
        cross-checked at all, and must not read as corroboration."""
        r = reconcile(_f({"2026-07-10": 1.0}), _f({"2020-01-02": 1.0}))
        assert r.overlap_days == 0
        assert r.agrees is False
        assert "NO OVERLAP" in r.summary()


class TestDiagnosis:
    def test_roc_calendar_error_is_flagged_as_date_convention(self):
        """The TWSE failure mode: ROC year 115 read as 115 AD misaligns everything."""
        a = _f({"2026-07-10": 1000.0, "2026-07-13": 1010.0, "2026-07-14": 1020.0})
        b = _f({"2026-07-10": 2280.0, "2026-07-13": 2295.0, "2026-07-14": 2310.0})
        r = reconcile(a, b, "tsmc_local", "twse", "yahoo")
        hints = diagnose(r)
        assert not r.agrees
        assert any("systematic" in h for h in hints)
        assert any("ROC" in h or "date convention" in h for h in hints)

    def test_episodic_disagreement_diagnosed_differently_from_systematic(self):
        a = _f({f"2026-07-{d:02d}": 100.0 for d in range(10, 26)})
        b = dict({f"2026-07-{d:02d}": 100.0 for d in range(10, 26)})
        b["2026-07-15"] = 130.0
        r = reconcile(a, _f(b))
        hints = diagnose(r)
        assert any("episodic" in h for h in hints)
        assert not any("systematic" in h for h in hints)

    def test_small_persistent_gap_diagnosed_as_different_prints(self):
        b = {k: v * 1.004 for k, v in BASE.items()}
        hints = diagnose(reconcile(_f(BASE), _f(b)))
        assert any("consolidated tape" in h for h in hints)

    def test_agreement_yields_no_diagnosis(self):
        assert diagnose(reconcile(_f(BASE), _f(BASE))) == []


class TestNeverRepairs:
    def test_reconcile_returns_a_report_not_a_merged_series(self):
        """Averaging two providers would hide the very defect this exists to surface."""
        r = reconcile(_f(BASE), _f({k: v * 1.5 for k, v in BASE.items()}))
        assert not hasattr(r, "merged")
        assert not hasattr(r, "corrected")
        assert isinstance(r.mismatches, list)


class TestLiveCorroboration:
    """Runs only when two providers' data for one series is actually on disk."""

    def test_stored_series_agree_across_providers_where_both_exist(self):
        import json
        from pathlib import Path

        from pipeline.ingest._common import RAW_ROOT

        by_series: dict[str, list[tuple[str, Path]]] = {}
        for meta in RAW_ROOT.rglob("*.meta.json"):
            try:
                m = json.loads(meta.read_text())
            except Exception:
                continue
            if "provider" not in m or "series_id" not in m:
                continue
            csv = meta.with_suffix("").with_suffix(".csv")
            if csv.is_file():
                by_series.setdefault(m["series_id"], []).append((m["provider"], csv))

        multi = {s: v for s, v in by_series.items() if len({p for p, _ in v}) > 1}
        if not multi:
            pytest.skip("no series yet held by two different providers")

        for series_id, entries in multi.items():
            (pa, fa), (pb, fb) = entries[0], entries[1]
            r = reconcile(
                pd.read_csv(fa, dtype={"date": str}), pd.read_csv(fb, dtype={"date": str}),
                series_id, pa, pb,
            )
            assert r.agrees, f"{r.summary()}\n" + "\n".join(diagnose(r))


class TestFxFixTolerance:
    """Two FX fixes taken hours apart are both correct; the gap is signal, not error."""

    def test_fx_tolerance_is_looser_than_equity_tolerance(self):
        assert FX_FIX_RTOL > DEFAULT_RTOL

    def test_typical_fix_gap_passes_at_fx_tolerance_but_fails_at_equity_tolerance(self):
        """Reproduces the measured ECB-vs-noon-NY USD/KRW gap: ~5bp mean, p95 ~51bp."""
        a = _f({"2026-07-10": 1460.76, "2026-07-13": 1455.00})
        b = _f({"2026-07-10": 1460.76 * 1.005, "2026-07-13": 1455.00 * 1.004})
        assert reconcile(_f(BASE), _f(BASE), rtol=FX_FIX_RTOL).agrees
        assert reconcile(a, b, rtol=FX_FIX_RTOL).agrees
        assert not reconcile(a, b, rtol=DEFAULT_RTOL).agrees

    def test_structural_break_still_fails_at_fx_tolerance(self):
        """An inverted quote or wrong scale must fail even at the loose FX tolerance."""
        a = _f({"2026-07-10": 1460.76})
        b = _f({"2026-07-10": 1 / 1460.76})
        assert not reconcile(a, b, rtol=FX_FIX_RTOL).agrees
