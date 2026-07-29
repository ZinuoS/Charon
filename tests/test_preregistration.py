"""Pre-registration integrity (README §9 S0, §11).

Two jobs:

1.  **Before the freeze** — assert the template is structurally complete, so the author
    is filling in a correct skeleton rather than discovering a missing field at 19:55 ET.
2.  **After the freeze** — assert the frozen file is actually frozen: no `TODO(ash)`
    left anywhere, every status advanced, `frozen_at` set.

The switch between the two modes is `frozen_at`. A file with `frozen_at: null` is a
draft and is checked as a draft; the moment it is set, the strict checks turn on
automatically. Nothing here fills in or validates the *values* of any threshold — those
are the author's alone and no test may ratify them.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CALLS_PATH = REPO_ROOT / "preregistration" / "calls.yaml"

HYPOTHESES = (
    "h1_term_structure",
    "h2_index_access",
    "h3_letf_loop",
    "h4_vol_decomposition",
    "h5_quota_ledger",
)

REQUIRED_FIELDS = (
    "statement",
    "direction",
    "threshold",
    "resolution_date",
    "resolution_criterion",
    "data_requirements",
    "status",
)

TODO_RE = re.compile(r"TODO\(ash\)")


@pytest.fixture(scope="module")
def calls() -> dict:
    assert CALLS_PATH.is_file(), "preregistration/calls.yaml is missing"
    return yaml.safe_load(CALLS_PATH.read_text())


@pytest.fixture(scope="module")
def is_frozen(calls) -> bool:
    return calls.get("frozen_at") is not None


class TestStructure:
    """Holds in both modes."""

    def test_all_five_hypotheses_present(self, calls):
        assert set(HYPOTHESES) <= set(calls), f"missing: {sorted(set(HYPOTHESES) - set(calls))}"

    @pytest.mark.parametrize("h", HYPOTHESES)
    def test_required_fields_present(self, calls, h):
        missing = [f for f in REQUIRED_FIELDS if f not in calls[h]]
        assert not missing, f"{h} missing fields: {missing}"

    @pytest.mark.parametrize("h", HYPOTHESES)
    def test_statement_and_direction_are_prefilled(self, calls, h):
        """These come verbatim from README §5 and are never a TODO — the author fills
        thresholds, not the hypothesis text."""
        for field in ("statement", "direction"):
            value = calls[h][field]
            assert isinstance(value, str) and len(value) > 40, f"{h}.{field} looks unfilled"
            assert not TODO_RE.search(value), f"{h}.{field} must be prefilled from README §5"

    @pytest.mark.parametrize("h", HYPOTHESES)
    def test_data_requirements_reference_real_d_sources(self, calls, h):
        reqs = calls[h]["data_requirements"]
        assert isinstance(reqs, list) and reqs, f"{h}.data_requirements must be a non-empty list"
        assert all(re.fullmatch(r"D[1-7]", str(r)) for r in reqs), f"{h}.data_requirements: {reqs}"

    def test_top_level_freeze_fields_exist(self, calls):
        assert "frozen_at" in calls
        assert "commit_note" in calls

    def test_global_rules_pin_the_doctrine(self, calls):
        rules = calls["global_rules"]
        assert "forward test" in rules["training_universe"].lower()
        assert "arbitrage" in rules["language_discipline"].lower()


class TestDraftMode:
    """Only while frozen_at is null."""

    def test_author_owned_fields_are_still_todo(self, calls, is_frozen):
        if is_frozen:
            pytest.skip("file is frozen; TestFrozenMode applies")
        for h in HYPOTHESES:
            for field in ("threshold", "resolution_date", "resolution_criterion"):
                assert TODO_RE.search(str(calls[h][field])), (
                    f"{h}.{field} was filled in while frozen_at is still null.\n"
                    "Threshold and resolution decisions are the author's alone (README §11). "
                    "If you filled these deliberately, set frozen_at and complete the freeze."
                )

    def test_status_is_pending_signature(self, calls, is_frozen):
        if is_frozen:
            pytest.skip("file is frozen; TestFrozenMode applies")
        for h in HYPOTHESES:
            assert calls[h]["status"] == "frozen_pending_signature"


class TestFrozenMode:
    """Turns on automatically once frozen_at is set."""

    def test_no_todos_survive_the_freeze(self, is_frozen):
        if not is_frozen:
            pytest.skip("file is still a draft")
        leftovers = [
            f"line {i}: {line.strip()}"
            for i, line in enumerate(CALLS_PATH.read_text().splitlines(), 1)
            if TODO_RE.search(line) and not line.lstrip().startswith("#")
        ]
        assert not leftovers, "frozen calls.yaml still contains TODO(ash):\n" + "\n".join(leftovers)

    def test_every_hypothesis_has_a_freeze_class_and_consistent_status(self, calls, is_frozen):
        """Post-freeze, every call carries a freeze_class, and status matches it:
        Class C/P => frozen, Class X => exploratory. The minimal-freeze design
        (preregistration/minimal_freeze_checklist.md) registers only what is genuinely
        pre-registrable and marks the rest exploratory rather than forcing a value."""
        if not is_frozen:
            pytest.skip("file is still a draft")
        for h in HYPOTHESES:
            fc = calls[h].get("freeze_class")
            assert fc in ("C", "P", "X"), f"{h} missing/invalid freeze_class: {fc!r}"
            if fc in ("C", "P"):
                assert calls[h]["status"] == "frozen", f"{h} is Class {fc} but status {calls[h]['status']!r}"
            else:
                assert calls[h]["status"] == "exploratory", f"{h} is Class X but status {calls[h]['status']!r}"

    def test_commit_note_written(self, calls, is_frozen):
        if not is_frozen:
            pytest.skip("file is still a draft")
        assert calls["commit_note"], "frozen file needs a commit_note"

    def test_frozen_call_resolution_dates_parse(self, calls, is_frozen):
        """Only Class C/P (registered) calls need a parseable resolution date; Class X
        (exploratory) calls carry a label, not a date."""
        if not is_frozen:
            pytest.skip("file is still a draft")
        import datetime
        for h in HYPOTHESES:
            if calls[h].get("freeze_class") not in ("C", "P"):
                continue
            value = calls[h]["resolution_date"]
            assert isinstance(value, (datetime.date, datetime.datetime)), (
                f"{h}.resolution_date must be a YAML date, got {value!r}"
            )


class TestAmendmentDiscipline:
    def test_amendments_directory_exists(self):
        assert (REPO_ROOT / "preregistration" / "amendments").is_dir()

    def test_amendment_files_are_dated(self):
        """Filenames carry the date so the append-only chain is readable without git."""
        amendments = (REPO_ROOT / "preregistration" / "amendments").glob("*.md")
        for path in amendments:
            assert re.match(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md", path.name), (
                f"{path.name} must be named <YYYY-MM-DD>-<slug>.md"
            )
