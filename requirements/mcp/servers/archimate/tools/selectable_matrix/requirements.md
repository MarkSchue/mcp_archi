# Tool: selectable_matrix

## User Stories

### US-SM-01 — Display query results as a matrix
As a user,  
I want to render a list of ArchiMate relationship-like objects in an interactive matrix  
so that I can see which row entities intersect with which column entities (e.g. actors vs. processes).

---

## Acceptance Criteria

### AC-SM-01 · Basic rendering
- **Given** a non-empty `entities_json` array, a `title`, a `row_field`, and a `column_field`  
  **Then** the response contains a JSON payload with `_kind: "selectable_matrix"`, `title`, `rowField`, `columnField`, and `entities`.

### AC-SM-02 · UI integration
- **Given** the tool response is received by the UI layer  
  **Then** the matrix is presented via the registered `MATRIX_VIEW_URI` resource.

### AC-SM-03 · Input validation — JSON
- **Given** `entities_json` is not valid JSON  
  **Then** `Error: Invalid JSON – …` is returned.
- **Given** `entities_json` is an empty array  
  **Then** `Error: entities_json must be a non-empty JSON array.` is returned.

### AC-SM-04 · Input validation — fields
- **Given** `row_field` or `column_field` is absent or empty  
  **Then** `Error: row_field and column_field are required.` is returned.
- **Given** any entity in the array is not a dict  
  **Then** `Error: entity at index <n> is not an object.` is returned.
- **Given** any entity does not contain both `row_field` and `column_field`  
  **Then** `Error: entity at index <n> must contain both fields '<row_field>' and '<column_field>'.` is returned.