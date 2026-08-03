"""Provider-fragility layer: the design lesson from the Yahoo 429.

Session 1 opened with a 14-symbol availability probe, tripped an IP rate limit, and lost
the rest of the session to it — the limit outlasted every retry strategy tried against
it. The failure was not the provider's; it was a client that fanned out first and paced
itself afterwards. This module encodes the corrections so no future puller repeats it.

Five rules, each enforced here rather than left to a puller's discretion:

1.  **Exponential backoff with jitter** on 429/602/503. Jitter matters because a
    deterministic backoff from several symbols re-synchronises into the same retry
    instant and re-trips the limit as a burst.
2.  **Single-flight per host.** One in-flight request per host at a time, held by a lock.
    Parallel probes against one host are what produced the original ban.
3.  **Resumable progress.** A symbol already persisted is never re-fetched, so an
    interrupted panel pull resumes instead of restarting — the difference between
    recovering from a throttle and re-triggering it.
4.  **A local response cache.** Repeated runs during development hit disk, not the
    provider. Cache entries are content-addressed by URL plus params.
5.  **No pacing against assumed quotas.** The widely-cited FRED "120/min" and ECOS
    "10,000/day" figures appear in neither provider's documentation
    (`docs/data_sources.md`). Pacing to folklore produces false confidence; this client
    paces to a conservative floor and reacts to what the server actually returns.

Analysis code never imports this module — ``tests/test_no_network_in_analysis.py``
enforces that separation.
"""

from __future__ import annotations

import hashlib
import json
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO_ROOT / "data" / "derived" / "_http_cache"

# Retry-worthy status codes. 602 is ECOS's over-call code, returned inside a 200 body;
# adapters translate it before raising.
RATE_LIMIT_STATUSES = frozenset({429, 503})

DEFAULT_MIN_INTERVAL = 2.5      # seconds between requests to one host
DEFAULT_MAX_ATTEMPTS = 6
DEFAULT_BASE_BACKOFF = 20.0     # first 429 wait, before jitter
MAX_BACKOFF = 600.0


class RateLimited(RuntimeError):
    """Provider signalled throttling. Retried with backoff, then surfaced."""


class ProviderError(RuntimeError):
    """Provider returned no usable data. Never silently substituted."""


class ProviderAdapter(Protocol):
    """The seam that keeps a source swappable without touching analysis code.

    A provider is swapped by writing a new adapter and pointing the puller at it; no
    module outside `pipeline/ingest/` knows which provider produced a series, because
    provenance travels in the sidecar rather than in an import path.
    """

    name: str

    def fetch(self, key: str, **kwargs: Any) -> tuple[Any, str, dict]:
        """Return ``(payload, source_url, request_params)`` for one series key."""
        ...


# --------------------------------------------------------------------------------
# Single-flight: one in-flight request per host
# --------------------------------------------------------------------------------

_host_locks: dict[str, threading.Lock] = {}
_host_locks_guard = threading.Lock()
_host_last_request: dict[str, float] = {}


def _lock_for(host: str) -> threading.Lock:
    with _host_locks_guard:
        return _host_locks.setdefault(host, threading.Lock())


# --------------------------------------------------------------------------------
# Response cache
# --------------------------------------------------------------------------------


def _cache_key(url: str, params: dict | None) -> str:
    blob = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:32]


def cache_path(url: str, params: dict | None) -> Path:
    return CACHE_ROOT / f"{_cache_key(url, params)}.bin"


def cache_read(url: str, params: dict | None) -> bytes | None:
    p = cache_path(url, params)
    return p.read_bytes() if p.is_file() else None


def cache_write(url: str, params: dict | None, payload: bytes) -> None:
    p = cache_path(url, params)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(payload)


# --------------------------------------------------------------------------------
# The client
# --------------------------------------------------------------------------------


