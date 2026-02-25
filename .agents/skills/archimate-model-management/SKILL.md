---
name: archimate-model-management
description:   Provides high-level assistance for managing ArchiMate models within the  MCP servers. Use this skill when the user asks to create, update, delete, import or export models, manage versions, or perform related actions. It knows how to call the `archimate_model_management` tool and interpret its JSON payloads and responses.
license: Complete terms in LICENSE.txt
---

This skill encapsulates the workflows around the `archimate_model_management`
MCP tool. It also cooperates with a companion `archimate_current_model` tool
which can remember a "current" model id for the duration of a conversation.

## Canonical execution path (must follow)

Use only MCP tool calls in this order:

1. Resolve model context (`archimate_current_model.get` / `find` / `set`)
2. Validate required fields for the target action
3. Call one ArchiMate tool (`archimate_model_management`, `archimate_model_query`, `archimate_model_cud`, or `archimate_attribute_dictionary`)
4. Parse `TextContent[0].text` as JSON when possible
5. Report result and next safe action

Do **not** switch transport or runtime mid-flow.

## Intent boundary and tool-chaining policy

Default behavior is single-intent execution:

- Perform only the tool action needed to satisfy the user request.
- Do not trigger secondary workflows unless explicitly requested.

Examples:

- "update element" → run update + optional verification query; do not export.
- "list models" → list only; do not open matrix/table automatically.
- "validate model" → validate only; do not generate report unless asked.

Disallowed implicit side effects:

- draw.io export
- CSV/XML export
- matrix/table visualization
- insights/report generation

Allowed implicit follow-up: minimal read-back verification for write operations.

## Transport and runtime rules

- Server transport is MCP over `stdio` (configured in `.vscode/mcp.json`).
- Use MCP tools directly; do not invent or assume HTTP endpoints.
- Do not run ad-hoc Python import scripts as a primary path for normal user requests.
- Keep one consistent execution context per request; avoid "tool call + curl + direct sqlite + python snippet" mixing.

## Preflight checks before any write action

Before calling any create/update/delete action, verify:

- `model_id` is resolved and exists
- required payload fields for the action are present
- ids referenced by relationships (source/target) exist
- if request is name-based, resolve names to IDs via query first
- if versioning is used, pass `expected_version`

If any check fails, fix the payload first instead of trying alternative transports.

## Error handling policy

- If tool returns `Error: ...`, keep the same MCP path and correct the payload/action.
- Never fall back to HTTP or ad-hoc module imports to "force" execution.
- When model lookup fails, call `list_models` or `archimate_current_model.find` and retry with the returned id.
- When action is unknown, map user intent to the action matrix and retry once with corrected action name.

When invoked the assistant should:

1. Determine the user's intent (create a model, list models, import from XML
   or CSV, upsert elements, etc.).
2. If the user refers to *the* current model (e.g. "in the testmodel" or
   "for my project"), either use the id previously stored via
   `archimate_current_model` or prompt the user to set it.
3. Construct the appropriate `action` string and JSON payload for the
   relevant tool – `archimate_model_management` for management operations,
   `archimate_model_query` for read‑only queries, or `archimate_current_model`
   when setting/getting the current model.
4. Call the tool(s) using the MCP API, handle errors, and interpret the
   results.
5. Present the outcome in clear plain language, optionally showing the JSON
   returned when useful.

The presence of the `archimate_current_model` tool allows natural-language
conversations like "remember that testmodel" followed by "list all business
actors in it" without re‑supply of the ID each time.

**Common scenarios**

- **Model creation**: ask for a name (and optional description/attributes),
  generate or accept a model ID, call `create_model`, and report the new ID.  The
  newly created model will automatically be remembered as the current model for
  subsequent conversational queries.

- **Attribute dictionary**: each model can maintain a list of allowed
  attribute keys for elements and relationships.  This is now exposed as a
  standalone tool (`archimate_attribute_dictionary`) with actions `define`,
  `list` and `delete`, though the management tool also proxies the same
  operations.  When defining an attribute you specify the model, target type
  (`element` or `relationship`), key, and optional description.  Subsequent
  element or relationship upserts may include those keys, and they can be
  searched via `attribute_key`/`attribute_value` filters.  This ensures
  consistent naming across the model.

- **Name lookup**: when the user refers to a model by (partial) name, the
  assistant can call the `archimate_current_model` tool with `action="find"`
  to search for matching model names.  If a unique or best match is found, the
  assistant may set it as the current model and proceed; otherwise it should
  ask the user to clarify which model they meant.
- **Importing data**: instruct the user to supply an XML/CSV file path or
  content, call `import_xml`/`import_csv` with the model_id and file, and show
  success or errors.
- **Querying models**: use `list_models` with filters or `get_model` to fetch
  details (graph, element counts, etc.).
- **Versioning**: call `list_versions`, `get_version`, `revert_version` as
  requested; explain the effect.
- **Element/relationship operations**: map user requests to `upsert_element`,
  `delete_element`, `upsert_relationship`, etc.
- **Matrix visualization of relations**: when users ask for cross-views like
  "business actors over processes", prepare relation entities containing the
  two axis fields and call `selectable_matrix` with:
  - `title` (for example "Business Actors × Processes")
  - `entities_json` (JSON array of relation objects)
  - `row_field` (for example `business_actor`)
  - `column_field` (for example `process`)
  Selections made in the matrix are propagated into chat selection context,
  so follow-up actions can target only selected relations.

  **Example dialogue**

  ```text
  User> Show business actors over processes in a matrix.
  Assistant> (assemble relations, call selectable_matrix with appropriate
            fields)

  User> I clicked a few checkboxes; what did I select?
  Assistant> (read selection_received context and describe the selected
            relation objects)
  ```
- **Exporting**: support `export_csv`/`export_xml` by specifying output paths.

**Guidelines**

- Always validate required fields (model_id, name, etc.) and inform the user
  if something is missing before calling the tool.
- When dealing with file I/O (import/export), clarify whether the user has
  provided a workspace path or expects to upload content; tailor the
  instructions accordingly.
- Remember that the tool returns results as a list of `TextContent` objects.
  The first element typically contains the JSON payload; decode it for the
  final message.
- For error cases, surface the tool's error message verbatim so the user can
  act on it.

## Anti-patterns (explicitly avoid)

- Calling `curl http://localhost...` for ArchiMate tools
- Running `python -m mcp.servers.archimate` when workspace config uses `python -m servers.archimate` from `src/mcp`
- Using relative-import hacks to execute tool modules directly
- Continuing with stale `model_id` after `Model not found` error

This skill is primarily used in the context of the MCP workspace and the
`archimate` server; it should not try to implement its own data persistence or
network logic. It orchestrates calls to the existing Python tools in the
repository.