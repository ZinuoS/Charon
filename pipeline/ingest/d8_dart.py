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

import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from pathlib import Path

from ._http import DEFAULT_CLIENT

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


#: DART issues 40-character lowercase-hex keys. Anything else never reached DART's registry,
#: so it cannot be an "unregistered key" — it is a local mistake wearing a remote error's face.
_KEY_SHAPE = re.compile(r"[0-9a-f]{40}")


def _key() -> str:
    """The API key, by the same convention every other adapter in this repo uses.

    Validated for SHAPE before it is spent on a request. Without this, a placeholder or a
    truncated paste travels to DART and comes back as status `010`, "unregistered key" — which
    reads as *the key was rejected* and sends you to the registration site to re-register a key
    that was never the problem. It cost exactly that detour once. A local mistake must not be
    allowed to impersonate a remote refusal; that is this module's whole thesis, applied to its
    own input. The `.env` scan takes the LAST assignment, matching dotenv precedence, so a
    freshly appended key wins over a stale line above it rather than losing to it silently.
    """
    import os

    key = os.environ.get("OPENDART_API_KEY", "").strip()
    if not key:
        env = _REPO_ROOT / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.strip().startswith("OPENDART_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        raise DartError("100", "no OPENDART_API_KEY in the environment or .env — register "
                               "free at opendart.fss.or.kr and set it")
    if not _KEY_SHAPE.fullmatch(key):
        raise DartError("100", f"OPENDART_API_KEY is not a DART key: got {len(key)} characters "
                               f"({key[:4]}...{key[-4:]}), expected 40 hex. This never left the "
                               f"machine — replace the value in .env with the real key.")
    return key


def _get(endpoint: str, **params) -> dict:
    """One DART call, with its in-body status decoded into an exception or a payload.

    Transport is the repository's shared client, not raw urllib. That is not a formality:
    `_http.py` owns the retry policy, the inter-request spacing, the response cache and the
    404-vs-429 doctrine, and `tests/test_no_network_in_analysis.py` asserts it is the ONLY
    module that opens a socket. The first draft of this file called urllib directly and the
    test caught it — while the docstring above was explaining the very doctrine it broke.
    """
    raw = DEFAULT_CLIENT.get(f"{BASE}/{endpoint}", params={"crtfc_key": _key(), **params})
    payload = json.loads(raw)
    status = str(payload.get("status", "900"))
    if status != "000":
        raise DartError(status, payload.get("message", ""))
    return payload


@lru_cache(maxsize=1)
def _corp_index() -> dict[str, tuple[str, str]]:
    """KRX stock code -> (DART corp_code, corp_name), from DART's own registry.

    The corp_code is NOT the ticker, and a wrong one does not error — it returns some other
    issuer's filings, which is the failure this repository has already paid for twice on
    symbology (Yahoo's `.KS` vs EODHD's `.KO`, and the KOSPI index code). So the mapping is
    fetched from the registry rather than typed from memory, and every pull re-checks the
    returned `corp_name` against it.

    This endpoint answers with a ZIP on success and JSON on failure, so the body is sniffed
    before it is parsed as either.
    """
    raw = DEFAULT_CLIENT.get(f"{BASE}/corpCode.xml", params={"crtfc_key": _key()})
    if raw[:1] in (b"{", b"<"):          # an error body, not the archive
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise DartError("900", f"corpCode returned neither ZIP nor JSON: {raw[:120]!r}")
        raise DartError(str(payload.get("status", "900")), payload.get("message", ""))

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        xml = archive.read(archive.namelist()[0])

    index: dict[str, tuple[str, str]] = {}
    for el in ET.fromstring(xml).iter("list"):
        stock = (el.findtext("stock_code") or "").strip()
        if stock:                        # blank for the many unlisted registered issuers
            index[stock] = ((el.findtext("corp_code") or "").strip(),
                            (el.findtext("corp_name") or "").strip())
    return index


def corp_code(stock_code: str) -> tuple[str, str]:
    """Resolve a six-digit KRX code to (corp_code, corp_name). Raises if absent."""
    hit = _corp_index().get(stock_code)
    if hit is None:
        raise DartError("013", f"KRX code {stock_code} is not in DART's registry of listed "
                               f"issuers ({len(_corp_index())} entries)")
    return hit


