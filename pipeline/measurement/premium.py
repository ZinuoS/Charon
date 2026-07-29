"""M1 — canonical premium construction (README §6).

Supersedes ``smoke_premium.py``, which was ingestion validation only.

The formula
-----------
README §3 defines

.. math::  \\pi_t = \\frac{P^{ADR}_t}{P^{local}_t \\cdot FX_t / 10} - 1

where ``/10`` is the SKHY deal ratio and ``FX_t`` is written USD-per-local. Public FX is
quoted the other way (``KRW=X``, ``DEXKOUS`` are **local per USD**), so substituting
``FX = 1/FX_local_per_usd`` and generalising the ratio gives the implemented form:

.. math::  \\pi_t = \\frac{P^{ADR}_t \\cdot FX^{local/USD}_t}{n_t \\cdot P^{local}_t} - 1

``n_t`` is local shares per ADR — **subscripted by date**, because ADR ratios change and
an unhandled ratio change is indistinguishable from a premium jump (README §6 / S3
Task 2.1). ``n = 0.1`` for SKHY (10 ADRs = 1 share), ``5.0`` for TSM.

Units check, which is the whole defence against the classic bug: the denominator
``n·P_local`` is the local-currency cost of the shares under **one** ADR; multiplying the
numerator by ``FX_local_per_usd`` puts the ADR's USD price into the same currency. Both
sides local currency, ratio dimensionless. Inverting FX yields ≈ −99.99%, not a plausible
wrong number — asserted in ``tests/test_premium_formula.py``.

Two measurement axes, both explicit
-----------------------------------
Sessions 5 measured two effects that are **the same class of thing** — analyst choices
whose magnitude is on the order of the daily phenomena being studied:

* **Close definition**, 24.6bp. README §2's $130.49 (consolidated tape) vs. Nasdaq's
  $130.17 (primary-listing official close) for 2026-07-28. Both internally consistent;
  they are different prints.
* **FX fix instant**, 5bp mean / 51bp p95 over 2,850 days. ECB ~16:00 CET vs. FRED H.10
  noon New York. Both correct; different fixes.

π is a *ratio of closes*, so both propagate into every observation. Burying either in a
default would put a noise floor into the series that nobody could decompose afterwards.
So both are **config axes**: every variant is computed where its inputs exist, stored
side by side, and every artifact records which pair it used. Notebook F6 plots all four.

Neither default is chosen here — both are ``TODO(ash: ratify)`` (README §11).

No network. Reads only what ingestion wrote to ``data/raw/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

import pandas as pd

from pipeline.ingest._common import latest_raw_file
from pipeline.ingest.registry import PairSpec, pair_by_id, series_by_id

# --------------------------------------------------------------------------------
# Config axes
# --------------------------------------------------------------------------------

#: FX leg variants -> the registry series_id supplying that leg.
#: `yahoo_snapshot` is dropped: Yahoo is no longer routed for FX, and its snapshot instant
#: was never documented, which is precisely the property that made it unusable here.
FX_LEGS: dict[str, str] = {
    "frankfurter": "usdkrw_spot_daily",       # ECB reference, ~16:00 CET, documented
    "fred": "usdkrw_spot_fred_daily",         # H.10 noon New York, documented
    # "ecos_1530_close": pending access (Korean identity verification). When it lands it
    # slots in here WITHOUT redefining pi retroactively — that is the point of the axis.
}

#: Close-definition variants. Only `primary_official` is currently sourced; `consolidated`
#: is declared so the axis exists and F6 can show the 24.6bp gap once a second print is
#: available, rather than the axis being retrofitted later.
CLOSE_DEFS: tuple[str, ...] = ("primary_official", "consolidated")

#: Neither default is chosen in code. README §11 reserves measurement definitions to the
#: author; a default here would become the de-facto decision.
DEFAULT_FX_LEG = "TODO(ash: ratify)"
DEFAULT_CLOSE_DEF = "TODO(ash: ratify)"

PAIR_SOURCE = {"skhy": "d1_prices"}
DEFAULT_SOURCE = "d6_comparators"


@dataclass(frozen=True)
class PremiumVariant:
    """One (fx_leg, close_def) reading of π, carrying its own provenance."""

    pair_id: str
    fx_leg: str
    close_def: str
    series: pd.Series
    n_obs: int
    first: str | None
    last: str | None
    dropped_to_join: int
    fx_series_id: str
    ratio_confirmed: bool

    @property
    def label(self) -> str:
        return f"{self.pair_id}/{self.fx_leg}/{self.close_def}"

    def describe(self) -> dict:
        s = self.series
        return {
            "pair": self.pair_id, "fx_leg": self.fx_leg, "close_def": self.close_def,
            "fx_series_id": self.fx_series_id, "ratio_confirmed": self.ratio_confirmed,
            "n_obs": self.n_obs, "first": self.first, "last": self.last,
            "dropped_to_join": self.dropped_to_join,
            "mean_pct": round(float(s.mean()) * 100, 3) if len(s) else None,
            "min_pct": round(float(s.min()) * 100, 3) if len(s) else None,
            "max_pct": round(float(s.max()) * 100, 3) if len(s) else None,
            "last_pct": round(float(s.iloc[-1]) * 100, 3) if len(s) else None,
        }


# --------------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------------


def compute_premium(
    adr_close: pd.Series,
    local_close: pd.Series,
    fx_local_per_usd: pd.Series,
    local_shares_per_adr: float | pd.Series,
) -> pd.Series:
    """Close-to-close π, inner-joined on date. Ratio may be scalar or a date-indexed series.

    The inner join is deliberate and is never relaxed to a forward-fill: carrying a stale
    leg across one market's holiday manufactures premium moves out of calendar mismatch,
    which is the same artifact D1(a) is already labelled for. Dropped rows are counted and
    reported rather than absorbed.
    """
    frame = pd.concat(
        {"adr": adr_close, "local": local_close, "fx": fx_local_per_usd},
        axis=1, join="inner",
    ).dropna()

    if isinstance(local_shares_per_adr, pd.Series):
        # Ratio-aware: reindex onto the joined dates and hold the last known ratio
        # forward. Forward-fill is correct HERE (a ratio persists until the depositary
        # changes it) where it is wrong for prices (a price does not persist).
        ratio = local_shares_per_adr.reindex(frame.index).ffill()
        if ratio.isna().any():
            raise ValueError(
                "ratio history does not cover the start of the joined sample; "
                "an unhandled ratio change looks exactly like a premium jump"
            )
    else:
        ratio = float(local_shares_per_adr)

    return (frame["adr"] * frame["fx"]) / (ratio * frame["local"]) - 1.0


def _load_close(source: str, series_id: str) -> pd.Series:
    path = latest_raw_file(source, f"{series_id}.csv")
    if path is None:
        raise FileNotFoundError(
            f"no raw file for {series_id} under data/raw/{source}/ — run `just ingest`"
        )
    frame = pd.read_csv(path, parse_dates=["date"])
    return frame.set_index("date")["close"].rename(series_id)


def build_variant(
    pair: PairSpec,
    fx_leg: str,
    close_def: str = "primary_official",
    start: str | None = None,
) -> PremiumVariant:
    """Build one π variant for ``pair``. Raises FileNotFoundError if a leg is missing."""
    if fx_leg not in FX_LEGS:
        raise KeyError(f"unknown fx_leg {fx_leg!r}; known: {sorted(FX_LEGS)}")
    if close_def not in CLOSE_DEFS:
        raise KeyError(f"unknown close_def {close_def!r}; known: {list(CLOSE_DEFS)}")

    source = PAIR_SOURCE.get(pair.pair_id, DEFAULT_SOURCE)
    adr = _load_close(source, pair.adr)
    local = _load_close(source, pair.local)

    # The SKHY pair's FX variants live in D1; a comparator's FX leg is its own registry
    # series and is not swappable across pairs.
    if pair.pair_id == "skhy":
        fx_series_id = FX_LEGS[fx_leg]
        fx = _load_close("d1_prices", fx_series_id)
    else:
        fx_series_id = pair.fx
        fx = _load_close(source, fx_series_id)

    if start:
        adr, local, fx = (s[s.index >= start] for s in (adr, local, fx))

    pi = compute_premium(adr, local, fx, pair.local_shares_per_adr)
    return PremiumVariant(
        pair_id=pair.pair_id, fx_leg=fx_leg, close_def=close_def, series=pi,
        n_obs=len(pi),
        first=str(pi.index[0].date()) if len(pi) else None,
        last=str(pi.index[-1].date()) if len(pi) else None,
        dropped_to_join=max(len(adr), len(local), len(fx)) - len(pi),
        fx_series_id=fx_series_id, ratio_confirmed=pair.confirmed,
    )


def build_all_variants(pair_id: str, start: str | None = None) -> list[PremiumVariant]:
    """Every (fx_leg, close_def) combination whose inputs exist on disk.

    Missing combinations are skipped silently *here* and reported by the caller — a
    variant that cannot be built is a coverage fact, and the alternative (raising) would
    make one absent FX series suppress the variants that do work.
    """
    pair = pair_by_id(pair_id)
    out: list[PremiumVariant] = []
    fx_legs = FX_LEGS if pair.pair_id == "skhy" else {"native": pair.fx}
    for fx_leg, close_def in product(fx_legs, CLOSE_DEFS):
        try:
            out.append(build_variant(pair, fx_leg, close_def, start=start)
                       if pair.pair_id == "skhy"
                       else _build_native(pair, close_def, start))
        except (FileNotFoundError, KeyError):
            continue
    return out


def _build_native(pair: PairSpec, close_def: str, start: str | None) -> PremiumVariant:
    """Comparator pairs have a single FX source; label it `native` rather than faking an axis."""
    source = PAIR_SOURCE.get(pair.pair_id, DEFAULT_SOURCE)
    adr = _load_close(source, pair.adr)
    local = _load_close(source, pair.local)
    fx = _load_close(source, pair.fx)
    if start:
        adr, local, fx = (s[s.index >= start] for s in (adr, local, fx))
    pi = compute_premium(adr, local, fx, pair.local_shares_per_adr)
    return PremiumVariant(
        pair_id=pair.pair_id, fx_leg="native", close_def=close_def, series=pi,
        n_obs=len(pi),
        first=str(pi.index[0].date()) if len(pi) else None,
        last=str(pi.index[-1].date()) if len(pi) else None,
        dropped_to_join=max(len(adr), len(local), len(fx)) - len(pi),
        fx_series_id=pair.fx, ratio_confirmed=pair.confirmed,
    )


def variant_spread(variants: list[PremiumVariant]) -> pd.DataFrame:
    """Pairwise spread between variants in basis points, on shared dates.

    This is the quantity notebook F6 exists to show: how much of a given day's premium
    reading is definitional rather than economic.
    """
    rows = []
    for i, a in enumerate(variants):
        for b in variants[i + 1:]:
            shared = a.series.index.intersection(b.series.index)
            if not len(shared):
                continue
            d = (a.series.loc[shared] - b.series.loc[shared]).abs() * 10_000
            rows.append({
                "a": a.label, "b": b.label, "n_shared": len(shared),
                "mean_bp": round(float(d.mean()), 2),
                "median_bp": round(float(d.median()), 2),
                "p95_bp": round(float(d.quantile(0.95)), 2),
                "max_bp": round(float(d.max()), 2),
            })
    return pd.DataFrame(rows)
