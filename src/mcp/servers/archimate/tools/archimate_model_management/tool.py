"""Tool: archimate_model_management – Manage ArchiMate models and versions."""

from __future__ import annotations

import json
from typing import Any

from mcp import types

from ...db import DB_PATH as METAMODEL_DB_PATH
from ...model_db import (
    MODEL_DB_PATH,
    ModelError,
    acquire_lock,
    create_model,
    delete_model,
    delete_model_element,
    delete_model_relationship,
    export_model_csv,
    export_model_xml,
    generate_insights,
    generate_report,
    get_lock,
    get_model,
    get_version,
    import_model_csv,
    import_model_xml,
    list_model_elements,
    list_model_relationships,
    list_models,
    list_versions,
    mermaid_view,
    release_lock,
    revert_to_version,
    update_model,
    upsert_model_element,
    upsert_model_relationship,
    validate_model,
)
from ...server import mcp


@mcp.tool()
def archimate_model_management(action: str, payload_json: str = "{}") -> list[types.TextContent]:
    """Manage ArchiMate models (CRUD, versioning, validation, reports, insights, query, import/export).

    Actions:
        - db_info
      - create_model, list_models, get_model, update_model, delete_model
      - upsert_element, list_elements, delete_element
      - upsert_relationship, list_relationships, delete_relationship
      - list_versions, get_version, revert_version
      - validate_model, generate_report, generate_insights, generate_view_mermaid
      - export_csv, import_csv, export_xml, import_xml
      - acquire_lock, release_lock, get_lock
      - define_attribute, list_attributes, delete_attribute  # manage per-model attribute dictionary
    """
    action = (action or "").strip().lower()

    try:
        payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: payload_json is invalid JSON – {exc}")]

    # conversational default model id if none provided
    if not payload.get("model_id"):
        from ...server import get_current_model
        cm = get_current_model()
        if cm:
            payload["model_id"] = cm

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

        if action == "create_model":
            if not payload.get("name"):
                return [types.TextContent(type="text", text="Error: missing required field 'name'")]
            result = create_model(
                name=str(payload["name"]),
                description=str(payload.get("description", "")),
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                model_id=str(payload.get("model_id")) if payload.get("model_id") else None,
                author=str(payload.get("author", "system")),
            )
            # remember as current model for conversational context
            from ...server import set_current_model
            set_current_model(result.get("id"))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "list_models":
            result = list_models(
                limit=int(payload.get("limit", 100)),
                search=str(payload.get("search")) if payload.get("search") is not None else None,
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "get_model":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = get_model(
                model_id=str(payload["model_id"]),
                include_graph=bool(payload.get("include_graph", True)),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "update_model":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = update_model(
                model_id=str(payload["model_id"]),
                name=str(payload.get("name")) if payload.get("name") is not None else None,
                description=str(payload.get("description")) if payload.get("description") is not None else None,
                attributes=payload.get("attributes") if isinstance(payload.get("attributes"), dict) else None,
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
                message=str(payload.get("message", "Model updated")),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "delete_model":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            deleted = delete_model(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps({"status": "deleted", "count": deleted}, ensure_ascii=False))]

        if action == "define_attribute":
            for key in ("model_id", "target_type", "key"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            from ...model_db import define_attribute
            define_attribute(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
                key=str(payload["key"]),
                description=str(payload.get("description", "")),
            )
            return [types.TextContent(type="text", text=json.dumps({"status": "ok"}, ensure_ascii=False))]

        if action == "list_attributes":
            for key in ("model_id", "target_type"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            from ...model_db import list_attribute_definitions
            attrs = list_attribute_definitions(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
            )
            return [types.TextContent(type="text", text=json.dumps(attrs, ensure_ascii=False))]

        if action == "delete_attribute":
            for key in ("model_id", "target_type", "key"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            from ...model_db import delete_attribute_definition
            count = delete_attribute_definition(
                model_id=str(payload["model_id"]),
                target_type=str(payload["target_type"]),
                key=str(payload["key"]),
            )
            return [types.TextContent(type="text", text=json.dumps({"deleted": count}, ensure_ascii=False))]

        if action == "upsert_element":
            for key in ("model_id", "type_name", "name"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
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
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "list_elements":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = list_model_elements(
                model_id=str(payload["model_id"]),
                type_name=str(payload.get("type_name")) if payload.get("type_name") is not None else None,
                search=str(payload.get("search")) if payload.get("search") is not None else None,
                valid_at=str(payload.get("valid_at")) if payload.get("valid_at") is not None else None,
                limit=int(payload.get("limit", 200)),
            )
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
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "upsert_relationship":
            for key in ("model_id", "type_name", "source_element_id", "target_element_id"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
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
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "list_relationships":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = list_model_relationships(
                model_id=str(payload["model_id"]),
                type_name=str(payload.get("type_name")) if payload.get("type_name") is not None else None,
                source_element_id=str(payload.get("source_element_id")) if payload.get("source_element_id") is not None else None,
                target_element_id=str(payload.get("target_element_id")) if payload.get("target_element_id") is not None else None,
                valid_at=str(payload.get("valid_at")) if payload.get("valid_at") is not None else None,
                limit=int(payload.get("limit", 200)),
            )
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
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "list_versions":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = list_versions(
                model_id=str(payload["model_id"]),
                limit=int(payload.get("limit", 100)),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "get_version":
            for key in ("model_id", "version"):
                if payload.get(key) is None:
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = get_version(model_id=str(payload["model_id"]), version=int(payload["version"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "revert_version":
            for key in ("model_id", "version"):
                if payload.get(key) is None:
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = revert_to_version(
                model_id=str(payload["model_id"]),
                version=int(payload["version"]),
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "validate_model":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = validate_model(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "generate_report":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = generate_report(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "generate_insights":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = generate_insights(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "generate_view_mermaid":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = {
                "model_id": str(payload["model_id"]),
                "mermaid": mermaid_view(
                    model_id=str(payload["model_id"]),
                    direction=str(payload.get("direction", "LR")),
                    limit=int(payload.get("limit", 300)),
                ),
            }
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "export_csv":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = export_model_csv(
                model_id=str(payload["model_id"]),
                filename_prefix=str(payload.get("filename_prefix")) if payload.get("filename_prefix") is not None else None,
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "import_csv":
            for key in ("model_id", "elements_csv", "relationships_csv"):
                if payload.get(key) is None:
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = import_model_csv(
                model_id=str(payload["model_id"]),
                elements_csv=str(payload["elements_csv"]),
                relationships_csv=str(payload["relationships_csv"]),
                replace=bool(payload.get("replace", False)),
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "export_xml":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            xml_content = export_model_xml(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps({"model_id": str(payload["model_id"]), "xml": xml_content}, ensure_ascii=False))]

        if action == "import_xml":
            for key in ("model_id", "xml"):
                if payload.get(key) is None:
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = import_model_xml(
                model_id=str(payload["model_id"]),
                xml_content=str(payload["xml"]),
                replace=bool(payload.get("replace", False)),
                expected_version=int(payload["expected_version"]) if payload.get("expected_version") is not None else None,
                author=str(payload.get("author", "system")),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "acquire_lock":
            for key in ("model_id", "owner"):
                if not payload.get(key):
                    return [types.TextContent(type="text", text=f"Error: missing required field '{key}'")]
            result = acquire_lock(
                model_id=str(payload["model_id"]),
                owner=str(payload["owner"]),
                force=bool(payload.get("force", False)),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "release_lock":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = release_lock(
                model_id=str(payload["model_id"]),
                owner=str(payload.get("owner")) if payload.get("owner") is not None else None,
                force=bool(payload.get("force", False)),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if action == "get_lock":
            if not payload.get("model_id"):
                return [types.TextContent(type="text", text="Error: missing required field 'model_id'")]
            result = get_lock(model_id=str(payload["model_id"]))
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        allowed = [
            "db_info",
            "create_model", "list_models", "get_model", "update_model", "delete_model",
            "upsert_element", "list_elements", "delete_element",
            "upsert_relationship", "list_relationships", "delete_relationship",
            "list_versions", "get_version", "revert_version",
            "validate_model", "generate_report", "generate_insights", "generate_view_mermaid",
            "export_csv", "import_csv", "export_xml", "import_xml",
            "acquire_lock", "release_lock", "get_lock",
        ]
        return [types.TextContent(type="text", text=f"Error: unknown action '{action}'. Allowed: {', '.join(allowed)}")]
    except ModelError as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]
