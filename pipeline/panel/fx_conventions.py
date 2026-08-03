"""FX quote conventions, declared once for the whole repo.

This is the single most likely silent-corruption point in the project, and it is the
reason this module exists as *data* rather than as a convention people remember.

The failure mode is asymmetric in a way that matters. Inverting an FX leg does not
produce a subtly wrong premium — it produces roughly −99.99%, which anyone would catch.
What *is* dangerous is a pair whose quote direction differs from its neighbours: get one
currency backwards in a five-pair panel and that pair alone is nonsense while the others
look fine, so the panel reads as "mostly working" rather than "broken".

**The repo-wide convention: every FX series is stored LOCAL UNITS PER USD.**

    USDKRW = 1453.67   -> 1453.67 KRW buys 1 USD
    USDTWD = 32.39     -> 32.39 TWD buys 1 USD
    USDINR = 95.84     -> 95.84 INR buys 1 USD
    USDHKD = 7.84      -> 7.84 HKD buys 1 USD

The premium formula consumes exactly this direction:

    pi = P_adr * FX_local_per_usd / (n * P_local) - 1

Any provider quoting the reciprocal must be inverted **in its adapter**, never at the
call site — a per-call inversion is how one pair ends up backwards.

Each entry below carries an ``expected_range`` used by :func:`validate_quote_direction`.
The ranges are deliberately wide: they exist to catch a *reciprocal* (0.0007 vs 1453),
which is off by six orders of magnitude, not to police market levels.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FxConvention:
    """One currency pair's storage convention and a sanity band for its direction."""

    code: str                    # e.g. "USDKRW"
    local_currency: str
    quote: str                   # always "local_per_usd" in this repo
    expected_min: float
    expected_max: float
    note: str
    peg: str | None = None

    def validate(self, value: float) -> None:
        if not (self.expected_min <= value <= self.expected_max):
            reciprocal = 1.0 / value if value else float("inf")
            hint = ""
            if self.expected_min <= reciprocal <= self.expected_max:
                hint = (
                    f"  NOTE: 1/{value} = {reciprocal:.4f} IS in range — this series is "
                    "almost certainly stored as USD-per-local and needs inverting in its "
                    "adapter, not at the call site."
                )
            raise ValueError(
                f"{self.code}: {value} outside expected {self.expected_min}–"
                f"{self.expected_max} ({self.quote}).\n{hint}"
            )


CONVENTIONS: dict[str, FxConvention] = {
    "USDKRW": FxConvention(
        "USDKRW", "KRW", "local_per_usd", 500.0, 3000.0,
        "Korean won. Held twice — frankfurter (ECB ~16:00 CET) and FRED H.10 (noon New "
        "York) — so the FX-observation-instant component of confound C2 is measurable "
        "rather than assumed.",
    ),
    "USDTWD": FxConvention(
        "USDTWD", "TWD", "local_per_usd", 15.0, 60.0,
        "New Taiwan dollar. FRED DEXTAUS only; ECB publishes no TWD, so frankfurter 404s. "
        "H.10 is a WEEKLY release, so this leg trails the equity legs by several days and "
        "truncates the TSM joint series — a coverage fact for every TSM caption.",
    ),
    "USDINR": FxConvention(
        "USDINR", "INR", "local_per_usd", 30.0, 150.0,
        "Indian rupee. frankfurter primary, FRED DEXINUS as reconciliation partner.",
    ),
    "USDBRL": FxConvention(
        "USDBRL", "BRL", "local_per_usd", 1.2, 12.0,
        "Brazilian real. EODHD USDBRL.FOREX. The band is wide because the history is: 1.21/USD "
        "in 2011 against 6.29 in 2021-2025, so a tight guard would reject valid observations. "
        "THE FLOOR IS THE POST-FLOAT (Jan 1999) MINIMUM, DELIBERATELY. The series reaches back "
        "to the real's 1994 introduction and spends its first two years below 1.0 (506 obs to "
        "1996-06-11) -- and a rate near 1.0 CANNOT be distinguished from its own reciprocal by "
        "any range, so no honest guard covers that window. It is excluded rather than "
        "accommodated: no pair in the panel uses it (the earliest control sample starts "
        "2000-01-01), so the guard is set where it can actually discriminate.",
    ),
    "USDPHP": FxConvention(
        "USDPHP", "PHP", "local_per_usd", 20.0, 80.0,
        "Philippine peso, for the PLDT pair. Declared 2026-08-03: the series was referenced by "
        "the registry and reachable from PAIRS, but absent from this table, so `for_series` "
        "raised on it and no direction guard ever ran against PLDT's FX leg. The gap stayed "
        "hidden because `all_series()` also omitted the Philippines collection — the registry "
        "and the convention table were missing the same pair, so neither contradicted the "
        "other. The band spans the managed float's realised range (roughly 40-59/USD since "
        "2000) with room either side; a reciprocal misread would land near 0.02 and trip it.",
    ),
    "USDHKD": FxConvention(
        "USDHKD", "HKD", "local_per_usd", 7.5, 8.0,
        "Hong Kong dollar. The narrow band is not a guess — see `peg`.",
        peg=(
            "Linked Exchange Rate System: HKMA maintains 7.75–7.85 HKD/USD via a "
            "Convertibility Undertaking. DESIGN CONSEQUENCE, not trivia: the BABA pair's "
            "FX leg is very nearly a constant, so its premium isolates cross-listing "
            "dynamics from FX dynamics almost completely. That makes BABA the panel's "
            "cleanest read on the barrier itself — the control pair's control variable."
        ),
    ),
}


def convention(code: str) -> FxConvention:
    key = code.upper()
    if key not in CONVENTIONS:
        raise KeyError(f"no FX convention declared for {code!r}; known: {sorted(CONVENTIONS)}")
    return CONVENTIONS[key]


def validate_quote_direction(code: str, value: float) -> None:
    """Raise if ``value`` looks like the reciprocal of the stored convention."""
    convention(code).validate(value)


def for_series(series_id: str) -> FxConvention:
    """Map a registry FX series_id onto its convention."""
    mapping = {
        "usdkrw_spot_daily": "USDKRW",
        "usdkrw_spot_fred_daily": "USDKRW",
        "usdtwd_spot_daily": "USDTWD",
        "usdinr_spot_daily": "USDINR",
        "usdhkd_spot_daily": "USDHKD",
        "usdbrl_spot_daily": "USDBRL",
        "usdphp_spot_daily": "USDPHP",
    }
    if series_id not in mapping:
        raise KeyError(f"{series_id!r} is not a declared FX series")
    return convention(mapping[series_id])


def pegged_currencies() -> list[str]:
    """Currencies whose FX leg is near-constant by policy. Panel design depends on this."""
    return sorted(c.code for c in CONVENTIONS.values() if c.peg)
