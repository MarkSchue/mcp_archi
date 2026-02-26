# Tool: archimate_model_query

## User Stories

### US-MQ-01 — Search elements
As an architect,  
I want to search for elements in a model by type, layer, aspect, attribute, or text  
so that I can find specific parts of the architecture without writing SQL.

### US-MQ-02 — Search relationships
As an architect,  
I want to filter relationships by type, category, source, or target element  
so that I can analyse dependencies and connections between elements.

### US-MQ-03 — Discover neighbours
As an architect,  
I want to retrieve all elements that are directly connected to a given element  
so that I can explore the local context of any node.

### US-MQ-04 — Check path existence
As an architect,  
I want to know whether a directed path exists between two elements  
so that I can verify reachability and traceability.

### US-MQ-05 — Temporal slice
As an architect,  
I want to retrieve all elements and relationships that were valid at a specific date  
so that I can reason about past or future states of the architecture.

### US-MQ-06 — Model statistics
As an architect,  
I want to get summary counts of elements, relationships, and types in a model  
so that I can quickly assess the size and distribution of the model.

### US-MQ-07 — Search tagged elements
As an architect,  
I want to search for elements tagged with custom attribute keys and values defined in the model's attribute dictionary as "tags",
so that I can search for elements based on project-specific categorical labels.

---

## Acceptance Criteria

### AC-MQ-01 · search_elements
- **Given** `model_id` and an optional `type_name`  
  **Then** only elements of that type are returned.
- **Given** `layer` or `aspect` filter  
  **Then** only elements matching the metamodel layer/aspect are returned.
- **Given** `valid_at` (ISO date string)  
  **Then** only elements where `valid_from ≤ valid_at ≤ valid_to` (nulls treated as open-ended) are returned.
- **Given** `search` text  
  **Then** only elements whose `id`, `name`, or `type_name` contain the text are returned.
- **Given** `attribute_key` and optional `attribute_value`  
  **Then** only elements whose `attributes_json` contains that key (and value if given) are returned.
- **Given** `limit` is provided  
  **Then** no more than `limit` records are returned.
- **Given** `model_id` is missing  
  **Then** `Error: missing required field 'model_id'` is returned.
- **Given** results are returned  
  **Then** each row includes `metamodel_layer` and `metamodel_aspect` from the metamodel DB.

### AC-MQ-02 · search_relationships
- **Given** `model_id` and optional filters (`type_name`, `category`, `source_element_id`, `target_element_id`, `valid_at`)  
  **Then** only matching relationships are returned.
- **Given** results are returned  
  **Then** each row includes `metamodel_category` and the boolean `metamodel_directed` flag.

### AC-MQ-03 · neighbors
- **Given** `model_id`, `element_id`, and `direction` (`in`, `out`, or `both`)  
  **Then** all directly connected element ids and the connecting relationships are returned.
- **Given** `relationship_type` is provided  
  **Then** only neighbours connected via that relationship type are included.

### AC-MQ-04 · path_exists
- **Given** `model_id`, `source_id`, and `target_id`  
  **Then** the response contains a boolean `exists` indicating whether a directed path is reachable via BFS.

### AC-MQ-05 · temporal_slice
- **Given** `model_id` and a `date` string  
  **Then** all elements and relationships valid on that date are returned.

### AC-MQ-06 · model_stats
- **Given** `model_id`  
  **Then** the response contains element count, relationship count, and a breakdown by type.

### AC-MQ-07 · Error handling
- **Given** an unknown action is supplied  
  **Then** the response lists all allowed action names.
- **Given** `payload_json` is malformed  
  **Then** a JSON parse error is returned.

### AC-MQ-08 · Search tagged elements
- **Given** `model_id` and `tag_key`  
  **Then** only elements whose `tags_json` contains that key are returned (case-insensitive comparison).
- **Given** `model_id`, `tag_key`, and `tag_value`  
  **Then** only elements whose `tags_json.[tag_key]` equals `tag_value` (case-insensitive) are returned.
- **Given** `tag_key` is omitted  
  **Then** the tag filter is not applied and all elements matching other criteria are returned.