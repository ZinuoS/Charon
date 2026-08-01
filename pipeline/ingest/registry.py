"""Series registry: the information-timing firewall, declared once.

README §4 requires that *every* series carry an availability timestamp — the instant
it became publicly knowable in its home timezone — alongside its observation
timestamp. With a dual-close pair (KRX 15:30 KST vs. Nasdaq 16:00 ET, ~13.5h apart)
that distinction is the whole measurement problem, not a formality, so it is declared
here in data rather than derived ad hoc at each call site.

Two kinds of entry live in this file:

*   **Mechanical facts** — exchange close times, quote currencies. Verifiable from the
    exchange, low risk.
*   **Assumptions** — availability lags, ADR ratios for the comparator legs, and the
    meaning of a "daily close" for an FX pair that never closes. Each carries
    ``confirmed=False`` and a ``TODO(ash)`` note until the author signs it off.
    Nothing downstream is allowed to treat an unconfirmed field as settled.

No hypothesis parameter appears in this file. Ratios and close times are plumbing;
thresholds, directions and half-lives live in ``preregistration/calls.yaml`` and are
the author's alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

AssetClass = Literal["adr", "local_equity", "fx"]


@dataclass(frozen=True)
class SeriesSpec:
    """One daily series: where it comes from and when it becomes knowable."""

    series_id: str  # filename stem under data/raw/<source>/<date>/
    symbol: str  # provider symbol
    asset_class: AssetClass
    currency: str  # quote currency of the price column
    market: str  # human label, e.g. "Nasdaq", "KRX"
    timezone: str  # IANA tz of the market
    close_local: time  # official regular-session close in `timezone`
    availability_lag: timedelta  # close -> publicly knowable
    availability_note: str
    units: str
    start: str | None = None  # ISO date; None = provider max history
    confirmed: bool = False  # author sign-off on the timing assumptions
    notes: str = ""
    # Provider routing, in preference order. The puller tries each in turn and records
    # which one actually served the bytes. Ordering is by PROVENANCE first, not
    # convenience: an issuer exchange outranks an aggregator even when both work.
    providers: tuple[str, ...] = ("yahoo_finance",)
    provider_symbols: dict = field(default_factory=dict)  # per-adapter symbol override

    def observation_ts_utc(self, obs_date: date) -> datetime:
        """UTC instant the bar's closing price refers to."""
        tz = ZoneInfo(self.timezone)
        return datetime.combine(obs_date, self.close_local, tzinfo=tz).astimezone(ZoneInfo("UTC"))

    def availability_ts_utc(self, obs_date: date) -> datetime:
        """UTC instant the closing price became publicly knowable."""
        return self.observation_ts_utc(obs_date) + self.availability_lag


@dataclass(frozen=True)
class PairSpec:
    """A cross-listed pair and the ratio that maps one ADR onto local shares.

    ``local_shares_per_adr`` is the *only* number that converts between the legs:

        pi = P_adr * fx_local_per_usd / (local_shares_per_adr * P_local) - 1

    For SKHY the deal term is "10 ADRs = 1 Korean common share" (README §2), so one
    ADR is 0.1 of a local share. For TSM one ADR is 5 ordinary shares. Getting this
    wrong does not produce an obviously broken number — it produces a plausible wrong
    one — which is why each ratio carries an explicit confirmation flag.
    """

    pair_id: str
    adr: str  # series_id of the ADR leg
    local: str  # series_id of the local leg
    fx: str  # series_id of the FX leg, quoted LOCAL per USD
    local_shares_per_adr: float
    ratio_source: str
    confirmed: bool = False
    notes: str = ""
    # Sample restrictions. These exist so an exclusion is DECLARED IN THE REGISTRY with its
    # reason, rather than applied ad hoc at a call site where a later reader cannot see it.
    # Both fields must be justified by a documented CORPORATE ACTION or listing event — never
    # by how the resulting series looks, which would be selecting on the outcome.
    sample_start: str | None = None
    sample_end: str | None = None
    sample_reason: str = ""
    excluded: bool = False


UTC = ZoneInfo("UTC")

# --------------------------------------------------------------------------------
# D1 — core SKHY premium legs
# --------------------------------------------------------------------------------

# Availability-lag assumption, all exchange series: the official close print is
# disseminated within ~15 minutes of the regular-session close. This is deliberately
# conservative relative to real-time tape (which is instantaneous) because the series
# stored here is the *daily bar*, and the daily bar is what a T+0 decision could have
# used. TODO(ash): confirm 15min is the lag you want, or tighten per venue.
_STD_LAG = timedelta(minutes=15)

_FX_NOTE = (
    "Yahoo's FX 'daily close' is a snapshot of a 24h OTC market, not an exchange "
    "print, and its snapshot instant is not documented. Assumed 21:00 UTC (~17:00 "
    "ET), the conventional NY rollover. This matters: the FX leg's snapshot time "
    "sits between the KRX close and the Nasdaq close, so it contributes its own "
    "asynchronicity term to close-to-close pi (README D1a). "
    "TODO(ash): decide whether D1(b) should replace this with a KRW NDF fix "
    "(e.g. a 15:30 KST or 16:00 ET fixing) before M1 is built."
)

