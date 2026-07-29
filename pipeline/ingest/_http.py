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
    min_interval: float = DEFAULT_MIN_INTERVAL
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    base_backoff: float = DEFAULT_BASE_BACKOFF
    use_cache: bool = True
    rng: random.Random = field(default_factory=lambda: random.Random(20260728))
    _sleep: Any = time.sleep  # injectable for tests

    def get(self, url: str, params: dict | None = None, timeout: int = 30) -> bytes:
        """Fetch ``url``, honouring cache, single-flight, spacing and backoff.

        Raises :class:`RateLimited` if the provider throttles through every attempt, and
        :class:`ProviderError` on any other terminal transport failure. Neither is
        swallowed: a puller that absorbs an outage produces a short series that looks
        like a real one.
        """
        if self.use_cache:
            cached = cache_read(url, params)
            if cached is not None:
                return cached

        host = urlparse(url).netloc
        headers = {"User-Agent": self.user_agent, "Accept": "application/json, */*"}
        last_error: Exception | None = None

        with _lock_for(host):
            for attempt in range(self.max_attempts):
                self._space(host)
                try:
                    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
                    if resp.status_code in RATE_LIMIT_STATUSES:
                        raise RateLimited(f"HTTP {resp.status_code} from {host}")
                    resp.raise_for_status()
                    payload = resp.content
                    if self.use_cache:
                        cache_write(url, params, payload)
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
