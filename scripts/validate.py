"""`just validate` — the hard gate. Run the leakage suite standalone, CI-style.

Exists as its own entry point because the validation layer is the one thing that must be
runnable and legible without running the whole suite. If this is red, nothing downstream
of it is trustworthy, and that should be visible in one command rather than inferred from
a pytest summary line.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=" * 66)
    print("VALIDATION LAYER — splitters, purging, embargo, leakage detectors")
    print("=" * 66)
    r = subprocess.run(
        ["uv", "run", "pytest", "tests/test_validation.py", "-q", "--tb=short", "-p", "no:warnings"],
        cwd=ROOT,
    )
    if r.returncode != 0:
        print("\nVALIDATION RED — stop. Models built on a broken validation layer are worse\n"
              "than no models: they produce numbers that look like results.")
        return 1

    # Each detector demonstrated against a live leak, not merely imported.
    from pipeline.validation.splitters import (
        LeakageError, assert_availability_respected, assert_filtered_not_smoothed,
        assert_no_forward_test_instrument, assert_scaler_fitted_on_train_only,
    )
    import pandas as pd

    checks: list[tuple[str, bool]] = []

    def caught(fn) -> bool:
        try:
            fn(); return False
        except LeakageError:
            return True

    checks.append(("SKHY rejected from any fitting index",
                   caught(lambda: assert_no_forward_test_instrument(["tsmc", "skhy"]))))
    checks.append(("feature published at/after decision instant rejected",
                   caught(lambda: assert_availability_respected(
                       pd.Series(pd.to_datetime(["2026-07-29 06:45"])),
                       pd.Timestamp("2026-07-29 00:00")))))
    checks.append(("full-sample scaler rejected",
                   caught(lambda: assert_scaler_fitted_on_train_only(
                       {"mean": 1.0, "std": 2.0}, {"mean": 1.0, "std": 2.0}))))
    checks.append(("smoothed regime probabilities rejected for prediction",
                   caught(lambda: assert_filtered_not_smoothed(
                       pd.DataFrame({"r0": [0.4, 0.6]}), is_smoothed=True))))

    print("\n" + "-" * 66)
    print("LEAKAGE DETECTORS — each shown a real leak")
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print("-" * 66)

    failed = [n for n, ok in checks if not ok]
    if failed:
        print(f"\nVALIDATION RED — {len(failed)} detector(s) did not catch their leak.")
        return 1
    print("\nVALIDATION GREEN — the gate is satisfied; inference may proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
