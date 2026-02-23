from __future__ import annotations
from pathlib import Path

"""Helper for VS Code–aligned CSS used by embedded views.

The raw stylesheet lives alongside this module in `styles.css`.  Keeping the
markup outside Python makes diffs easier to review and tools simpler (e.g.
syntax highlighting).

Clients simply import ``VSCODE_CSS`` the same way they did previously; the
module reads the file lazily.
"""

_css: str | None = None


def _load_css() -> str:
    global _css
    if _css is None:
        path = Path(__file__).parent / "styles.css"
        _css = path.read_text()
    return _css


# public constant used by views
VSCODE_CSS = _load_css()
