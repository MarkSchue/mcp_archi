# Tool: archimate_attribute_dictionary

## User Stories

### US-AD-01 — Define a custom attribute
As an architect,  
I want to define a named attribute key for a given model and target type (element or relationship)  
so that I can extend the metamodel with project-specific metadata fields.

### US-AD-02 — List defined attributes
As an architect,  
I want to list all defined attribute keys for a specific model and target type  
so that I can see which custom fields are available.

### US-AD-03 — Delete a custom attribute
As an architect,  
I want to remove an attribute key from a model's dictionary  
so that obsolete metadata definitions are cleaned up.


### US-AD-03 - Tag attributes
As an architect,
I want to mark certain attribute keys as "tags" in the dictionary
so that they can be treated as categorical labels in the UI and analysis.

---

## Acceptance Criteria

### AC-AD-01 · define
- **Given** a payload with `model_id`, `target_type`, and `key`  
  **Then** the attribute is persisted and the response is `{"status": "ok"}`.
- **Given** an optional `description` is included  
  **Then** it is stored alongside the key.
- **Given** any of `model_id`, `target_type`, or `key` is missing  
  **Then** `Error: missing required field '…'` is returned.

### AC-AD-02 · list
- **Given** a payload with `model_id` and `target_type`  
  **Then** all attribute keys defined for that combination are returned as a JSON array.
- **Given** either `model_id` or `target_type` is missing  
  **Then** `Error: missing required field '…'` is returned.

### AC-AD-03 · delete
- **Given** a payload with `model_id`, `target_type`, and `key`  
  **Then** the matching attribute key is removed and `{"deleted": <count>}` is returned.
- **Given** the key does not exist  
  **Then** `{"deleted": 0}` is returned without error.
- **Given** any of `model_id`, `target_type`, or `key` is missing  
  **Then** `Error: missing required field '…'` is returned.

### AC-AD-04 · Error handling
- **Given** `payload_json` is invalid JSON  
  **Then** `Error: payload_json invalid – …` is returned.
- **Given** an unknown action is supplied  
  **Then** `Error: unknown action '…'` is returned.

### AC-AD-05 · Tagging attributes
- **Given** a payload with `model_id`, `target_type`, `key`, and optional `is_tag` (boolean, default `false`)  
  **Then** the attribute is stored with the tag status and `{"status": "ok", "is_tag": <bool>}` is returned.
- **Given** `is_tag` is omitted  
  **Then** it defaults to `false` and the attribute is created as a regular attribute (not a tag).
- **Given** `is_tag` is provided as a string value `"true"`, `"1"`, or `"yes"`  
  **Then** it is normalised to `true`.

### AC-AD-06 · List tags
- **Given** action `list_tags` with `model_id` and `target_type`  
  **Then** only attribute keys with `is_tag=true` for that combination are returned as a JSON array (each entry has `key`, `description`, `is_tag`).
- **Given** action `list` with `model_id` and `target_type`  
  **Then** all attribute keys are returned including their `is_tag` field.
- **Given** either `model_id` or `target_type` is missing  
  **Then** `Error: missing required field '…'` is returned.