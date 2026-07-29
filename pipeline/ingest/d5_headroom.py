"""D5 — KSD/SEIBro DR conversion headroom, per ISIN, daily.

This is the barrier-state observable. README §3.3 says the barrier's on/off/partial state
is "observable via quota headroom (§4 D5), which makes regime modelling a data problem
rather than a latent-variable guess" — this puller is that observability.

What the field actually is
--------------------------
``DR전환가능주식수량`` is the **remaining capacity to convert ordinary shares into DRs**:
a programme's issuance ceiling minus its DRs outstanding. It is **not** DR outstanding,
and mistaking it for that would invert the H5 signal.

* **level** = barrier state (M2)
* **first difference** = net creation (headroom consumed) or cancellation (headroom freed),
  which is the H5 flow signal

Programme-specific, and that is the finding
-------------------------------------------
The first pull established empirically what documentation could not settle: the field is
**per-programme**, not a company-level foreign-ownership limit. SK Hynix carries two DR
programmes with different values, and one company cannot have two foreign-ownership
limits.

* ``US78392B2060`` — the 2026 ADR programme. Headroom **0**: the 2.5% deal cap, exhausted
  at the offering. **This is the series H5 is about.**
* ``US78392B1070`` — a legacy programme with history to 2010 and live movement. A
  different, unconstrained channel. Building H5 on it would answer a different question
  confidently and wrongly.

Both are pulled: the legacy series is the **control for publication itself**. If the
capped programme prints nothing on a given day, the legacy series distinguishes "KSD did
not publish today" from "headroom did not move" — which is exactly the distinction H5's
untestable branch turns on.

Terms: ``seibro.or.kr/robots.txt`` returns HTTP 200 and is zero bytes — no restrictions
declared. Gated on ``approved: yes`` for ``seibro_dr_capacity`` regardless.

Usage::

    uv run python -m pipeline.ingest.d5_headroom
"""

from __future__ import annotations

import argparse
import html
import io
import re
from dataclasses import dataclass

import pandas as pd

from . import _common as C
from ._http import DEFAULT_CLIENT, ProviderError
from .approval import require_approved

SOURCE = "d5_headroom"
SOURCE_ID = "seibro_dr_capacity"
URL = "https://m.seibro.or.kr/cnts/ovssec/selectOverSecDRConvPoss.do"


@dataclass(frozen=True)
class DrProgramme:
    series_id: str
    isin: str
    korean_name: str
    role: str
    note: str


PROGRAMMES: tuple[DrProgramme, ...] = (
    DrProgramme(
        "skhynix_dr_headroom_capped", "US78392B2060", "에스케이하이닉스",
        "barrier_state",
        "The 2026 ADR programme. Headroom 0 at first observation (2026-07-15) — the "
        "exhausted 2.5% deal cap. THIS is H5's observable.",
    ),
    DrProgramme(
        "skhynix_dr_headroom_legacy", "US78392B1070", "에스케이하이닉스",
        "publication_control",
        "Legacy programme, history to 2010, actively moving. NOT the SKHY barrier — "
        "carried as a control that distinguishes 'KSD did not publish' from "
        "'headroom did not move'.",
    ),
)

_ROW_RE = re.compile(r"(20\d{2})[./-](\d{2})[./-](\d{2})\s+([\d,]+)")


def fetch_programme(prog: DrProgramme) -> tuple[pd.DataFrame, str, dict]:
    params = {"searchCode": prog.isin, "txt_code": prog.isin, "txt_sch": prog.korean_name}
    raw = DEFAULT_CLIENT.get(URL, params=params)
    text = re.sub(r"<[^>]+>", " ", raw.decode("utf-8", errors="replace"))
    text = re.sub(r"\s+", " ", html.unescape(text))

    rows = [
        {"date": f"{y}-{m}-{d}", "headroom_shares": int(v.replace(",", ""))}
        for y, m, d, v in _ROW_RE.findall(text)
    ]
    if not rows:
        raise ProviderError(f"{prog.isin}: no headroom rows parsed from SEIBro response")

    frame = pd.DataFrame(rows).drop_duplicates(subset=["date"], keep="last")
    return frame.sort_values("date").reset_index(drop=True), URL, params


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    frame.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode("utf-8")


def pull(prog: DrProgramme, pull_date: str | None = None) -> dict:
    require_approved(SOURCE_ID)
    partition = C.pull_partition(SOURCE, pull_date)
    out = partition / f"{prog.series_id}.csv"
    pulled_at = C.utc_now_iso()

    frame, url, params = fetch_programme(prog)
    payload = to_csv_bytes(frame)
    digest, written = C.write_immutable(out, payload)

    C.write_sidecar(out, {
        "series_id": prog.series_id,
        "isin": prog.isin,
        "role": prog.role,
        "provider": "ksd_seibro",
        "transport": "selectOverSecDRConvPoss",
        "source_url": url,
        "request_params": params,
        "pulled_at_utc": pulled_at,
        "native_timezone": "Asia/Seoul",
        "availability_lag": (
            "TODO(ash): KSD's publication time for the daily capacity figure is "
            "unverified. Rows appear to be published on change rather than daily."
        ),
        "units": "shares (remaining ordinary shares convertible into DRs — HEADROOM, not DR outstanding)",
        "semantics": (
            "Issuance ceiling minus DRs outstanding, per PROGRAMME. Level = barrier "
            "state; first difference = creation (consumed) / cancellation (freed)."
        ),
        "rows": int(len(frame)),
        "first_obs_date": str(frame["date"].iloc[0]),
        "last_obs_date": str(frame["date"].iloc[-1]),
        "sha256": digest,
        "notes": prog.note,
    })
    C.append_pull_log(SOURCE, C.PullRecord(
        pulled_at_utc=pulled_at, source=SOURCE, series_id=prog.series_id,
        provider="ksd_seibro", source_url=url, params=params, rows=int(len(frame)),
        first_obs_date=str(frame["date"].iloc[0]), last_obs_date=str(frame["date"].iloc[-1]),
        sha256=digest, path=C.rel_to_repo(out), status="written" if written else "unchanged",
    ))
    C.update_checksums(SOURCE, {C.rel_to_repo(out): digest})
    return {"series_id": prog.series_id, "isin": prog.isin, "rows": len(frame),
            "first": frame["date"].iloc[0], "last": frame["date"].iloc[-1],
            "latest": int(frame["headroom_shares"].iloc[-1]), "status": "written" if written else "unchanged"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pull-date", default=None)
    args = parser.parse_args(argv)

    print(f"\n=== {SOURCE} ===")
    failed = 0
    for prog in PROGRAMMES:
        try:
            r = pull(prog, args.pull_date)
            print(f"  {r['status']:9s} {r['series_id']:28s} {r['isin']}  rows={r['rows']:5d}  "
                  f"{r['first']}..{r['last']}  latest={r['latest']:,}")
        except Exception as exc:  # noqa: BLE001 — reported, never substituted
            print(f"  FAILED    {prog.series_id:28s} {type(exc).__name__}: {str(exc)[:90]}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
