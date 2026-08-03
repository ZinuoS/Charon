"""Notebook assembly. `nbformat` ships this; five builders were hand-rolling the JSON.

Each builder had its own `cells = []` plus md/code closures plus a one-line `json.dumps`
with the schema version and kernelspec typed out. Five copies of the same dict literals,
and the copies had already drifted — one used functions where the others used lambdas, and
one wrote its metadata block with different whitespace.

The reason to switch is not only the duplication. **`nbformat.write` validates against the
schema; `json.dumps` does not.** A hand-built cell missing a required key produced a file
that looked fine on disk and failed later inside nbconvert, which is where the
`validate(nb)` warnings during execution were coming from.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

#: The kernel every notebook here executes under. One definition; it was previously
#: repeated verbatim in each builder, which is how two of them ended up formatted
#: differently for no reason.
KERNELSPEC = {"display_name": "Python 3", "language": "python", "name": "python3"}
LANGUAGE_INFO = {"name": "python", "version": "3.12"}


def notebook():
    """Return ``(md, code, write)`` bound to one fresh notebook.

    Shaped to match the existing call sites exactly — ``md(r\"\"\"...\"\"\")`` and
    ``code(r'''...''')`` — so adopting it is a two-line change per builder rather than a
    rewrite of five files.
    """
    nb = nbf.v4.new_notebook()
    nb.metadata.update(kernelspec=KERNELSPEC, language_info=LANGUAGE_INFO)

    def md(src: str) -> None:
        nb.cells.append(nbf.v4.new_markdown_cell(src.strip()))

    def code(src: str) -> None:
        nb.cells.append(nbf.v4.new_code_cell(src.strip()))

    def write(path: str | Path, require: tuple[str, ...] = ()) -> int:
        """Write the notebook, optionally asserting that named sections are present.

        WHY `require` EXISTS. Every builder in this repository assembles itself with
        `str.replace` calls against anchors in its own source, and `str.replace` on a
        substring that is not there is a SILENT NO-OP. On 2026-08-03 a whole section shipped
        as a commit -- module, figures and tests all present -- with no section in the
        notebook, because one anchor had drifted and nothing checked. A manifest turns that
        into a loud failure at build time instead of a reader noticing months later.
        """
        src = "".join("".join(c["source"]) for c in nb.cells)
        missing = [h for h in require if h not in src]
        assert not missing, f"sections missing from the built notebook: {missing}"
        nbf.validate(nb)                 # loud here, not later inside nbconvert
        nbf.write(nb, str(path))
        return len(nb.cells)

    return md, code, write


if __name__ == "__main__":
    md, code, write = notebook()
    md("# check")
    code("1 + 1")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as f:
        assert write(f.name) == 2
        again = nbf.read(f.name, as_version=4)
    assert [c.cell_type for c in again.cells] == ["markdown", "code"]
    assert again.metadata.kernelspec["name"] == "python3"
    print("ok")
