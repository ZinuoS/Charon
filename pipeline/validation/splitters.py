"""Validation splitters. Purged, embargoed, and hostile to leakage by construction.

README §8 requires purged and embargoed CV on overlapping labels (López de Prado ch. 7)
and expanding walk-forward for one-step forecasts. Both are implemented inline rather than
imported, per the doctrine's note that the package mirror may balk.

Why purging is not optional here
--------------------------------
This repo's labels overlap. A convergence label formed over a 5-day horizon at time *t*
shares four days of price path with the label at *t+1*. Standard K-fold puts those in
different folds, so the model sees, in training, the same price moves it is scored on in
test. The measured skill is then partly memory, and it does not survive contact with live
data — the classic reason a backtest degrades exactly when it starts being used.

**Purging** removes training observations whose label window overlaps the test window.
**Embargo** additionally drops training observations immediately *after* the test block,
because serial correlation leaks backwards through features built on trailing windows.

The SKHY exclusion is structural, not a convention
--------------------------------------------------
README §8: "All backtests live on D6; SKHY is a forward test, full stop." That is enforced
here by :func:`assert_no_forward_test_instrument`, which raises if the forward-test
instrument appears in any fitting index — a rule that lives in code cannot be forgotten in
a refactor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd

FORWARD_TEST_INSTRUMENTS = frozenset({"skhy"})


class LeakageError(AssertionError):
    """Raised when a split or a fit would let future information reach training."""


def assert_no_forward_test_instrument(index_labels) -> None:
    """Refuse any fit that includes the forward-test instrument (README §8)."""
    found = {str(x).lower() for x in index_labels} & FORWARD_TEST_INSTRUMENTS
    if found:
        raise LeakageError(
            f"forward-test instrument in a fitting index: {sorted(found)}. "
            "SKHY is scored, never fitted (README §8). Score it with the harness instead."
        )


@dataclass(frozen=True)
class Split:
    train: np.ndarray
    test: np.ndarray
    fold: int

    def __post_init__(self) -> None:
        if np.intersect1d(self.train, self.test).size:
            raise LeakageError(f"fold {self.fold}: train and test overlap")


def expanding_walk_forward(n: int, n_splits: int = 5, min_train: int | None = None,
                           embargo: int = 0) -> Iterator[Split]:
    """Expanding-window walk-forward: train on everything before the block, test on it.

    The training window only ever grows and never reaches past the test block's start —
    which is what makes it a one-step-forecast design rather than a backtest with hindsight.
    """
    min_train = min_train or max(n // (n_splits + 1), 1)
    if min_train >= n:
        raise ValueError("min_train exceeds the sample")
    edges = np.linspace(min_train, n, n_splits + 1).astype(int)
    for k in range(n_splits):
        lo, hi = edges[k], edges[k + 1]
        if hi <= lo:
            continue
        train_end = max(lo - embargo, 0)
        yield Split(np.arange(0, train_end), np.arange(lo, hi), k)


def purged_kfold(n: int, n_splits: int = 5, label_horizon: int = 1,
                 embargo: int = 0) -> Iterator[Split]:
    """K-fold with label-overlap purging and a forward embargo.

    ``label_horizon`` is how many periods forward a label looks. Any training index whose
    label window [i, i+horizon] intersects the test block is purged. ``embargo`` drops a
    further band after the test block.
    """
    if label_horizon < 1:
        raise ValueError("label_horizon must be >= 1")
    folds = np.array_split(np.arange(n), n_splits)
    for k, test in enumerate(folds):
        if not test.size:
            continue
        t0, t1 = int(test[0]), int(test[-1])
        keep = []
        for i in range(n):
            if t0 <= i <= t1:
                continue
            if i + label_horizon - 1 >= t0 and i <= t1:   # label window overlaps test
                continue
            if t1 < i <= t1 + embargo:                     # embargo band after test
                continue
            keep.append(i)
        yield Split(np.asarray(keep, dtype=int), test.astype(int), k)


# --------------------------------------------------------------------------------
# Leakage detectors
# --------------------------------------------------------------------------------


def assert_availability_respected(feature_ts: pd.Series, decision_ts: pd.Timestamp) -> None:
    """No feature may carry an availability timestamp at or after the decision instant.

    This is README §4's information-timing firewall applied at fit time rather than only at
    ingestion: a series can be stored correctly and still be *used* early.
    """
    late = feature_ts[feature_ts >= decision_ts]
    if len(late):
        raise LeakageError(
            f"{len(late)} feature(s) not yet public at the decision instant "
            f"{decision_ts}: first offender {late.iloc[0]}"
        )


def assert_scaler_fitted_on_train_only(train_stats: dict, full_stats: dict,
                                       rtol: float = 1e-9) -> None:
    """A scaler whose statistics match the FULL sample was fitted on the full sample.

    The most common silent leak in a pipeline: normalising before splitting. It rarely
    changes results enough to look wrong, which is exactly why it survives review.
    """
    for key in ("mean", "std"):
        if key in train_stats and key in full_stats:
            if np.isclose(train_stats[key], full_stats[key], rtol=rtol):
                raise LeakageError(
                    f"scaler {key} equals the full-sample {key} — fitted on all data, "
                    "not train-only (README §8: everything fits train-only inside every fold)"
                )


def assert_filtered_not_smoothed(probabilities: pd.DataFrame, *, is_smoothed: bool) -> None:
    """Smoothed regime probabilities use the whole sample and must never drive prediction.

    README §6 M2: "Filtered (not smoothed) probabilities for anything predictive."
    Smoothed output is descriptive only and is named so it cannot be mistaken.
    """
    if is_smoothed:
        raise LeakageError(
            "smoothed regime probabilities condition on the full sample and cannot be "
            "used predictively; expose them as `_smoothed_descriptive_only`"
        )
    if probabilities.isna().all().all():
        raise LeakageError("empty probability frame")


def split_report(splits: list[Split], n: int) -> pd.DataFrame:
    """Per-fold sizes and the purge/embargo cost, so a thin fold is visible not silent."""
    rows = []
    for s in splits:
        rows.append({
            "fold": s.fold, "n_train": len(s.train), "n_test": len(s.test),
            "purged_or_embargoed": n - len(s.train) - len(s.test),
            "train_ends_before_test": (len(s.train) == 0) or (s.train.max() < s.test.min()),
        })
    return pd.DataFrame(rows)
