"""Tool: archimate_metamodel_info – Query ArchiMate 3.2 metamodel information."""

from __future__ import annotations

import json
from mcp import types

from ...db import DB_PATH, get_connection
from ...server import mcp


def _rows_to_dicts(cursor) -> list[dict]:
    columns = [col[0] for col in cursor.description]
    result = []
    for row in cursor.fetchall():
        item = dict(zip(columns, row))
        for key in ("attributes_json", "constraints_json"):
            if key in item and isinstance(item[key], str):
                try:
                    item[key] = json.loads(item[key])
                except json.JSONDecodeError:
                    pass
        if "directed" in item:
            item["directed"] = bool(item["directed"])
        result.append(item)
    return result


@mcp.tool()
def archimate_metamodel_info(
    query_type: str = "overview",
    name: str | None = None,
    layer: str | None = None,
    category: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[types.TextContent]:
    """Query the ArchiMate 3.2 metamodel database.

    Supported query_type values:
            - db_info: return metamodel/model SQLite locations
      - overview: return dataset metadata + counts + available layers/categories
      - elements: list element types (optional filter: layer, search)
      - relationships: list relationship types (optional filter: category, search)
      - element: return one element type by exact name
      - relationship: return one relationship type by exact name
      - rules: list metamodel rules (optional filter: search)
    """
    query_type = (query_type or "overview").strip().lower()
    limit = max(1, min(int(limit), 500))

    if query_type == "db_info":
        from ...model_db import MODEL_DB_PATH

        payload = {
            "metamodel_db": {"path": str(DB_PATH), "exists": DB_PATH.exists()},
            "model_db": {"path": str(MODEL_DB_PATH), "exists": MODEL_DB_PATH.exists()},
        }
        return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

    with get_connection() as connection:
        cursor = connection.cursor()

        if query_type == "overview":
            cursor.execute("SELECT key, value FROM metamodel_info ORDER BY key")
            metadata = {k: v for k, v in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) FROM elements")
            element_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM relationships")
            relationship_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM metamodel_rules")
            rule_count = cursor.fetchone()[0]

            cursor.execute("SELECT DISTINCT layer FROM elements ORDER BY layer")
            layers = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT category FROM relationships ORDER BY category")
            categories = [row[0] for row in cursor.fetchall()]

            payload = {
                "db_path": str(DB_PATH),
                "metadata": metadata,
                "counts": {
                    "elements": element_count,
                    "relationships": relationship_count,
                    "rules": rule_count,
                },
                "layers": layers,
                "relationship_categories": categories,
            }
            return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

        if query_type == "elements":
            sql = "SELECT * FROM elements"
            clauses = []
            params: list[str | int] = []
            if layer:
                clauses.append("lower(layer) = lower(?)")
                params.append(layer)
            if search:
                clauses.append("(lower(name) LIKE lower(?) OR lower(definition) LIKE lower(?))")
                like = f"%{search}%"
                params.extend([like, like])
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY layer, name LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            return [types.TextContent(type="text", text=json.dumps(_rows_to_dicts(cursor), ensure_ascii=False))]

        if query_type == "relationships":
            sql = "SELECT * FROM relationships"
            clauses = []
            params: list[str | int] = []
            if category:
                clauses.append("lower(category) = lower(?)")
                params.append(category)
            if search:
                clauses.append("(lower(name) LIKE lower(?) OR lower(definition) LIKE lower(?))")
                like = f"%{search}%"
                params.extend([like, like])
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY category, name LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            return [types.TextContent(type="text", text=json.dumps(_rows_to_dicts(cursor), ensure_ascii=False))]

        if query_type == "element":
            if not name:
                return [types.TextContent(type="text", text="Error: name is required for query_type='element'")]
            cursor.execute("SELECT * FROM elements WHERE lower(name) = lower(?)", (name,))
            rows = _rows_to_dicts(cursor)
            if not rows:
                return [types.TextContent(type="text", text=f"Error: element '{name}' not found")]
            return [types.TextContent(type="text", text=json.dumps(rows[0], ensure_ascii=False))]

        if query_type == "relationship":
            if not name:
                return [types.TextContent(type="text", text="Error: name is required for query_type='relationship'")]
            cursor.execute("SELECT * FROM relationships WHERE lower(name) = lower(?)", (name,))
            rows = _rows_to_dicts(cursor)
            if not rows:
                return [types.TextContent(type="text", text=f"Error: relationship '{name}' not found")]
            return [types.TextContent(type="text", text=json.dumps(rows[0], ensure_ascii=False))]

        if query_type == "rules":
            sql = "SELECT rule_type, source, relationship, target, notes FROM metamodel_rules"
            params: list[str | int] = []
            if search:
                sql += " WHERE lower(source) LIKE lower(?) OR lower(target) LIKE lower(?) OR lower(notes) LIKE lower(?)"
                like = f"%{search}%"
                params.extend([like, like, like])
            sql += " ORDER BY rule_type, source LIMIT ?"
            params.append(limit)
            cursor.execute(sql, params)
            return [types.TextContent(type="text", text=json.dumps(_rows_to_dicts(cursor), ensure_ascii=False))]

    allowed = ["db_info", "overview", "elements", "relationships", "element", "relationship", "rules"]
    return [
        types.TextContent(
            type="text",
            text=f"Error: unknown query_type '{query_type}'. Allowed values: {', '.join(allowed)}",
        )
    ]
