# Tool: drawio

## User Stories

### US-DIO-01 — Export elements to a Draw.io diagram
As an architect,  
I want to generate a Draw.io XML file from a list of ArchiMate elements  
so that I can visualize the architecture in diagrams.net using correct ArchiMate shapes.

### US-DIO-02 — Include relationships as edges
As an architect,  
I want to include relationships between elements in the generated diagram  
so that the structural connections are visible in the visual output.

### US-DIO-03 — Embed element data attributes in shapes
As an architect,  
I want all element and relationship metadata to be embedded as XML attributes on `<object>` wrappers  
so that I can inspect and use the data inside Draw.io's Edit Data panel.

### US-DIO-04 — Enforce correct XML structure
As a developer,  
I want the tool to validate the generated XML before writing the file  
so that structurally invalid diagrams are never produced.

### US-DIO-05 — Block accidental post-mutation exports
As a developer,  
I want the tool to refuse a draw.io export that immediately follows a model mutation  
unless the caller explicitly confirms the intent  
so that stale diagrams are not silently generated.

---

## Acceptance Criteria

### AC-DIO-01 · Shape rendering
- **Given** a valid list of entities  
  **Then** each entity is rendered as a `<object>` wrapping a `<mxCell>` with the correct ArchiMate shape style (`mxgraph.archimate3.*`, `appType`, `archiType`).
- **Given** an element type that has no registered style  
  **Then** a default fallback style is used without error.

### AC-DIO-02 · Relationship edges
- **Given** a list of relationships whose `source_element_id` and `target_element_id` match nodes in the entity list  
  **Then** each is rendered as an edge `<object>` with `source` and `target` referencing the correct node ids.
- **Given** a relationship references an element not in the entity list  
  **Then** the edge is still generated (draw.io will show a disconnected edge).

### AC-DIO-03 · Canonical `<object>` structure
- **Given** any generated node or edge  
  **Then** the `id` attribute is present on `<object>` and absent from the inner `<mxCell>`.
- **Given** any generated node or edge  
  **Then** the `value` attribute is absent from the inner `<mxCell>` (label is on `<object>` as `label="%name%"`).
- **Given** any generated node  
  **Then** `placeholders="1"` is set on `<object>`.

### AC-DIO-04 · Data attribute embedding
- **Given** an entity has nested `attributes` dict (e.g. `{"Department": "R&D"}`)  
  **Then** these are flattened and embedded as `attributes.Department="R&amp;D"` on the `<object>`.
- **Given** an entity has a `tags_json` dict (e.g. `{
    "critical": "yes", "priority": "yes"}`)  
  **Then** these are flattened and embedded as `tags="critical priority"` on the `<object>` (values containing spaces use dots).  
- **Given** reserved keys (`id`, `label`, `placeholder`, `placeholders`) appear in the raw data  
  **Then** they are prefixed with `data_` to avoid XML attribute collisions.

### AC-DIO-04.1 Tag attribute embedding
- **Given** an element has a `tags_json` dict (e.g. `{"priority": "high", "status": "critical"}`)  
  **Then** these are flattened and embedded as `tags="high critical"` on the `<object>`, seperated by spaces for easy searching in Draw.io.
- **Given** a tag value contains spaces (e.g. `{"high value": "yes"}`)  
  **Then** the entire value is included in the `tags` attribute with a dot (e.g. `tags="high.value"`), allowing for multi-word tags.


### AC-DIO-05 · Unique IDs
- **Given** the XML is generated  
  **Then** nodes receive ids `n1`, `n2`, … and edges receive ids `r1`, `r2`, …, with no duplicates across the entire document.
- **Given** the validator finds a duplicate id  
  **Then** export is aborted with a descriptive error.

### AC-DIO-06 · Wrapper validation
- **Given** the generated XML contains a `<UserObject>` tag or any non-`object` wrapper  
  **Then** export is aborted with `Error: forbidden wrapper tag '…'`.
- **Given** `<mxCell>` inside `<object>` has an `id` or `value` attribute  
  **Then** export is aborted with a structural validation error.

### AC-DIO-07 · Post-mutation guardrail
- **Given** a model write operation was performed in the same session  
  **Then** calling the draw.io tool without `explicit_after_mutation=true` returns an error or warning.
- **Given** `explicit_after_mutation=true` is passed  
  **Then** the export proceeds normally.

### AC-DIO-08 · Output file
- **Given** the export succeeds  
  **Then** a `.drawio` file is written to the `output/` directory with a timestamped name.
- **Given** the export succeeds  
  **Then** the response contains `file`, `entity_count`, `relationship_count`, `object_count`, and the full `drawio_xml`.