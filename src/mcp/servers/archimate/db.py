"""SQLite store for the ArchiMate 3.2 metamodel."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "archimate_3_2.sqlite"


ELEMENTS: list[dict[str, str]] = [
    {"name": "Resource", "layer": "Strategy", "aspect": "Passive Structure", "definition": "An asset owned or controlled by an organization."},
    {"name": "Capability", "layer": "Strategy", "aspect": "Behavior", "definition": "An ability that an active structure element possesses."},
    {"name": "Value Stream", "layer": "Strategy", "aspect": "Behavior", "definition": "A sequence of activities that creates an overall result for a customer or stakeholder."},
    {"name": "Course of Action", "layer": "Strategy", "aspect": "Active Structure", "definition": "An approach or plan for configuring capabilities and resources."},
    {"name": "Business Actor", "layer": "Business", "aspect": "Active Structure", "definition": "An organizational entity capable of performing behavior."},
    {"name": "Business Role", "layer": "Business", "aspect": "Active Structure", "definition": "The responsibility for performing specific behavior."},
    {"name": "Business Collaboration", "layer": "Business", "aspect": "Active Structure", "definition": "An aggregate of two or more business internal active structure elements."},
    {"name": "Business Interface", "layer": "Business", "aspect": "Active Structure", "definition": "A point of access where business services are made available."},
    {"name": "Business Process", "layer": "Business", "aspect": "Behavior", "definition": "A sequence of business behaviors that achieves a specific result."},
    {"name": "Business Function", "layer": "Business", "aspect": "Behavior", "definition": "A collection of business behavior based on a chosen set of criteria."},
    {"name": "Business Interaction", "layer": "Business", "aspect": "Behavior", "definition": "A unit of behavior performed by a collaboration of two or more roles."},
    {"name": "Business Event", "layer": "Business", "aspect": "Behavior", "definition": "A business behavior element that denotes a state change."},
    {"name": "Business Service", "layer": "Business", "aspect": "Behavior", "definition": "Explicitly defined business behavior exposed to the environment."},
    {"name": "Business Object", "layer": "Business", "aspect": "Passive Structure", "definition": "A concept used within a particular business domain."},
    {"name": "Contract", "layer": "Business", "aspect": "Passive Structure", "definition": "A formal or informal specification of an agreement."},
    {"name": "Representation", "layer": "Business", "aspect": "Passive Structure", "definition": "A perceptible form of the information carried by a business object."},
    {"name": "Product", "layer": "Business", "aspect": "Composite", "definition": "A coherent collection of services and associated contract/value offered as a whole."},
    {"name": "Application Component", "layer": "Application", "aspect": "Active Structure", "definition": "A modular, deployable, and replaceable part of a software system."},
    {"name": "Application Collaboration", "layer": "Application", "aspect": "Active Structure", "definition": "An aggregate of two or more application components that work together."},
    {"name": "Application Interface", "layer": "Application", "aspect": "Active Structure", "definition": "A point of access where application services are made available."},
    {"name": "Application Function", "layer": "Application", "aspect": "Behavior", "definition": "Automated behavior that can be performed by an application component."},
    {"name": "Application Interaction", "layer": "Application", "aspect": "Behavior", "definition": "A unit of collective application behavior performed by a collaboration."},
    {"name": "Application Process", "layer": "Application", "aspect": "Behavior", "definition": "A sequence of application behavior that achieves a specific result."},
    {"name": "Application Event", "layer": "Application", "aspect": "Behavior", "definition": "An application behavior element that denotes a state change."},
    {"name": "Application Service", "layer": "Application", "aspect": "Behavior", "definition": "An explicitly defined exposed application behavior."},
    {"name": "Data Object", "layer": "Application", "aspect": "Passive Structure", "definition": "Data suitable for automated processing."},
    {"name": "Node", "layer": "Technology", "aspect": "Active Structure", "definition": "A computational or physical resource that hosts software or artifacts."},
    {"name": "Device", "layer": "Technology", "aspect": "Active Structure", "definition": "A physical IT resource upon which artifacts can be deployed."},
    {"name": "System Software", "layer": "Technology", "aspect": "Active Structure", "definition": "A software environment for specific types of components and objects."},
    {"name": "Technology Collaboration", "layer": "Technology", "aspect": "Active Structure", "definition": "An aggregate of two or more internal active structure technology elements."},
    {"name": "Technology Interface", "layer": "Technology", "aspect": "Active Structure", "definition": "A point of access where technology services are made available."},
    {"name": "Path", "layer": "Technology", "aspect": "Active Structure", "definition": "A link between two or more nodes through which data or material can flow."},
    {"name": "Communication Network", "layer": "Technology", "aspect": "Active Structure", "definition": "A set of structures that connects nodes for transmission."},
    {"name": "Technology Function", "layer": "Technology", "aspect": "Behavior", "definition": "A collection of technology behavior based on a chosen set of criteria."},
    {"name": "Technology Process", "layer": "Technology", "aspect": "Behavior", "definition": "A sequence of technology behavior that achieves a specific result."},
    {"name": "Technology Interaction", "layer": "Technology", "aspect": "Behavior", "definition": "A unit of collective technology behavior performed by collaboration."},
    {"name": "Technology Event", "layer": "Technology", "aspect": "Behavior", "definition": "A technology behavior element that denotes a state change."},
    {"name": "Technology Service", "layer": "Technology", "aspect": "Behavior", "definition": "An explicitly defined exposed technology behavior."},
    {"name": "Artifact", "layer": "Technology", "aspect": "Passive Structure", "definition": "A physical piece of data that can be used or produced in development/deployment."},
    {"name": "Equipment", "layer": "Physical", "aspect": "Active Structure", "definition": "One or more physical machines, tools, or instruments."},
    {"name": "Facility", "layer": "Physical", "aspect": "Active Structure", "definition": "A physical structure or environment."},
    {"name": "Distribution Network", "layer": "Physical", "aspect": "Active Structure", "definition": "A physical network used to transport materials or energy."},
    {"name": "Material", "layer": "Physical", "aspect": "Passive Structure", "definition": "Tangible physical matter or energy."},
    {"name": "Stakeholder", "layer": "Motivation", "aspect": "Motivation", "definition": "A role of an individual, team, or organization representing interests."},
    {"name": "Driver", "layer": "Motivation", "aspect": "Motivation", "definition": "An internal or external condition that motivates change."},
    {"name": "Assessment", "layer": "Motivation", "aspect": "Motivation", "definition": "The outcome of an analysis of a state of affairs."},
    {"name": "Goal", "layer": "Motivation", "aspect": "Motivation", "definition": "A high-level statement of intent, direction, or desired end state."},
    {"name": "Outcome", "layer": "Motivation", "aspect": "Motivation", "definition": "An end result produced by behavior or capabilities."},
    {"name": "Principle", "layer": "Motivation", "aspect": "Motivation", "definition": "A qualitative statement of intent to guide behavior and design."},
    {"name": "Requirement", "layer": "Motivation", "aspect": "Motivation", "definition": "A statement of need that must be realized by a system."},
    {"name": "Constraint", "layer": "Motivation", "aspect": "Motivation", "definition": "A restriction on how a system is realized or behavior is performed."},
    {"name": "Meaning", "layer": "Motivation", "aspect": "Motivation", "definition": "The knowledge or expertise present in a concept."},
    {"name": "Value", "layer": "Motivation", "aspect": "Motivation", "definition": "The relative worth, utility, or importance of a concept."},
    {"name": "Work Package", "layer": "Implementation & Migration", "aspect": "Behavior", "definition": "A series of actions identified and designed to achieve specific results."},
    {"name": "Deliverable", "layer": "Implementation & Migration", "aspect": "Passive Structure", "definition": "A precisely-defined outcome of a work package."},
    {"name": "Implementation Event", "layer": "Implementation & Migration", "aspect": "Behavior", "definition": "A state change related to implementation or migration."},
    {"name": "Plateau", "layer": "Implementation & Migration", "aspect": "Passive Structure", "definition": "A relatively stable state of architecture at a point in time."},
    {"name": "Gap", "layer": "Implementation & Migration", "aspect": "Passive Structure", "definition": "A statement of difference between two plateaus."},
    {"name": "Location", "layer": "Cross-Layer", "aspect": "Composite", "definition": "A conceptual or physical place where structure elements can be assigned."},
    {"name": "Grouping", "layer": "Cross-Layer", "aspect": "Composite", "definition": "An arbitrary aggregation of concepts for convenience."},
    {"name": "Junction", "layer": "Cross-Layer", "aspect": "Relationship Connector", "definition": "A connector used to model logical AND/OR combinations of relationships."},
]


RELATIONSHIPS: list[dict[str, object]] = [
    {"name": "Composition", "category": "Structural", "directed": 1, "definition": "Indicates that an element consists of one or more other concepts.", "constraints": ["Strong whole-part relation", "Part typically has one composite"]},
    {"name": "Aggregation", "category": "Structural", "directed": 1, "definition": "Indicates that an element groups one or more other concepts.", "constraints": ["Weak whole-part relation"]},
    {"name": "Assignment", "category": "Structural", "directed": 1, "definition": "Links active structure elements to behavior they perform, own, or are responsible for.", "constraints": ["Commonly between active structure and behavior"]},
    {"name": "Realization", "category": "Structural", "directed": 1, "definition": "Indicates that one concept makes another concept real.", "constraints": ["From concrete/implementation to abstract/specification"]},
    {"name": "Serving", "category": "Dependency", "directed": 1, "definition": "Indicates that an element provides functionality to another element.", "constraints": ["Also known as Used-By inverse"]},
    {"name": "Access", "category": "Dependency", "directed": 1, "definition": "Indicates ability of behavior/active elements to read and/or write passive structure elements.", "constraints": ["Access type is read, write, or readwrite"]},
    {"name": "Influence", "category": "Dependency", "directed": 1, "definition": "Indicates that an element affects implementation or achievement of another element.", "constraints": ["Influence strength can be qualitative or quantitative"]},
    {"name": "Triggering", "category": "Dynamic", "directed": 1, "definition": "Indicates temporal or causal precedence between elements.", "constraints": ["Often between behavior and events/behavior"]},
    {"name": "Flow", "category": "Dynamic", "directed": 1, "definition": "Indicates transfer from one element to another.", "constraints": ["Can represent information, value, or material transfer"]},
    {"name": "Specialization", "category": "Other", "directed": 1, "definition": "Indicates that one element is a more specific form of another.", "constraints": ["Inherits properties from generic element"]},
    {"name": "Association", "category": "Other", "directed": 0, "definition": "A generic relationship between elements not covered by other relation types.", "constraints": ["May be directed or undirected"]},
]


RULES: list[dict[str, str]] = [
    {"rule_type": "layering", "source": "Business", "relationship": "Serving", "target": "Application", "notes": "Application services may serve business behavior/elements."},
    {"rule_type": "layering", "source": "Application", "relationship": "Serving", "target": "Technology", "notes": "Technology services may serve application behavior/elements."},
    {"rule_type": "structural", "source": "Active Structure", "relationship": "Assignment", "target": "Behavior", "notes": "Active structure elements can be assigned to behavior."},
    {"rule_type": "structural", "source": "Behavior", "relationship": "Access", "target": "Passive Structure", "notes": "Behavior can access passive structure elements."},
    {"rule_type": "motivation", "source": "Driver", "relationship": "Influence", "target": "Goal", "notes": "Drivers can influence goals and requirements."},
    {"rule_type": "implementation", "source": "Work Package", "relationship": "Realization", "target": "Deliverable", "notes": "Work packages realize deliverables."},
]


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metamodel_info (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS elements (
                name TEXT PRIMARY KEY,
                layer TEXT NOT NULL,
                aspect TEXT NOT NULL,
                definition TEXT NOT NULL,
                attributes_json TEXT NOT NULL,
                constraints_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relationships (
                name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                directed INTEGER NOT NULL,
                definition TEXT NOT NULL,
                attributes_json TEXT NOT NULL,
                constraints_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metamodel_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                source TEXT NOT NULL,
                relationship TEXT NOT NULL,
                target TEXT NOT NULL,
                notes TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metamodel_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                target_name TEXT NOT NULL,
                note TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_rule_unique
            ON metamodel_rules(rule_type, source, relationship, target, notes)
            """
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metamodel_info(key, value)
            VALUES (?, ?)
            """,
            ("version", "3.2"),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO metamodel_info(key, value)
            VALUES (?, ?)
            """,
            ("description", "ArchiMate metamodel reference dataset for MCP usage."),
        )

        for element in ELEMENTS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO elements(name, layer, aspect, definition, attributes_json, constraints_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    element["name"],
                    element["layer"],
                    element["aspect"],
                    element["definition"],
                    json.dumps({"name": "string", "layer": "string", "aspect": "string", "definition": "string"}),
                    json.dumps([]),
                ),
            )

        for relationship in RELATIONSHIPS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO relationships(name, category, directed, definition, attributes_json, constraints_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    relationship["name"],
                    relationship["category"],
                    relationship["directed"],
                    relationship["definition"],
                    json.dumps({"name": "string", "category": "string", "directed": "boolean", "definition": "string"}),
                    json.dumps(relationship.get("constraints", [])),
                ),
            )

        for rule in RULES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO metamodel_rules(rule_type, source, relationship, target, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rule["rule_type"], rule["source"], rule["relationship"], rule["target"], rule["notes"]),
            )

        connection.commit()


