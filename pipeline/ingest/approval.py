"""Source-approval gate, enforced in code rather than by promise.

`docs/data_sources.md` carries one ``approved:`` field per source. README §11 reserves
that decision to the author, and a session that "remembers" not to pull an unapproved
source is one refactor away from pulling it anyway. So the gate is mechanical: every
puller for a sign-off-gated source calls :func:`require_approved` first, and the call
raises unless the author has written ``approved: yes`` in the document.

The document is the single source of truth. There is no override flag and no environment
variable, deliberately — adding one would recreate exactly the bypass this exists to
prevent.

Recognised values::

    approved: yes          -> puller may run
    approved: no           -> puller must not run (an explicit rejection, recorded)
    approved: TODO(ash)    -> undecided; puller must not run
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_SOURCES = REPO_ROOT / "docs" / "data_sources.md"

# Matches the `source:` / `approved:` pairs inside the fenced yaml blocks.
_BLOCK_RE = re.compile(
    r"^source:\s*(?P<source>[a-z0-9_]+)\s*$\n^approved:\s*(?P<approved>\S+)",
    re.MULTILINE,
)


class SourceNotApprovedError(RuntimeError):
    """Raised when a puller runs against a source the author has not approved."""


def _parse(path: Path | None = None) -> dict[str, str]:
    doc = (path or DATA_SOURCES)
    if not doc.is_file():
        raise FileNotFoundError(
            f"{doc} not found. The approval gate cannot be evaluated without it; "
            "no sign-off-gated puller may run."
        )
    text = doc.read_text()
    return {m.group("source"): m.group("approved").strip() for m in _BLOCK_RE.finditer(text)}


def approval_status(source: str, path: Path | None = None) -> str:
    """Return ``"yes"``, ``"no"``, or ``"pending"`` for ``source``.

    An unknown source is ``"pending"``, not an error: a puller written before its
    proposal lands in the document should be blocked, not crash with a different
    message that might read as a bug to route around.
    """
    value = _parse(path).get(source)
    if value is None:
        return "pending"
    if value == "yes":
        return "yes"
    if value == "no":
        return "no"
    return "pending"


def _near_misses(source: str, known: list[str]) -> list[str]:
    """Known keys that share a token with `source` — catches a mis-transcribed name.

    A marked-but-misnamed approval is the worst failure this gate has: it looks approved
    to the author and stays blocked to the code, silently, with no error anyone reads.
    """
    tokens = {t for t in source.lower().replace("-", "_").split("_") if len(t) > 2}
    return sorted(k for k in known if tokens & set(k.lower().split("_")))


def require_approved(source: str, path: Path | None = None) -> None:
    """Raise unless the author has marked ``source`` as ``approved: yes``."""
    status = approval_status(source, path)
    if status == "yes":
        return
    detail = {
        "no": "has been explicitly declined by the author",
        "pending": "has not been signed off (still TODO(ash), or absent from the document)",
    }[status]
    known = list(_parse(path))
    hint = ""
    if source not in known:
        near = _near_misses(source, known)
        hint = (
            f"\n  NOTE: {source!r} is not a key in the document at all."
            + (f" Did you mean: {near}?" if near else "")
        )
    raise SourceNotApprovedError(
        f"source {source!r} {detail}.\n"
        f"  Set `approved: yes` under `source: {source}` in {DATA_SOURCES.relative_to(REPO_ROOT)} "
        "to authorise it.\n"
        "  Approval is the author's decision (README §11); it is not overridable in code."
        + hint
    )


def summary(path: Path | None = None) -> dict[str, list[str]]:
    """All sources bucketed by status — used by the gate reports."""
    out: dict[str, list[str]] = {"yes": [], "no": [], "pending": []}
    for source, value in sorted(_parse(path).items()):
        key = value if value in ("yes", "no") else "pending"
        out[key].append(source)
    return out
