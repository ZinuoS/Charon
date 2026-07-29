"""Doctrine enforcement: analysis code performs no network I/O (README §8).

"Pulls are a separate, logged ingestion step" is only a real guarantee if it is
checked. This test walks the AST of every analysis module and fails on any import of a
networking library, so a convenience `requests.get` cannot drift into a modelling
module and make a backtest quietly non-reproducible.

The scan is static and import-name based. It catches the realistic failure (someone
imports requests/yfinance in a hypothesis engine) and does not attempt to catch
deliberate evasion via `__import__` or subprocess — the point is a guardrail against
drift, not a sandbox.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Everything under these roots is analysis: no network, ever.
ANALYSIS_ROOTS = (
    REPO_ROOT / "pipeline" / "measurement",
    REPO_ROOT / "pipeline" / "regimes",
    REPO_ROOT / "pipeline" / "convergence",
    REPO_ROOT / "hypotheses",
    REPO_ROOT / "execution",
)

# Ingestion is the ONE place network access is allowed.
INGEST_ROOT = REPO_ROOT / "pipeline" / "ingest"

FORBIDDEN_TOP_LEVEL = {
    "requests", "urllib", "urllib3", "http", "httpx", "aiohttp", "socket",
    "yfinance", "ftplib", "telnetlib", "websocket", "websockets", "pandas_datareader",
}

# No LLM API calls anywhere in pipeline code (README §8), ingestion included.
FORBIDDEN_LLM = {"anthropic", "openai", "cohere", "google", "litellm", "langchain", "transformers", "ollama"}


def _module_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _imported_top_level_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # level > 0 is a relative import: it cannot reach a third-party network lib.
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


ANALYSIS_FILES = [p for root in ANALYSIS_ROOTS for p in _module_files(root)]
ALL_PIPELINE_FILES = ANALYSIS_FILES + _module_files(INGEST_ROOT)


@pytest.mark.parametrize("path", ANALYSIS_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_analysis_module_imports_no_networking(path: Path):
    offending = _imported_top_level_names(path) & FORBIDDEN_TOP_LEVEL
    assert not offending, (
        f"{path.relative_to(REPO_ROOT)} imports {sorted(offending)}.\n"
        "Analysis code must not reach the network (README §8). Move the pull into "
        "pipeline/ingest/ and read the result from data/raw/."
    )


@pytest.mark.parametrize("path", ALL_PIPELINE_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_llm_imports_anywhere_in_pipeline(path: Path):
    offending = _imported_top_level_names(path) & FORBIDDEN_LLM
    assert not offending, (
        f"{path.relative_to(REPO_ROOT)} imports {sorted(offending)}.\n"
        "No LLM API calls anywhere in pipeline code (README §8). Feature extraction is "
        "deterministic end to end."
    )


def test_analysis_roots_are_actually_populated():
    """A vacuous pass is worse than a failure: if the analysis tree is empty this test
    would be trivially green while enforcing nothing."""
    assert ANALYSIS_FILES, "no analysis modules found; the network guard is scanning nothing"


def test_ingest_is_the_only_networked_package():
    """The complement of the rule: networking should appear in exactly one module, so
    swapping providers stays a one-file change."""
    networked = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in _module_files(INGEST_ROOT)
        if _imported_top_level_names(p) & FORBIDDEN_TOP_LEVEL
    }
    assert networked == {"pipeline/ingest/_http.py"}, (
        f"expected network access confined to pipeline/ingest/_http.py, found {sorted(networked)}"
    )
