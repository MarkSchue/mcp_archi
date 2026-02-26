# Tool: archimate_model_management

## User Stories

### US-MM-01 — Manage model lifecycle
As an architecture administrator,  
I want to create, read, update, and delete ArchiMate models  
so that I can manage the overall architecture repository.

### US-MM-02 — Browse and analyse model contents
As an architect,  
I want to list, upsert, and delete elements and relationships from a management perspective  
so that I have a single tool for all high-level model operations.

### US-MM-03 — Version history and rollback
As an architect,  
I want to list versions, retrieve a specific version, and revert a model to a prior state  
so that I can audit changes and undo mistakes.

### US-MM-04 — Validate and report
As an architect,  
I want to validate a model against the metamodel and generate reports or Mermaid diagrams  
so that I can ensure quality and communicate the architecture.

### US-MM-05 — Import / Export
As an architect,  
I want to import and export model data as CSV or XML  
so that I can integrate with other tools and archive architecture snapshots.

### US-MM-06 — Concurrency control
As a team lead,  
I want to acquire, check, and release an edit lock on a model  
so that simultaneous edits from multiple users are prevented.

### US-MM-07 — Per-model attribute dictionary
As an architect,  
I want to define, list, and delete custom attribute keys for a model  
so that elements and relationships can carry project-specific metadata.

---

## Acceptance Criteria

### AC-MM-01 · create_model
- **Given** a payload with `name`  
  **Then** a new model is created, its `id` is returned, and it becomes the current model.
- **Given** `name` is absent  
  **Then** `Error: missing required field 'name'` is returned.

### AC-MM-02 · list_models
- **Given** no filters  
  **Then** all models up to the default limit of 100 are returned.
- **Given** `search` text  
  **Then** only models whose names contain the search text are returned.

### AC-MM-03 · get_model
- **Given** a valid `model_id`  
  **Then** the model record including its element/relationship graph is returned.
- **Given** `model_id` is missing  
  **Then** `Error: missing required field 'model_id'` is returned.

### AC-MM-04 · update_model
- **Given** `model_id` and at least one of `name`, `description`, or `attributes`  
  **Then** the model is updated and the response reflects the new values.
- **Given** `expected_version` is provided and matches  
  **Then** the update succeeds; contradiction causes a `ModelError`.

### AC-MM-05 · delete_model
- **Given** a valid `model_id`  
  **Then** the model and all its contents are deleted; response contains `{"status":"deleted","count":…}`.

### AC-MM-06 · upsert_element / delete_element / list_elements
- **Given** `model_id`, `type_name`, and `name` for upsert  
  **Then** the element is created or updated.
- **Given** `model_id` for `list_elements`  
  **Then** all matching elements are returned, optionally filtered by `type_name`, `search`, or `valid_at`.
- **Given** `model_id` and `element_id` for delete  
  **Then** the element is removed.

### AC-MM-07 · upsert_relationship / delete_relationship / list_relationships
- **Given** `model_id`, `type_name`, `source_element_id`, `target_element_id`  
  **Then** the relationship is created or updated.
- **Given** `model_id` for `list_relationships`  
  **Then** relationships are returned, optionally filtered.
- **Given** `model_id` and `relationship_id` for delete  
  **Then** the relationship is removed.

### AC-MM-08 · Version operations
- **Given** `model_id` for `list_versions`  
  **Then** a list of version records is returned.
- **Given** `model_id` and `version` for `get_version`  
  **Then** the state snapshot for that version is returned.
- **Given** `model_id` and `version` for `revert_version`  
  **Then** the model is restored to that version and a mutation is noted.

### AC-MM-09 · validate_model / generate_report / generate_insights / generate_view_mermaid
- **Given** a valid `model_id`  
  **Then** each action returns its respective result payload without error.
- **Given** `model_id` is absent  
  **Then** the missing-field error is returned.

### AC-MM-10 · Import / Export (CSV and XML)
- **Given** `model_id` for `export_csv` or `export_xml`  
  **Then** file paths are returned or XML content is included in the response.
- **Given** `model_id`, `elements_csv`, and `relationships_csv` for `import_csv`  
  **Then** data is imported and a mutation is noted.
- **Given** `model_id` and `xml` for `import_xml`  
  **Then** the model content is replaced/merged and a mutation is noted.

### AC-MM-11 · Lock management
- **Given** `model_id` and `owner` for `acquire_lock`  
  **Then** the lock is acquired; if already locked by another owner, an error is returned unless `force=true`.
- **Given** `model_id` for `release_lock`  
  **Then** the lock is cleared.
- **Given** `model_id` for `get_lock`  
  **Then** the current lock owner and timestamp are returned.

### AC-MM-12 · Attribute dictionary
- **Given** `model_id`, `target_type`, and `key` for `define_attribute`  
  **Then** the attribute key is persisted.
- **Given** `model_id` and `target_type` for `list_attributes`  
  **Then** all defined keys are returned.
- **Given** `model_id`, `target_type`, and `key` for `delete_attribute`  
  **Then** the key is removed and deletion count is returned.

### AC-MM-13 · Error handling
- **Given** any unknown action is supplied  
  **Then** the response lists all allowed action names.
- **Given** `payload_json` is invalid JSON  
  **Then** a parse error message is returned.