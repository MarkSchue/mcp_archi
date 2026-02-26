"""SQLite model-management store for ArchiMate models."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

EXPORTS_DIR = Path("/home/markus/Workspace/mcp_archi/exports")
DATA_DIR = Path(__file__).parent / "data"
MODEL_DB_PATH = DATA_DIR / "archimate_models.sqlite"


class ModelError(Exception):
    """Domain-level error for model management operations."""


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(MODEL_DB_PATH)


def init_model_db() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                attributes_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                current_version INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                author TEXT NOT NULL DEFAULT 'system',
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                snapshot_json TEXT NOT NULL,
                UNIQUE(model_id, version),
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_elements (
                model_id TEXT NOT NULL,
                id TEXT NOT NULL,
                type_name TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                attributes_json TEXT NOT NULL DEFAULT '{}',
                valid_from TEXT,
                valid_to TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(model_id, id),
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_relationships (
                model_id TEXT NOT NULL,
                id TEXT NOT NULL,
                type_name TEXT NOT NULL,
                source_element_id TEXT NOT NULL,
                target_element_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                attributes_json TEXT NOT NULL DEFAULT '{}',
                valid_from TEXT,
                valid_to TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(model_id, id),
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        # dictionary of allowed custom attributes per model
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_attribute_definitions (
                model_id TEXT NOT NULL,
                target_type TEXT NOT NULL CHECK(target_type IN ('element','relationship')),
                key TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                is_tag INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(model_id, target_type, key),
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        # --- schema migrations for tables that may already exist ---
        for migration in (
            "ALTER TABLE model_attribute_definitions ADD COLUMN is_tag INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE model_elements ADD COLUMN tags_json TEXT NOT NULL DEFAULT '{}'",
            "ALTER TABLE model_relationships ADD COLUMN tags_json TEXT NOT NULL DEFAULT '{}'",
        ):
            try:
                cursor.execute(migration)
            except Exception:
                pass  # column already exists; SQLite does not support IF NOT EXISTS on ALTER
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_locks (
                model_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                acquired_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_elements_type ON model_elements(model_id, type_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_relationships_type ON model_relationships(model_id, type_name)")
        connection.commit()


def _row_dicts(cursor) -> list[dict[str, Any]]:
    cols = [col[0] for col in cursor.description]
    rows = []
    for row in cursor.fetchall():
        data = dict(zip(cols, row))
        for json_key in ("attributes_json", "tags_json"):
            if json_key in data and isinstance(data[json_key], str):
                try:
                    data[json_key.replace("_json", "")] = json.loads(data[json_key])
                except json.JSONDecodeError:
                    data[json_key.replace("_json", "")] = {}
                del data[json_key]
        rows.append(data)
    return rows


def _get_model_row(connection, model_id: str) -> dict[str, Any] | None:
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
    rows = _row_dicts(cursor)
    return rows[0] if rows else None


def _ensure_model_exists(connection, model_id: str) -> dict[str, Any]:
    model = _get_model_row(connection, model_id)
    if not model:
        raise ModelError(f"Model '{model_id}' not found")
    return model


def _ensure_expected_version(connection, model_id: str, expected_version: int | None) -> None:
    if expected_version is None:
        return
    cursor = connection.cursor()
    cursor.execute("SELECT current_version FROM models WHERE id = ?", (model_id,))
    row = cursor.fetchone()
    if not row:
        raise ModelError(f"Model '{model_id}' not found")
    current_version = int(row[0])
    if int(expected_version) != current_version:
        raise ModelError(
            f"Version conflict: expected {expected_version}, but current version is {current_version}"
        )


def _snapshot(connection, model_id: str) -> dict[str, Any]:
    model = _ensure_model_exists(connection, model_id)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM model_elements WHERE model_id = ? ORDER BY id", (model_id,))
    elements = _row_dicts(cursor)
    cursor.execute("SELECT * FROM model_relationships WHERE model_id = ? ORDER BY id", (model_id,))
    relationships = _row_dicts(cursor)
    return {
        "model": model,
        "elements": elements,
        "relationships": relationships,
    }


def _create_version(connection, model_id: str, author: str, message: str) -> int:
    cursor = connection.cursor()
    cursor.execute("SELECT current_version FROM models WHERE id = ?", (model_id,))
    row = cursor.fetchone()
    if not row:
        raise ModelError(f"Model '{model_id}' not found")

    next_version = int(row[0]) + 1
    snapshot_json = json.dumps(_snapshot(connection, model_id), ensure_ascii=False)

    cursor.execute(
        """
        INSERT INTO model_versions(model_id, version, author, message, snapshot_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (model_id, next_version, author or "system", message or "" , snapshot_json),
    )
    cursor.execute(
        """
        UPDATE models
        SET current_version = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (next_version, model_id),
    )
    return next_version


def create_model(
    name: str,
    description: str = "",
    attributes: dict[str, Any] | None = None,
    model_id: str | None = None,
    author: str = "system",
) -> dict[str, Any]:
    model_id = model_id or str(uuid.uuid4())
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM models WHERE id = ?", (model_id,))
        if cursor.fetchone():
            raise ModelError(f"Model id '{model_id}' already exists")

        cursor.execute(
            """
            INSERT INTO models(id, name, description, attributes_json)
            VALUES (?, ?, ?, ?)
            """,
            (model_id, name, description, json.dumps(attributes or {}, ensure_ascii=False)),
        )
        version = _create_version(connection, model_id, author, "Model created")
        connection.commit()

        return get_model(model_id, include_graph=False) | {"version": version}


def list_models(limit: int = 100, search: str | None = None) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with get_connection() as connection:
        cursor = connection.cursor()
        sql = "SELECT * FROM models"
        params: list[Any] = []
        if search:
            sql += " WHERE lower(name) LIKE lower(?) OR lower(description) LIKE lower(?)"
            like = f"%{search}%"
            params.extend([like, like])
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        return _row_dicts(cursor)


def get_model(model_id: str, include_graph: bool = True) -> dict[str, Any]:
    with get_connection() as connection:
        model = _ensure_model_exists(connection, model_id)
        if not include_graph:
            return model
        snapshot = _snapshot(connection, model_id)
        return {
            **model,
            "elements": snapshot["elements"],
            "relationships": snapshot["relationships"],
        }


def update_model(
    model_id: str,
    name: str | None = None,
    description: str | None = None,
    attributes: dict[str, Any] | None = None,
    expected_version: int | None = None,
    author: str = "system",
    message: str = "Model updated",
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)

        fields = []
        params: list[Any] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if attributes is not None:
            fields.append("attributes_json = ?")
            params.append(json.dumps(attributes, ensure_ascii=False))

        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            sql = "UPDATE models SET " + ", ".join(fields) + " WHERE id = ?"
            params.append(model_id)
            connection.cursor().execute(sql, params)

        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return get_model(model_id, include_graph=False) | {"version": version}


def delete_model(model_id: str) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        connection.commit()
        return int(cursor.rowcount)


def upsert_model_element(
    model_id: str,
    type_name: str,
    name: str,
    element_id: str | None = None,
    attributes: dict[str, Any] | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
    expected_version: int | None = None,
    author: str = "system",
    message: str = "Element upserted",
) -> dict[str, Any]:
    element_id = element_id or str(uuid.uuid4())
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)

        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM model_elements WHERE model_id = ? AND id = ?", (model_id, element_id))
        exists = cursor.fetchone() is not None
        cursor.execute(
            """
            INSERT OR REPLACE INTO model_elements(model_id, id, type_name, name, attributes_json, tags_json, valid_from, valid_to, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT tags_json FROM model_elements WHERE model_id=? AND id=?), '{}'), ?, ?, COALESCE((SELECT created_at FROM model_elements WHERE model_id=? AND id=?), CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
            """,
            (
                model_id,
                element_id,
                type_name,
                name,
                json.dumps(attributes or {}, ensure_ascii=False),
                model_id,
                element_id,
                valid_from,
                valid_to,
                model_id,
                element_id,
            ),
        )
        version = _create_version(connection, model_id, author, message)
        connection.commit()

        return {
            "status": "updated" if exists else "created",
            "model_id": model_id,
            "element_id": element_id,
            "version": version,
        }


def delete_model_element(
    model_id: str,
    element_id: str,
    expected_version: int | None = None,
    author: str = "system",
    message: str = "Element deleted",
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)

        cursor = connection.cursor()
        cursor.execute("DELETE FROM model_relationships WHERE model_id = ? AND (source_element_id = ? OR target_element_id = ?)", (model_id, element_id, element_id))
        rel_deleted = int(cursor.rowcount)
        cursor.execute("DELETE FROM model_elements WHERE model_id = ? AND id = ?", (model_id, element_id))
        elem_deleted = int(cursor.rowcount)
        if elem_deleted == 0:
            raise ModelError(f"Element '{element_id}' not found in model '{model_id}'")

        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {
            "status": "deleted",
            "model_id": model_id,
            "element_id": element_id,
            "relationships_deleted": rel_deleted,
            "version": version,
        }


def list_model_elements(
    model_id: str,
    type_name: str | None = None,
    search: str | None = None,
    valid_at: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 1000))
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        sql = "SELECT * FROM model_elements WHERE model_id = ?"
        params: list[Any] = [model_id]
        if type_name:
            sql += " AND lower(type_name)=lower(?)"
            params.append(type_name)
        if search:
            sql += " AND (lower(id) LIKE lower(?) OR lower(name) LIKE lower(?))"
            like = f"%{search}%"
            params.extend([like, like])
        if valid_at:
            sql += " AND (valid_from IS NULL OR valid_from <= ?) AND (valid_to IS NULL OR valid_to >= ?)"
            params.extend([valid_at, valid_at])
        sql += " ORDER BY id LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        return _row_dicts(cursor)


def upsert_model_relationship(
    model_id: str,
    type_name: str,
    source_element_id: str,
    target_element_id: str,
    relationship_id: str | None = None,
    name: str = "",
    attributes: dict[str, Any] | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
    expected_version: int | None = None,
    author: str = "system",
    message: str = "Relationship upserted",
) -> dict[str, Any]:
    relationship_id = relationship_id or str(uuid.uuid4())
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)

        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM model_elements WHERE model_id=? AND id=?", (model_id, source_element_id))
        if cursor.fetchone() is None:
            raise ModelError(f"Source element '{source_element_id}' not found in model '{model_id}'")
        cursor.execute("SELECT 1 FROM model_elements WHERE model_id=? AND id=?", (model_id, target_element_id))
        if cursor.fetchone() is None:
            raise ModelError(f"Target element '{target_element_id}' not found in model '{model_id}'")

        cursor.execute("SELECT 1 FROM model_relationships WHERE model_id = ? AND id = ?", (model_id, relationship_id))
        exists = cursor.fetchone() is not None
        cursor.execute(
            """
            INSERT OR REPLACE INTO model_relationships(model_id, id, type_name, source_element_id, target_element_id, name, attributes_json, tags_json, valid_from, valid_to, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT tags_json FROM model_relationships WHERE model_id=? AND id=?), '{}'), ?, ?, COALESCE((SELECT created_at FROM model_relationships WHERE model_id=? AND id=?), CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
            """,
            (
                model_id,
                relationship_id,
                type_name,
                source_element_id,
                target_element_id,
                name,
                json.dumps(attributes or {}, ensure_ascii=False),
                model_id,
                relationship_id,
                valid_from,
                valid_to,
                model_id,
                relationship_id,
            ),
        )

        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {
            "status": "updated" if exists else "created",
            "model_id": model_id,
            "relationship_id": relationship_id,
            "version": version,
        }


def delete_model_relationship(
    model_id: str,
    relationship_id: str,
    expected_version: int | None = None,
    author: str = "system",
    message: str = "Relationship deleted",
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM model_relationships WHERE model_id = ? AND id = ?", (model_id, relationship_id))
        deleted = int(cursor.rowcount)
        if deleted == 0:
            raise ModelError(f"Relationship '{relationship_id}' not found in model '{model_id}'")
        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {
            "status": "deleted",
            "model_id": model_id,
            "relationship_id": relationship_id,
            "version": version,
        }


def list_model_relationships(
    model_id: str,
    type_name: str | None = None,
    source_element_id: str | None = None,
    target_element_id: str | None = None,
    valid_at: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 1000))
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        sql = "SELECT * FROM model_relationships WHERE model_id = ?"
        params: list[Any] = [model_id]
        if type_name:
            sql += " AND lower(type_name)=lower(?)"
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
        return _row_dicts(cursor)


def list_versions(model_id: str, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 1000))
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, model_id, version, author, message, created_at
            FROM model_versions
            WHERE model_id = ?
            ORDER BY version DESC
            LIMIT ?
            """,
            (model_id, limit),
        )
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_version(model_id: str, version: int) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, model_id, version, author, message, created_at, snapshot_json
            FROM model_versions
            WHERE model_id = ? AND version = ?
            """,
            (model_id, int(version)),
        )
        row = cursor.fetchone()
        if not row:
            raise ModelError(f"Version {version} not found for model '{model_id}'")
        return {
            "id": row[0],
            "model_id": row[1],
            "version": row[2],
            "author": row[3],
            "message": row[4],
            "created_at": row[5],
            "snapshot": json.loads(row[6]),
        }


def revert_to_version(
    model_id: str,
    version: int,
    expected_version: int | None = None,
    author: str = "system",
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)
        version_data = get_version(model_id, version)
        snapshot = version_data["snapshot"]

        cursor = connection.cursor()
        cursor.execute("DELETE FROM model_elements WHERE model_id = ?", (model_id,))
        cursor.execute("DELETE FROM model_relationships WHERE model_id = ?", (model_id,))

        model = snapshot.get("model", {})
        cursor.execute(
            """
            UPDATE models
            SET name = ?, description = ?, attributes_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                model.get("name", ""),
                model.get("description", ""),
                json.dumps(model.get("attributes", {}), ensure_ascii=False),
                model_id,
            ),
        )

        for element in snapshot.get("elements", []):
            cursor.execute(
                """
                INSERT INTO model_elements(model_id, id, type_name, name, attributes_json, valid_from, valid_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    element["id"],
                    element["type_name"],
                    element.get("name", ""),
                    json.dumps(element.get("attributes", {}), ensure_ascii=False),
                    element.get("valid_from"),
                    element.get("valid_to"),
                ),
            )

        for relationship in snapshot.get("relationships", []):
            cursor.execute(
                """
                INSERT INTO model_relationships(model_id, id, type_name, source_element_id, target_element_id, name, attributes_json, valid_from, valid_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    relationship["id"],
                    relationship["type_name"],
                    relationship["source_element_id"],
                    relationship["target_element_id"],
                    relationship.get("name", ""),
                    json.dumps(relationship.get("attributes", {}), ensure_ascii=False),
                    relationship.get("valid_from"),
                    relationship.get("valid_to"),
                ),
            )

        new_version = _create_version(connection, model_id, author, f"Reverted to version {version}")
        connection.commit()
        return {"status": "reverted", "model_id": model_id, "from_version": int(version), "version": new_version}


