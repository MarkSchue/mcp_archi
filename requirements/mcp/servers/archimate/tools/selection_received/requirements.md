# Tool: selection_received

## User Stories

### US-SR-01 — Receive and store a table/diagram selection
As an application,  
I want to receive the list of rows or elements selected by the user in the UI  
so that subsequent agent actions can operate on the user's chosen subset.

---

## Acceptance Criteria

### AC-SR-01 · Store selection
- **Given** a non-empty `selection` list  
  **Then** the selection is stored via `set_selection` and `{"received": […]}` is returned.
- **Given** an empty list  
  **Then** `set_selection` is still called (clearing the selection) and the response echoes the empty list.

### AC-SR-02 · Error handling
- **Given** an exception is raised inside `set_selection`  
  **Then** `Error processing selection: …` is returned and the error is logged to stdout.