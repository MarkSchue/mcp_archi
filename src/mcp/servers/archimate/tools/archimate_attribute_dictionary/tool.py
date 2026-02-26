"""Tool: archimate_attribute_dictionary – CRUD on per-model attribute definitions.

Provides dedicated actions for defining, listing and deleting keys that are
allowed as element/relationship attributes within a particular model.  This
separates that responsibility from the more general `archimate_model_management`
tool and makes interactive prompts simpler.

Attribute definitions can be marked with ``is_tag=true`` to designate them as
*tags* – lightweight key/value labels that are stored separately from the main
``attributes`` dict, can be added/removed individually via the CUD tool's
``add_tag`` / ``remove_tag`` actions, and are searchable via the query tool's
``tag_key`` / ``tag_value`` filters.
"""

import json
from typing import Any

from mcp import types

from ...server import mcp
from ...model_db import (
    define_attribute,
    list_attribute_definitions,
    list_tag_definitions,
    delete_attribute_definition,
    ModelError,
)


@mcp.tool()
def archimate_attribute_dictionary(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Actions:
    - define: {model_id, target_type, key, description?, is_tag?}
    - list: {model_id, target_type}
    - list_tags: {model_id, target_type}
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
            is_tag_raw = payload.get("is_tag", False)
            is_tag = bool(is_tag_raw) if not isinstance(is_tag_raw, str) else is_tag_raw.lower() in ("true", "1", "yes")
            define_attribute(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
                key=str(payload["key"]),
                description=str(payload.get("description", "")),
                is_tag=is_tag,
            )
            return [types.TextContent(type="text", text=json.dumps({"status": "ok", "is_tag": is_tag}))]

        if action == "list":
            for key in ("model_id", "target_type"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            attrs = list_attribute_definitions(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
            )
            return [types.TextContent(type="text", text=json.dumps(attrs, ensure_ascii=False))]

        if action == "list_tags":
            for key in ("model_id", "target_type"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            tags = list_tag_definitions(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
            )
            return [types.TextContent(type="text", text=json.dumps(tags, ensure_ascii=False))]

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

        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'. Allowed: define, list, list_tags, delete")]
    except ModelError as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
