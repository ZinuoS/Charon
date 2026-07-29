"""H5 barrier-state monitor — scope discipline and the publication control."""
from __future__ import annotations
import pandas as pd, pytest
from hypotheses.h5_quota_ledger import monitor as M


def test_scope_note_is_appended_unconditionally():
    """A headroom figure quoted without its scope invites exactly the inference the
    author's option-(a) ruling forbids."""
    r = M.status_report()
    assert "SCOPE OF OBSERVABLE" in r
    assert "NOT the operative deposit gate" in r
    assert "prior consent" in r


def test_report_never_claims_the_barrier_opened():
    """Guards against an AFFIRMATIVE claim that the barrier opened.

    Deliberately not a substring check on "barrier open": the report legitimately says
    "headroom can move without the barrier opening", which is the caution, not the claim.
    A crude match flags the correct sentence and would push someone to weaken the caveat
    to satisfy the test — the opposite of what this guards.
    """
    r = M.status_report().lower()
    forbidden = ["barrier is open", "barrier has opened", "barrier opened",
                 "can be arbitraged", "arbitrage opportunity"]
    hits = [p for p in forbidden if p in r]
    assert not hits, f"report makes an affirmative opening claim: {hits}"


def test_capped_programme_is_the_subject_and_control_is_named_as_control():
    assert M.CAPPED.endswith("capped") and M.CONTROL.endswith("legacy")
    assert "publication control" in M.__doc__.lower()


class TestPublicationCheck:
    def _state(self, name, isin, last, n=5, level=100):
        return M.LedgerState(name, isin, n, "2026-07-01", last, level)

    def test_control_ahead_means_sealed_by_observation(self):
        s = {"capped": self._state("cap", "A", "2026-07-15", 1, 0),
             "control": self._state("ctl", "B", "2026-07-28")}
        msg = M.publication_check(s)
        assert "PUBLISHING" in msg and "NOT MOVED" in msg

    def test_no_control_series_is_indeterminate_not_a_conclusion(self):
        s = {"capped": self._state("cap", "A", "2026-07-15"),
             "control": M.LedgerState("ctl", "B", 0, None, None, None)}
        assert "INDETERMINATE" in M.publication_check(s)

    def test_aligned_dates_report_aligned(self):
        s = {"capped": self._state("cap", "A", "2026-07-28"),
             "control": self._state("ctl", "B", "2026-07-28")}
        assert "ALIGNED" in M.publication_check(s)


class TestLive:
    def test_capped_programme_reads_sealed(self):
        st = M.ledger()["capped"]
        if not st.n_obs:
            pytest.skip("d5 not ingested")
        assert st.level == 0
        assert any("SEALED" in n for n in st.notes)

    def test_control_shows_bidirectional_revolving_flow(self):
        """The evidence for the ruling that the field is revolving ceiling-headroom."""
        st = M.ledger()["control"]
        if not st.n_obs:
            pytest.skip("d5 not ingested")
        assert (st.flow > 0).sum() > 100 and (st.flow < 0).sum() > 100
        assert (st.flow == 0).sum() == 0, "publishes on change only"

    def test_episodes_are_a_reporting_filter_not_a_registered_threshold(self):
        st = M.ledger()["control"]
        if not st.n_obs:
            pytest.skip("d5 not ingested")
        assert len(M.flow_episodes(st, 0.0025)) >= len(M.flow_episodes(st, 0.01))
