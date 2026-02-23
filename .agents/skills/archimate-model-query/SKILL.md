---
name: archimate-model-query
description: Provides conversational access to the read-only query APIs for ArchiMate models.  Use this skill when the user wants to look up elements, relationships, neighbors, path existence, or other derived information from a model without writing any code. It knows how to call the `archimate_model_query` tool with appropriate JSON payloads based on the user's natural language requests, and can also coordinate with `archimate_current_model` to resolve model references and `selectable_table` to display results in an interactive format.
license: Complete terms in LICENSE.txt
---

This skill is centred around the `archimate_model_query` tool and knows about
related utilities such as `archimate_current_model`, the `archimate_attribute_dictionary`
tool for managing attribute vocabularies, and the selectable-table UI.  It allows users to ask questions like "find all business actors",
"what serves the sales process?", or "show me the neighbors of element X"
using plain language.  No Python snippets are required.

## Core capabilities

- **search_elements** – filter elements by type, layer, aspect, attribute,
  text search or validity date.  Commonly used to list all actors/services/etc.
- **search_relationships** – find relationships (with optional type,
  category, source/target filters) and return their metadata.
- **neighbors** – given an element ID, fetch adjacent elements and connecting
  relationships in a specified direction.
- **path_exists** – check whether a directed path exists between two element
  IDs (useful for reachability queries).
- **temporal_slice** – return the set of elements/relationships valid at a
  particular date, optionally restricted to layers.
- **model_stats** – quick counts of elements/relationships/types for a model.
- **db_info** – return the file locations and existence of the metamodel and
  model databases (mostly for debugging).

Every action accepts a `payload_json` argument.  For convenience, the skill
will automatically supply the currently selected model ID (via the
`archimate_current_model` tool) when the user doesn’t specify one.  In other
words, after you’ve said "remember the Testmodel", simply asking "list all
business actors" will work without further identifiers.

## Conversational patterns

- **Direct requests**: "List all business actors in the current model",
  "Search for application components containing 'auth' in the name",
  "Show me all relationships of type Serving".
- **Natural filters**: "Give me the elements in the Business layer",
  "Anything valid on 2026-03-01?", "Relationships where the source is Alice".
- **Existence questions**: "Does a path exist from actor A to process B?"
- **Neighbor queries**: "What neighbors does the sales process have?"
- **Combined with current model**: "In the Testmodel, who serves the sales
  process?" (the skill will lookup the model by name using
  `archimate_current_model` if needed).
- **Displaying results**: invoke `selectable_table` when tabular output would
  be helpful.  The skill can automatically render lists of elements or
  relationships in selectable tables; just ask "show them in a table".

## Coordinating tools

- **`archimate_current_model`** – used to remember or resolve the active
  model when the user refers to it by name ("that model", "Testmodel").
  The query skill will call this when a `model_id` isn’t provided by the
  user.
- **`selectable_table`** – after executing a query, the skill can pass the
  returned list to this tool to display an interactive table.  For example,
  "show the result in a selectable table".
- **Model-management tools** – while this skill is read-only, it is aware of
  the larger management skill and may suggest creating or modifying elements
  via `archimate_model_management` or `archimate_model_cud` when appropriate.

**Note:** Because the skill handles payload construction internally, you can
ask questions and the assistant will translate them into the appropriate
`action` and JSON.  There is no need to write or execute any Python code.

## Example dialogues

```text
User> In the Testmodel, find all business actors.
Assistant> (runs search_elements with type_name=Business Actor)

User> Show the results in a table.
Assistant> (passes rows to selectable_table)

User> Who serves the sales process?
Assistant> (search_relationships for type=Serving, target=SalesProcessID,
          then look up source element names)

User> Are there any paths from actor A to process B?
Assistant> (path_exists query)

User> What neighbors does that element have?
Assistant> (neighbors query)
```

The goal of this skill is to make model exploration as easy as chatting with a
colleague.  Just describe what you want to know; the underlying MCP tools
(and the companion query/query-management skills) will handle the details.