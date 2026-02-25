# Overview
I want to create an mcp-tool for my agents and skills. The input of this tool is a json-format with entities and their relationships inside. The tool itself is a python tool registered as @mcp_tool. The tool should output a draw.io diagram based on the input data, leveraging the draw.io XML format to represent the entities and their relationships visually. Inside draw.io, use the shapes representing archimate 3.2 elements and relationships, so that the resulting diagram is not only visually appealing but also semantically meaningful for users familiar with ArchiMate. The tool should be able to handle various types of entities and relationships, allowing for a comprehensive visualization of complex models.

# Requirements
- The tool should be created under src/mcp/tools/ and named drawio.
- The tool should take a json-format input with entities and their relationships and output a draw.io XML diagram representing those entities and relationships visually.
- The tool should use shapes representing ArchiMate 3.2 elements and relationships to ensure that the resulting diagram is semantically meaningful for users familiar with ArchiMate.
- The tool should be able to handle various types of entities and relationships, allowing for a comprehensive visualization of complex models. For example, it should be able to represent business actors, processes, applications, and their interactions in a clear and organized manner.
- The tool should also allow for customization of the diagram, such as adjusting the layout, colors, and styles of the shapes to enhance the visual appeal and clarity of the diagram. This will help users to better understand the relationships between the entities and to identify key components in the model more easily.
- The tool should be efficient in processing the input data and generating the draw.io XML output, ensuring that it can handle large and complex models without significant performance issues. This will allow users to visualize their models quickly and effectively, even when dealing with a large number of entities and relationships.
- The tool should also create a stylesheet file, where color, font and shape information is stored, so that the resulting diagram can be easily customized and styled according to user preferences. This will provide users with greater flexibility in how they visualize their models and allow them to create diagrams that are both informative and visually appealing.

# ArchiMate Element → draw.io Shape Mapping (with appType + archiType)
For mapping of archimate elements, use the following shape mapping:

Application Collaboration: shape=mxgraph.archimate3.collaboration; appType=collab; archiType=square
Application Component: shape=mxgraph.archimate3.component; appType=comp; archiType=square
Application Event: shape=mxgraph.archimate3.event; appType=event; archiType=rounded
Application Function: shape=mxgraph.archimate3.function; appType=func; archiType=rounded
Application Interaction: shape=mxgraph.archimate3.interaction; appType=interaction; archiType=rounded
Application Interface: shape=mxgraph.archimate3.interface; appType=interface; archiType=square
Application Process: shape=mxgraph.archimate3.process; appType=proc; archiType=rounded
Application Service: shape=mxgraph.archimate3.service; appType=serv; archiType=rounded
Artifact: shape=mxgraph.archimate3.artifact; appType=artifact; archiType=square
Assessment: shape=mxgraph.archimate3.assess; appType=assess; archiType=oct
Business Actor: shape=mxgraph.archimate3.actor; appType=actor; archiType=square
Business Collaboration: shape=mxgraph.archimate3.collaboration; appType=collab; archiType=square
Business Event: shape=mxgraph.archimate3.event; appType=event; archiType=rounded
Business Function: shape=mxgraph.archimate3.function; appType=func; archiType=rounded
Business Interaction: shape=mxgraph.archimate3.interaction; appType=interaction; archiType=rounded
Business Interface: shape=mxgraph.archimate3.interface; appType=interface; archiType=square
Business Object: shape=mxgraph.archimate3.businessObject; appType=passive; archiType=square
Business Process: shape=mxgraph.archimate3.process; appType=proc; archiType=rounded
Business Role: shape=mxgraph.archimate3.role; appType=role; archiType=square
Business Service: shape=mxgraph.archimate3.service; appType=serv; archiType=rounded
Capability: shape=mxgraph.archimate3.capability; appType=capability; archiType=rounded
Communication Network: shape=mxgraph.archimate3.network; appType=netw; archiType=square
Constraint: shape=mxgraph.archimate3.constraint; appType=constraint; archiType=oct
Contract: shape=mxgraph.archimate3.contract; appType=contract; archiType=square
Course of Action: shape=mxgraph.archimate3.course; appType=course; archiType=rounded
Data Object: shape=mxgraph.archimate3.passive; appType=passive; archiType=square
Deliverable: shape=mxgraph.archimate3.deliverable; appType=deliverable; archiType=None
Device: shape=mxgraph.archimate3.device; appType=device; archiType=None
Distribution Network: shape=mxgraph.archimate3.distribution; appType=distribution; archiType=square
Driver: shape=mxgraph.archimate3.driver; appType=driver; archiType=oct
Equipment: shape=mxgraph.archimate3.equipment; appType=equipment; archiType=square
Facility: shape=mxgraph.archimate3.facility; appType=facility; archiType=square
Gap: shape=mxgraph.archimate3.gapIcon; appType=gap; archiType=None
Goal: shape=mxgraph.archimate3.goal; appType=goal; archiType=oct
Grouping: shape=mxgraph.archimate3.grouping; appType=grouping; archiType=square
Implementation Event: shape=mxgraph.archimate3.event; appType=event; archiType=rounded
Junction: shape=mxgraph.archimate3.junction; appType=None; archiType=None
Location: shape=mxgraph.archimate3.locationIcon; appType=location; archiType=square
Material: shape=mxgraph.archimate3.material; appType=material; archiType=square
Meaning: shape=mxgraph.archimate3.meaning; appType=meaning; archiType=oct
Node: shape=mxgraph.archimate3.node; appType=node; archiType=square
Outcome: shape=mxgraph.archimate3.outcome; appType=outcome; archiType=oct
Path: shape=mxgraph.archimate3.path; appType=path; archiType=square
Plateau: shape=mxgraph.archimate3.plateau; appType=plateau; archiType=None
Principle: shape=mxgraph.archimate3.principle; appType=principle; archiType=oct
Product: shape=mxgraph.archimate3.product; appType=product; archiType=square
Representation: shape=mxgraph.archimate3.representation; appType=representation; archiType=square
Requirement: shape=mxgraph.archimate3.requirement; appType=requirement; archiType=oct
Resource: shape=mxgraph.archimate3.resource; appType=resource; archiType=square
Stakeholder: shape=mxgraph.archimate3.role; appType=role; archiType=oct
System Software: shape=mxgraph.archimate3.sysSw; appType=sysSw; archiType=square
Technology Collaboration: shape=mxgraph.archimate3.collaboration; appType=collab; archiType=square
Technology Event: shape=mxgraph.archimate3.event; appType=event; archiType=rounded
Technology Function: shape=mxgraph.archimate3.function; appType=func; archiType=square
Technology Interaction: shape=mxgraph.archimate3.interaction; appType=interaction; archiType=rounded
Technology Interface: shape=mxgraph.archimate3.interface; appType=interface; archiType=square
Technology Process: shape=mxgraph.archimate3.process; appType=proc; archiType=rounded
Technology Service: shape=mxgraph.archimate3.service; appType=serv; archiType=rounded
Value: shape=mxgraph.archimate3.value; appType=amValue; archiType=oct
Value Stream: shape=mxgraph.archimate3.valueStream; appType=valueStream; archiType=rounded
Work Package: shape=mxgraph.archimate3.workPackage; appType=workPackage; archiType=rounded

