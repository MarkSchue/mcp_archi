---
name: archimate-model-cud
description: Helps users create, update, and delete elements and relationships within an ArchiMate model. This skill is used when the user wants to modify the contents of a model rather than just query it; typical requests include adding a new actor, deleting a process, or adjusting relationships.  

license: Complete terms in LICENSE.txt
---

The `archimate_model_cud` tool provides CRUD operations on model elements and
relationships. It is designed to work together with the `archimate_current_model`
tool (for remembering which model is in focus) and the broader
`archimate_model_management` skill for model-wide operations.

## Actions

- **db_info** – return database file locations.
- **create_element/update_element/delete_element** – manage individual
  elements.  The skill will ask for type, name, attributes, validity dates,
  etc., and supply the current model ID if one is active.
- **create_relationship/update_relationship/delete_relationship** – manage
  relationships linking two elements.  Type name, source/target IDs, and
  optional name or attributes can be specified.
- Short aliases are available (create_el, update_el, create_rel, etc.).

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