D1_SERIES: tuple[SeriesSpec, ...] = (
    SeriesSpec(
        series_id="skhy_adr_daily",
        symbol="SKHY",
        asset_class="adr",
        currency="USD",
        market="Nasdaq",
        timezone="America/New_York",
        close_local=time(16, 0),
        availability_lag=_STD_LAG,
        availability_note="Nasdaq regular-session close 16:00 ET; daily bar assumed knowable 16:15 ET.",
        units="USD per ADR",
        start="2026-07-10",
        confirmed=False,
        notes="SK Hynix ADR, listed 2026-07-10 (README §2). Forward-test instrument only (README §8).",
        providers=("nasdaq", "yahoo_finance"),
        provider_symbols={"nasdaq": "SKHY"},
    ),
    SeriesSpec(
        series_id="skhynix_local_daily",
        symbol="000660.KS",
        asset_class="local_equity",
        currency="KRW",
        market="KRX",
        timezone="Asia/Seoul",
        close_local=time(15, 30),
        availability_lag=_STD_LAG,
        availability_note=(
            "KRX regular session closes 15:30 KST; daily bar assumed knowable 15:45 KST. "
            "KRX also runs an after-hours single-price session to 18:00 KST which does NOT "
            "set the official close. TODO(ash): confirm the daily bar we store is the 15:30 "
            "regular-session close and not an after-hours print."
        ),
        units="KRW per common share",
        start="2015-01-01",
        confirmed=False,
        notes=(
            "SK Hynix common. >=5y history per Task 3.1. UNROUTED: no keyless provider "
            "verified. Yahoo is throttled; KRX Open API needs a key + admin approval; "
            "Stooq serves a JS bot-challenge; Naver's terms are unreviewed. This is the "
            "binding gap — without the local leg the SKHY premium cannot be computed."
        ),
        providers=("eodhd", "yahoo_finance"),
        provider_symbols={"eodhd": "000660.KO"},
    ),
    SeriesSpec(
        series_id="usdkrw_spot_daily",
        symbol="KRW=X",
        asset_class="fx",
        currency="KRW",
        market="OTC FX",
        timezone="UTC",
        close_local=time(21, 0),
        availability_lag=timedelta(0),
        availability_note=_FX_NOTE,
        units="KRW per 1 USD",
        start="2015-01-01",
        confirmed=False,
        notes="Quoted LOCAL-per-USD. Direction is load-bearing for pi; see tests/test_premium_formula.py.",
        providers=("frankfurter", "fred", "yahoo_finance"),
        provider_symbols={"frankfurter": "KRW", "fred": "DEXKOUS"},
    ),
    # Second, independently-timed USDKRW series. NOT a fallback — it is stored alongside
    # the frankfurter series specifically so the two can be reconciled. They are
    # different FIXES of the same pair (ECB ~16:00 CET vs. noon New York), so a
    # persistent gap between them is a MEASUREMENT of the FX-observation-instant
    # component of confound C2, not an error in either.
    SeriesSpec(
        series_id="usdkrw_spot_fred_daily",
        symbol="DEXKOUS",
        asset_class="fx",
        currency="KRW",
        market="Federal Reserve H.10",
        timezone="America/New_York",
        close_local=time(12, 0),
        availability_lag=timedelta(hours=6),
        availability_note=(
            "H.10 noon buying rate in New York — a DOCUMENTED fix instant, unlike the "
            "Yahoo snapshot. Published with a lag: H.10 is a weekly release, so the most "
            "recent observations trail the equity legs by up to several days. "
            "TODO(ash): confirm the +6h availability lag against the H.10 release schedule."
        ),
        units="KRW per 1 USD",
        start="2015-01-01",
        confirmed=False,
        notes="Reconciliation partner for usdkrw_spot_daily. Public Domain (citation requested).",
        providers=("fred",),
        provider_symbols={"fred": "DEXKOUS"},
    ),
)

# --------------------------------------------------------------------------------
# D6 — comparator panel (the training universe; README §4 D6, §8)
# --------------------------------------------------------------------------------