# Tool Usage (`drawio`)

## Tool signature

`drawio(entities_json: str, relationships_json: str = "[]", title: str = "ArchiMate Diagram")`

## Input format

- `entities_json`: JSON array of objects with at least:
	- `id` (or `element_id`)
	- `type_name` (or `type`)
	- `name`
- `relationships_json`: JSON array of objects with at least:
	- `source_element_id` (or `source_id` / `source`)
	- `target_element_id` (or `target_id` / `target`)
	- `type_name` (or `type`)

## Example call payload

```json
{
	"title": "Business Example",
	"entities_json": "[\n  {\"id\":\"a1\",\"type_name\":\"Business Actor\",\"name\":\"Sales Rep\"},\n  {\"id\":\"p1\",\"type_name\":\"Business Process\",\"name\":\"Order Handling\"}\n]",
	"relationships_json": "[\n  {\"id\":\"r1\",\"type_name\":\"Triggering\",\"source_element_id\":\"a1\",\"target_element_id\":\"p1\"}\n]"
}
```

## Output format

The tool returns a JSON payload (inside `TextContent`) with:

- `title`
- `entity_count`
- `relationship_count`
- `drawio_xml` (complete draw.io XML document)
- `stylesheet` (the ArchiMate element mapping used by the tool)
- `file` *(optional)* – full path to a `.drawio` file written in the workspace `output/` directory.
- `stylesheet_file` – path to the static editable stylesheet at `src/mcp/servers/archimate/tools/drawio/styles.css`.

The XML file is created automatically whenever possible; the filename uses the diagram title and a timestamp to avoid collisions.
The CSS stylesheet is static and is not generated dynamically.

## Data mapping
- Each entity is exported in a wrapped `<object>` node with `placeholders="1"` and data attributes for all fields. When having a `raw_json` the json-object is flattened and also exported as data attribute. Use the "." notation to flatten nested JSON objects (for example `attributes.confidence=high`).
- Each relationship is exported as an `<object>` edge with `placeholders="1"` and data attributes for all fields, including `source_element_id` and `target_element_id` to link to the corresponding entity nodes. The relationship's `raw_json` is also flattened and exported as data attributes.
- The tool should ensure that all required metadata is included in the exported XML to maintain the integrity of the diagram and to allow for potential round-tripping (importing back into the system with full fidelity).


## Notes

- Element rendering uses the mapping in this document.
- Unknown element types fall back to a generic ArchiMate application shape.
- Relationship arrow styles are inferred from relationship type (for example `Triggering`, `Serving`, `Composition`, `Access`).
- Each element is exported as a draw.io `UserObject` with data key-value attributes so the shape contains the full input JSON payload (including nested objects serialized as JSON text).