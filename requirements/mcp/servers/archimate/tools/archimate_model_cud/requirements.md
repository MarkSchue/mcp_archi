# Tool: archimate_model_cud

## User Stories

### US-CUD-01 — Create an element
As a modeler,  
I want to create a new ArchiMate element inside a model  
so that I can build up the architecture incrementally.

### US-CUD-02 — Update an element
As a modeler,  
I want to update the name, attributes, or validity dates of an existing element  
so that I can keep the architecture current.

### US-CUD-03 — Delete an element
As a modeler,  
I want to delete an obsolete element from a model  
so that the model stays clean and accurate.

### US-CUD-04 — Create a relationship
As a modeler,  
I want to create a directed relationship between two elements  
so that I can express dependencies, flows, and associations.

### US-CUD-05 — Update a relationship
As a modeler,  
I want to update name, attributes, or validity of an existing relationship  
so that structural changes are reflected correctly.

### US-CUD-06 — Delete a relationship
As a modeler,  
I want to delete a relationship that is no longer valid  
so that the model graph remains accurate.

## US-CUD-07 — Add and delete tags on elements and relationships
As a modeler,  
I want to add and remove tags (custom attribute keys marked as "tags" in the attribute dictionary) on elements and relationships.

---

## Acceptance Criteria

### AC-CUD-01 · db_info
- **Given** the tool is called with `action=db_info`  
  **Then** the response contains `metamodel_db.path`, `metamodel_db.exists`, `model_db.path`, and `model_db.exists`.

### AC-CUD-02 · create_element / create_el
- **Given** a payload with `model_id`, `type_name`, and `name`  
  **Then** the element is persisted and the response contains the new element's `id`.
- **Given** `model_id`, `type_name`, or `name` is missing  
  **Then** the response starts with `Error: missing required field '…'`.
- **Given** optional fields `attributes`, `valid_from`, `valid_to`, `author`, `message` are provided  
  **Then** they are stored on the element.

### AC-CUD-03 · update_element / update_el
- **Given** a payload with `model_id`, `type_name`, `name`, and `element_id`  
  **Then** the existing element is updated and the response reflects the change.
- **Given** `element_id` is missing  
  **Then** the response contains `Error: update_element requires 'element_id'`.
- **Given** `expected_version` is provided and matches the current version  
  **Then** the update succeeds; if it does not match, a `ModelError` is returned.

### AC-CUD-04 · delete_element / delete_el
- **Given** a payload with `model_id` and `element_id`  
  **Then** the element is removed and the response confirms deletion.
- **Given** either `model_id` or `element_id` is missing  
  **Then** the response contains the appropriate `Error: missing required field '…'`.

### AC-CUD-05 · create_relationship / create_rel
- **Given** a payload with `model_id`, `type_name`, `source_element_id`, and `target_element_id`  
  **Then** the relationship is persisted and the response contains the new `id`.
- **Given** any of the four required fields is missing  
  **Then** the response contains `Error: missing required field '…'`.

### AC-CUD-06 · update_relationship / update_rel
- **Given** a payload with `model_id`, `type_name`, `source_element_id`, `target_element_id`, and `relationship_id`  
  **Then** the relationship is updated.
- **Given** `relationship_id` is absent  
  **Then** the response contains `Error: update_relationship requires 'relationship_id'`.

### AC-CUD-07 · delete_relationship / delete_rel
- **Given** a payload with `model_id` and `relationship_id`  
  **Then** the relationship is removed and deletion is confirmed.
- **Given** either required field is missing  
  **Then** the response contains `Error: missing required field '…'`.

### AC-CUD-08 · Mutation notification
- **Given** any write action (create/update/delete element or relationship) succeeds  
  **Then** `note_model_mutation` is invoked, recording the tool name, action, and model_id.

### AC-CUD-09 · Short aliases
- **Given** any short alias (`create_el`, `update_el`, `delete_el`, `create_rel`, `update_rel`, `delete_rel`) is used  
  **Then** it behaves identically to its full-name counterpart.

### AC-CUD-10 · Error handling
- **Given** `payload_json` is malformed JSON  
  **Then** the response starts with `Error: payload_json is invalid JSON`.
- **Given** an unknown action is supplied  
  **Then** the response lists all allowed action names.
- **Given** a `ModelError` is raised internally  
  **Then** the response starts with `Error:` and contains the error message.

### AC-CUD-11 · Add and remove tags on elements and relationships
- **Given** action `add_tag` with `model_id`, `key`, and exactly one of `element_id` or `relationship_id`  
  **Then** the tag is added (or updated) in the target's `tags_json` field, the response includes `{"status": "ok", "tags": {...}, "version": N}`, and a model version is created.
- **Given** action `remove_tag` with `model_id`, `key`, and exactly one of `element_id` or `relationship_id`  
  **Then** the key is removed from `tags_json` (silently no-ops if absent), the response includes the remaining tags and version.
- **Given** the supplied `key` is not registered with `is_tag=true` in the attribute dictionary  
  **Then** the response starts with `Error:` and references the missing tag key definition.
- **Given** neither `element_id` nor `relationship_id` is provided  
  **Then** `Error: add_tag requires 'element_id' or 'relationship_id'` is returned.
- **Given** both `element_id` and `relationship_id` are provided  
  **Then** `Error: add_tag accepts either 'element_id' or 'relationship_id', not both` is returned.
- **Given** `key` is missing  
  **Then** `Error: missing required field 'key'` is returned.