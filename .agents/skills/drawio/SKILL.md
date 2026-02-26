````skill
---
name: drawio
description: Provides conversational generation of draw.io XML diagrams from ArchiMate entities and relationships. Use this skill when users want a diagram export or visual artifact from model data and need consistent ArchiMate 3.2 shapes (including appType and archiType metadata).
license: Complete terms in LICENSE.txt
---

This skill encapsulates usage of the `drawio` MCP tool in the ArchiMate
server. It converts model entities and relationships into draw.io XML that can
be opened directly in diagrams.net or used by downstream tooling.

## Core capabilities

- Accept entities and relationships in JSON format and generate complete
  draw.io XML (`mxfile` / `mxGraphModel` structure).
- Apply the project’s ArchiMate element mapping from `drawio.md`, including:
  - `shape`
  - `appType`
  - `archiType`
- Apply all attributes of entities and relationships as custom data attributes on the
  corresponding XML elements, ensuring that no information is lost in the
  transformation.
- Flatten json-serializable nested structures into string attributes using **dot notation** (e.g., `attributes.Department=R&D`), so that complex properties are preserved in the diagram metadata and shape data.  
- Special-case `tags`/`tags_json`: export all tag values as a single space-separated `tags` attribute (spaces within values are replaced by dots) to make tag searches easy in diagrams.net.
- Return XML plus stylesheet metadata for traceability and customization.
- Support mixed relationship types (for example `Serving`, `Triggering`,
  `Composition`, `Access`) with suitable edge styles.

## When to use

Use this skill when the user asks to:

- "create a draw.io diagram"
- "export this model/view as draw.io"
- "render entities and relations as ArchiMate diagram"
- "generate diagram XML for import into diagrams.net"

## Invocation policy

- Use this skill/tool only when the user explicitly asks to create, generate,
  render, or export a draw.io diagram.
- Do not call `drawio` implicitly for standard model exploration, CRUD tasks,
  or selectable table/matrix workflows.
- Do not call `drawio` as an automatic post-step after `create/update/delete`
  operations unless the user explicitly asked for a diagram in the same request.

## Mandatory data-embedding behavior

Every export MUST preserve shape/edge metadata in draw.io object format.

- Element nodes MUST be emitted as `<object ...>` wrappers with:
  - canonical wrapper form: `<object label="%name%" ...><mxCell .../></object>`
  - `placeholders="1"`
  - flattened attributes using dot notation (e.g., `attributes.Owner="Alice"`)
  - `element_id`, `type_name`, `name`
- Relationship edges MUST be emitted as `<object ...>` wrappers with:
  - canonical wrapper form: `<object label="%name%" ...><mxCell .../></object>`
  - `placeholders="1"`
  - flattened attributes using dot notation
  - `relationship_id`, `source_element_id`, `target_element_id`, `type_name`, `name`
- If required metadata is missing for any shape, the export is considered invalid.

## Agent execution requirements

When acting as the coding agent, you must not stop at calling the tool. You must validate the generated file:

1. Open the produced `.drawio` file.
2. Verify it contains `<object` nodes in canonical form with `label="%name%"` (not only plain `<mxCell>` nodes for elements).
3. Verify at least one element object contains `element_id=` and flattened data attributes.
4. Verify at least one relationship object contains `relationship_id=` and flattened data attributes.
5. If checks fail, fix tool/code and re-export in the same session.

Do not report success without these checks.

## Tool contract

Call:

- `drawio(entities_json, relationships_json="[]", title="ArchiMate Diagram", explicit_after_mutation=false)`

Input expectations:

- `entities_json` (required, non-empty array):
  - `id` or `element_id`
  - `type_name` or `type`
  - `name`
- `relationships_json` (optional array):
  - `source_element_id` or `source_id` or `source`
  - `target_element_id` or `target_id` or `target`
  - `type_name` or `type`
- `explicit_after_mutation` (optional bool, default `false`):
  - required to be `true` when calling drawio immediately after a write action
    (`create/update/delete/import/revert`) and the user explicitly asked for export.

Output payload includes:

- `title`
- `entity_count`
- `relationship_count`
- `drawio_xml`
- `stylesheet`
- `file` (path to exported `.drawio` file in the workspace `output/` directory, when writing succeeds)
- `stylesheet_file` (path to the static editable CSS file in `src/mcp/servers/archimate/tools/drawio/styles.css`)

## Runtime guardrail

- The server blocks drawio calls shortly after model mutations unless
  `explicit_after_mutation=true`.
- This prevents accidental diagram exports as unintended side effects of
  update/delete workflows.

## Conversational pattern

The tool writes its XML to a timestamped file under `output/` and returns the
`file` path; it also returns the static `stylesheet_file` path for styling updates.


1. Determine the target scope (current model, filtered subset, selected rows,
   etc.).
2. Gather entities/relationships from query tools or selection context.
3. Normalize to the drawio tool contract.
4. Call `drawio` and present a concise result summary.
5. Offer next actions (save/export/open/import).

## Example dialogue

```text
User> Generate a draw.io diagram for business actors and their processes.
Assistant> (queries entities + relationships, calls drawio)
Assistant> Created draw.io XML with 12 entities and 18 relationships.

User> Include only triggering relations.
Assistant> (filters relationship set and calls drawio again)
```

## Notes

- If a type is unknown to the mapping, the tool falls back to a generic
  ArchiMate application shape.
- For reproducibility, keep stable IDs when possible.
- Element shapes include embedded draw.io data attributes containing the full
  entity JSON input (nested values are serialized as JSON strings).
- Relationship edges include embedded draw.io data attributes containing the full
  relationship JSON input (nested values are serialized as JSON strings).
- For large graphs, consider filtering to a focused viewpoint before
  generation.
````
