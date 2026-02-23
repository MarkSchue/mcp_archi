"""Tool: archimate_current_model – remember or query the active model.

This simple tool allows the assistant to set a "current" model ID in server
state, and later retrieve it.  Skills can use it to avoid passing model_id
explicitly on every call.
"""

import json
from typing import Any

from mcp import types

from ...server import mcp, set_current_model, get_current_model


@mcp.tool()
def archimate_current_model(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Actions:
    - set: payload must include "model_id" string
    - get: returns the current model_id or null
    """
    action = (action or "").strip().lower()
    try:
        payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: payload_json invalid – {exc}")]

    if action == "set":
        model_id = payload.get("model_id")
        if not model_id:
            return [types.TextContent(type="text", text="Error: missing required field 'model_id' for set")]
        set_current_model(str(model_id))
        return [types.TextContent(type="text", text=json.dumps({"model_id": model_id}))]

    if action == "get":
        current = get_current_model()
        return [types.TextContent(type="text", text=json.dumps({"model_id": current}))]

    if action == "find":
        # search for models by name fragment
        name = payload.get("name")
        if not name:
            return [types.TextContent(type="text", text="Error: missing required field 'name' for find")]
        # use the management tool's list_models helper
        from ...model_db import list_models
        results = list_models(limit=50, search=name)
        # return list of {id,name}
        simple = [{"id": r.get("id"), "name": r.get("name")} for r in results]
        return [types.TextContent(type="text", text=json.dumps(simple, ensure_ascii=False))]

    return [types.TextContent(type="text", text=f"Error: unknown action '{action}'")]