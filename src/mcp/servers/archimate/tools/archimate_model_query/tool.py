"""Tool: archimate_model_query – Read-only advanced querying for ArchiMate models."""

from __future__ import annotations

import json
from collections import deque
from typing import Any

from mcp import types

from ...db import DB_PATH as METAMODEL_DB_PATH
from ...model_db import MODEL_DB_PATH, ModelError, get_connection
from ...server import mcp


def _model_exists(model_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM models WHERE id = ?", (model_id,))
        return cursor.fetchone() is not None


def _row_dicts(cursor) -> list[dict[str, Any]]:
    cols = [col[0] for col in cursor.description]
    rows: list[dict[str, Any]] = []
    for row in cursor.fetchall():
        data = dict(zip(cols, row))
        if "attributes_json" in data and isinstance(data["attributes_json"], str):
            try:
                data["attributes"] = json.loads(data["attributes_json"])
            except json.JSONDecodeError:
                data["attributes"] = {}
            del data["attributes_json"]
        rows.append(data)
    return rows


def _search_elements(
    model_id: str,
    type_name: str | None,
    layer: str | None,
    aspect: str | None,
    attribute_key: str | None,
    attribute_value: str | None,
    search: str | None,
    valid_at: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        # make metamodel data available via attached database so we can enrich
        # element results with their metamodel properties.  sqlite allows the
        # same connection to query two files simultaneously.
        cursor = connection.cursor()
        try:
            cursor.execute(f"ATTACH DATABASE '{METAMODEL_DB_PATH}' AS metamodel")
        except Exception:
            # if it's already attached or fails, ignore; queries will still run
            pass
        sql = (
            "SELECT me.*, e.layer AS metamodel_layer, e.aspect AS metamodel_aspect "
            "FROM model_elements me "
            "LEFT JOIN metamodel.elements e ON lower(e.name) = lower(me.type_name) "
            "WHERE me.model_id = ?"
        )
        params: list[Any] = [model_id]

        if type_name:
            sql += " AND lower(me.type_name) = lower(?)"
            params.append(type_name)
        if layer:
            sql += " AND lower(COALESCE(e.layer, '')) = lower(?)"
            params.append(layer)
        if aspect:
            sql += " AND lower(COALESCE(e.aspect, '')) = lower(?)"
            params.append(aspect)
        if search:
            like = f"%{search}%"
            sql += " AND (lower(me.id) LIKE lower(?) OR lower(me.name) LIKE lower(?) OR lower(me.type_name) LIKE lower(?))"
            params.extend([like, like, like])
        if valid_at:
            sql += " AND (me.valid_from IS NULL OR me.valid_from <= ?) AND (me.valid_to IS NULL OR me.valid_to >= ?)"
            params.extend([valid_at, valid_at])
        if attribute_key:
            sql += " AND json_extract(me.attributes_json, ?) IS NOT NULL"
            params.append(f"$.{attribute_key}")
            if attribute_value is not None:
                sql += " AND lower(CAST(json_extract(me.attributes_json, ?) AS TEXT)) = lower(?)"
                params.extend([f"$.{attribute_key}", str(attribute_value)])

        sql += " ORDER BY me.id LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        return _row_dicts(cursor)


def _search_relationships(
    model_id: str,
    type_name: str | None,
    category: str | None,
    source_element_id: str | None,
    target_element_id: str | None,
    valid_at: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"ATTACH DATABASE '{METAMODEL_DB_PATH}' AS metamodel")
        except Exception:
            pass
        # build SQL with optional metamodel join; if the join fails later we
        # will re-run without it.
        base_sql = (
            "SELECT mr.*, r.category AS metamodel_category, r.directed AS metamodel_directed "
            "FROM model_relationships mr "
            "LEFT JOIN metamodel.relationships r ON lower(r.name) = lower(mr.type_name) "
            "WHERE mr.model_id = ?"
        )
        params: list[Any] = [model_id]

        if type_name:
            base_sql += " AND lower(mr.type_name) = lower(?)"
            params.append(type_name)
        if category:
            base_sql += " AND lower(COALESCE(r.category, '')) = lower(?)"
            params.append(category)
        if source_element_id:
            base_sql += " AND mr.source_element_id = ?"
            params.append(source_element_id)
        if target_element_id:
            base_sql += " AND mr.target_element_id = ?"
            params.append(target_element_id)
        if valid_at:
            base_sql += " AND (mr.valid_from IS NULL OR mr.valid_from <= ?) AND (mr.valid_to IS NULL OR mr.valid_to >= ?)"
            params.extend([valid_at, valid_at])

        sql = base_sql + " ORDER BY mr.id LIMIT ?"
        params.append(limit)

        try:
            cursor.execute(sql, params)
        except Exception:
            # probably the metamodel.relationships table is missing; retry
            sql = "SELECT * FROM model_relationships WHERE model_id = ?"
            params = [model_id]
            if type_name:
                sql += " AND lower(type_name) = lower(?)"
                params.append(type_name)
            if source_element_id:
                sql += " AND source_element_id = ?"
                params.append(source_element_id)
            if target_element_id:
                sql += " AND target_element_id = ?"
                params.append(target_element_id)
            if valid_at:
                sql += " AND (valid_from IS NULL OR valid_from <= ?) AND (valid_to IS NULL OR valid_to >= ?)"
                params.extend([valid_at, valid_at])
            sql += " ORDER BY id LIMIT ?"
            params.append(limit)
            cursor.execute(sql, params)
            rows = _row_dicts(cursor)
            return rows

        rows = _row_dicts(cursor)
        for row in rows:
            if row.get("metamodel_directed") is not None:
                row["metamodel_directed"] = bool(row["metamodel_directed"])
        return rows


def _neighbors(model_id: str, element_id: str, direction: str, relationship_type: str | None, limit: int) -> list[dict[str, Any]]:
    direction = direction.lower()
    with get_connection() as connection:
        cursor = connection.cursor()
        base_sql = "SELECT * FROM model_relationships WHERE model_id = ?"
        params: list[Any] = [model_id]

        if relationship_type:
            base_sql += " AND lower(type_name) = lower(?)"
            params.append(relationship_type)

        if direction == "out":
            sql = base_sql + " AND source_element_id = ? ORDER BY id LIMIT ?"
            params.extend([element_id, limit])
        elif direction == "in":
            sql = base_sql + " AND target_element_id = ? ORDER BY id LIMIT ?"
            params.extend([element_id, limit])
        else:
            sql = base_sql + " AND (source_element_id = ? OR target_element_id = ?) ORDER BY id LIMIT ?"
            params.extend([element_id, element_id, limit])

        cursor.execute(sql, params)
        relationships = _row_dicts(cursor)

        neighbor_ids: set[str] = set()
        for rel in relationships:
            if rel["source_element_id"] != element_id:
                neighbor_ids.add(rel["source_element_id"])
            if rel["target_element_id"] != element_id:
                neighbor_ids.add(rel["target_element_id"])

        element_rows: list[dict[str, Any]] = []
        if neighbor_ids:
            placeholders = ",".join("?" for _ in neighbor_ids)
            cursor.execute(
                f"SELECT * FROM model_elements WHERE model_id = ? AND id IN ({placeholders}) ORDER BY id",
                [model_id, *neighbor_ids],
            )
            element_rows = _row_dicts(cursor)

        return [{"neighbors": element_rows, "relationships": relationships}]


def _path_exists(model_id: str, source: str, target: str, max_depth: int = 5) -> dict[str, Any]:
    max_depth = max(1, min(int(max_depth), 10))

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT source_element_id, target_element_id, type_name FROM model_relationships WHERE model_id = ?",
            (model_id,),
        )
        edges = cursor.fetchall()

    graph: dict[str, list[tuple[str, str]]] = {}
    for source_id, target_id, rel_type in edges:
        graph.setdefault(source_id, []).append((target_id, rel_type))

    queue: deque[tuple[str, int, list[dict[str, str]]]] = deque([(source, 0, [])])
    visited: set[tuple[str, int]] = {(source, 0)}

    while queue:
        node, depth, path = queue.popleft()
        if node == target:
            return {"exists": True, "depth": depth, "path": path}
        if depth >= max_depth:
            continue
        for next_node, rel_type in graph.get(node, []):
            next_state = (next_node, depth + 1)
            if next_state in visited:
                continue
            visited.add(next_state)
            queue.append(
                (
                    next_node,
                    depth + 1,
                    path + [{"from": node, "to": next_node, "relationship_type": rel_type}],
                )
            )

    return {"exists": False, "depth": None, "path": []}


@mcp.tool()
def archimate_model_query(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Read-only advanced model queries.

    Actions:
            - db_info: return metamodel/model SQLite locations
      - search_elements: filter by type/layer/aspect/attribute/time/text
      - search_relationships: filter by type/category/source/target/time
      - neighbors: get adjacent nodes and connecting relationships
      - path_exists: check if directed path exists (BFS)
      - temporal_slice: return elements and relationships valid at a date
      - model_stats: quick summary for query-oriented retrieval
    """
    action = (action or "").strip().lower()

    try:
        payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: payload_json is invalid JSON – {exc}")]

    try:
        if action == "db_info":
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "metamodel_db": {"path": str(METAMODEL_DB_PATH), "exists": METAMODEL_DB_PATH.exists()},
                            "model_db": {"path": str(MODEL_DB_PATH), "exists": MODEL_DB_PATH.exists()},
                        },
                        ensure_ascii=False,
                    ),
                )
            ]

        model_id = str(payload.get("model_id", "")).strip()
        if not model_id:
            # try conversational context
            from ...server import get_current_model
            cm = get_current_model()
            if cm:
                model_id = cm
        if not model_id:
            return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
        if not _model_exists(model_id):
            raise ModelError(f"Model '{model_id}' not found")

        if action == "search_elements":
            # handle potential typos in attribute_key by consulting the model's
            # attribute dictionary.  if we find a close match, we swap it and add
            # a warning message to the response.
            attr_key = str(payload.get("attribute_key")) if payload.get("attribute_key") is not None else None
            warning: str | None = None
            if attr_key and not attr_key.strip() == "":
                # get definitions for the current model
                try:
                    from ...model_db import list_attribute_definitions
                    defs = list_attribute_definitions(model_id, "element")
                    keys = [d["key"] for d in defs]
                    import difflib
                    matches = difflib.get_close_matches(attr_key, keys, n=1, cutoff=0.6)
                    if matches and matches[0].lower() != attr_key.lower():
                        warning = f"Attribute key '{attr_key}' not found; using '{matches[0]}' instead."
                        attr_key = matches[0]
                except Exception:
                    # if dictionary lookup fails, just continue without warning
                    pass
            rows = _search_elements(
                model_id=model_id,
                type_name=str(payload.get("type_name")) if payload.get("type_name") is not None else None,
                layer=str(payload.get("layer")) if payload.get("layer") is not None else None,
                aspect=str(payload.get("aspect")) if payload.get("aspect") is not None else None,
                attribute_key=attr_key,
                attribute_value=str(payload.get("attribute_value")) if payload.get("attribute_value") is not None else None,
                search=str(payload.get("search")) if payload.get("search") is not None else None,
                valid_at=str(payload.get("valid_at")) if payload.get("valid_at") is not None else None,
                limit=max(1, min(int(payload.get("limit", 200)), 1000)),
            )
            if warning:
                return [types.TextContent(type="text", text=warning), types.TextContent(type="text", text=json.dumps(rows, ensure_ascii=False))]
            return [types.TextContent(type="text", text=json.dumps(rows, ensure_ascii=False))]

        if action == "search_relationships":
            rows = _search_relationships(
                model_id=model_id,
                type_name=str(payload.get("type_name")) if payload.get("type_name") is not None else None,
                category=str(payload.get("category")) if payload.get("category") is not None else None,
                source_element_id=str(payload.get("source_element_id")) if payload.get("source_element_id") is not None else None,
                target_element_id=str(payload.get("target_element_id")) if payload.get("target_element_id") is not None else None,
                valid_at=str(payload.get("valid_at")) if payload.get("valid_at") is not None else None,
                limit=max(1, min(int(payload.get("limit", 200)), 1000)),
            )
            return [types.TextContent(type="text", text=json.dumps(rows, ensure_ascii=False))]

        if action == "neighbors":
            if not payload.get("element_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'element_id'")]
            rows = _neighbors(
                model_id=model_id,
                element_id=str(payload["element_id"]),
                direction=str(payload.get("direction", "both")),
                relationship_type=str(payload.get("relationship_type")) if payload.get("relationship_type") is not None else None,
                limit=max(1, min(int(payload.get("limit", 200)), 1000)),
            )
            return [types.TextContent(type="text", text=json.dumps(rows[0], ensure_ascii=False))]

        if action == "path_exists":
            for key in ("source_element_id", "target_element_id"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = _path_exists(
                model_id=model_id,
                source=str(payload["source_element_id"]),
                target=str(payload["target_element_id"]),
                max_depth=int(payload.get("max_depth", 5)),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "temporal_slice":
            if not payload.get("valid_at"):
                return [types.TextContent(type="text", text="Error: missing required field 'valid_at'")]
            valid_at = str(payload["valid_at"])
            elements = _search_elements(
                model_id=model_id,
                type_name=None,
                layer=str(payload.get("layer")) if payload.get("layer") is not None else None,
                aspect=None,
                attribute_key=None,
                attribute_value=None,
                search=None,
                valid_at=valid_at,
                limit=max(1, min(int(payload.get("element_limit", 1000)), 2000)),
            )
            relationships = _search_relationships(
                model_id=model_id,
                type_name=None,
                category=None,
                source_element_id=None,
                target_element_id=None,
                valid_at=valid_at,
                limit=max(1, min(int(payload.get("relationship_limit", 1000)), 2000)),
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"model_id": model_id, "valid_at": valid_at, "elements": elements, "relationships": relationships}, ensure_ascii=False),
                )
            ]

        if action == "model_stats":
            with get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM model_elements WHERE model_id = ?", (model_id,))
                element_count = int(cursor.fetchone()[0])
                cursor.execute("SELECT COUNT(*) FROM model_relationships WHERE model_id = ?", (model_id,))
                relationship_count = int(cursor.fetchone()[0])
                cursor.execute("SELECT COUNT(DISTINCT type_name) FROM model_elements WHERE model_id = ?", (model_id,))
                element_type_count = int(cursor.fetchone()[0])
                cursor.execute("SELECT COUNT(DISTINCT type_name) FROM model_relationships WHERE model_id = ?", (model_id,))
                relationship_type_count = int(cursor.fetchone()[0])
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "model_id": model_id,
                            "counts": {
                                "elements": element_count,
                                "relationships": relationship_count,
                                "element_types": element_type_count,
                                "relationship_types": relationship_type_count,
                            },
                            "density": round((relationship_count / element_count), 3) if element_count else 0.0,
                        },
                        ensure_ascii=False,
                    ),
                )
            ]

        allowed = [
            "db_info",
            "search_elements",
            "search_relationships",
            "neighbors",
            "path_exists",
            "temporal_slice",
            "model_stats",
        ]
        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'. Allowed: {', '.join(allowed)}")]
    except ModelError as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
