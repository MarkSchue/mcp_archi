# Tool: archimate_current_model

## User Stories

### US-CM-01 — Set the active model
As a user,  
I want to declare a model as the current working model  
so that all subsequent tool calls can resolve the model context automatically without requiring explicit `model_id` in every payload.

### US-CM-02 — Retrieve the active model
As a user,  
I want to query which model is currently active  
so that I can confirm the correct context before performing operations.

### US-CM-03 — Find a model by name
As a user,  
I want to search for models by name fragment  
so that I can discover and set the correct model when the id is not known.

---

## Acceptance Criteria

### AC-CM-01 · set
- **Given** a payload with a non-empty `model_id`  
  **Then** the model_id is stored in server state and `{"model_id": "…"}` is returned.
- **Given** `model_id` is missing or empty  
  **Then** `Error: missing required field 'model_id' for set` is returned.

### AC-CM-02 · get
- **Given** a current model has been set  
  **Then** `{"model_id": "<id>"}` is returned.
- **Given** no current model has been set  
  **Then** `{"model_id": null}` is returned.

### AC-CM-03 · find
- **Given** a payload with a non-empty `name` fragment  
  **Then** a list of up to 50 matching models as `[{"id": …, "name": …}]` is returned.
- **Given** `name` is missing or empty  
  **Then** `Error: missing required field 'name' for find` is returned.
- **Given** no models match the fragment  
  **Then** an empty list `[]` is returned.

### AC-CM-04 · Error handling
- **Given** `payload_json` is invalid JSON  
  **Then** `Error: payload_json invalid – …` is returned.
- **Given** an unknown action is supplied  
  **Then** `Error: unknown action '…'` is returned.