D6_TSMC_SERIES: tuple[SeriesSpec, ...] = (
    SeriesSpec(
        series_id="tsm_adr_daily",
        symbol="TSM",
        asset_class="adr",
        currency="USD",
        market="NYSE",
        timezone="America/New_York",
        close_local=time(16, 0),
        availability_lag=_STD_LAG,
        availability_note="NYSE regular-session close 16:00 ET; daily bar assumed knowable 16:15 ET.",
        units="USD per ADR",
        start=None,
        confirmed=False,
        notes=(
            "Structural comparator: same asymmetric conversion regime as SKHY (README §2). "
            "PROVIDER ORDER IS DELIBERATE AND IS A DEPTH DECISION. Nasdaq is the listing "
            "venue and outranks an aggregator on provenance, but its API serves a rolling "
            "10-year window, which truncated this leg at 2016 and cost the panel its only "
            "deep history. EODHD serves from 1997-10-08. It is preferred here ONLY because "
            "it is corroborated against Nasdaq over the whole 2016-2026 overlap by "
            "tests/test_tsmc_deep_history.py; if that agreement test fails, this ordering "
            "must be reverted, not loosened."
        ),
        providers=("eodhd", "nasdaq", "yahoo_finance"),
        provider_symbols={"nasdaq": "TSM", "eodhd": "TSM.US"},
    ),
    SeriesSpec(
        series_id="tsmc_local_daily",
        symbol="2330.TW",
        asset_class="local_equity",
        currency="TWD",
        market="TWSE",
        timezone="Asia/Taipei",
        close_local=time(13, 30),
        availability_lag=_STD_LAG,
        availability_note="TWSE regular-session close 13:30 TPE; daily bar assumed knowable 13:45 TPE.",
        units="TWD per common share",
        start=None,
        confirmed=False,
        notes=(
            "Same depth decision as the ADR leg: the TWSE route starts 2010, EODHD serves "
            "from 1994-09-05, and the ordering is justified by the overlap agreement test, "
            "not by convenience."
        ),
        providers=("eodhd", "twse", "yahoo_finance"),
        provider_symbols={"twse": "2330", "eodhd": "2330.TW"},
    ),
    SeriesSpec(
        series_id="usdtwd_spot_daily",
        symbol="TWD=X",
        asset_class="fx",
        currency="TWD",
        market="OTC FX",
        timezone="UTC",
        close_local=time(21, 0),
        availability_lag=timedelta(0),
        availability_note=_FX_NOTE,
        units="TWD per 1 USD",
        start=None,
        confirmed=False,
        notes=(
            "FRED DEXTAUS is the primary: ECB publishes no TWD, so frankfurter 404s. "
            "H.10 noon-New-York fix — a DOCUMENTED instant, unlike the Yahoo snapshot."
        ),
        providers=("fred", "yahoo_finance"),
        provider_symbols={"fred": "DEXTAUS"},
    ),
)

D6_EXTRA_SERIES: tuple[SeriesSpec, ...] = (
    # Indian ADR pairs — capped conversion regimes, the closest structural analogue
    # to SKHY outside Taiwan (README §4 D6).
    SeriesSpec(
        series_id="infy_adr_daily", symbol="INFY", asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADR", start=None, confirmed=False,
        providers=("nasdaq", "eodhd"),
        provider_symbols={"nasdaq": "INFY", "eodhd": "INFY.US"},
    ),
    SeriesSpec(
        series_id="infy_local_daily", symbol="INFY.NS", asset_class="local_equity", currency="INR",
        market="NSE", timezone="Asia/Kolkata", close_local=time(15, 30),
        availability_lag=_STD_LAG, availability_note="NSE close 15:30 IST, +15min.",
        units="INR per common share", start=None, confirmed=False,
        providers=("yahoo_finance",),
        provider_symbols={},
    ),
    SeriesSpec(
        series_id="ibn_adr_daily", symbol="IBN", asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADR", start=None, confirmed=False,
        providers=("nasdaq", "eodhd"),
        provider_symbols={"nasdaq": "IBN", "eodhd": "IBN.US"},
    ),
    SeriesSpec(
        series_id="icicibank_local_daily", symbol="ICICIBANK.NS", asset_class="local_equity", currency="INR",
        market="NSE", timezone="Asia/Kolkata", close_local=time(15, 30),
        availability_lag=_STD_LAG, availability_note="NSE close 15:30 IST, +15min.",
        units="INR per common share", start=None, confirmed=False,
        providers=("yahoo_finance",),
        provider_symbols={},
    ),
    SeriesSpec(
        series_id="usdinr_spot_daily", symbol="INR=X", asset_class="fx", currency="INR",
        market="OTC FX", timezone="UTC", close_local=time(21, 0),
        availability_lag=timedelta(0), availability_note=_FX_NOTE,
        units="INR per 1 USD", start=None, confirmed=False,
        providers=("frankfurter", "fred"),
        provider_symbols={"frankfurter": "INR", "fred": "DEXINUS"},
    ),
    # BABA — fungible US/HK pair, the UNCONSTRAINED control (no barrier at all).
    SeriesSpec(
        series_id="baba_adr_daily", symbol="BABA", asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADS", start=None, confirmed=False,
        providers=("nasdaq", "eodhd"),
        provider_symbols={"nasdaq": "BABA", "eodhd": "BABA.US"},
    ),
    SeriesSpec(
        series_id="baba_local_daily", symbol="9988.HK", asset_class="local_equity", currency="HKD",
        market="HKEX", timezone="Asia/Hong_Kong", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="HKEX close 16:00 HKT, +15min.",
        units="HKD per common share", start=None, confirmed=False,
        providers=("eodhd",),
        provider_symbols={"eodhd": "9988.HK"},
    ),
    SeriesSpec(
        series_id="usdhkd_spot_daily", symbol="HKD=X", asset_class="fx", currency="HKD",
        market="OTC FX", timezone="UTC", close_local=time(21, 0),
        availability_lag=timedelta(0), availability_note=_FX_NOTE,
        units="HKD per 1 USD", start=None, confirmed=False,
        providers=("frankfurter", "fred"),
        provider_symbols={"frankfurter": "HKD", "fred": "DEXHKUS"},
    ),
)