def upsert_element(
    name: str,
    layer: str,
    aspect: str,
    definition: str,
    attributes: dict[str, Any] | None = None,
    constraints: list[Any] | None = None,
) -> str:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM elements WHERE lower(name)=lower(?)", (name,))
        exists = cursor.fetchone() is not None
        cursor.execute(
            """
            INSERT OR REPLACE INTO elements(name, layer, aspect, definition, attributes_json, constraints_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                layer,
                aspect,
                definition,
                json.dumps(attributes or {}, ensure_ascii=False),
                json.dumps(constraints or [], ensure_ascii=False),
            ),
        )
        connection.commit()
    return "updated" if exists else "created"


def upsert_relationship(
    name: str,
    category: str,
    directed: bool,
    definition: str,
    attributes: dict[str, Any] | None = None,
    constraints: list[Any] | None = None,
) -> str:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM relationships WHERE lower(name)=lower(?)", (name,))
        exists = cursor.fetchone() is not None
        cursor.execute(
            """
            INSERT OR REPLACE INTO relationships(name, category, directed, definition, attributes_json, constraints_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                category,
                int(bool(directed)),
                definition,
                json.dumps(attributes or {}, ensure_ascii=False),
                json.dumps(constraints or [], ensure_ascii=False),
            ),
        )
        connection.commit()
    return "updated" if exists else "created"