def validate_model(model_id: str) -> dict[str, Any]:
    with get_connection() as connection:
        model = _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()

        cursor.execute("SELECT id, type_name, valid_from, valid_to FROM model_elements WHERE model_id = ?", (model_id,))
        elements = cursor.fetchall()
        element_ids = {row[0] for row in elements}

        cursor.execute("SELECT name FROM elements")
        known_element_types = {row[0].lower() for row in cursor.fetchall()}

        cursor.execute("SELECT id, type_name, source_element_id, target_element_id, valid_from, valid_to FROM model_relationships WHERE model_id = ?", (model_id,))
        relationships = cursor.fetchall()

        cursor.execute("SELECT name FROM relationships")
        known_relationship_types = {row[0].lower() for row in cursor.fetchall()}

        issues: list[dict[str, Any]] = []

        for element_id, type_name, valid_from, valid_to in elements:
            if type_name.lower() not in known_element_types:
                issues.append(
                    {
                        "severity": "error",
                        "code": "UNKNOWN_ELEMENT_TYPE",
                        "message": f"Element '{element_id}' uses unknown type '{type_name}'",
                        "element_id": element_id,
                    }
                )
            if valid_from and valid_to and valid_from > valid_to:
                issues.append(
                    {
                        "severity": "error",
                        "code": "INVALID_ELEMENT_TIME_RANGE",
                        "message": f"Element '{element_id}' has valid_from later than valid_to",
                        "element_id": element_id,
                    }
                )

        elem_time = {row[0]: (row[2], row[3]) for row in elements}

        for rel_id, type_name, src, tgt, valid_from, valid_to in relationships:
            if type_name.lower() not in known_relationship_types:
                issues.append(
                    {
                        "severity": "error",
                        "code": "UNKNOWN_RELATIONSHIP_TYPE",
                        "message": f"Relationship '{rel_id}' uses unknown type '{type_name}'",
                        "relationship_id": rel_id,
                    }
                )
            if src not in element_ids or tgt not in element_ids:
                issues.append(
                    {
                        "severity": "error",
                        "code": "MISSING_REL_ENDPOINT",
                        "message": f"Relationship '{rel_id}' references missing endpoint(s): source={src}, target={tgt}",
                        "relationship_id": rel_id,
                    }
                )
            if valid_from and valid_to and valid_from > valid_to:
                issues.append(
                    {
                        "severity": "error",
                        "code": "INVALID_REL_TIME_RANGE",
                        "message": f"Relationship '{rel_id}' has valid_from later than valid_to",
                        "relationship_id": rel_id,
                    }
                )
            if src in elem_time and tgt in elem_time and valid_from:
                src_from, src_to = elem_time[src]
                tgt_from, tgt_to = elem_time[tgt]
                if src_from and valid_from < src_from:
                    issues.append(
                        {
                            "severity": "warning",
                            "code": "REL_BEFORE_SOURCE",
                            "message": f"Relationship '{rel_id}' starts before source element validity",
                            "relationship_id": rel_id,
                        }
                    )
                if tgt_from and valid_from < tgt_from:
                    issues.append(
                        {
                            "severity": "warning",
                            "code": "REL_BEFORE_TARGET",
                            "message": f"Relationship '{rel_id}' starts before target element validity",
                            "relationship_id": rel_id,
                        }
                    )
                if valid_to and src_to and valid_to > src_to:
                    issues.append(
                        {
                            "severity": "warning",
                            "code": "REL_AFTER_SOURCE",
                            "message": f"Relationship '{rel_id}' ends after source element validity",
                            "relationship_id": rel_id,
                        }
                    )
                if valid_to and tgt_to and valid_to > tgt_to:
                    issues.append(
                        {
                            "severity": "warning",
                            "code": "REL_AFTER_TARGET",
                            "message": f"Relationship '{rel_id}' ends after target element validity",
                            "relationship_id": rel_id,
                        }
                    )

        error_count = sum(1 for issue in issues if issue["severity"] == "error")
        warning_count = len(issues) - error_count

        return {
            "model_id": model["id"],
            "model_name": model["name"],
            "is_valid": error_count == 0,
            "summary": {
                "elements": len(elements),
                "relationships": len(relationships),
                "errors": error_count,
                "warnings": warning_count,
            },
            "issues": issues,
        }


