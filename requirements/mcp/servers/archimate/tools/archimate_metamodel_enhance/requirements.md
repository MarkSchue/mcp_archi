# Tool: archimate_metamodel_enhance

## User Stories

### US-ME-01 — Add or update a metamodel element type
As a metamodel administrator,  
I want to upsert a new element type with its layer, aspect, and definition  
so that the metamodel can be extended with project-specific or domain concepts.

### US-ME-02 — Add or update a metamodel relationship type
As a metamodel administrator,  
I want to upsert a new relationship type with its category and directedness  
so that custom connection semantics can be modelled.

### US-ME-03 — Add a metamodel rule
As a metamodel administrator,  
I want to add a rule that constrains which element types may be connected by which relationship  
so that the modelling tool enforces structural correctness.

### US-ME-04 — Annotate metamodel entities
As a modeler,  
I want to add, list, and delete free-text annotations on metamodel elements, relationships, or rules  
so that project-specific guidance is attached directly to the metamodel.

---

## Acceptance Criteria

### AC-ME-01 · db_info
- **Given** `action=db_info`  
  **Then** the response contains both database paths and their existence status.

### AC-ME-02 · upsert_element
- **Given** a payload with `name`, `layer`, `aspect`, and `definition`  
  **Then** the element type is created or updated and `{"status": "inserted"|"updated", "entity": "element", "name": …}` is returned.
- **Given** any of the four required fields is absent  
  **Then** `Error: missing required field '…'` is returned.
- **Given** optional `attributes` (dict) or `constraints` (list) are provided  
  **Then** they are stored on the element type.

### AC-ME-03 · upsert_relationship
- **Given** a payload with `name`, `category`, `directed` (bool), and `definition`  
  **Then** the relationship type is created or updated and status is returned.
- **Given** `directed` is missing from the payload  
  **Then** `Error: missing required field 'directed'` is returned.

### AC-ME-04 · add_rule
- **Given** a payload with `rule_type`, `source`, `relationship`, `target`, and `notes`  
  **Then** the rule is persisted and `{"status": "stored", "entity": "rule", "id": <int>}` is returned.
- **Given** any required field is absent  
  **Then** the appropriate missing-field error is returned.

### AC-ME-05 · add_annotation
- **Given** a payload with `target_type`, `target_name`, and `note`  
  **Then** the annotation is stored and `{"status": "stored", "entity": "annotation", "id": <int>}` is returned.
- **Given** optional `source` is provided  
  **Then** it is stored; otherwise `"user"` is used as default.

### AC-ME-06 · list_annotations
- **Given** no filters  
  **Then** all annotations up to the default limit (100) are returned.
- **Given** `target_type` and/or `target_name` filters  
  **Then** only matching annotations are returned.

### AC-ME-07 · delete_annotation
- **Given** a payload with `id` or at least one filter field (`target_type`, `target_name`, `note`, `source`)  
  **Then** matching annotations are deleted and `{"status": "deleted", "count": …}` is returned.
- **Given** no criteria at all are provided  
  **Then** an error requiring at least one criterion is returned.

### AC-ME-08 · delete_rule
- **Given** a payload with `id` or at least one filter field (`rule_type`, `source`, `relationship`, `target`, `notes`)  
  **Then** matching rules are deleted and count is returned.
- **Given** no criteria are provided  
  **Then** an error is returned.

### AC-ME-09 · Error handling
- **Given** `payload_json` is invalid JSON  
  **Then** `Error: payload_json is invalid JSON – …` is returned.
- **Given** an unknown action is supplied  
  **Then** the response lists all allowed actions.