def add_rule(rule_type: str, source: str, relationship: str, target: str, notes: str) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO metamodel_rules(rule_type, source, relationship, target, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rule_type, source, relationship, target, notes),
        )
        connection.commit()
        if cursor.rowcount == 0:
            cursor.execute(
                """
                SELECT id FROM metamodel_rules
                WHERE rule_type=? AND source=? AND relationship=? AND target=? AND notes=?
                """,
                (rule_type, source, relationship, target, notes),
            )
            row = cursor.fetchone()
            return int(row[0])
        return int(cursor.lastrowid)


def add_annotation(target_type: str, target_name: str, note: str, source: str = "user") -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO metamodel_annotations(target_type, target_name, note, source)
            VALUES (?, ?, ?, ?)
            """,
            (target_type, target_name, note, source),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_annotations(target_type: str | None = None, target_name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with get_connection() as connection:
        cursor = connection.cursor()
        sql = "SELECT id, target_type, target_name, note, source, created_at FROM metamodel_annotations"
        clauses = []
        params: list[Any] = []
        if target_type:
            clauses.append("lower(target_type) = lower(?)")
            params.append(target_type)
        if target_name:
            clauses.append("lower(target_name) = lower(?)")
            params.append(target_name)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def delete_annotation(
    annotation_id: int | None = None,
    target_type: str | None = None,
    target_name: str | None = None,
    note: str | None = None,
    source: str | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        if annotation_id is not None:
            cursor.execute("DELETE FROM metamodel_annotations WHERE id = ?", (int(annotation_id),))
            connection.commit()
            return int(cursor.rowcount)

        clauses = []
        params: list[Any] = []
        if target_type:
            clauses.append("lower(target_type) = lower(?)")
            params.append(target_type)
        if target_name:
            clauses.append("lower(target_name) = lower(?)")
            params.append(target_name)
        if note:
            clauses.append("note = ?")
            params.append(note)
        if source:
            clauses.append("lower(source) = lower(?)")
            params.append(source)

        if not clauses:
            return 0

        sql = "DELETE FROM metamodel_annotations WHERE " + " AND ".join(clauses)
        cursor.execute(sql, params)
        connection.commit()
        return int(cursor.rowcount)


def delete_rule(
    rule_id: int | None = None,
    rule_type: str | None = None,
    source: str | None = None,
    relationship: str | None = None,
    target: str | None = None,
    notes: str | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        if rule_id is not None:
            cursor.execute("DELETE FROM metamodel_rules WHERE id = ?", (int(rule_id),))
            connection.commit()
            return int(cursor.rowcount)

        clauses = []
        params: list[Any] = []
        if rule_type:
            clauses.append("lower(rule_type) = lower(?)")
            params.append(rule_type)
        if source:
            clauses.append("lower(source) = lower(?)")
            params.append(source)
        if relationship:
            clauses.append("lower(relationship) = lower(?)")
            params.append(relationship)
        if target:
            clauses.append("lower(target) = lower(?)")
            params.append(target)
        if notes:
            clauses.append("notes = ?")
            params.append(notes)

        if not clauses:
            return 0

        sql = "DELETE FROM metamodel_rules WHERE " + " AND ".join(clauses)
        cursor.execute(sql, params)
        connection.commit()
        return int(cursor.rowcount)
