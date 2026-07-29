"""H5 — the headroom ledger monitor. The barrier-state observable, with its scope attached.

README §5 H5 casts this as "more monitor than trade at research scale... the state variable
that switches the model between barrier-off / barrier-partial regimes." That is what this
module is: it does not test the hypothesis, it maintains the observable the hypothesis
would be tested against.

What the observable is (ruled in `docs/data_sources.md`)
-------------------------------------------------------
KSD/SEIBro's ``DR전환가능주식수량`` is **programme-specific issuance-ceiling headroom** —
``ceiling - outstanding``, revolving. Established from the series' own behaviour: 502 up,
757 down, **zero** unchanged across 1,260 observations (it publishes only on change), in
block-sized steps; and the capped programme reading exactly 0 after the full board
authorization went to the depositary.

**Level** = barrier state. **First difference** = flow: a rise is capacity freed by
cancellation, a fall is capacity consumed by issuance.

The scope limit, printed on every output
----------------------------------------
Measured headroom and the *operative* gate are not the same object. The deposit agreement
gates on *"a level from time to time determined by the Company"* plus prior consent — a
level disclosed nowhere. So headroom can rise via cancellation while deposits remain
blocked by consent never granted.

This is why H5's registered criterion (author ruling, option (a)) carries an
**INDETERMINATE** branch: headroom moved, no deposit cleared, consent-state unobserved,
mechanism never demonstrably engaged. Without it a never-granted consent would look
identical to a refuted hypothesis.

Every function here emits :data:`SCOPE_NOTE` alongside its numbers, because a headroom
figure quoted without it invites exactly the inference the ruling forbids.

Two programmes, and only one is the subject
-------------------------------------------
* ``US78392B2060`` — the 2026 ADR programme. **This is H5's observable.**
* ``US78392B1070`` — legacy, history to 2010, actively moving. A *different, unconstrained*
  channel. It is carried as a **publication control**: when the capped programme prints
  nothing, the legacy series distinguishes "KSD did not publish today" from "headroom did
  not move" — the distinction the UNTESTABLE branch turns on.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from pipeline.ingest._common import latest_raw_file

CAPPED = "skhynix_dr_headroom_capped"      # US78392B2060 — the subject
CONTROL = "skhynix_dr_headroom_legacy"     # US78392B1070 — publication control

SCOPE_NOTE = (
    "SCOPE OF OBSERVABLE: this series measures programme issuance-ceiling headroom "
    "(ceiling - outstanding), NOT the operative deposit gate. Deposits additionally "
    "require the Company's prior consent against an undisclosed, revisable level "
    "(deposit agreement, F-6 Ex. 99(a)). Headroom can move without the barrier opening; "
    "a deposit clearing on US78392B2060 is what would evidence consent operates."
)


@dataclass
class LedgerState:
    """Current barrier state plus the flow that produced it."""

    programme: str
    isin: str
    n_obs: int
    first_obs: str | None
    last_obs: str | None
    level: int | None
    flow: pd.Series = field(default_factory=pd.Series)
    published_today: bool = False
    notes: list[str] = field(default_factory=list)

    def report(self) -> str:
        lines = [
            f"{self.programme}  ({self.isin})",
            f"  observations : {self.n_obs}"
            + (f"   {self.first_obs} .. {self.last_obs}" if self.n_obs else "   (none)"),
            f"  headroom     : {self.level:,}" if self.level is not None else "  headroom     : —",
        ]
        if len(self.flow):
            creations = int((self.flow > 0).sum())
            consumptions = int((self.flow < 0).sum())
            lines.append(f"  flow         : {creations} creation(s), {consumptions} consumption(s)")
            lines.append(f"  latest move  : {int(self.flow.iloc[-1]):+,}")
        else:
            lines.append("  flow         : no movement observed — level has never changed in sample")
        lines += [f"  ! {n}" for n in self.notes]
        return "\n".join(lines)


def _load(series_id: str) -> pd.DataFrame | None:
    path = latest_raw_file("d5_headroom", f"{series_id}.csv")
    if path is None:
        return None
    return pd.read_csv(path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)


def read_programme(series_id: str, isin: str) -> LedgerState:
    frame = _load(series_id)
    if frame is None or frame.empty:
        return LedgerState(series_id, isin, 0, None, None, None,
                           notes=["series not ingested — run `uv run python -m pipeline.ingest.d5_headroom`"])
    flow = frame.set_index("date")["headroom_shares"].diff().dropna()
    st = LedgerState(
        programme=series_id, isin=isin, n_obs=len(frame),
        first_obs=str(frame["date"].iloc[0].date()), last_obs=str(frame["date"].iloc[-1].date()),
        level=int(frame["headroom_shares"].iloc[-1]), flow=flow,
    )
    if st.level == 0:
        st.notes.append("headroom is ZERO — the barrier reads SEALED at this observation.")
    if st.n_obs == 1:
        st.notes.append(
            "single observation: KSD appears to publish only on change, so this is "
            "consistent with 'has not moved' rather than 'not published'. The control "
            "programme distinguishes the two."
        )
    return st


def ledger() -> dict[str, LedgerState]:
    return {"capped": read_programme(CAPPED, "US78392B2060"),
            "control": read_programme(CONTROL, "US78392B1070")}


def publication_check(states: dict[str, LedgerState]) -> str:
    """Did KSD publish at all recently? Answers 'no movement' vs 'no publication'.

    This is the whole reason the legacy programme is carried. Without it, a capped series
    that has not printed since 2026-07-15 is ambiguous between a sealed-and-static barrier
    and a silent data feed — and H5's UNTESTABLE branch depends on telling them apart.
    """
    cap, ctl = states["capped"], states["control"]
    if not ctl.n_obs:
        return "INDETERMINATE — no control series; cannot distinguish silence from stasis."
    if cap.last_obs and ctl.last_obs and cap.last_obs < ctl.last_obs:
        return (f"PUBLISHING — control printed to {ctl.last_obs} while the capped programme's "
                f"last print is {cap.last_obs}. The feed is live, so the capped programme "
                "has NOT MOVED. Barrier remains sealed by observation, not by absence of data.")
    return f"ALIGNED — both programmes print to {cap.last_obs}."


def flow_episodes(state: LedgerState, min_frac_of_level: float = 0.0025) -> pd.DataFrame:
    """Headroom-creation episodes above a fractional threshold.

    Threshold is expressed as a fraction of level rather than an absolute share count so
    the same rule applies across programmes of different size. It is a *reporting* filter
    here — H5's registered threshold lives in `calls.yaml` and is the author's, not this
    module's.
    """
    if not len(state.flow) or not state.level:
        return pd.DataFrame(columns=["date", "delta", "frac_of_level", "direction"])
    base = abs(state.level) or 1
    df = state.flow.reset_index()
    df.columns = ["date", "delta"]
    df["frac_of_level"] = df["delta"].abs() / base
    df["direction"] = df["delta"].apply(lambda d: "creation" if d > 0 else "consumption")
    return df[df["frac_of_level"] >= min_frac_of_level].reset_index(drop=True)


def status_report() -> str:
    """Full monitor output. SCOPE_NOTE is appended unconditionally, by design."""
    states = ledger()
    out = ["H5 — BARRIER-STATE LEDGER", "=" * 74]
    out += [states["capped"].report(), "", states["control"].report(), ""]
    out += ["PUBLICATION CHECK", "  " + publication_check(states), ""]
    eps = flow_episodes(states["control"])
    out.append(f"CONTROL-PROGRAMME EPISODES ≥0.25% of level: {len(eps)}")
    out += ["", "-" * 74, SCOPE_NOTE]
    return "\n".join(out)
