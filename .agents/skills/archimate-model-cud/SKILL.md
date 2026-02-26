---
name: archimate-model-cud
description: Helps users create, update, and delete elements and relationships within an ArchiMate model. This skill is used when the user wants to modify the contents of a model rather than just query it; typical requests include adding a new actor, deleting a process, or adjusting relationships.  

license: Complete terms in LICENSE.txt
---

The `archimate_model_cud` tool provides CRUD operations on model elements and
relationships. It is designed to work together with the `archimate_current_model`
tool (for remembering which model is in focus) and the broader
`archimate_model_management` skill for model-wide operations.

## Canonical write workflow (must follow)

1. Resolve model context (`archimate_current_model.get` or `find` + `set`)
2. Resolve IDs via `archimate_model_query` if user input is name-based
3. Validate required fields for selected CUD action
4. Execute one `archimate_model_cud` action with valid JSON payload
5. Verify outcome with a read query (`search_elements` / `search_relationships`)

Keep all steps in MCP tool calls; do not switch to HTTP or ad-hoc Python execution.

## Intent boundary (critical)

For CUD requests, execute only CUD + optional read verification.

- Allowed implicit follow-up: one read verification query to confirm the write.
- Forbidden implicit follow-ups: `drawio`, `export_csv`, `export_xml`, `selectable_table`, `selectable_matrix`, report/insight generation.
- Run export/diagram/table actions only if the user explicitly asks for them in the same turn.

If the user says "update element X", do exactly that and stop after confirmation.

## Required field checklist

- `create_element`: `model_id`, `type_name`, `name`
- `update_element`: `model_id`, `element_id`, `type_name`, `name`
- `delete_element`: `model_id`, `element_id`
- `create_relationship`: `model_id`, `type_name`, `source_element_id`, `target_element_id`
- `update_relationship`: `model_id`, `relationship_id`, `type_name`, `source_element_id`, `target_element_id`
- `delete_relationship`: `model_id`, `relationship_id`
- `add_tag`: `model_id`, `key`, and exactly one of `element_id` or `relationship_id`; optional `value` (default "")
- `remove_tag`: `model_id`, `key`, and exactly one of `element_id` or `relationship_id`

If any required field is missing, request/resolve it before executing.

## Transport rules

- Use MCP tool invocation only (configured `stdio` server).
- Do not call local HTTP endpoints for CUD operations.
- Do not use direct module-import hacks to invoke tools.

## Actions

- **db_info** – return database file locations.
- **create_element/update_element/delete_element** – manage individual
  elements.  The skill will ask for type, name, attributes, validity dates,
  etc., and supply the current model ID if one is active.
- **create_relationship/update_relationship/delete_relationship** – manage
  relationships linking two elements.  Type name, source/target IDs, and
  optional name or attributes can be specified.
- **add_tag** – attach a tag (key/value pair) to an element or relationship.
  The tag key must be pre-registered in the attribute dictionary with
  `is_tag=true`.  Tags are stored separately from `attributes` and can be
  searched via the query tool's `tag_key` / `tag_value` filters.
  Example payload: `{"model_id": "...", "element_id": "...", "key": "priority", "value": "high"}`
- **remove_tag** – remove a tag key from an element or relationship.
  Silently no-ops if the key is absent.
  Example payload: `{"model_id": "...", "element_id": "...", "key": "priority"}`
- Short aliases are available (create_el, update_el, create_rel, etc.).

## Tag workflow

Before using `add_tag` / `remove_tag`, the tag key must exist in the
attribute dictionary for the same `target_type`:

1. `archimate_attribute_dictionary` action=`define` with `is_tag=true`
2. `archimate_model_cud` action=`add_tag` with `element_id` or `relationship_id`
3. Verify with `archimate_model_query` action=`search_elements` using `tag_key`

## Conversational examples

```text
User> Add a business actor named 'Sales Rep' to the current model.
Assistant> (calls create_element with type_name='Business Actor', name='Sales Rep')

User> Connect Sales Rep to the sales process with a Serving relationship.
Assistant> (asks for the IDs or resolves names, then calls create_relationship)

User> Update the name of that actor to 'Senior Sales Rep'.
Assistant> (calls update_element specifying the element_id and new name)

User> Delete the "obsolete" process element.
Assistant> (calls delete_element with appropriate ID)

User> Tag the 'Sales Rep' element with priority=high.
Assistant> (verifies 'priority' exists in the attribute dictionary with is_tag=true,
          then calls add_tag with element_id=<Sales Rep ID>, key='priority', value='high')

User> Remove the priority tag from 'Sales Rep'.
Assistant> (calls remove_tag with element_id=<Sales Rep ID>, key='priority')
```

## Model context and defaults

When no `model_id` is provided, this skill will attempt to use the current
model remembered via `archimate_current_model`.  New elements and
relationships will automatically be added to that model unless another is
specified.

## Safeguards

- The skill checks for required fields and prompts for missing information
  (e.g. you can’t create a relationship without both source and target IDs).
- When deleting, the assistant will usually confirm to prevent accidental
  removals.

## Common failure recovery

- `Model '<id>' not found`: run model lookup (`list_models` / `find`), then retry with valid id
- `missing required field`: resolve ID/name mismatch via query tool and retry
- `unknown action`: remap to canonical action or alias and retry once

## Integration

This skill is part of the ArchiMate tooling family and complements:

- **`archimate_model_query`** – for looking up IDs or verifying structure.
- **`archimate_model_management`** – for higher‑level model operations such as
  importing/exporting or version control.
- **`selectable_table`** – results of queries used to choose elements before
  modifying them can be shown in a table for easy selection.

Use this skill whenever you want to make changes to your model.  Describe the
modification in natural language, and the assistant will translate it into the
appropriate tool call; no Python code is needed.