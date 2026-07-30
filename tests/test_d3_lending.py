"""D3 lending — the two traps in KOFIA's response, and the landed series.

Offline. Nothing here touches the network; the parser is exercised on a fixture that
reproduces both hazards found in the live payload.
"""

from __future__ import annotations

import json
import re

import pytest

from pipeline.ingest._adapters import KofiaAdapter

# A real response, trimmed: two dated rows plus the two aggregate rows, and the 합계 row
# carries the masked overflow exactly as the server emits it — digits then bare ######,
# unquoted, which makes the document invalid JSON.
RAW = (
    b'{"unit":"","ds1":['
    b'{"TMPV1":"20260729","TMPV2":"SK\xed\x95\x98\xec\x9d\xb4\xeb\x8b\x89\xec\x8a\xa4",'
    b'"TMPV3":1156990,"TMPV4":371416,"TMPV5":14348212,"TMPV6":20101845},'
    b'{"TMPV1":"20260728","TMPV2":"SK\xed\x95\x98\xec\x9d\xb4\xeb\x8b\x89\xec\x8a\xa4",'
    b'"TMPV3":691679,"TMPV4":205619,"TMPV5":13562638,"TMPV6":21022089},'
    b'{"TMPV1":"\xed\x95\xa9\xea\xb3\x84","TMPV2":"-","TMPV3":1848669,"TMPV4":577035,'
    b'"TMPV5":181258######,"TMPV6":10531######},'
    b'{"TMPV1":"\xed\x8f\x89\xea\xb7\xa0","TMPV2":"-","TMPV3":924334,"TMPV4":288517,'
    b'"TMPV5":13955425,"TMPV6":20561967}'
    b'],"dsmHeader":""}'
)


def _parse(raw: bytes) -> list[dict]:
    payload = json.loads(KofiaAdapter._MASKED.sub(rb"\1null", raw).decode("utf-8"))
    return [r for r in payload["ds1"] if r["TMPV1"] not in KofiaAdapter.AGGREGATE_ROWS]


def test_the_raw_payload_really_is_invalid_json():
    """If this ever passes, the server stopped masking and the repair is dead weight."""
    with pytest.raises(json.JSONDecodeError):
        json.loads(RAW.decode("utf-8"))


def test_masked_overflow_is_repaired_not_dropped():
    repaired = KofiaAdapter._MASKED.sub(rb"\1null", RAW)
    assert b"######" not in repaired
    assert json.loads(repaired.decode("utf-8"))["ds1"][2]["TMPV5"] is None


def test_aggregate_rows_are_excluded():
    """합계 and 평균 are not dates. Left in, they enter a time series as two observations
    with garbage timestamps."""
    rows = _parse(RAW)
    assert [r["TMPV1"] for r in rows] == ["20260729", "20260728"]


def test_frame_is_sorted_ascending_with_typed_dates():
    import datetime as dt
    df = KofiaAdapter.to_frame(_parse(RAW))
    assert list(df.date) == sorted(df.date)
    assert isinstance(df.date.iloc[0], dt.date)
    assert df.balance_shares.iloc[-1] == 14348212


def test_value_column_is_named_as_unverified():
    """The unit is not established: tmpV40=1000000 implies millions of KRW, but the implied
    per-share value is several times the traded price. Naming it honestly is cheaper than
    landing a wrong unit that a cost calculation later trusts."""
    df = KofiaAdapter.to_frame(_parse(RAW))
    assert "balance_value_unverified_unit" in df.columns


def test_landed_series_covers_the_barrier_window():
    """The point of the pull: 000660 lending must span the SKHY listing, or it cannot inform
    recall risk on the position that exists now."""
    import pandas as pd
    from pipeline.ingest._common import latest_raw_file
    try:
        path = latest_raw_file("d3_lending", "skhynix_lending_daily.csv")
    except Exception:
        pytest.skip("d3 not pulled in this environment")
    df = pd.read_csv(path, parse_dates=["date"])
    assert len(df) > 3000, f"only {len(df)} rows; expected a decade of history"
    assert (df.date > "2026-07-10").any(), "series does not reach the SKHY listing"
    assert df.balance_shares.gt(0).all()