def generate_report(model_id: str) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT me.type_name, COUNT(*)
            FROM model_elements me
            WHERE me.model_id = ?
            GROUP BY me.type_name
            ORDER BY COUNT(*) DESC, me.type_name
            """,
            (model_id,),
        )
        element_type_counts = [{"type": row[0], "count": row[1]} for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT mr.type_name, COUNT(*)
            FROM model_relationships mr
            WHERE mr.model_id = ?
            GROUP BY mr.type_name
            ORDER BY COUNT(*) DESC, mr.type_name
            """,
            (model_id,),
        )
        relationship_type_counts = [{"type": row[0], "count": row[1]} for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT COALESCE(e.layer, 'Unknown') AS layer, COUNT(*)
            FROM model_elements me
            LEFT JOIN elements e ON lower(e.name) = lower(me.type_name)
            WHERE me.model_id = ?
            GROUP BY COALESCE(e.layer, 'Unknown')
            ORDER BY COUNT(*) DESC, layer
            """,
            (model_id,),
        )
        layer_counts = [{"layer": row[0], "count": row[1]} for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM model_elements WHERE model_id = ?", (model_id,))
        element_total = int(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM model_relationships WHERE model_id = ?", (model_id,))
        relationship_total = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT id, name
            FROM model_elements
            WHERE model_id = ?
            """,
            (model_id,),
        )
        elements = cursor.fetchall()
        degree = {row[0]: 0 for row in elements}

        cursor.execute(
            """
            SELECT source_element_id, target_element_id
            FROM model_relationships
            WHERE model_id = ?
            """,
            (model_id,),
        )
        for source_element_id, target_element_id in cursor.fetchall():
            if source_element_id in degree:
                degree[source_element_id] += 1
            if target_element_id in degree:
                degree[target_element_id] += 1

        top_connected = sorted(
            (
                {"element_id": row[0], "name": row[1], "degree": degree.get(row[0], 0)}
                for row in elements
            ),
            key=lambda item: (-item["degree"], item["element_id"]),
        )[:10]

    validation = validate_model(model_id)

    return {
        "model_id": model_id,
        "totals": {
            "elements": element_total,
            "relationships": relationship_total,
            "relationship_density": round((relationship_total / element_total), 3) if element_total else 0.0,
        },
        "by_element_type": element_type_counts,
        "by_relationship_type": relationship_type_counts,
        "by_layer": layer_counts,
        "top_connected_elements": top_connected,
        "validation_summary": validation["summary"],
    }