# --------------------------------------------------------------------------------
# Pairs
# --------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------
# D6 Taiwan cohort (S18) — every OTHER TWSE-listed company with a US ADR programme.
#
# Added as a COHORT, not as a selection. The regime label is assigned from the documented
# re-issuance rule, which is market-wide, so either all of these qualify or none do.
# Picking the two or three whose premiums looked most persistent would be selecting on the
# outcome, which is exactly the error the pre-registration exists to prevent — so the
# inclusion rule is mechanical: TWSE local line + US ADR + retrievable history.
#
# These share TSMC's regulator. They therefore reduce ISSUER-idiosyncratic noise in the
# one_way_constrained estimate; they do NOT provide independent variation in the RULE.
# That limitation is stated wherever the pooled estimate is reported.
# ------------------------------------------------------------------------------------
def _tw_local(series_id: str, symbol: str) -> SeriesSpec:
    return SeriesSpec(
        series_id=series_id, symbol=symbol, asset_class="local_equity", currency="TWD",
        market="TWSE", timezone="Asia/Taipei", close_local=time(13, 30),
        availability_lag=_STD_LAG,
        availability_note="TWSE regular-session close 13:30 TPE; daily bar assumed knowable 13:45 TPE.",
        units="TWD per common share", start=None, confirmed=False,
        providers=("eodhd", "twse"),
        provider_symbols={"eodhd": symbol, "twse": symbol.split(".")[0]},
    )


def _tw_adr(series_id: str, symbol: str) -> SeriesSpec:
    return SeriesSpec(
        series_id=series_id, symbol=symbol, asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADR", start=None, confirmed=False,
        providers=("eodhd", "nasdaq"),
        provider_symbols={"eodhd": f"{symbol}.US", "nasdaq": symbol},
    )


D6_TAIWAN_SERIES: tuple[SeriesSpec, ...] = (
    _tw_adr("umc_adr_daily", "UMC"),      _tw_local("umc_local_daily", "2303.TW"),
    _tw_adr("ase_adr_daily", "ASX"),      _tw_local("ase_local_daily", "3711.TW"),
    _tw_adr("auo_adr_daily", "AUO"),      _tw_local("auo_local_daily", "2409.TW"),
    _tw_adr("cht_adr_daily", "CHT"),      _tw_local("cht_local_daily", "2412.TW"),
)


# ------------------------------------------------------------------------------------
# D6 Brazil cohort (S19) — the FUNGIBLE control class.
#
# Ratifying a two-class taxonomy on one control pair would be ratifying half of it. Brazil
# is the literature's standard control (Stigler/Shah/Patnaik use Brazil and Mexico against
# India) and is free in BOTH directions: Resolucao Conjunta BCB/CVM no. 13/2024 (effective
# Jan 2025, revoking CMN 4.373/2014) imposes no quantity cap on DR issuance.
#
# ⚠️ SHARE-LINE MAPPING IS A TRAP HERE. Brazilian issuers list multiple classes and the ADR
# maps to a SPECIFIC one: PBR -> PETR3 (ordinary) while PBR.A -> PETR4 (preferred); BBD ->
# BBDC4; ITUB -> ITUB4; GGB -> GGBR4. Mapping PBR to PETR4 yields an implied ratio of 2.169
# with a wide interquartile range instead of 1.999 +/- 0.3% -- wrong, but not obviously
# wrong, which is exactly the failure mode the ratio check exists to catch.
# ------------------------------------------------------------------------------------
def _br_local(series_id: str, symbol: str) -> SeriesSpec:
    return SeriesSpec(
        series_id=series_id, symbol=symbol, asset_class="local_equity", currency="BRL",
        market="B3", timezone="America/Sao_Paulo", close_local=time(17, 0),
        availability_lag=_STD_LAG, availability_note="B3 close 17:00 BRT, +15min.",
        units="BRL per share", start=None, confirmed=False,
        providers=("eodhd",), provider_symbols={"eodhd": symbol},
    )


def _br_adr(series_id: str, symbol: str) -> SeriesSpec:
    return SeriesSpec(
        series_id=series_id, symbol=symbol, asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADR", start=None, confirmed=False,
        providers=("eodhd", "nasdaq"),
        provider_symbols={"eodhd": f"{symbol}.US", "nasdaq": symbol},
    )


