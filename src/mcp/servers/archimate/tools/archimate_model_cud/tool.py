"""Tool: archimate_model_cud – Dedicated create/update/delete for model elements and relationships."""

from __future__ import annotations

import json
from typing import Any

from mcp import types

from ...db import DB_PATH as METAMODEL_DB_PATH
from ...model_db import (
    MODEL_DB_PATH,
    ModelError,
    delete_model_element,
    delete_model_relationship,
    upsert_model_element,
    upsert_model_relationship,
)
from ...server import mcp, note_model_mutation


@mcp.tool()
def archimate_model_cud(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Create/update/delete ArchiMate model elements and relationships.

    Actions:
      - db_info
      - create_element, update_element, delete_element
        - create_el/update_el/delete_el (short aliases)
      - create_relationship/update_relationship/delete_relationship (full names)
      - create_rel/update_rel/delete_rel (short aliases)
    """
    action = (action or "").strip().lower()
    action_aliases = {
        "create_el": "create_element",
        "update_el": "update_element",
        "delete_el": "delete_element",
        "create_rel": "create_relationship",
        "update_rel": "update_relationship",
        "delete_rel": "delete_relationship",
    }
    action = action_aliases.get(action, action)
    try:
        payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: payload_json is invalid JSON – {exc}")]

    try:
        if action == "db_info":
            result = {
                "metamodel_db": {
                    "path": str(METAMODEL_DB_PATH),
                    "exists": METAMODEL_DB_PATH.exists(),
                },
                "model_db": {
                    "path": str(MODEL_DB_PATH),
                    "exists": MODEL_DB_PATH.exists(),
                },
            }
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action in {"create_element", "update_element"}:
            for key in ("model_id", "type_name", "name"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            if action == "update_element" and not payload.get("element_id"):
                return [types.TextContent(type="text", text="Error: update_element requires 'element_id'")]

            result = upsert_model_element(
                model_id=str(payload["model_id"]),
                type_name=str(payload["type_name"]),
                name=str(payload["name"]),
                element_id=str(payload["element_id"]) if payload.get("element_id") else None,
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                valid_from=str(payload.get("valid_from")) if payload.get("valid_from") is not None else None,
                valid_to=str(payload.get("valid_to")) if payload.get("valid_to") is not None else None,
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
                message=str(payload.get("message", "Element upserted")),
            )
            note_model_mutation("archimate_model_cud", action, str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "delete_element":
            for key in ("model_id", "element_id"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = delete_model_element(
                model_id=str(payload["model_id"]),
                element_id=str(payload["element_id"]),
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
                message=str(payload.get("message", "Element deleted")),
            )
            note_model_mutation("archimate_model_cud", action, str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action in {"create_relationship", "update_relationship"}:
            for key in ("model_id", "type_name", "source_element_id", "target_element_id"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            if action == "update_relationship" and not payload.get("relationship_id"):
                return [types.TextContent(type="text", text="Error: update_relationship requires 'relationship_id'")]

            result = upsert_model_relationship(
                model_id=str(payload["model_id"]),
                type_name=str(payload["type_name"]),
                source_element_id=str(payload["source_element_id"]),
                target_element_id=str(payload["target_element_id"]),
                relationship_id=str(payload["relationship_id"]) if payload.get("relationship_id") else None,
                name=str(payload.get("name", "")),
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                valid_from=str(payload.get("valid_from")) if payload.get("valid_from") is not None else None,
                valid_to=str(payload.get("valid_to")) if payload.get("valid_to") is not None else None,
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
                message=str(payload.get("message", "Relationship upserted")),
            )
            note_model_mutation("archimate_model_cud", action, str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "delete_relationship":
            for key in ("model_id", "relationship_id"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = delete_model_relationship(
                model_id=str(payload["model_id"]),
                relationship_id=str(payload["relationship_id"]),
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
                message=str(payload.get("message", "Relationship deleted")),
            )
            note_model_mutation("archimate_model_cud", action, str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        allowed = [
            "db_info",
            "create_element",
            "update_element",
            "delete_element",
            "create_el",
            "update_el",
            "delete_el",
            "create_relationship",
            "update_relationship",
            "delete_relationship",
            "create_rel",
            "update_rel",
            "delete_rel",
        ]
        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'. Allowed: {', '.join(allowed)}")]
    except ModelError as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
