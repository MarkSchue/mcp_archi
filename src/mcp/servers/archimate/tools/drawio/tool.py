"""Tool: drawio – Generate draw.io XML for ArchiMate entities and relationships."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from mcp import types

from ...server import clear_recent_model_mutation, get_recent_model_mutation, mcp


STATIC_STYLESHEET_FILENAME = "styles.css"


ELEMENT_STYLE_MAP: dict[str, dict[str, str | None]] = {
    "Application Collaboration": {"shape": "mxgraph.archimate3.collaboration", "appType": "collab", "archiType": "square"},
    "Application Component": {"shape": "mxgraph.archimate3.component", "appType": "comp", "archiType": "square"},
    "Application Event": {"shape": "mxgraph.archimate3.event", "appType": "event", "archiType": "rounded"},
    "Application Function": {"shape": "mxgraph.archimate3.function", "appType": "func", "archiType": "rounded"},
    "Application Interaction": {"shape": "mxgraph.archimate3.interaction", "appType": "interaction", "archiType": "rounded"},
    "Application Interface": {"shape": "mxgraph.archimate3.interface", "appType": "interface", "archiType": "square"},
    "Application Process": {"shape": "mxgraph.archimate3.process", "appType": "proc", "archiType": "rounded"},
    "Application Service": {"shape": "mxgraph.archimate3.service", "appType": "serv", "archiType": "rounded"},
    "Artifact": {"shape": "mxgraph.archimate3.artifact", "appType": "artifact", "archiType": "square"},
    "Assessment": {"shape": "mxgraph.archimate3.assess", "appType": "assess", "archiType": "oct"},
    "Business Actor": {"shape": "mxgraph.archimate3.actor", "appType": "actor", "archiType": "square"},
    "Business Collaboration": {"shape": "mxgraph.archimate3.collaboration", "appType": "collab", "archiType": "square"},
    "Business Event": {"shape": "mxgraph.archimate3.event", "appType": "event", "archiType": "rounded"},
    "Business Function": {"shape": "mxgraph.archimate3.function", "appType": "func", "archiType": "rounded"},
    "Business Interaction": {"shape": "mxgraph.archimate3.interaction", "appType": "interaction", "archiType": "rounded"},
    "Business Interface": {"shape": "mxgraph.archimate3.interface", "appType": "interface", "archiType": "square"},
    "Business Object": {"shape": "mxgraph.archimate3.businessObject", "appType": "passive", "archiType": "square"},
    "Business Process": {"shape": "mxgraph.archimate3.process", "appType": "proc", "archiType": "rounded"},
    "Business Role": {"shape": "mxgraph.archimate3.role", "appType": "role", "archiType": "square"},
    "Business Service": {"shape": "mxgraph.archimate3.service", "appType": "serv", "archiType": "rounded"},
    "Capability": {"shape": "mxgraph.archimate3.capability", "appType": "capability", "archiType": "rounded"},
    "Communication Network": {"shape": "mxgraph.archimate3.network", "appType": "netw", "archiType": "square"},
    "Constraint": {"shape": "mxgraph.archimate3.constraint", "appType": "constraint", "archiType": "oct"},
    "Contract": {"shape": "mxgraph.archimate3.contract", "appType": "contract", "archiType": "square"},
    "Course of Action": {"shape": "mxgraph.archimate3.course", "appType": "course", "archiType": "rounded"},
    "Data Object": {"shape": "mxgraph.archimate3.passive", "appType": "passive", "archiType": "square"},
    "Deliverable": {"shape": "mxgraph.archimate3.deliverable", "appType": "deliverable", "archiType": None},
    "Device": {"shape": "mxgraph.archimate3.device", "appType": "device", "archiType": None},
    "Distribution Network": {"shape": "mxgraph.archimate3.distribution", "appType": "distribution", "archiType": "square"},
    "Driver": {"shape": "mxgraph.archimate3.driver", "appType": "driver", "archiType": "oct"},
    "Equipment": {"shape": "mxgraph.archimate3.equipment", "appType": "equipment", "archiType": "square"},
    "Facility": {"shape": "mxgraph.archimate3.facility", "appType": "facility", "archiType": "square"},
    "Gap": {"shape": "mxgraph.archimate3.gapIcon", "appType": "gap", "archiType": None},
    "Goal": {"shape": "mxgraph.archimate3.goal", "appType": "goal", "archiType": "oct"},
    "Grouping": {"shape": "mxgraph.archimate3.grouping", "appType": "grouping", "archiType": "square"},
    "Implementation Event": {"shape": "mxgraph.archimate3.event", "appType": "event", "archiType": "rounded"},
    "Junction": {"shape": "mxgraph.archimate3.junction", "appType": None, "archiType": None},
    "Location": {"shape": "mxgraph.archimate3.locationIcon", "appType": "location", "archiType": "square"},
    "Material": {"shape": "mxgraph.archimate3.material", "appType": "material", "archiType": "square"},
    "Meaning": {"shape": "mxgraph.archimate3.meaning", "appType": "meaning", "archiType": "oct"},
    "Node": {"shape": "mxgraph.archimate3.node", "appType": "node", "archiType": "square"},
    "Outcome": {"shape": "mxgraph.archimate3.outcome", "appType": "outcome", "archiType": "oct"},
    "Path": {"shape": "mxgraph.archimate3.path", "appType": "path", "archiType": "square"},
    "Plateau": {"shape": "mxgraph.archimate3.plateau", "appType": "plateau", "archiType": None},
    "Principle": {"shape": "mxgraph.archimate3.principle", "appType": "principle", "archiType": "oct"},
    "Product": {"shape": "mxgraph.archimate3.product", "appType": "product", "archiType": "square"},
    "Representation": {"shape": "mxgraph.archimate3.representation", "appType": "representation", "archiType": "square"},
    "Requirement": {"shape": "mxgraph.archimate3.requirement", "appType": "requirement", "archiType": "oct"},
    "Resource": {"shape": "mxgraph.archimate3.resource", "appType": "resource", "archiType": "square"},
    "Stakeholder": {"shape": "mxgraph.archimate3.role", "appType": "role", "archiType": "oct"},
    "System Software": {"shape": "mxgraph.archimate3.sysSw", "appType": "sysSw", "archiType": "square"},
    "Technology Collaboration": {"shape": "mxgraph.archimate3.collaboration", "appType": "collab", "archiType": "square"},
    "Technology Event": {"shape": "mxgraph.archimate3.event", "appType": "event", "archiType": "rounded"},
    "Technology Function": {"shape": "mxgraph.archimate3.function", "appType": "func", "archiType": "square"},
    "Technology Interaction": {"shape": "mxgraph.archimate3.interaction", "appType": "interaction", "archiType": "rounded"},
    "Technology Interface": {"shape": "mxgraph.archimate3.interface", "appType": "interface", "archiType": "square"},
    "Technology Process": {"shape": "mxgraph.archimate3.process", "appType": "proc", "archiType": "rounded"},
    "Technology Service": {"shape": "mxgraph.archimate3.service", "appType": "serv", "archiType": "rounded"},
    "Value": {"shape": "mxgraph.archimate3.value", "appType": "amValue", "archiType": "oct"},
    "Value Stream": {"shape": "mxgraph.archimate3.valueStream", "appType": "valueStream", "archiType": "rounded"},
    "Work Package": {"shape": "mxgraph.archimate3.workPackage", "appType": "workPackage", "archiType": "rounded"},
}


def _normalize_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, entity in enumerate(entities):
        entity_id = str(entity.get("id") or entity.get("element_id") or f"e{index + 1}")
        type_name = str(entity.get("type_name") or entity.get("type") or "Unknown")
        name = str(entity.get("name") or entity_id)
        normalized.append({"id": entity_id, "type_name": type_name, "name": name, "raw": dict(entity)})
    return normalized


def _sanitize_data_key(key: str) -> str:
    sanitized = "".join(char if (char.isalnum() or char in {"_", "-", "."}) else "_" for char in key.strip())
    if not sanitized:
        sanitized = "attr"
    if sanitized[0].isdigit():
        sanitized = f"k_{sanitized}"
    return sanitized


def _to_data_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _next_unique_key(base_key: str, used_keys: set[str]) -> str:
    key = base_key
    suffix = 2
    while key in used_keys:
        key = f"{base_key}_{suffix}"
        suffix += 1
    used_keys.add(key)
    return key


def _maybe_parse_json_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    candidate = value.strip()
    if not candidate or candidate[0] not in "[{":
        return value
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return value


def _flatten_data(prefix: str, value: Any, out: dict[str, str], used_keys: set[str]) -> None:
    parsed_value = _maybe_parse_json_string(value)

    if isinstance(parsed_value, dict):
        for child_key, child_value in parsed_value.items():
            next_key = f"{prefix}.{_sanitize_data_key(str(child_key))}" if prefix else _sanitize_data_key(str(child_key))
            _flatten_data(next_key, child_value, out, used_keys)
        return

    if isinstance(parsed_value, list):
        if not parsed_value:
            leaf_key = _next_unique_key(prefix or "value", used_keys)
            out[leaf_key] = "[]"
            return
        for index, child_value in enumerate(parsed_value, start=1):
            next_key = f"{prefix}.{index}" if prefix else f"item_{index}"
            _flatten_data(next_key, child_value, out, used_keys)
        return

    base_key = prefix or "value"
    leaf_key = base_key if base_key not in used_keys else _next_unique_key(base_key, used_keys)
    used_keys.add(leaf_key)
    out[leaf_key] = _to_data_value(parsed_value)


def _entity_data_attributes(entity: dict[str, Any]) -> dict[str, str]:
    raw = entity.get("raw", {})
    data_attrs: dict[str, str] = {}
    used_keys: set[str] = set()
    reserved_keys = {"id", "label", "placeholder", "placeholders"}

    if isinstance(raw, dict):
        for original_key, original_value in raw.items():
            key_base = _sanitize_data_key(str(original_key))
            if key_base.endswith("_json"):
                key_base = key_base[:-5] or "data"
            if key_base in reserved_keys:
                key_base = f"data_{key_base}"
            _flatten_data(key_base, original_value, data_attrs, used_keys)

    for required_key, required_value in {
        "element_id": entity.get("id"),
        "type_name": entity.get("type_name"),
        "name": entity.get("name"),
    }.items():
        if required_key not in data_attrs:
            data_attrs[required_key] = _to_data_value(required_value)

    return data_attrs


def _relationship_data_attributes(relationship: dict[str, Any]) -> dict[str, str]:
    raw = relationship.get("raw", {})
    data_attrs: dict[str, str] = {}
    used_keys: set[str] = set()
    reserved_keys = {"id", "label", "placeholder", "placeholders", "source", "target", "value"}

    if isinstance(raw, dict):
        for original_key, original_value in raw.items():
            key_base = _sanitize_data_key(str(original_key))
            if key_base.endswith("_json"):
                key_base = key_base[:-5] or "data"
            if key_base in reserved_keys:
                key_base = f"data_{key_base}"
            _flatten_data(key_base, original_value, data_attrs, used_keys)

    required = {
        "relationship_id": relationship.get("id"),
        "type_name": relationship.get("type_name"),
        "name": relationship.get("name"),
        "source_element_id": relationship.get("source"),
        "target_element_id": relationship.get("target"),
    }
    for required_key, required_value in required.items():
        if required_key not in data_attrs:
            data_attrs[required_key] = _to_data_value(required_value)

    return data_attrs


def _normalize_relationships(relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, relation in enumerate(relationships):
        source = relation.get("source_element_id") or relation.get("source_id") or relation.get("source")
        target = relation.get("target_element_id") or relation.get("target_id") or relation.get("target")
        if not source or not target:
            continue
        relation_id = str(relation.get("id") or relation.get("relationship_id") or f"r{index + 1}")
        type_name = str(relation.get("type_name") or relation.get("type") or "Association")
        name = str(relation.get("name") or type_name)
        normalized.append(
            {
                "id": relation_id,
                "source": str(source),
                "target": str(target),
                "type_name": type_name,
                "name": name,
                "raw": dict(relation),
            }
        )
    return normalized


def _node_style(type_name: str) -> str:
    style_info = ELEMENT_STYLE_MAP.get(type_name)
    if not style_info:
        return "html=1;whiteSpace=wrap;placeholders=1;shape=mxgraph.archimate3.application;appType=generic;archiType=square;"
    parts = [f"html=1;whiteSpace=wrap;placeholders=1;shape={style_info['shape']}"]
    if style_info.get("appType"):
        parts.append(f"appType={style_info['appType']}")
    if style_info.get("archiType"):
        parts.append(f"archiType={style_info['archiType']}")
    return ";".join(parts) + ";"


def _edge_style(type_name: str) -> str:
    rel = type_name.lower()
    if rel in {"composition"}:
        return "html=1;placeholders=1;edgeStyle=orthogonalEdgeStyle;rounded=0;startArrow=diamondThin;startFill=1;endArrow=none;"
    if rel in {"aggregation"}:
        return "html=1;placeholders=1;edgeStyle=orthogonalEdgeStyle;rounded=0;startArrow=diamondThin;startFill=0;endArrow=none;"
    if rel in {"triggering", "flow", "serving", "assignment", "realization"}:
        return "html=1;placeholders=1;edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;"
    if rel in {"access"}:
        return "html=1;placeholders=1;edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=open;endFill=1;"
    return "html=1;placeholders=1;edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=none;"


def _generate_drawio_xml(title: str, entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> str:
    mxfile = ET.Element("mxfile", host="app.diagrams.net", version="28.1.2")
    diagram = ET.SubElement(mxfile, "diagram", name=title or "Page-1", id="archi-diagram")
    graph_model = ET.SubElement(
        diagram,
        "mxGraphModel",
        dx="1360",
        dy="759",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="1600",
        pageHeight="900",
        math="0",
        shadow="0",
    )
    root = ET.SubElement(graph_model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    node_id_by_entity: dict[str, str] = {}
    width, height = 180, 80
    x0, y0 = 80, 80
    x_gap, y_gap = 50, 40
    columns = 5

    for index, entity in enumerate(entities):
        row = index // columns
        col = index % columns
        x = x0 + col * (width + x_gap)
        y = y0 + row * (height + y_gap)
        node_id = f"n{index + 1}"
        node_id_by_entity[entity["id"]] = node_id

        object_attrs = {
            "id": node_id,
            "label": "%name%",
            "placeholders": "1",
        }
        data_attrs = _entity_data_attributes(entity)
        object_attrs.update(data_attrs)

        object_node = ET.SubElement(root, "object", **object_attrs)
        cell = ET.SubElement(
            object_node,
            "mxCell",
            style=_node_style(entity["type_name"]),
            vertex="1",
            parent="1",
        )
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(width), height=str(height), **{"as": "geometry"})

    for index, relation in enumerate(relationships):
        source_node = node_id_by_entity.get(relation["source"])
        target_node = node_id_by_entity.get(relation["target"])
        if not source_node or not target_node:
            continue
        relation_label = relation.get("name") or relation["type_name"]
        edge_id = f"r{index + 1}"
        edge_attrs = {
            "id": edge_id,
            "label": "%name%",
            "placeholders": "1",
        }
        edge_data_attrs = _relationship_data_attributes(relation)
        edge_attrs.update(edge_data_attrs)

        edge_object = ET.SubElement(root, "object", **edge_attrs)
        edge_cell = ET.SubElement(
            edge_object,
            "mxCell",
            style=_edge_style(relation["type_name"]),
            edge="1",
            parent="1",
            source=source_node,
            target=target_node,
        )
        ET.SubElement(edge_cell, "mxGeometry", relative="1", **{"as": "geometry"})

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode")


def _count_object_nodes(drawio_xml: str) -> int:
    try:
        root = ET.fromstring(drawio_xml)
    except ET.ParseError:
        return 0
    return len(root.findall(".//object"))


def _validate_object_only_wrappers(drawio_xml: str) -> tuple[bool, str | None]:
    try:
        mxfile = ET.fromstring(drawio_xml)
    except ET.ParseError as exc:
        return False, f"draw.io XML parse failed: {exc}"

    disallowed = mxfile.findall(".//UserObject")
    if disallowed:
        return False, "draw.io wrapper validation failed: found disallowed <UserObject> nodes; only <object> is allowed."

    root = mxfile.find("./diagram/mxGraphModel/root")
    if root is None:
        return False, "draw.io wrapper validation failed: XML missing /diagram/mxGraphModel/root."

    invalid_children = [child.tag for child in root if child.tag not in {"mxCell", "object"}]
    if invalid_children:
        unique_invalid = sorted(set(invalid_children))
        return (
            False,
            "draw.io wrapper validation failed: root contains disallowed wrapper tag(s): "
            + ", ".join(unique_invalid)
            + "; only <object> and <mxCell> are allowed.",
        )

    return True, None


def _validate_no_duplicate_ids(drawio_xml: str) -> tuple[bool, str | None]:
    """Fail if any two elements in the XML share the same id attribute."""
    try:
        mxfile = ET.fromstring(drawio_xml)
    except ET.ParseError as exc:
        return False, f"draw.io XML parse failed: {exc}"

    seen: dict[str, str] = {}  # id -> tag
    for elem in mxfile.iter():
        elem_id = elem.get("id")
        if elem_id is None:
            continue
        if elem_id in seen:
            return (
                False,
                f"draw.io duplicate ID validation failed: id='{elem_id}' used by both <{seen[elem_id]}> and <{elem.tag}>.",
            )
        seen[elem_id] = elem.tag

    return True, None


def _validate_object_mxcell_structure(drawio_xml: str) -> tuple[bool, str | None]:
    """Fail if an <object> wrapper's child <mxCell> carries id or value attributes."""
    try:
        mxfile = ET.fromstring(drawio_xml)
    except ET.ParseError as exc:
        return False, f"draw.io XML parse failed: {exc}"

    for obj in mxfile.findall(".//object"):
        obj_id = obj.get("id", "?")
        for cell in obj.findall("mxCell"):
            if cell.get("id") is not None:
                return (
                    False,
                    f"draw.io structure validation failed: <mxCell> inside <object id='{obj_id}'> "
                    "must not have its own 'id' attribute; the id belongs on the <object> wrapper.",
                )
            if cell.get("value") is not None:
                return (
                    False,
                    f"draw.io structure validation failed: <mxCell> inside <object id='{obj_id}'> "
                    "must not have a 'value' attribute; the label belongs on the <object> wrapper.",
                )

    return True, None