# ------------------------------------------------------------------------------------
# D6 Philippines — the search for a constrained pair OUTSIDE Taiwan.
#
# WHY THIS TIER EXISTS. All four one-way-constrained pairs in the panel are Taiwanese, so
# they share one regulator and one currency and give NO independent variation in the RULE.
# PLDT is the strongest reachable candidate for breaking that: the Philippine constitution
# caps foreign ownership of public utilities at 40%, which is a hard statutory ceiling of
# exactly the kind the taxonomy is about, and it is a different legal system, currency and
# regulator from Taiwan.
#
# WHAT THE DATA SAYS AND WHAT IT DOES NOT. The implied ratio is 1.000 and stable across all
# 32 years (median 0.998, no year outside 0.98-1.01), so the pair is clean and the ratio is
# empirically confirmed over 7,454 sessions. It also implies the premium sits at PARITY
# throughout -- which is a PRICE fact and therefore says nothing about the pair's class,
# because this repository classifies on the rule and never on the behaviour.
# ------------------------------------------------------------------------------------
D6_PHILIPPINES_SERIES: tuple[SeriesSpec, ...] = (
    SeriesSpec(
        series_id="pldt_adr_daily", symbol="PHI", asset_class="adr", currency="USD",
        market="NYSE", timezone="America/New_York", close_local=time(16, 0),
        availability_lag=_STD_LAG, availability_note="NYSE close 16:00 ET, +15min.",
        units="USD per ADR", start=None, confirmed=False,
        providers=("eodhd", "nasdaq"), provider_symbols={"eodhd": "PHI.US", "nasdaq": "PHI"},
    ),
    SeriesSpec(
        series_id="pldt_local_daily", symbol="TEL.PSE", asset_class="local_equity",
        currency="PHP", market="PSE", timezone="Asia/Manila", close_local=time(15, 30),
        availability_lag=_STD_LAG,
        availability_note="PSE regular-session close 15:30 PHT; bar assumed knowable 15:45.",
        units="PHP per common share", start=None, confirmed=False,
        providers=("eodhd",), provider_symbols={"eodhd": "TEL.PSE"},
    ),
    SeriesSpec(
        series_id="usdphp_spot_daily", symbol="USDPHP", asset_class="fx", currency="PHP",
        market="OTC FX", timezone="UTC", close_local=time(21, 0),
        availability_lag=_STD_LAG, availability_note="OTC spot close.",
        units="PHP per USD", start=None, confirmed=False,
        providers=("eodhd",), provider_symbols={"eodhd": "USDPHP.FOREX"},
    ),
)

D6_BRAZIL_SERIES: tuple[SeriesSpec, ...] = (
    _br_adr("vale_adr_daily", "VALE"),   _br_local("vale_local_daily", "VALE3.SA"),
    _br_adr("itub_adr_daily", "ITUB"),   _br_local("itub_local_daily", "ITUB4.SA"),
    _br_adr("abev_adr_daily", "ABEV"),   _br_local("abev_local_daily", "ABEV3.SA"),
    _br_adr("pbr_adr_daily", "PBR"),     _br_local("pbr_local_daily", "PETR3.SA"),
    _br_adr("ggb_adr_daily", "GGB"),     _br_local("ggb_local_daily", "GGBR4.SA"),
    SeriesSpec(
        series_id="usdbrl_spot_daily", symbol="USDBRL", asset_class="fx", currency="BRL",
        market="OTC FX", timezone="UTC", close_local=time(21, 0),
        availability_lag=timedelta(0), availability_note=_FX_NOTE,
        units="BRL per 1 USD", start=None, confirmed=False,
        providers=("eodhd",), provider_symbols={"eodhd": "USDBRL.FOREX"},
    ),
)

# Shared preamble for control-class sample restrictions. Stated once so the reasoning cannot
# drift between pairs, and so it is obvious that it is a CLASS-level argument.
_CONTROL_RATIO_REGIME = (
    "CONTROL-CLASS RATIO REGIME. This restriction is sound only because the pair is classified "
    "`fungible` on the RULE: a freely arbitraged premium cannot be 20x or 500x, so a deviation "
    "of that size is unambiguously a ratio change, not a premium. The same reasoning is NOT "
    "applied to constrained pairs, where a large premium is the object of study -- ASE was "
    "located instead by an explicit price-step diagnostic at a known reorganisation. "
)