def _sec_user_agent() -> str:
    """The declarative User-Agent the SEC asks automated clients to send.

    MUST CONTAIN AN EMAIL ADDRESS. Measured 2026-08-03 against three endpoints: a UA naming
    the project with a repository URL is refused 403 by `company_tickers.json`, the Archives
    index and `efts.sec.gov` alike, while the same string with an address is accepted by all
    three. The SEC wants a way to contact whoever is making the requests, and a URL is not one.

    There is deliberately no default. A placeholder address would satisfy the server and defeat
    the purpose — the point of the header is that a human can be reached — and it would be the
    same class of error as the browser-string spoof this replaced: telling the provider
    something untrue in order to be let through. Absent configuration, this raises with the fix
    rather than silently 403-ing every SEC call.
    """
    import os

    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        env = REPO_ROOT / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.strip().startswith("SEC_USER_AGENT="):
                    ua = line.split("=", 1)[1].strip().strip("\"'")
    if "@" not in ua or "." not in ua.split("@")[-1]:
        raise RuntimeError(
            "SEC_USER_AGENT must be set to a declarative User-Agent CONTAINING A REAL EMAIL "
            "ADDRESS, e.g. 'Charon Research you@example.com'. The SEC refuses 403 without one. "
            f"Currently: {ua!r}. Set it in .env (gitignored) — it is a contact string, not a "
            "secret, but it is personal data and must not be committed.")
    return ua


