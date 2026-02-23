"""Tool: selectable_table – Displays entities in an interactive selectable table.

This tool is now packaged under the ArchiMate server's namespace so it
shares the same MCP instance and resources.
"""

import json
from mcp import types

from ...server import mcp
from ...server import VIEW_URI


@mcp.tool(
    meta={
        "ui": {"resourceUri": VIEW_URI},
        "ui/resourceUri": VIEW_URI,
    }
)
def selectable_table(
    title: str,
    entities_json: str,
) -> list[types.TextContent]:
    """Displays entities in a selectable table.

    Args:
        title: The title displayed above the table.
        entities_json: A JSON string containing an array of entity objects.
    """
    try:
        entities = json.loads(entities_json)
    except json.JSONDecodeError as e:
        return [types.TextContent(type="text", text=f"Error: Invalid JSON – {e}")]

    if not isinstance(entities, list) or len(entities) == 0:
        return [types.TextContent(type="text", text="Error: entities_json must be a non-empty JSON array.")]

    columns = list(entities[0].keys())

    payload = json.dumps({
        "_kind": "selectable_table",
        "title": title,
        "columns": columns,
        "entities": entities,
    })

    return [types.TextContent(type="text", text=payload)]
