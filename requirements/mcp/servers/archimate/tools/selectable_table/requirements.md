# Tool: selectable_table

## User Stories

### US-ST-01 — Display query results as a table
As a user,  
I want to render a list of ArchiMate elements or relationships in an interactive table  
so that I can browse, sort, and select rows in the UI without reading raw JSON.

---

## Acceptance Criteria

### AC-ST-01 · Basic rendering
- **Given** a non-empty `entities_json` array and a `title`  
  **Then** the response contains a JSON payload with `_kind: "selectable_table"`, `title`, `columns`, and `entities`.
- **Given** `columns` is derived from the first entity's keys  
  **Then** all subsequent rows are rendered in the same column order.

### AC-ST-02 · UI integration
- **Given** the tool response is received by the UI layer  
  **Then** the table is presented via the registered `VIEW_URI` resource.

### AC-ST-03 · Input validation
- **Given** `entities_json` is not valid JSON  
  **Then** `Error: Invalid JSON – …` is returned.
- **Given** `entities_json` is an empty array  
  **Then** `Error: entities_json must be a non-empty JSON array.` is returned.
- **Given** `entities_json` is not an array (e.g. an object)  
  **Then** the same non-empty array error is returned.