@dataclass
class FragileHttpClient:
    """HTTP client that assumes the provider will throttle it, because it will.

    ``rng`` is injectable so jitter is deterministic under test — the pipeline is
    required to be reproducible (README §8), and unseeded randomness in the retry path
    would make failure modes irreproducible exactly when reproducing them matters.
    """

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    #: Hosts that require identifying yourself rather than imitating a browser.
    #:
    #: The SEC's Internet Security Policy asks automated clients to send a DECLARATIVE
    #: User-Agent naming the requester and a contact. Sending the Chrome string above earns a
    #: flat 403 from `www.sec.gov` -- discovered 2026-08-03, when a Form ADV pull failed on
    #: every path including nonexistent ones, which is the signature of a host-level refusal
    #: rather than a bad URL. `data.sec.gov` happens to tolerate the browser string, so the
    #: repository's existing EDGAR calls worked and the defect stayed hidden.
    #:
    #: Worth being precise about what this is: NOT a workaround for a bot challenge. It is the
    #: opposite. The provider documents programmatic access as permitted on condition that you
    #: say who you are; the browser string was the non-compliant setting, and this fixes it.
    #: `docs/data_sources.md` D5-d already recorded the condition -- "programmatic access
    #: explicitly permitted with a User-Agent header" -- and the client simply never met it.
    #:
    #: A public repository URL is used as the contact rather than a personal email, which
    #: would be PII in a public repo. Override with SEC_USER_AGENT to supply an address.
    #: Resolved lazily, per request. Eager resolution would raise at import time for anyone
    #: who never touches SEC — breaking every unrelated pull to enforce a rule about one host.
    host_user_agents: dict = field(default_factory=lambda: {"sec.gov": _sec_user_agent})
    min_interval: float = DEFAULT_MIN_INTERVAL
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    base_backoff: float = DEFAULT_BASE_BACKOFF
    use_cache: bool = True
    rng: random.Random = field(default_factory=lambda: random.Random(20260728))
    _sleep: Any = time.sleep  # injectable for tests

    def user_agent_for(self, host: str) -> str:
        """The UA for ``host``: a declarative one where the provider requires it.

        Matched on domain suffix so every subdomain inherits it — `www.sec.gov`,
        `data.sec.gov` and `reports.adviserinfo.sec.gov` are one policy, not three.
        """
        for domain, agent in self.host_user_agents.items():
            if host == domain or host.endswith("." + domain):
                return agent() if callable(agent) else agent
        return self.user_agent

    def get(self, url: str, params: dict | None = None, timeout: int = 30,
            json_body: dict | None = None) -> bytes:
        """Fetch ``url``, honouring cache, single-flight, spacing and backoff.

        ``json_body`` switches the verb to POST and sends it as JSON. It lives on ``get``
        rather than in a sibling ``post`` because everything that matters here — the cache,
        the per-host lock, the spacing, the 4xx-is-not-a-throttle rule — is the same for both
        verbs, and a second method would have been 50 lines of copied retry logic waiting to
        drift out of step with this one.

        Raises :class:`RateLimited` if the provider throttles through every attempt, and
        :class:`ProviderError` on any other terminal transport failure. Neither is
        swallowed: a puller that absorbs an outage produces a short series that looks
        like a real one.
        """
        # The body is part of the cache identity. Keying on url+params alone would serve one
        # query's response to a different query against the same endpoint -- and this whole
        # module exists because a cache that lies is worse than no cache.
        cache_key = params if json_body is None else {**(params or {}), "__body": json_body}
        if self.use_cache:
            cached = cache_read(url, cache_key)
            if cached is not None:
                return cached

        host = urlparse(url).netloc
        headers = {"User-Agent": self.user_agent_for(host),
                   "Accept": "application/json, */*"}
        last_error: Exception | None = None

        with _lock_for(host):
            for attempt in range(self.max_attempts):
                self._space(host)
                try:
                    if json_body is None:
                        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
                    else:
                        resp = requests.post(url, params=params, json=json_body, timeout=timeout,
                                             headers={**headers,
                                                      "Content-Type": "application/json; charset=UTF-8"})
                    if resp.status_code in RATE_LIMIT_STATUSES:
                        raise RateLimited(f"HTTP {resp.status_code} from {host}")
                    resp.raise_for_status()
                    payload = resp.content
                    if self.use_cache:
                        cache_write(url, cache_key, payload)
                    return payload
                except RateLimited as exc:
                    last_error = exc
                    if attempt < self.max_attempts - 1:
                        self._sleep(self._backoff(attempt))
                except requests.HTTPError as exc:
                    # A 4xx other than 429 is a statement about the REQUEST, not about
                    # server load: a wrong symbol or a missing entitlement will 404
                    # identically on every retry. Retrying it wastes the throttle budget
                    # that a genuine rate limit will need.
                    status = getattr(exc.response, "status_code", None)
                    if status is not None and 400 <= status < 500:
                        raise ProviderError(f"{host}: HTTP {status} (not retried — client error)") from exc
                    last_error = exc
                    if attempt < self.max_attempts - 1:
                        self._sleep(min(self.base_backoff / 4 * (attempt + 1), MAX_BACKOFF))
                except Exception as exc:  # noqa: BLE001 — retried, then surfaced
                    last_error = exc
                    if attempt < self.max_attempts - 1:
                        self._sleep(min(self.base_backoff / 4 * (attempt + 1), MAX_BACKOFF))

        if isinstance(last_error, RateLimited):
            raise RateLimited(
                f"{host}: throttled through {self.max_attempts} attempts. "
                "Wait for the limit to decay; do not retry harder."
            ) from last_error
        raise ProviderError(f"{host}: transport failed after {self.max_attempts} attempts: {last_error}")

    def _space(self, host: str) -> None:
        last = _host_last_request.get(host, 0.0)
        elapsed = time.monotonic() - last
        if last and elapsed < self.min_interval:
            self._sleep(self.min_interval - elapsed)
        _host_last_request[host] = time.monotonic()

    def _backoff(self, attempt: int) -> float:
        """Exponential with full jitter, capped.

        Full jitter (uniform over [0, computed]) rather than a fixed multiplier: several
        symbols backing off deterministically re-synchronise into one burst, which is
        how a throttle gets re-tripped the instant it lifts.
        """
        ceiling = min(self.base_backoff * (2 ** attempt), MAX_BACKOFF)
        return self.rng.uniform(ceiling / 2, ceiling)


DEFAULT_CLIENT = FragileHttpClient()