def generate_insights(model_id: str) -> dict[str, Any]:
    report = generate_report(model_id)
    validation = validate_model(model_id)

    suggestions: list[dict[str, str]] = []
    totals = report["totals"]

    if totals["elements"] == 0:
        suggestions.append(
            {
                "type": "model_bootstrap",
                "message": "The model is empty. Start by adding core business/application/technology elements.",
            }
        )

    if totals["elements"] > 0 and totals["relationship_density"] < 0.5:
        suggestions.append(
            {
                "type": "connectivity",
                "message": "Relationship density is low. Add explicit dependencies (Serving, Realization, Access) to improve traceability.",
            }
        )

    layer_names = {item["layer"] for item in report["by_layer"]}
    for key_layer in ("Business", "Application", "Technology"):
        if key_layer not in layer_names:
            suggestions.append(
                {
                    "type": "layer_coverage",
                    "message": f"No {key_layer} layer elements detected. Consider adding them for cross-layer architecture views.",
                }
            )

    if validation["summary"]["errors"] > 0:
        suggestions.append(
            {
                "type": "validation",
                "message": "Resolve validation errors before publishing or exporting the model.",
            }
        )

    warnings = validation["summary"]["warnings"]
    if warnings > 0:
        suggestions.append(
            {
                "type": "temporal_consistency",
                "message": "Temporal inconsistencies were detected. Align relationship validity windows with source/target elements.",
            }
        )

    return {
        "model_id": model_id,
        "insight_count": len(suggestions),
        "suggestions": suggestions,
    }


