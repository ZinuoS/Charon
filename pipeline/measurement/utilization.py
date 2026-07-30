"""Borrow-utilization state for 000660, from the D3 lending series.

WHAT THIS IS NOT: an M5 panel feature. `docs/features_m5.md` listed "lending utilization
state" under M5 and the ablation harness pools features across a regime class's pairs — but
D3 covers **000660 only**, and 000660 is SKHY's local leg, which is forward-test-only and
never fitted. A utilization feature can therefore enter **zero fitted pairs**, so there is no
fold structure to ablate it in. `tests/test_utilization.py` asserts that rather than leaving
it as a claim.

WHAT IT IS: a barrier-state observable, the same kind of thing H5's headroom monitor is.
`docs/regime_taxonomy.md` draws the distinction the project runs on — regime is a *rule*,
binding-ness is a *state* — and borrow scarcity is a state reading on the short side. Its live
consumer is the financing sheet's RECALL RISK line, which is the public half of a borrow
question whose other half the desk quotes.

**Utilization here is RELATIVE, not a true ratio.** A real utilization figure is on-loan over
lendable, and lendable is not public. What is public is the on-loan balance, so the state is
that balance against its OWN history — a percentile, terciled. That measures scarcity
relative to normal for this name, which is the question recall risk actually asks, and it does
not pretend to be a fraction of supply.
"""

from __future__ import annotations

import pandas as pd

from pipeline.ingest._common import latest_raw_file

#: Lookback for the percentile. Five years of sessions: long enough that a tercile means
#: "unusual for this name" rather than "unusual this quarter", short enough that a 2010
#: regime does not define today's normal.
WINDOW = 1250
TERCILES = ("low", "normal", "tight")


def load() -> pd.DataFrame:
    """The landed D3 series, indexed by date."""
    path = latest_raw_file("d3_lending", "skhynix_lending_daily.csv")
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df


def utilization_state(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Balance percentile against its own trailing history, plus the flow, plus a tercile.

    Percentile is computed on a TRAILING window and excludes the current point's future by
    construction — `rolling` only ever sees the past. That is the information-timing rule
    (README §4) applied to a feature rather than asserted about one.
    """
    d = load() if df is None else df.copy()
    bal = d["balance_shares"]
    # ponytail: rolling rank via apply is O(n·WINDOW); at 4k rows it runs in under a second,
    # and a rank-preserving incremental structure would be the upgrade if this ever ran per-tick.
    pct = bal.rolling(WINDOW, min_periods=60).apply(
        lambda w: (w[:-1] <= w[-1]).mean(), raw=True)
    out = pd.DataFrame({
        "balance_shares": bal,
        "net_lending_shares": d["new_lending_shares"] - d["repaid_shares"],
        "balance_pctile": pct,
        "state": pd.cut(pct, [-0.01, 1 / 3, 2 / 3, 1.01], labels=list(TERCILES)),
    })
    return out


def current(df: pd.DataFrame | None = None) -> dict:
    """Latest reading, for the financing sheet's recall-risk line."""
    u = utilization_state(df).dropna(subset=["balance_pctile"])
    last = u.iloc[-1]
    return {
        "as_of": str(u.index[-1].date()),
        "balance_shares": int(last.balance_shares),
        "balance_pctile": round(float(last.balance_pctile), 3),
        "state": str(last.state),
        "net_lending_5d": int(u.net_lending_shares.tail(5).sum()),
        "n_obs": int(len(u)),
        "caveat": (
            "RELATIVE state, not a utilization ratio: lendable supply is not public, so this "
            "is the on-loan balance against its own trailing 1,250-session history."
        ),
    }


def ablation_status() -> dict:
    """Why this is not in the metrics table, computed rather than asserted."""
    from pipeline.convergence.jorda import FORWARD_TEST_PAIRS, REGIME_OF_PAIR
    fitted = sorted(set(REGIME_OF_PAIR) - FORWARD_TEST_PAIRS)
    covered = ["skhy"]                    # D3 is 000660 only
    usable = sorted(set(fitted) & set(covered))
    return {
        "fitted_pairs": fitted,
        "pairs_with_lending_data": covered,
        "usable_in_panel_fit": usable,
        "ablatable": bool(usable),
        "reason": (
            "D3 covers 000660 only, which is SKHY's local leg. SKHY is forward-test-only and "
            "never enters a fit, so the feature reaches zero fitted pairs and there is no fold "
            "structure to ablate it in."
        ),
        "route_to_a_real_ablation": (
            "Lending data for the panel pairs — TWSE SBL for the Taiwanese four, B3 BTB for "
            "the Brazilian five. Both need `approved:` marks in docs/data_sources.md, which "
            "are the author's alone."
        ),
    }


if __name__ == "__main__":
    print(current())
    print()
    for k, v in ablation_status().items():
        print(f"{k:26s} {v}")
