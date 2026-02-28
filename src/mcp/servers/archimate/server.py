"""ArchiMate MCP Server – entry point.

This module establishes the FastMCP instance, initializes the database, and
imports all tools (including the selectable-table interactive view and
selection-handling tools) so that their @mcp.tool() decorators register with
this server.
"""

from mcp.server.fastmcp import FastMCP

import json
import time
from pathlib import Path
from typing import Any

from .db import init_db
from .model_db import init_model_db

# ----------------------------------------------------------------------------
# Shared constants and in‑memory state for selectable-table functionality
# ----------------------------------------------------------------------------

VIEW_URI = "ui://selectable-table/view.html"
MATRIX_VIEW_URI = "ui://selectable-matrix/view.html"

# exports directory (resolved relative to workspace root, 4 levels above this file)
EXPORTS_DIR = Path(__file__).resolve().parents[4] / "exports"

_current_selection: list = []

# optional "current model" context used by conversational tools/skills
CURRENT_MODEL: str | None = None
LAST_MODEL_MUTATION: dict[str, Any] | None = None

# ---------------------------------------------------------------------------
# selection helpers (for selectable_table)
# ---------------------------------------------------------------------------
def get_selection() -> list:
    return _current_selection


def set_selection(selection: list) -> None:
    global _current_selection
    _current_selection = selection


# ---------------------------------------------------------------------------
# model context helpers
# ---------------------------------------------------------------------------
def set_current_model(model_id: str) -> None:
    """Remember the given model id for later conversational use."""
    global CURRENT_MODEL
    CURRENT_MODEL = model_id


def get_current_model() -> str | None:
    """Return the currently remembered model id, or None if none set."""
    return CURRENT_MODEL


def note_model_mutation(tool: str, action: str, model_id: str | None = None) -> None:
    """Record the latest model mutation to support runtime guardrails."""
    global LAST_MODEL_MUTATION
    LAST_MODEL_MUTATION = {
        "tool": tool,
        "action": action,
        "model_id": model_id,
        "at_monotonic": time.monotonic(),
    }


def get_recent_model_mutation(max_age_seconds: int = 90) -> dict[str, Any] | None:
    """Return recent mutation metadata if it happened within max_age_seconds."""
    if not LAST_MODEL_MUTATION:
        return None
    age = time.monotonic() - float(LAST_MODEL_MUTATION.get("at_monotonic", 0.0))
    if age > max_age_seconds:
        return None
    result = dict(LAST_MODEL_MUTATION)
    result["age_seconds"] = round(age, 3)
    return result


def clear_recent_model_mutation() -> None:
    """Clear mutation metadata, typically after an explicitly requested post-write diagram export."""
    global LAST_MODEL_MUTATION
    LAST_MODEL_MUTATION = None


# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP("ArchiMate")

# ---------------------------------------------------------------------------
# Initialize metamodel database once on server startup
# ---------------------------------------------------------------------------
init_db()
init_model_db()

# ---------------------------------------------------------------------------
# Import tool modules so their decorators register with `mcp`
# ---------------------------------------------------------------------------
from .tools.archimate_metamodel import tool as _t1  # noqa: E402, F401
from .tools.archimate_metamodel_enhance import tool as _t2  # noqa: E402, F401
from .tools.archimate_current_model import tool as _tX  # noqa: E402, F401
from .tools.archimate_model_management import tool as _t3  # noqa: E402, F401
from .tools.archimate_attribute_dictionary import tool as _tA  # noqa: E402, F401
from .tools.archimate_model_query import tool as _t4  # noqa: E402, F401
from .tools.archimate_model_cud import tool as _t5  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Selectable-table support (resources and selection state)
# ---------------------------------------------------------------------------

# state and constants now defined above in this module (see earlier block)


# resource: HTML view for the selectable table UI
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
def selectable_table_view() -> str:
    """Return the HTML view used by the selectable table tool."""
    from .tools.selectable_table.view import EMBEDDED_VIEW_HTML
    return EMBEDDED_VIEW_HTML


# resource: HTML view for the selectable matrix UI
@mcp.resource(
    MATRIX_VIEW_URI,
    mime_type="text/html;profile=mcp-app",
    meta={
        "ui": {
            "csp": {
                "resourceDomains": [
                    "https://unpkg.com",
                    "https://esm.sh",
                ]
            }
        }
    },
)
def selectable_matrix_view() -> str:
    """Return the HTML view used by the selectable matrix tool."""
    from .tools.selectable_matrix.view import EMBEDDED_VIEW_HTML
    return EMBEDDED_VIEW_HTML


# resource: current selection as JSON
@mcp.resource("data://selectable-table/selection.json", mime_type="application/json")
def current_selection() -> str:
    """Returns the current selection as JSON."""
    return json.dumps(get_selection(), ensure_ascii=False)


# register the tool itself so its decorator sees the shared mcp
from .tools.selectable_table import tool as _t6  # noqa: E402, F401
from .tools.selectable_matrix import tool as _t7  # noqa: E402, F401
from .tools.drawio import tool as _t8  # noqa: E402, F401
