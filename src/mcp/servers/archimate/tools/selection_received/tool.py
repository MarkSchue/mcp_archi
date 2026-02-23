"""Tool: selection_received – Receives selected entities from the UI."""

import json
from mcp import types

from ...server import mcp
from ...server import set_selection


@mcp.tool()
def selection_received(selection: list) -> list[types.TextContent]:
    """Receive selected entities from the UI and store them in memory."""
    try:
        set_selection(selection)
        print("[selectable_table] selection_received:", len(selection), "rows")
        return [types.TextContent(type="text", text=json.dumps({"received": selection}))]
    except Exception as e:
        print("[selectable_table] selection_received ERROR:", e)
        return [types.TextContent(type="text", text=f"Error processing selection: {e}")]
