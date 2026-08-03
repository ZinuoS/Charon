"""D8 — DART 5%+ substantial-shareholding filings: the only public view of the LOCAL leg.

WHY THIS SOURCE EXISTS IN THIS REPOSITORY. Session 32R established that a swap-financed
ADR/local pair is invisible in US disclosure: 13F reports US-listed LONGS only, and Korean
lines are not SEC-registered so no beneficial-ownership regime reaches them. DART's
`majorstock` endpoint is the single public route to the leg that actually matters — who holds
5%+ of a Korean listed name, including foreign managers. It is the one source that can
evidence local-leg execution capacity from paper rather than from assumption.

THE TRAP THIS MODULE EXISTS TO NEUTRALISE. **DART returns HTTP 200 for its errors.** A missing
key, an expired key, a rate limit and "no data" all arrive as a 200 with a `status` field in
the body. The repository's `_http.py` doctrine turns on distinguishing a 404 (the request is
wrong, permanently) from a 429 (server load, decays) — and DART hides both inside a success
code. A caller that checks only the HTTP status sees success and an empty result, which is the
worst possible failure: silent, and indistinguishable from a genuine absence of filings.

So every response is decoded through :data:`STATUS`, and anything other than `000` raises with
the meaning attached.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "https://opendart.fss.or.kr/api"

#: DART's own status codes. `000` is the only success.
STATUS = {
    "000": "normal",
    "010": "unregistered key",
    "011": "key is not usable (suspended or not yet active)",
    "013": "no data for this query — a real answer, not an error",
    "020": "request limit exceeded (DART throttles per day, not per second)",
    "100": "missing or invalid parameter — including a missing certification key",
    "800": "system maintenance",
    "900": "undefined error",
    "901": "expired key",
}

#: Statuses that mean "wait and retry" rather than "this request is wrong".
TRANSIENT = {"020", "800"}


class DartError(RuntimeError):
    """A DART status other than 000, with its meaning and whether retrying could help."""

    def __init__(self, status: str, message: str) -> None:
        self.status, self.message = status, message
        self.transient = status in TRANSIENT
        kind = "TRANSIENT — retry later" if self.transient else "PERMANENT for this request"
        super().__init__(f"DART status {status} ({STATUS.get(status, 'unknown')}): "
                         f"{message} [{kind}]")


def _key() -> str:
    """The API key, by the same convention every other adapter in this repo uses."""
    import os

    key = os.environ.get("OPENDART_API_KEY")
    if not key:
        env = _REPO_ROOT / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.strip().startswith("OPENDART_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise DartError("100", "no OPENDART_API_KEY in the environment or .env — register "
                               "free at opendart.fss.or.kr and set it")
    return key


def _get(endpoint: str, **params) -> dict:
    """One DART call, with its in-body status decoded into an exception or a payload."""
    q = urllib.parse.urlencode({"crtfc_key": _key(), **params})
    req = urllib.request.Request(f"{BASE}/{endpoint}?{q}",
                                 headers={"User-Agent": "charon-research"})
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.loads(r.read().decode("utf-8"))
    status = str(payload.get("status", "900"))
    if status != "000":
        raise DartError(status, payload.get("message", ""))
    return payload


def major_holders(corp_code: str) -> list[dict]:
    """5%+ substantial-shareholding reports for one issuer.

    `corp_code` is DART's own eight-digit issuer id, NOT the KRX ticker. The mapping lives in
    the `corpCode.xml` bundle, which is a zipped index of every registered issuer.
    """
    return _get("majorstock.json", corp_code=corp_code).get("list", [])


def probe() -> dict:
    """Is the key present and usable? Answers without pulling anything."""
    try:
        _key()
    except DartError as exc:
        return {"key_present": False, "usable": False, "status": exc.status,
                "detail": exc.message}
    try:
        # SK hynix's DART corp_code; any valid id proves the key rather than the query.
        major_holders("00164779")
        return {"key_present": True, "usable": True, "status": "000"}
    except DartError as exc:
        return {"key_present": True, "usable": exc.status == "013",
                "status": exc.status, "detail": str(exc)}


if __name__ == "__main__":
    # The check that matters: an error hidden in a 200 must raise, not return empty.
    assert STATUS["000"] == "normal" and "013" in STATUS
    assert "020" in TRANSIENT and "010" not in TRANSIENT, (
        "a rate limit decays and an unregistered key does not — conflating them is how a "
        "caller retries forever against a permanent refusal")
    e = DartError("020", "limit")
    assert e.transient and "retry later" in str(e)
    e = DartError("901", "expired")
    assert not e.transient and "PERMANENT" in str(e)
    print("ok:", probe())
