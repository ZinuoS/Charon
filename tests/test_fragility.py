"""Provider-fragility behaviour: backoff, single-flight, caching, approval gating.

These encode the Session 1 post-mortem. The Yahoo 429 was not bad luck — it was a client
that fanned out across 14 symbols before it paced itself, and then retried on a
deterministic schedule that re-synchronised into fresh bursts. Each rule that prevents a
repeat is asserted here, against a mocked transport, so the behaviour is verifiable
without a live provider.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from pipeline.ingest import _http
from pipeline.ingest.approval import (
    SourceNotApprovedError,
    approval_status,
    require_approved,
    summary,
)


class FakeResponse:
    def __init__(self, status: int, content: bytes = b"{}"):
        self.status_code = status
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A client with sleeps recorded rather than performed, and cache in tmp_path."""
    monkeypatch.setattr(_http, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(_http, "_host_last_request", {})
    slept: list[float] = []
    c = _http.FragileHttpClient(min_interval=0.0, _sleep=slept.append)
    c.slept = slept  # type: ignore[attr-defined]
    return c


class TestBackoff:
    def test_retries_429_then_succeeds(self, client, monkeypatch):
        calls = {"n": 0}

        def fake_get(url, params=None, headers=None, timeout=None):
            calls["n"] += 1
            return FakeResponse(429) if calls["n"] < 3 else FakeResponse(200, b"payload")

        monkeypatch.setattr(_http.requests, "get", fake_get)
        assert client.get("https://example.invalid/x") == b"payload"
        assert calls["n"] == 3
        assert len(client.slept) == 2  # one wait per retry

    def test_backoff_is_exponential(self, client):
        """Each attempt's ceiling doubles, so a persistent throttle is not hammered."""
        waits = [client._backoff(i) for i in range(4)]
        for lo, hi in zip(waits, waits[1:]):
            assert hi > lo

    def test_backoff_is_jittered_not_deterministic(self, client):
        """Full jitter is the point: several symbols backing off on an identical
        schedule re-synchronise into one burst and re-trip the limit the moment it
        lifts. Two draws at the same attempt index must differ."""
        draws = {client._backoff(3) for _ in range(12)}
        assert len(draws) > 1

    def test_backoff_is_capped(self, client):
        assert client._backoff(50) <= _http.MAX_BACKOFF

    def test_backoff_is_reproducible_given_a_seed(self, tmp_path, monkeypatch):
        """README §8 requires a deterministic pipeline. Unseeded jitter would make a
        retry-path failure irreproducible exactly when reproducing it matters."""
        import random
        a = _http.FragileHttpClient(rng=random.Random(7))
        b = _http.FragileHttpClient(rng=random.Random(7))
        assert [a._backoff(i) for i in range(5)] == [b._backoff(i) for i in range(5)]

    def test_persistent_429_raises_rate_limited_not_provider_error(self, client, monkeypatch):
        """The two failure modes must stay distinguishable: a throttle means wait, a
        transport error means investigate."""
        monkeypatch.setattr(_http.requests, "get", lambda *a, **k: FakeResponse(429))
        with pytest.raises(_http.RateLimited, match="throttled"):
            client.get("https://example.invalid/x")

    def test_503_is_treated_as_rate_limiting(self, client, monkeypatch):
        monkeypatch.setattr(_http.requests, "get", lambda *a, **k: FakeResponse(503))
        with pytest.raises(_http.RateLimited):
            client.get("https://example.invalid/x")

    def test_hard_failure_surfaces_as_provider_error(self, client, monkeypatch):
        monkeypatch.setattr(_http.requests, "get", lambda *a, **k: FakeResponse(404))
        with pytest.raises(_http.ProviderError):
            client.get("https://example.invalid/x")


class TestCache:
    def test_second_fetch_is_served_from_cache(self, client, monkeypatch):
        calls = {"n": 0}

        def fake_get(url, params=None, headers=None, timeout=None):
            calls["n"] += 1
            return FakeResponse(200, b"payload")

        monkeypatch.setattr(_http.requests, "get", fake_get)
        assert client.get("https://example.invalid/x") == b"payload"
        assert client.get("https://example.invalid/x") == b"payload"
        assert calls["n"] == 1, "cache did not prevent the second network call"

    def test_cache_key_distinguishes_params(self, client, monkeypatch):
        calls = {"n": 0}

        def fake_get(url, params=None, headers=None, timeout=None):
            calls["n"] += 1
            return FakeResponse(200, b"payload")

        monkeypatch.setattr(_http.requests, "get", fake_get)
        client.get("https://example.invalid/x", params={"a": 1})
        client.get("https://example.invalid/x", params={"a": 2})
        assert calls["n"] == 2

    def test_cache_can_be_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_http, "CACHE_ROOT", tmp_path / "c")
        monkeypatch.setattr(_http, "_host_last_request", {})
        calls = {"n": 0}

        def fake_get(url, params=None, headers=None, timeout=None):
            calls["n"] += 1
            return FakeResponse(200, b"p")

        monkeypatch.setattr(_http.requests, "get", fake_get)
        c = _http.FragileHttpClient(min_interval=0.0, use_cache=False, _sleep=lambda s: None)
        c.get("https://example.invalid/x")
        c.get("https://example.invalid/x")
        assert calls["n"] == 2