# ------------------------------------------------------------------------------------
# D2 macro context (S24). The three named gaps on G20, closed where a sanctioned route
# existed. All three had a route through access already held -- no new registration.
#
# KOSPI: EODHD index symbology is `KS11.INDX`. `^KS11`, `KOSPI.INDX` and `KS11.KO` all 404,
# so the symbology matters more than the ticker one knows.
#
# RATE DIFFERENTIAL: both legs from FRED, which is public domain -- the cleanest provenance in
# the repo. The Korea leg is OECD-sourced and MONTHLY; it is landed and presented at its native
# frequency. Interpolating a monthly policy-adjacent series to daily for a CONTEXT panel would
# manufacture 20 observations a month that no one published.
# ------------------------------------------------------------------------------------
D2_MACRO_SERIES: tuple[SeriesSpec, ...] = (
    SeriesSpec(
        series_id="kospi_index_daily", symbol="KS11.INDX", asset_class="index", currency="KRW",
        market="KRX (index)", timezone="Asia/Seoul", close_local=time(15, 30),
        availability_lag=_STD_LAG,
        availability_note="KRX close 15:30 KST; index level disseminated with the close.",
        units="index points", start=None, confirmed=False,
        providers=("eodhd",), provider_symbols={"eodhd": "KS11.INDX"},
    ),
    SeriesSpec(
        series_id="kr_rate_3m_monthly", symbol="IR3TIB01KRM156N", asset_class="rate",
        currency="KRW", market="FRED (OECD)", timezone="America/New_York", close_local=time(12, 0),
        availability_lag=timedelta(days=30),
        availability_note=(
            "MONTHLY, OECD-sourced, published with a material lag -- latest observation is "
            "several weeks behind the equity legs. Context only; never a same-day input."
        ),
        units="percent per annum, 3-month interbank", start=None, confirmed=False,
        providers=("fred",), provider_symbols={"fred": "IR3TIB01KRM156N"},
    ),
    SeriesSpec(
        series_id="vix_index_daily", symbol="VIXCLS", asset_class="vol_index", currency="USD",
        market="FRED (CBOE)", timezone="America/New_York", close_local=time(16, 15),
        availability_lag=_STD_LAG,
        availability_note="CBOE close; FRED publishes same evening.",
        units="annualised implied vol, percentage points", start=None, confirmed=False,
        providers=("fred",), provider_symbols={"fred": "VIXCLS"},
        notes=("The US vol leg. Implied rather than realised, and the asymmetry is stated "
               "wherever it is used: Korea has no freely reachable implied-vol series, so the "
               "Korean leg is REALISED and the two are not like-for-like."),
    ),
    SeriesSpec(
        series_id="us_rate_effr_daily", symbol="EFFR", asset_class="rate", currency="USD",
        market="FRED (NY Fed)", timezone="America/New_York", close_local=time(9, 0),
        availability_lag=timedelta(days=1),
        availability_note="Effective federal funds rate, published T+1.",
        units="percent per annum", start=None, confirmed=False,
        providers=("fred",), provider_symbols={"fred": "EFFR"},
    ),
)

