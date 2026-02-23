"""Tool: archimate_metamodel_enhance – Persist enhancements to metamodel data."""

from __future__ import annotations

import json
from typing import Any

from mcp import types

from ...db import DB_PATH as METAMODEL_DB_PATH, add_annotation, add_rule, delete_annotation, delete_rule, get_annotations, upsert_element, upsert_relationship
from ...model_db import MODEL_DB_PATH
from ...server import mcp


@mcp.tool()
def archimate_metamodel_enhance(
    action: str,
    payload_json: str,
) -> list[types.TextContent]:
    """Enhance the ArchiMate metamodel dataset.

    Args:
        action: One of `db_info`, `upsert_element`, `upsert_relationship`, `add_rule`, `add_annotation`, `list_annotations`, `delete_annotation`, `delete_rule`.
        payload_json: JSON payload for the selected action.

    Action payloads:
      - upsert_element:
        {"name": str, "layer": str, "aspect": str, "definition": str, "attributes": dict?, "constraints": list?}
      - upsert_relationship:
        {"name": str, "category": str, "directed": bool, "definition": str, "attributes": dict?, "constraints": list?}
      - add_rule:
        {"rule_type": str, "source": str, "relationship": str, "target": str, "notes": str}
      - add_annotation:
        {"target_type": "element"|"relationship"|"rule"|"general", "target_name": str, "note": str, "source": str?}
      - list_annotations:
        {"target_type": str?, "target_name": str?, "limit": int?}
            - delete_annotation:
                {"id": int? , "target_type": str?, "target_name": str?, "note": str?, "source": str?}
            - delete_rule:
                {"id": int? , "rule_type": str?, "source": str?, "relationship": str?, "target": str?, "notes": str?}
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

        if action == "upsert_element":
            for key in ("name", "layer", "aspect", "definition"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            status = upsert_element(
                name=str(payload["name"]),
                layer=str(payload["layer"]),
                aspect=str(payload["aspect"]),
                definition=str(payload["definition"]),
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                constraints=payload.get("constraints") if isinstance(payload.get("constraints"), list) else None,
            )
            return [types.TextContent(type="text", text=json.dumps({"status": status, "entity": "element", "name": payload["name"]}, ensure_ascii=False))]

        if action == "upsert_relationship":
            for key in ("name", "category", "directed", "definition"):
                if key not in payload:
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            status = upsert_relationship(
                name=str(payload["name"]),
                category=str(payload["category"]),
                directed=bool(payload["directed"]),
                definition=str(payload["definition"]),
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                constraints=payload.get("constraints") if isinstance(payload.get("constraints"), list) else None,
            )
            return [types.TextContent(type="text", text=json.dumps({"status": status, "entity": "relationship", "name": payload["name"]}, ensure_ascii=False))]

        if action == "add_rule":
            for key in ("rule_type", "source", "relationship", "target", "notes"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            rule_id = add_rule(
                rule_type=str(payload["rule_type"]),
                source=str(payload["source"]),
                relationship=str(payload["relationship"]),
                target=str(payload["target"]),
                notes=str(payload["notes"]),
            )
            return [types.TextContent(type="text", text=json.dumps({"status": "stored", "entity": "rule", "id": rule_id}, ensure_ascii=False))]

        if action == "add_annotation":
            for key in ("target_type", "target_name", "note"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            annotation_id = add_annotation(
                target_type=str(payload["target_type"]),
                target_name=str(payload["target_name"]),
                note=str(payload["note"]),
                source=str(payload.get("source", "user")),
            )
            return [types.TextContent(type="text", text=json.dumps({"status": "stored", "entity": "annotation", "id": annotation_id}, ensure_ascii=False))]

        if action == "list_annotations":
            rows = get_annotations(
                target_type=str(payload.get("target_type")) if payload.get("target_type") is not None else None,
                target_name=str(payload.get("target_name")) if payload.get("target_name") is not None else None,
                limit=int(payload.get("limit", 100)),
            )
            return [types.TextContent(type="text", text=json.dumps(rows, ensure_ascii=False))]

        if action == "delete_annotation":
            deleted = delete_annotation(
                annotation_id=int(payload["id"]) if payload.get("id") is not None else None,
                target_type=str(payload.get("target_type")) if payload.get("target_type") is not None else None,
                target_name=str(payload.get("target_name")) if payload.get("target_name") is not None else None,
                note=str(payload.get("note")) if payload.get("note") is not None else None,
                source=str(payload.get("source")) if payload.get("source") is not None else None,
            )
            if deleted == 0 and payload.get("id") is None and not any(
                payload.get(k) is not None for k in ("target_type", "target_name", "note", "source")
            ):
                return [types.TextContent(type="text", text="Error: delete_annotation requires id or at least one filter field")]
            return [types.TextContent(type="text", text=json.dumps({"status": "deleted", "entity": "annotation", "count": deleted}, ensure_ascii=False))]

        if action == "delete_rule":
            deleted = delete_rule(
                rule_id=int(payload["id"]) if payload.get("id") is not None else None,
                rule_type=str(payload.get("rule_type")) if payload.get("rule_type") is not None else None,
                source=str(payload.get("source")) if payload.get("source") is not None else None,
                relationship=str(payload.get("relationship")) if payload.get("relationship") is not None else None,
                target=str(payload.get("target")) if payload.get("target") is not None else None,
                notes=str(payload.get("notes")) if payload.get("notes") is not None else None,
            )
            if deleted == 0 and payload.get("id") is None and not any(
                payload.get(k) is not None for k in ("rule_type", "source", "relationship", "target", "notes")
            ):
                return [types.TextContent(type="text", text="Error: delete_rule requires id or at least one filter field")]
            return [types.TextContent(type="text", text=json.dumps({"status": "deleted", "entity": "rule", "count": deleted}, ensure_ascii=False))]

        allowed = [
            "db_info",
            "upsert_element",
            "upsert_relationship",
            "add_rule",
            "add_annotation",
            "list_annotations",
            "delete_annotation",
            "delete_rule",
        ]
        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'. Allowed: {', '.join(allowed)}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