def major_holders(corp_code: str) -> list[dict]:
    """5%+ substantial-shareholding reports for one issuer.

    `corp_code` is DART's own eight-digit issuer id, NOT the KRX ticker. The mapping lives in
    the `corpCode.xml` bundle, which is a zipped index of every registered issuer.
    """
    return _get("majorstock.json", corp_code=corp_code).get("list", [])


#: Issuers outside the pair registry worth pulling anyway.
EXTRA_ISSUERS = {
    # The only positive hit in the session-32R evidence log was a US fund holding its
    # PREFERENCE line — the discount instrument this desk's thesis generalises to.
    "005930": "Samsung Electronics (preference-line comparator)",
    # SK hynix's holding company. Governance-adjacent: a holding-company discount and an ADR
    # premium are the same species of Law-of-One-Price gap, and the shareholder register of
    # the parent is where a manager expressing the SK complex through the holdco would appear.
    "402340": "SK Square (governance-adjacent holdco)",
}


def korean_stock_codes() -> dict[str, str]:
    """KRX codes for every Korean local leg in the pair registry, plus the comparators.

    Driven off the registry rather than a hand-kept list, so landing another Korean pair
    extends this pull instead of silently leaving it out of the evidence base.
    """
    from .registry import PAIRS, series_by_id

    # `series_by_id` spans every D*_SERIES collection. Reading one of them directly — as the
    # first draft of this function did with D1_SERIES — silently returned SK hynix alone and
    # dropped KT and SKM, the two pairs this pull most needed. A partial view of the registry
    # produces a pull that looks complete and is not.
    out = dict(EXTRA_ISSUERS)
    for pair in PAIRS:
        symbol = getattr(series_by_id(pair.local), "symbol", "")
        if symbol.endswith((".KS", ".KO", ".KQ")):
            out[symbol.split(".")[0]] = pair.pair_id
    return out


def pull(codes: dict[str, str] | None = None, out_root: Path | None = None) -> dict:
    """The 5%+ substantial-shareholding pull, snapshotted to ``data/raw/d8_dart/<date>/``.

    Every issuer's returned `corp_name` is checked against the registry's name for the code we
    asked about. A wrong corp_code does not error at DART — it answers with a DIFFERENT
    issuer's filings, and an unchecked pull would file those under our label. That is the same
    silent-substitution failure as a symbology miss, which has cost this repository data twice.
    """
    from ._common import RAW_ROOT

    codes = codes or korean_stock_codes()
    root = (out_root or RAW_ROOT / "d8_dart") / _today()
    root.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict] = {}
    for stock_code, label in sorted(codes.items()):
        code, name = corp_code(stock_code)
        try:
            rows = major_holders(code)
        except DartError as exc:
            if exc.status != "013":          # 013 is "no filings", a real answer
                raise
            rows = []
        mismatched = {r.get("corp_name") for r in rows} - {name}
        if mismatched:
            raise DartError("900", f"corp_code {code} was asked for {name!r} but returned "
                                   f"filings for {mismatched!r} — refusing to file these")
        (root / f"{stock_code}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest[stock_code] = {"label": label, "corp_code": code, "corp_name": name,
                                "rows": len(rows),
                                "first": min((r["rcept_dt"] for r in rows), default=None),
                                "last": max((r["rcept_dt"] for r in rows), default=None)}
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


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

    # A malformed key must be caught HERE, not by DART. The placeholder below is the exact
    # value that shipped into .env once and came back as "unregistered key".
    import os

    for bad in ("your_key_here", "abc123", "A" * 40, "0" * 39):
        os.environ["OPENDART_API_KEY"] = bad
        try:
            _key()
        except DartError as exc:
            assert exc.status == "100" and "never left the machine" in exc.message
        else:
            raise AssertionError(f"malformed key {bad!r} passed the shape check")
    os.environ["OPENDART_API_KEY"] = "0123456789abcdef" * 2 + "01234567"
    assert len(_key()) == 40, "a well-formed key must survive the shape check"
    del os.environ["OPENDART_API_KEY"]

    print("ok:", probe())