def export_model_csv(model_id: str, filename_prefix: str | None = None) -> dict[str, Any]:
    model = get_model(model_id, include_graph=True)
    prefix = filename_prefix or f"archimate_{model_id}"
    safe_prefix = "".join(ch for ch in prefix if ch.isalnum() or ch in ("-", "_", ".")) or f"archimate_{model_id}"

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    elem_path = EXPORTS_DIR / f"{safe_prefix}_elements.csv"
    rel_path = EXPORTS_DIR / f"{safe_prefix}_relationships.csv"

    with elem_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "type_name", "name", "valid_from", "valid_to", "attributes_json"],
        )
        writer.writeheader()
        for element in model["elements"]:
            writer.writerow(
                {
                    "id": element["id"],
                    "type_name": element["type_name"],
                    "name": element.get("name", ""),
                    "valid_from": element.get("valid_from") or "",
                    "valid_to": element.get("valid_to") or "",
                    "attributes_json": json.dumps(element.get("attributes", {}), ensure_ascii=False),
                }
            )

    with rel_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "type_name", "source_element_id", "target_element_id", "name", "valid_from", "valid_to", "attributes_json"],
        )
        writer.writeheader()
        for relationship in model["relationships"]:
            writer.writerow(
                {
                    "id": relationship["id"],
                    "type_name": relationship["type_name"],
                    "source_element_id": relationship["source_element_id"],
                    "target_element_id": relationship["target_element_id"],
                    "name": relationship.get("name", ""),
                    "valid_from": relationship.get("valid_from") or "",
                    "valid_to": relationship.get("valid_to") or "",
                    "attributes_json": json.dumps(relationship.get("attributes", {}), ensure_ascii=False),
                }
            )

    return {
        "model_id": model_id,
        "elements_csv": str(elem_path),
        "relationships_csv": str(rel_path),
    }