class TestSingleFlight:
    def test_requests_to_one_host_are_serialised(self, client, monkeypatch):
        """Parallel probes against a single host are what produced the original ban."""
        concurrent = {"now": 0, "max": 0}
        lock = threading.Lock()

        def fake_get(url, params=None, headers=None, timeout=None):
            with lock:
                concurrent["now"] += 1
                concurrent["max"] = max(concurrent["max"], concurrent["now"])
            try:
                return FakeResponse(200, b"p")
            finally:
                with lock:
                    concurrent["now"] -= 1

        monkeypatch.setattr(_http.requests, "get", fake_get)
        c = _http.FragileHttpClient(min_interval=0.0, use_cache=False, _sleep=lambda s: None)
        threads = [
            threading.Thread(target=lambda i=i: c.get(f"https://one-host.invalid/{i}"))
            for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert concurrent["max"] == 1, f"observed {concurrent['max']} concurrent requests to one host"


class TestResumability:
    def test_already_persisted_symbol_is_not_refetched(self, tmp_path):
        """A symbol already on disk is never re-pulled, so an interrupted panel pull
        resumes instead of restarting — the difference between recovering from a
        throttle and re-triggering it."""
        from pipeline.ingest._common import write_immutable

        target = tmp_path / "series.csv"
        payload = b"date,close\n2026-07-10,168.01\n"
        _, first = write_immutable(target, payload)
        _, second = write_immutable(target, payload)
        assert (first, second) == (True, False)


class TestApprovalGate:
    def test_every_source_has_a_recognised_status(self):
        """The document must parse cleanly into the three buckets, with none lost."""
        s = summary()
        total = len(s["yes"]) + len(s["no"]) + len(s["pending"])
        assert total >= 22, f"expected all proposals to parse, got {total}"

    def test_approvals_are_confined_to_the_authors_intended_set(self):
        """Approval is the author's decision (README §11). This does not assert a count —
        counts change as the author decides — it asserts that nothing OUTSIDE the set the
        author named in writing has become approved, which is what a session
        self-approving would look like."""
        # Each entry here corresponds to an explicit, written authorisation by the
        # author. Adding to this set is itself a record of that decision — it is not a
        # place to silence the test.
        author_approved = {
            "seibro_dr_capacity",         # named in the Session 7 task list
            "kodex_issuer_disclosure",    # named in the Session 7 task list
            "tiger_issuer_disclosure",    # named in the Session 7 task list
            "sgx_krw_futures",            # named in the Session 7 task list
            "eodhd_krx",                  # "use eodhd puller" + key supplied directly
            # Session 8, "approve everything": granted to the TERMS-CLEAN subset only.
            # The prohibited set below is withheld and guarded by the next test.
            "krx_open_api", "krx_usd_futures", "krx_openapi_etp",
            "krx_night_session_futures", "kmb_fx_swap", "smbs_manual_snapshot",
            "bok_ecos", "fred_dexkous", "kofia_freesis_lending", "ksfc_lending",
            "opendart", "ksd_opendata_api", "sec_edgar_f6", "twelvedata_krx",
        }
        unexpected = set(summary()["yes"]) - author_approved
        assert not unexpected, (
            f"sources approved that the author never named: {sorted(unexpected)}. "
            "Approval marks are the author's alone."
        )

    def test_terms_prohibited_sources_are_never_approved(self):
        """A hard floor. These carry stated anti-automation clauses or fail README §8's
        licence rule; no instruction should ever flip them to `yes`."""
        forbidden = {
            "smbs_fx_swap_scraper", "investing_com_fx_forwards",
            "krx_short_selling_via_pykrx", "financedatareader_krx",
        }
        approved = set(summary()["yes"])
        assert not (forbidden & approved), (
            f"terms-prohibited source approved: {sorted(forbidden & approved)}"
        )

    def test_require_approved_raises_for_pending_source(self):
        with pytest.raises(SourceNotApprovedError, match="has not been signed off"):
            require_approved("naver_etf_navlist")

    def test_unknown_source_is_pending_not_crash(self):
        assert approval_status("no_such_source_xyz") == "pending"

    def test_yes_permits(self, tmp_path):
        doc = tmp_path / "d.md"
        doc.write_text("```yaml\nsource: demo\napproved: yes\n```\n")
        require_approved("demo", doc)  # must not raise

    def test_explicit_no_is_distinguished_from_pending(self, tmp_path):
        doc = tmp_path / "d.md"
        doc.write_text("```yaml\nsource: demo\napproved: no\n```\n")
        assert approval_status("demo", doc) == "no"
        with pytest.raises(SourceNotApprovedError, match="explicitly declined"):
            require_approved("demo", doc)

    def test_missing_document_blocks_everything(self, tmp_path):
        """No document means no approvals can be evaluated, so nothing may run."""
        with pytest.raises(FileNotFoundError):
            approval_status("demo", tmp_path / "absent.md")


class TestSnapshotHarnessIsGated:
    def test_harness_refuses_to_capture_unapproved_sources(self):
        """Only the still-unapproved specs must refuse; approved ones are allowed to run
        (and are not exercised here, because that would hit the network)."""
        from pipeline.ingest.snapshot_daily import SNAPSHOTS, capture

        checked = 0
        for spec in SNAPSHOTS:
            if approval_status(spec.source_id) == "yes":
                continue
            with pytest.raises(SourceNotApprovedError):
                capture(spec)
            checked += 1
        assert checked, "no unapproved snapshot specs left to exercise the gate against"

    def test_every_snapshot_spec_names_a_documented_source(self):
        """A spec whose source_id is absent from data_sources.md could never be
        approved, which would be a silent dead end rather than a visible block."""
        from pipeline.ingest.snapshot_daily import SNAPSHOTS

        known = set(summary()["pending"]) | set(summary()["yes"]) | set(summary()["no"])
        for spec in SNAPSHOTS:
            assert spec.source_id in known, f"{spec.source_id} not proposed in data_sources.md"