def _resolve_output_dir() -> Path:
    # `tool.py` is at .../src/mcp/servers/archimate/tools/drawio/tool.py
    # workspace root is 6 levels above this file.
    workspace_root = Path(__file__).resolve().parents[6]
    return workspace_root / "output"


@mcp.tool()
def drawio(
    entities_json: str,
    relationships_json: str = "[]",
    title: str = "ArchiMate Diagram",
    explicit_after_mutation: bool = False,
) -> list[types.TextContent]:
    """Generate draw.io XML from ArchiMate entities and relationships.

    Args:
        entities_json: JSON array of entities. Expected keys per entity: id/element_id, type_name/type, name.
        relationships_json: JSON array of relationships. Expected keys: source_element_id/source_id, target_element_id/target_id, type_name/type.
        title: Draw.io diagram tab title.
        explicit_after_mutation: Must be True when exporting immediately after a write action.
    """
    recent_mutation = get_recent_model_mutation(max_age_seconds=120)
    if recent_mutation and not explicit_after_mutation:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "drawio_guardrail_blocked",
                        "message": (
                            "Draw.io export is blocked right after a model write to prevent unintended side effects. "
                            "If the user explicitly requested this export, call drawio again with explicit_after_mutation=true."
                        ),
                        "recent_mutation": recent_mutation,
                    },
                    ensure_ascii=False,
                ),
            )
        ]

    try:
        entities_raw = json.loads(entities_json)
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: entities_json invalid JSON – {exc}")]

    try:
        relationships_raw = json.loads(relationships_json) if relationships_json else []
    except json.JSONDecodeError as exc:
        return [types.TextContent(type="text", text=f"Error: relationships_json invalid JSON – {exc}")]

    if not isinstance(entities_raw, list) or not entities_raw:
        return [types.TextContent(type="text", text="Error: entities_json must be a non-empty JSON array.")]
    if not isinstance(relationships_raw, list):
        return [types.TextContent(type="text", text="Error: relationships_json must be a JSON array.")]

    entities = [row for row in entities_raw if isinstance(row, dict)]
    relationships = [row for row in relationships_raw if isinstance(row, dict)]
    if not entities:
        return [types.TextContent(type="text", text="Error: entities_json contains no valid objects.")]

    normalized_entities = _normalize_entities(entities)
    normalized_relationships = _normalize_relationships(relationships)
    drawio_xml = _generate_drawio_xml(title=title, entities=normalized_entities, relationships=normalized_relationships)
    wrappers_valid, wrapper_error = _validate_object_only_wrappers(drawio_xml)
    if not wrappers_valid:
        return [types.TextContent(type="text", text=f"Error: {wrapper_error}")]

    ids_valid, id_error = _validate_no_duplicate_ids(drawio_xml)
    if not ids_valid:
        return [types.TextContent(type="text", text=f"Error: {id_error}")]

    structure_valid, structure_error = _validate_object_mxcell_structure(drawio_xml)
    if not structure_valid:
        return [types.TextContent(type="text", text=f"Error: {structure_error}")]

    object_count = _count_object_nodes(drawio_xml)
    minimum_expected_objects = len(normalized_entities) + len(normalized_relationships)
    if object_count < minimum_expected_objects:
        return [
            types.TextContent(
                type="text",
                text=(
                    "Error: draw.io object format validation failed; "
                    f"expected at least {minimum_expected_objects} object nodes, got {object_count}."
                ),
            )
        ]

    # persist to file in workspace output dir
    import datetime

    out_dir = _resolve_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    # sanitize title for filename
    safe_title = "".join(c if (c.isalnum() or c in " -_") else "_" for c in title).strip().replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"drawio_{safe_title}_{timestamp}.drawio"
    filepath = str(out_dir / filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(drawio_xml)
    except Exception:
        # if file write fails we still return the XML but note absence
        filepath = None

    payload = {
        "title": title,
        "entity_count": len(normalized_entities),
        "relationship_count": len(normalized_relationships),
        "shape_data_mode": "object-attributes-v2",
        "object_count": object_count,
        "shape_data_embedded": True,
        "drawio_xml": drawio_xml,
        "stylesheet": ELEMENT_STYLE_MAP,
    }
    if filepath:
        payload["file"] = filepath

    payload["stylesheet_file"] = os.path.join(os.path.dirname(__file__), STATIC_STYLESHEET_FILENAME)

    if explicit_after_mutation:
        clear_recent_model_mutation()

    return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]