def import_model_csv(
    model_id: str,
    elements_csv: str,
    relationships_csv: str,
    replace: bool = False,
    expected_version: int | None = None,
    author: str = "system",
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)
        cursor = connection.cursor()

        if replace:
            cursor.execute("DELETE FROM model_relationships WHERE model_id = ?", (model_id,))
            cursor.execute("DELETE FROM model_elements WHERE model_id = ?", (model_id,))

        element_rows = list(csv.DictReader(io.StringIO(elements_csv)))
        relationship_rows = list(csv.DictReader(io.StringIO(relationships_csv)))

        for row in element_rows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO model_elements(model_id, id, type_name, name, attributes_json, valid_from, valid_to, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    model_id,
                    row["id"],
                    row["type_name"],
                    row.get("name", ""),
                    row.get("attributes_json") or "{}",
                    row.get("valid_from") or None,
                    row.get("valid_to") or None,
                ),
            )

        for row in relationship_rows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO model_relationships(model_id, id, type_name, source_element_id, target_element_id, name, attributes_json, valid_from, valid_to, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    model_id,
                    row["id"],
                    row["type_name"],
                    row["source_element_id"],
                    row["target_element_id"],
                    row.get("name", ""),
                    row.get("attributes_json") or "{}",
                    row.get("valid_from") or None,
                    row.get("valid_to") or None,
                ),
            )

        version = _create_version(connection, model_id, author, "Model imported from CSV")
        connection.commit()
        return {
            "status": "imported",
            "model_id": model_id,
            "elements": len(element_rows),
            "relationships": len(relationship_rows),
            "version": version,
        }


def export_model_xml(model_id: str) -> str:
    model = get_model(model_id, include_graph=True)

    root = ET.Element("archimateModel", attrib={"id": model_id, "name": model["name"]})
    ET.SubElement(root, "description").text = model.get("description", "")
    ET.SubElement(root, "attributes").text = json.dumps(model.get("attributes", {}), ensure_ascii=False)

    elements_node = ET.SubElement(root, "elements")
    for element in model["elements"]:
        node = ET.SubElement(
            elements_node,
            "element",
            attrib={
                "id": element["id"],
                "type": element["type_name"],
                "name": element.get("name", ""),
            },
        )
        if element.get("valid_from"):
            node.set("valid_from", str(element["valid_from"]))
        if element.get("valid_to"):
            node.set("valid_to", str(element["valid_to"]))
        ET.SubElement(node, "attributes").text = json.dumps(element.get("attributes", {}), ensure_ascii=False)

    relationships_node = ET.SubElement(root, "relationships")
    for relationship in model["relationships"]:
        node = ET.SubElement(
            relationships_node,
            "relationship",
            attrib={
                "id": relationship["id"],
                "type": relationship["type_name"],
                "source": relationship["source_element_id"],
                "target": relationship["target_element_id"],
                "name": relationship.get("name", ""),
            },
        )
        if relationship.get("valid_from"):
            node.set("valid_from", str(relationship["valid_from"]))
        if relationship.get("valid_to"):
            node.set("valid_to", str(relationship["valid_to"]))
        ET.SubElement(node, "attributes").text = json.dumps(relationship.get("attributes", {}), ensure_ascii=False)

    return ET.tostring(root, encoding="unicode")


def import_model_xml(
    model_id: str,
    xml_content: str,
    replace: bool = False,
    expected_version: int | None = None,
    author: str = "system",
) -> dict[str, Any]:
    root = ET.fromstring(xml_content)
    if root.tag != "archimateModel":
        raise ModelError("Invalid XML root. Expected 'archimateModel'")

    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _ensure_expected_version(connection, model_id, expected_version)
        cursor = connection.cursor()

        if replace:
            cursor.execute("DELETE FROM model_relationships WHERE model_id = ?", (model_id,))
            cursor.execute("DELETE FROM model_elements WHERE model_id = ?", (model_id,))

        element_count = 0
        relationship_count = 0

        elements_node = root.find("elements")
        if elements_node is not None:
            for node in elements_node.findall("element"):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO model_elements(model_id, id, type_name, name, attributes_json, valid_from, valid_to, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        model_id,
                        node.attrib["id"],
                        node.attrib.get("type", ""),
                        node.attrib.get("name", ""),
                        (node.findtext("attributes") or "{}"),
                        node.attrib.get("valid_from"),
                        node.attrib.get("valid_to"),
                    ),
                )
                element_count += 1

        relationships_node = root.find("relationships")
        if relationships_node is not None:
            for node in relationships_node.findall("relationship"):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO model_relationships(model_id, id, type_name, source_element_id, target_element_id, name, attributes_json, valid_from, valid_to, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        model_id,
                        node.attrib["id"],
                        node.attrib.get("type", ""),
                        node.attrib.get("source", ""),
                        node.attrib.get("target", ""),
                        node.attrib.get("name", ""),
                        (node.findtext("attributes") or "{}"),
                        node.attrib.get("valid_from"),
                        node.attrib.get("valid_to"),
                    ),
                )
                relationship_count += 1

        version = _create_version(connection, model_id, author, "Model imported from XML")
        connection.commit()
        return {
            "status": "imported",
            "model_id": model_id,
            "elements": element_count,
            "relationships": relationship_count,
            "version": version,
        }


