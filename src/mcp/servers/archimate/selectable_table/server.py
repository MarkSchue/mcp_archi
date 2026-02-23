"""SelectableTable support inside the ArchiMate MCP server.

This module does **not** create its own FastMCP instance; instead it re‑uses
`mcp` from the parent archimate server so that resources and tools are
registered on the same server.
"""

import json

# reuse the MCP instance created by the archimate package
from ..server import mcp

from .state import VIEW_URI, get_selection



# ---------------------------------------------------------------------------
# Resource: the HTML View, served with MCP Apps MIME type
# ---------------------------------------------------------------------------
@mcp.resource(
    VIEW_URI,
    mime_type="text/html;profile=mcp-app",
    meta={
        "ui": {
            "csp": {
                "resourceDomains": [
                    "https://unpkg.com",
                ]
            }
        }
    },
)
def view() -> str:
    """View HTML resource for the selectable table UI."""
    from ..tools.selectable_table.view import EMBEDDED_VIEW_HTML
    return EMBEDDED_VIEW_HTML


# ---------------------------------------------------------------------------
# Resource: current selection as JSON
# ---------------------------------------------------------------------------
@mcp.resource("data://selectable-table/selection.json", mime_type="application/json")
def current_selection() -> str:
    """Returns the current selection as JSON."""
    return json.dumps(get_selection(), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Import tool modules so their decorators register with `mcp`
# ---------------------------------------------------------------------------
from ..tools.selectable_table import tool as _t1  # noqa: E402, F401
from ..tools.selection_received import tool as _t2  # noqa: E402, F401

