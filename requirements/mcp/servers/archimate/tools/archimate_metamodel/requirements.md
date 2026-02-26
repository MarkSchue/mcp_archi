# Tool: archimate_metamodel_info

## User Stories

### US-META-01 — Get an overview of the metamodel
As an architect,  
I want to see a summary of the ArchiMate metamodel (counts, layers, categories)  
so that I understand the scope of element and relationship types available.

### US-META-02 — Browse element types
As a modeler,  
I want to list all element types, optionally filtered by layer or free text  
so that I can discover which types to use in my model.

### US-META-03 — Browse relationship types
As a modeler,  
I want to list all relationship types, optionally filtered by category or free text  
so that I can choose the correct relationship for a given connection.

### US-META-04 — Lookup a specific element or relationship type
As a modeler,  
I want to retrieve the full definition of a named element or relationship type  
so that I understand its meaning, aspect, and constraints.

### US-META-05 — Browse metamodel rules
As a modeler,  
I want to list the valid source/relationship/target rules in the metamodel  
so that I can verify whether a relationship between two types is allowed.

---

## Acceptance Criteria

### AC-META-01 · db_info
- **Given** `query_type=db_info`  
  **Then** the response contains `metamodel_db.path`, `metamodel_db.exists`, `model_db.path`, and `model_db.exists`.

### AC-META-02 · overview
- **Given** `query_type=overview` (or no query_type)  
  **Then** the response contains `counts.elements`, `counts.relationships`, `counts.rules`, `layers` list, and `relationship_categories` list.

### AC-META-03 · elements
- **Given** `query_type=elements` with no filters  
  **Then** all element types are returned ordered by layer then name.
- **Given** `layer` filter  
  **Then** only elements in that layer are returned (case-insensitive).
- **Given** `search` text  
  **Then** only elements whose name or definition contain the text are returned.
- **Given** `limit` is specified  
  **Then** no more than `limit` records are returned (max 500).

### AC-META-04 · relationships
- **Given** `query_type=relationships` with no filters  
  **Then** all relationship types are returned ordered by category then name.
- **Given** `category` filter  
  **Then** only relationships of that category are returned.
- **Given** `search` text  
  **Then** only matching relationships are returned.

### AC-META-05 · element (single lookup)
- **Given** `query_type=element` and a valid `name`  
  **Then** the single matching element record is returned.
- **Given** `name` is absent  
  **Then** `Error: name is required for query_type='element'` is returned.
- **Given** the name does not exist  
  **Then** `Error: element '…' not found` is returned.

### AC-META-06 · relationship (single lookup)
- **Given** `query_type=relationship` and a valid `name`  
  **Then** the single matching relationship record is returned.
- **Given** `name` is absent or not found  
  **Then** corresponding error messages are returned.

### AC-META-07 · rules
- **Given** `query_type=rules` with no filters  
  **Then** all rules are returned ordered by rule_type and source.
- **Given** `search` text  
  **Then** only rules whose source, target, or notes contain the text are returned.