def acquire_lock(model_id: str, owner: str, force: bool = False) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute("SELECT owner, acquired_at FROM model_locks WHERE model_id = ?", (model_id,))
        row = cursor.fetchone()
        if row:
            current_owner, acquired_at = row
            if current_owner == owner:
                return {"status": "already_locked", "model_id": model_id, "owner": owner, "acquired_at": acquired_at}
            if not force:
                raise ModelError(f"Model '{model_id}' is locked by '{current_owner}'")
            cursor.execute("DELETE FROM model_locks WHERE model_id = ?", (model_id,))

        cursor.execute(
            """
            INSERT INTO model_locks(model_id, owner)
            VALUES (?, ?)
            """,
            (model_id, owner),
        )
        connection.commit()
        cursor.execute("SELECT owner, acquired_at FROM model_locks WHERE model_id = ?", (model_id,))
        owner_value, acquired_at = cursor.fetchone()
        return {"status": "locked", "model_id": model_id, "owner": owner_value, "acquired_at": acquired_at}


def release_lock(model_id: str, owner: str | None = None, force: bool = False) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute("SELECT owner FROM model_locks WHERE model_id = ?", (model_id,))
        row = cursor.fetchone()
        if not row:
            return {"status": "not_locked", "model_id": model_id}
        current_owner = row[0]
        if not force and owner and owner != current_owner:
            raise ModelError(f"Lock owner mismatch. Model '{model_id}' is locked by '{current_owner}'")

        cursor.execute("DELETE FROM model_locks WHERE model_id = ?", (model_id,))
        connection.commit()
        return {"status": "released", "model_id": model_id, "owner": current_owner}



# ---------------------------------------------------------------------------
# attribute definition helpers (per-model dictionary)
# ---------------------------------------------------------------------------

def list_attribute_definitions(model_id: str, target_type: str) -> list[dict]:
    """Return attribute keys, descriptions, and is_tag flags for a given model and target_type.
    target_type must be 'element' or 'relationship'."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT key, description, is_tag FROM model_attribute_definitions "
            "WHERE model_id = ? AND target_type = ?",
            (model_id, target_type),
        )
        return [{"key": row[0], "description": row[1], "is_tag": bool(row[2])} for row in cursor.fetchall()]


def list_tag_definitions(model_id: str, target_type: str) -> list[dict]:
    """Return only attribute definitions that are marked as tags (is_tag=1)."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT key, description FROM model_attribute_definitions "
            "WHERE model_id = ? AND target_type = ? AND is_tag = 1",
            (model_id, target_type),
        )
        return [{"key": row[0], "description": row[1], "is_tag": True} for row in cursor.fetchall()]


def define_attribute(model_id: str, target_type: str, key: str, description: str = "", is_tag: bool = False) -> None:
    """Create or update an attribute definition for the given model.

    Set ``is_tag=True`` to mark the key as a tag, which enables the
    ``add_tag`` / ``remove_tag`` CUD actions and the ``tag_key`` /
    ``tag_value`` query filters to use it.
    """
    if target_type not in ("element", "relationship"):
        raise ModelError("target_type must be 'element' or 'relationship'")
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO model_attribute_definitions
            (model_id, target_type, key, description, is_tag)
            VALUES (?, ?, ?, ?, ?)
            """,
            (model_id, target_type, key, description, 1 if is_tag else 0),
        )
        connection.commit()


def delete_attribute_definition(model_id: str, target_type: str, key: str) -> int:
    """Remove a definition from the dictionary; returns number removed."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM model_attribute_definitions "
            "WHERE model_id = ? AND target_type = ? AND key = ?",
            (model_id, target_type, key),
        )
        connection.commit()
        return int(cursor.rowcount)


# ---------------------------------------------------------------------------
# tag management helpers (element and relationship)
# ---------------------------------------------------------------------------

