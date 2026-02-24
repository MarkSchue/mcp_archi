"""Tool: selectable_matrix – Displays entities in an interactive matrix UI."""

import json
from mcp import types

from ...server import mcp
from ...server import MATRIX_VIEW_URI


@mcp.tool(
    meta={
        "ui": {"resourceUri": MATRIX_VIEW_URI},
        "ui/resourceUri": MATRIX_VIEW_URI,
    }
)
def selectable_matrix(
    title: str,
    entities_json: str,
    row_field: str,
    column_field: str,
) -> list[types.TextContent]:
    """Displays entities in a selectable matrix.

    Args:
        title: Title displayed above the matrix.
        entities_json: JSON array of relation-like objects.
        row_field: Entity field used for matrix rows.
        column_field: Entity field used for matrix columns.
    """
    try:
        entities = json.loads(entities_json)
    except json.JSONDecodeError as e:
        return [types.TextContent(type="text", text=f"Error: Invalid JSON – {e}")]

    if not isinstance(entities, list) or len(entities) == 0:
        return [types.TextContent(type="text", text="Error: entities_json must be a non-empty JSON array.")]

    if not row_field or not column_field:
        return [types.TextContent(type="text", text="Error: row_field and column_field are required.")]

    for idx, entity in enumerate(entities):
        if not isinstance(entity, dict):
            return [types.TextContent(type="text", text=f"Error: entity at index {idx} is not an object.")]
        if row_field not in entity or column_field not in entity:
            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Error: entity at index {idx} must contain both fields "
                        f"'{row_field}' and '{column_field}'."
                    ),
                )
            ]

    payload = json.dumps(
        {
            "_kind": "selectable_matrix",
            "title": title,
            "rowField": row_field,
            "columnField": column_field,
            "entities": entities,
        }
    )

    return [types.TextContent(type="text", text=payload)]