PAIRS: tuple[PairSpec, ...] = (
    # --- Brazil control cohort (S19). Every ratio verified against the implied ratio and
    # every one lands within 1.1% of an exact integer -- which is itself evidence of
    # fungibility, since a freely arbitraged pair has nowhere to drift TO.
    PairSpec(
        pair_id="pldt", adr="pldt_adr_daily", local="pldt_local_daily", fx="usdphp_spot_daily",
        local_shares_per_adr=1.0,
        ratio_source=(
            "Empirically derived and stable: implied local-shares-per-ADR is 1.000 over all "
            "7,454 joined sessions 1994-2026, median 0.998, no annual median outside "
            "0.98-1.01. TODO(ash): confirm against the PLDT 20-F depositary terms."
        ),
        confirmed=False,
        notes=(
            "CLASSIFICATION DELIBERATELY WITHHELD -- this pair is NOT in REGIME_OF_PAIR and "
            "therefore enters no fit or test. The Philippine constitution caps foreign "
            "ownership of public utilities at 40%, which is the right SHAPE of rule for the "
            "one_way_constrained class and comes from a different regulator, legal system "
            "and currency than the four Taiwanese pairs -- exactly the independent variation "
            "the panel lacks. What is NOT established is whether that ceiling constrains ADR "
            "ISSUANCE at the margin: PLDT has historically managed the ratio through voting "
            "preferred shares issued to Filipino holders, which would leave the depositary "
            "unconstrained. Classifying it from the observed parity would be circular, and "
            "the taxonomy forbids it: regime is a rule, binding-ness is a state. Resolve by "
            "reading the 20-F foreign-ownership disclosure and the depositary agreement, "
            "then add to REGIME_OF_PAIR.\n"
            "ONE PERIOD NEEDS QA BEFORE ANY USE. 1997 shows an annual mean premium of +18.3% "
            "and a single-day maximum of +103.5% against a 32-year median of -0.20%; every "
            "other year sits inside +/-1.7%. That is the Asian Financial Crisis window, when "
            "the peso went from roughly 26 to 42 per USD, and a large phantom premium is "
            "exactly what a date-mismatched FX leg produces during a currency collapse. It "
            "may be real dislocation or it may be measurement; nothing here depends on which, "
            "because this pair enters no fit -- but a sample restriction is likely needed "
            "before it ever does."
        ),
    ),
    PairSpec(
        pair_id="vale", adr="vale_adr_daily", local="vale_local_daily", fx="usdbrl_spot_daily",
        local_shares_per_adr=1.0, ratio_source="Vale ADR: 1 ADS = 1 ordinary share.",
        confirmed=False, notes="Implied ratio 1.000, IQR [0.997, 1.003].",
    ),
    PairSpec(
        pair_id="itub", adr="itub_adr_daily", local="itub_local_daily", fx="usdbrl_spot_daily",
        local_shares_per_adr=1.0, ratio_source="Itau Unibanco ADR: 1 ADS = 1 preferred share (ITUB4).",
        confirmed=False, notes="Implied ratio 0.997, IQR [0.993, 1.001].",
        sample_start="2006-01-01",
        sample_reason=(
            _CONTROL_RATIO_REGIME
            + "ADR ratio regime. Annual median implied ratio runs ~499 (2002-2004), 0.50 (2005), then 1.00 from 2006 to date -- two ratio changes before the current 1:1 regime. Sample starts at the current regime. TODO(ash): confirm the change dates against Itau's 20-F/6-K."
        ),
    ),
    PairSpec(
        pair_id="abev", adr="abev_adr_daily", local="abev_local_daily", fx="usdbrl_spot_daily",
        local_shares_per_adr=1.0, ratio_source="Ambev ADR: 1 ADS = 1 ordinary share.",
        confirmed=False, notes="Implied ratio 0.994, IQR [0.989, 1.000].",
        sample_start="2008-01-01",
        sample_reason=(
            _CONTROL_RATIO_REGIME
            + "ADR ratio regime. Annual median implied ratio runs ~100 (2000), ~20 (2001-2007), then 1.00 from 2008 to date. TODO(ash): confirm against AmBev/Ambev S.A. filings; note the 2013 Ambev S.A. reorganisation sits INSIDE the stable regime and does not move the ratio."
        ),
    ),
    PairSpec(
        pair_id="pbr", adr="pbr_adr_daily", local="pbr_local_daily", fx="usdbrl_spot_daily",
        local_shares_per_adr=2.0,
        ratio_source="Petrobras ADR (PBR): 1 ADS = 2 ORDINARY shares (PETR3).",
        confirmed=False,
        notes=(
            "PBR maps to PETR3, NOT PETR4 -- PBR.A is the preferred-line ADR. Against PETR3 "
            "the implied ratio is 1.999, IQR [1.993, 2.005]; against PETR4 it is 2.169 with "
            "IQR [2.090, 2.232]. The wrong mapping is plausible, not obviously broken."
        ),
        sample_start="2008-01-01",
        sample_reason=(
            _CONTROL_RATIO_REGIME
            + "ADR ratio regime: annual median implied ratio runs 1.00 (2000-2005), 4.00 "
              "(2006-2007), then 2.00 from 2008 to date. TODO(ash): confirm against Petrobras "
              "filings."
        ),
    ),
    PairSpec(
        pair_id="ggb", adr="ggb_adr_daily", local="ggb_local_daily", fx="usdbrl_spot_daily",
        local_shares_per_adr=1.0, ratio_source="Gerdau ADR: 1 ADS = 1 preferred share (GGBR4).",
        confirmed=False, notes="Implied ratio 0.995, IQR [0.989, 1.001]. GGB maps to GGBR4, not GGBR3.",
        sample_start="2000-01-01",
        sample_reason=(
            _CONTROL_RATIO_REGIME
            + "First-year artefact: annual median implied ratio 0.02 in 1999 against 1.00 from 2000 to date. TODO(ash): confirm whether 1999 is a ratio regime or a bad-print window."
        ),
    ),
    # --- Taiwan cohort (S18). Ratios from each issuer's ADS terms; all unconfirmed
    # pending a filing check, and each is sanity-checked against the implied ratio
    # P_adr*FX/P_local, which flags a gross error without being used to TUNE the value.
    PairSpec(
        pair_id="umc", adr="umc_adr_daily", local="umc_local_daily", fx="usdtwd_spot_daily",
        local_shares_per_adr=5.0,
        ratio_source="UMC ADS terms: 1 ADS = 5 common shares.",
        confirmed=False,
        notes="TODO(ash): confirm against UMC 20-F / deposit agreement.",
    ),
    PairSpec(
        pair_id="ase", adr="ase_adr_daily", local="ase_local_daily", fx="usdtwd_spot_daily",
        local_shares_per_adr=2.0,
        ratio_source="ASE Technology Holding ADS terms: 1 ADS = 2 common shares.",
        confirmed=False,
        sample_start="2018-05-02",
        sample_reason=(
            "2018 ASE Inc -> ASE Technology Holding share exchange. The provider's 3711.TW "
            "series splices the predecessor 2311.TW history in UNADJUSTED: on 2018-04-30 the "
            "local close steps 44.5 -> 80.3 while the implied ratio steps 4.0 -> 2.0, and the "
            "constructed premium reaches +57,714%. A ratio spline would NOT fix it -- the "
            "price step is 1.80x against a 2.0x ratio change, so splining injects a spurious "
            "~10% level shift. Pre-exchange, the two legs are different securities."
        ),
        notes="TODO(ash): confirm the post-exchange ratio against the ASE 20-F.",
    ),
    PairSpec(
        pair_id="auo", adr="auo_adr_daily", local="auo_local_daily", fx="usdtwd_spot_daily",
        local_shares_per_adr=10.0,
        ratio_source="AU Optronics ADS terms: 1 ADS = 10 common shares.",
        confirmed=False,
        excluded=True,
        sample_end="2019-10-01",
        sample_reason=(
            "AU Optronics filed Form 25 on 2019-09-20 to delist its ADSs from the NYSE, "
            "moving to a sponsored Level I OTC programme (AUOTY) and later deregistering. "
            "The exchange-listed series therefore ends 2019-10-01. EXCLUDED rather than "
            "truncated: an OTC ADR quote is thin and stale, so a premium built on it measures "
            "quote staleness as much as mispricing. The 2002-2019 window is usable and is "
            "retained in the registry for anyone who wants it, but it is out of the pooled "
            "estimate because a delisted programme is no longer the object of study."
        ),
        notes="Landed and kept for the record; not pooled. See sample_reason.",
    ),
    PairSpec(
        pair_id="cht", adr="cht_adr_daily", local="cht_local_daily", fx="usdtwd_spot_daily",
        local_shares_per_adr=10.0,
        ratio_source="Chunghwa Telecom ADS terms: 1 ADS = 10 common shares.",
        confirmed=False,
        notes="TODO(ash): confirm against CHT 20-F; CHT pays large annual dividends, so the "
              "premium series needs a dividend-timing check the others may not.",
    ),
    PairSpec(
        pair_id="skhy",
        adr="skhy_adr_daily",
        local="skhynix_local_daily",
        fx="usdkrw_spot_daily",
        local_shares_per_adr=0.1,
        ratio_source="README §2: '10 ADRs = 1 Korean common share (000660.KS)'.",
        confirmed=True,
        notes="Ratio is stated in the repo constitution, so it is treated as given.",
    ),
    PairSpec(
        pair_id="tsmc",
        adr="tsm_adr_daily",
        local="tsmc_local_daily",
        fx="usdtwd_spot_daily",
        local_shares_per_adr=5.0,
        ratio_source="TSMC depositary terms: 1 ADR = 5 common shares.",
        confirmed=False,
        sample_start="2005-01-03",
        sample_reason=(
            "TSMC's stock-dividend era. Both legs are raw closes and the ratio is a constant "
            "5.0, so an annual stock dividend that the two providers adjust inconsistently "
            "accumulates into the level: the constructed premium averages -55% in 1997 and "
            "walks monotonically to roughly zero by 2005, which is a compounded share-count "
            "artefact, not a discount any arbitrageur left on the table. Eleven one-leg-only "
            "price jumps >5sd are detected, ALL of them between 1997-10-09 and 2002-07-25 "
            "and clustered in the June-August ex-dividend season; none occur afterwards in "
            "24 years. Using adjusted closes on both legs is WORSE (annual mean +10% by 2004 "
            "against +2% raw) because the two legs' cash-dividend adjustments differ. "
            "The cause-based cut is 2002-07-26, the day after the last detected event; this "
            "start is the conservative one, which additionally requires the level to sit in "
            "an economically possible band. Both are reported: notebooks/09_tsmc_lab.ipynb "
            "runs its headline number under both starts as a curation sensitivity."
        ),
        notes=(
            "Cross-checked against the live sanity anchor: with this ratio the 2026-07-28 "
            "close-to-close premium lands in low double digits, consistent with the ~12.6% "
            "five-year average in README §2. TODO(ash): confirm against the depositary "
            "agreement before this pair enters the S3 comparator panel."
        ),
    ),
    PairSpec(
        pair_id="infy",
        adr="infy_adr_daily",
        local="infy_local_daily",
        fx="usdinr_spot_daily",
        local_shares_per_adr=1.0,
        ratio_source="Infosys ADR: 1 ADS = 1 equity share (post-2018 ratio change).",
        confirmed=False,
        notes="TODO(ash): confirm ratio AND whether the pre-change history needs a ratio spline.",
    ),
    PairSpec(
        pair_id="ibn",
        adr="ibn_adr_daily",
        local="icicibank_local_daily",
        fx="usdinr_spot_daily",
        local_shares_per_adr=2.0,
        ratio_source="ICICI Bank ADR: 1 ADS = 2 equity shares.",
        confirmed=False,
        notes="TODO(ash): confirm ratio and check for splits/bonus issues on the local leg.",
    ),
    PairSpec(
        pair_id="baba",
        adr="baba_adr_daily",
        local="baba_local_daily",
        fx="usdhkd_spot_daily",
        local_shares_per_adr=8.0,
        ratio_source="Alibaba: 1 ADS = 8 ordinary shares.",
        confirmed=False,
        notes=(
            "Unconstrained control: US/HK lines are fully fungible, so pi should sit at "
            "conversion cost with no one-sided drift. TODO(ash): confirm ratio."
        ),
    ),
)


def all_series() -> tuple[SeriesSpec, ...]:
    return (D1_SERIES + D6_TSMC_SERIES + D6_EXTRA_SERIES + D6_TAIWAN_SERIES
            + D6_BRAZIL_SERIES + D2_MACRO_SERIES)


def series_by_id(series_id: str) -> SeriesSpec:
    for spec in all_series():
        if spec.series_id == series_id:
            return spec
    raise KeyError(f"unknown series_id: {series_id}")


def pair_by_id(pair_id: str) -> PairSpec:
    for pair in PAIRS:
        if pair.pair_id == pair_id:
            return pair
    raise KeyError(f"unknown pair_id: {pair_id}")