def _resolve_tag_key(connection, model_id: str, target_type: str, key: str) -> None:
    """Raise ModelError if ``key`` is not defined with is_tag=1 in the dictionary."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT 1 FROM model_attribute_definitions "
        "WHERE model_id = ? AND target_type = ? AND key = ? AND is_tag = 1",
        (model_id, target_type, key),
    )
    if cursor.fetchone() is None:
        raise ModelError(
            f"Tag key '{key}' is not defined for {target_type}s in model '{model_id}'. "
            "Define it first with archimate_attribute_dictionary define + is_tag=true."
        )


def add_element_tag(
    model_id: str,
    element_id: str,
    key: str,
    value: str = "",
    author: str = "system",
    message: str = "Tag added",
) -> dict[str, Any]:
    """Add or update a tag on an element.  The key must exist in the attribute
    dictionary with ``is_tag=True``.  Returns the updated tags dict."""
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _resolve_tag_key(connection, model_id, "element", key)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT tags_json FROM model_elements WHERE model_id = ? AND id = ?",
            (model_id, element_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ModelError(f"Element '{element_id}' not found in model '{model_id}'")
        tags: dict = json.loads(row[0] or "{}")
        tags[key] = value
        cursor.execute(
            "UPDATE model_elements SET tags_json = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE model_id = ? AND id = ?",
            (json.dumps(tags, ensure_ascii=False), model_id, element_id),
        )
        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {"status": "ok", "element_id": element_id, "tags": tags, "version": version}


def remove_element_tag(
    model_id: str,
    element_id: str,
    key: str,
    author: str = "system",
    message: str = "Tag removed",
) -> dict[str, Any]:
    """Remove a tag from an element.  No-ops silently if the key is absent."""
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT tags_json FROM model_elements WHERE model_id = ? AND id = ?",
            (model_id, element_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ModelError(f"Element '{element_id}' not found in model '{model_id}'")
        tags: dict = json.loads(row[0] or "{}")
        tags.pop(key, None)
        cursor.execute(
            "UPDATE model_elements SET tags_json = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE model_id = ? AND id = ?",
            (json.dumps(tags, ensure_ascii=False), model_id, element_id),
        )
        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {"status": "ok", "element_id": element_id, "tags": tags, "version": version}


def add_relationship_tag(
    model_id: str,
    relationship_id: str,
    key: str,
    value: str = "",
    author: str = "system",
    message: str = "Tag added",
) -> dict[str, Any]:
    """Add or update a tag on a relationship.  The key must exist in the attribute
    dictionary with ``is_tag=True``."""
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        _resolve_tag_key(connection, model_id, "relationship", key)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT tags_json FROM model_relationships WHERE model_id = ? AND id = ?",
            (model_id, relationship_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ModelError(f"Relationship '{relationship_id}' not found in model '{model_id}'")
        tags: dict = json.loads(row[0] or "{}")
        tags[key] = value
        cursor.execute(
            "UPDATE model_relationships SET tags_json = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE model_id = ? AND id = ?",
            (json.dumps(tags, ensure_ascii=False), model_id, relationship_id),
        )
        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {"status": "ok", "relationship_id": relationship_id, "tags": tags, "version": version}


def remove_relationship_tag(
    model_id: str,
    relationship_id: str,
    key: str,
    author: str = "system",
    message: str = "Tag removed",
) -> dict[str, Any]:
    """Remove a tag from a relationship.  No-ops silently if the key is absent."""
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT tags_json FROM model_relationships WHERE model_id = ? AND id = ?",
            (model_id, relationship_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ModelError(f"Relationship '{relationship_id}' not found in model '{model_id}'")
        tags: dict = json.loads(row[0] or "{}")
        tags.pop(key, None)
        cursor.execute(
            "UPDATE model_relationships SET tags_json = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE model_id = ? AND id = ?",
            (json.dumps(tags, ensure_ascii=False), model_id, relationship_id),
        )
        version = _create_version(connection, model_id, author, message)
        connection.commit()
        return {"status": "ok", "relationship_id": relationship_id, "tags": tags, "version": version}



def get_lock(model_id: str) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_model_exists(connection, model_id)
        cursor = connection.cursor()
        cursor.execute("SELECT owner, acquired_at FROM model_locks WHERE model_id = ?", (model_id,))
        row = cursor.fetchone()
        if not row:
            return {"model_id": model_id, "locked": False}
        return {
            "model_id": model_id,
            "locked": True,
            "owner": row[0],
            "acquired_at": row[1],
        }


def mermaid_view(model_id: str, direction: str = "LR", limit: int = 300) -> str:
    direction = direction if direction in {"LR", "RL", "TB", "BT"} else "LR"
    elements = list_model_elements(model_id=model_id, limit=limit)
    relationships = list_model_relationships(model_id=model_id, limit=limit)

    lines = [f"graph {direction}"]
    for element in elements:
        node_id = element["id"].replace("-", "_")
        label = (element.get("name") or element["id"]).replace('"', "'")
        lines.append(f'  {node_id}["{label}\\n<{element["type_name"]}>"]')

    for relationship in relationships:
        src = relationship["source_element_id"].replace("-", "_")
        tgt = relationship["target_element_id"].replace("-", "_")
        rel_label = relationship["type_name"].replace('"', "'")
        lines.append(f"  {src} -->|{rel_label}| {tgt}")

    return "\n".join(lines)
