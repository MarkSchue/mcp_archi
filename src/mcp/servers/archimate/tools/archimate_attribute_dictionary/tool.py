"""Tool: archimate_attribute_dictionary – CRUD on per-model attribute definitions.

Provides dedicated actions for defining, listing and deleting keys that are
allowed as element/relationship attributes within a particular model.  This
separates that responsibility from the more general `archimate_model_management`
tool and makes interactive prompts simpler.
"""

import json
from typing import Any

from mcp import types

from ...server import mcp
from ...model_db import (
    define_attribute,
    list_attribute_definitions,
    delete_attribute_definition,
    ModelError,
)


@mcp.tool()
def archimate_attribute_dictionary(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Actions:
    - define: {model_id, target_type, key, description?}
    - list: {model_id, target_type}
    - delete: {model_id, target_type, key}
    """
    action = (action or "").strip().lower()
    try:
        payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: payload_json invalid – {exc}")]

    try:
        if action == "define":
            for key in ("model_id", "target_type", "key"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            define_attribute(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
                key=str(payload["key"]),
                description=str(payload.get("description", "")),
            )
            return [types.TextContent(type="text", text=json.dumps({"status": "ok"}))]

        if action == "list":
            for key in ("model_id", "target_type"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            attrs = list_attribute_definitions(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
            )
            return [types.TextContent(type="text", text=json.dumps(attrs, ensure_ascii=False))]

        if action == "delete":
            for key in ("model_id", "target_type", "key"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            count = delete_attribute_definition(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
                key=str(payload["key"]),
            )
            return [types.TextContent(type="text", text=json.dumps({"deleted": count}))]

        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'")]
    except ModelError as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
