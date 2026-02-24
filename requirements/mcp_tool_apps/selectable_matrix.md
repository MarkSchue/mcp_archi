# Overview
I want to create an mcp-tool for my agents and skills. The input of this tool is a json-format with entities inside. The tool is an mcp app with MCP Elicitation giving back a matrix where entries inside the matrix can be selected. We use the existing selectable_table as a template for that tool, which is an @mcp_tool registered in Python. The tool itself is a python tool registered as @mcp_tool.

# Requirements
- The tool should be created under src/mcp/tools/ and named selectable_matrix.
- The tool should take a json-format input with entities and display them in a matrix format.
- The entries in the matrix should be selectable, allowing users to interact with the data.
- When the user asks to show "business actors" over "processes" as an example, the matrix should show business actors as rows and processes as columns. The user should be able to select specific business actors and processes to see their interactions or relationships. 
- The user should be able to tik checkboxes to select specific relations in the matrix
- The relations selected in the matrix should be part of the selection in the chat, so that the user can further act on the selected relations (like it is done in the selectable_table). For example, if the user selects the relation between a specific business actor and a process, that relation should be included in the selection in the chat, allowing the user to ask for more details about that relation or to perform actions based on that selection.
- The matrix should also allow for filtering and sorting of the entries to help users find specific information more easily. For instance, users should be able to filter the matrix to show only certain types of entities or relationships, or sort the entries based on specific criteria such as name or relevance. This will enhance the usability of the tool and make it easier for users to navigate through the data presented in the matrix.
- We also need the column-filter like in the selectable_table, so that the user can filter the columns of the matrix based on specific criteria. 
- We also need the json-object functionality like in the selectable_table, so that the user can see the json-object of a specific entry in the matrix when they select it. This will provide users with more detailed information about the selected entry and allow them to understand the underlying data structure better. The json-object should be displayed in a clear and organized manner, making it easy for users to read and interpret the information.

# Task
Create a selectable matrix mcp-tool under src/mcp/tools/ for my agents and skills. The tool should take a json-format input with entities and display them in a matrix format. The entries in the matrix should be selectable, allowing users to interact with the data. Use React for the visualization part and ensure that the tool is registered as @mcp_tool in Python. The selected entries should be able to trigger further actions or provide additional information based on user interaction.

# Example: Business Actors over Processes
Use this example in skills/agents when a user asks for "business actors over processes".

## Expected relation shape
The matrix tool expects a list of relation objects where each object contains at least:
- `business_actor`
- `process`

Additional fields (for example `relationship_id`, `relationship_type`, `name`, `attributes`) are preserved and available in the JSON detail panel.

## Direct tool call example
```python
from mcp.servers.archimate.tools.selectable_matrix.tool import selectable_matrix
import json

relations = [
	{
		"relationship_id": "r1",
		"business_actor": "Erika Gruen",
		"process": "Order Handling",
		"relationship_type": "Assignment",
		"attributes": {"confidence": "high"}
	},
	{
		"relationship_id": "r2",
		"business_actor": "Max Mustermann",
		"process": "Customer Support",
		"relationship_type": "Serving",
		"attributes": {"confidence": "medium"}
	}
]

result = selectable_matrix(
	title="Business Actors × Processes",
	entities_json=json.dumps(relations),
	row_field="business_actor",
	column_field="process",
)
```

## Skill/agent prompt snippet
```text
When the user asks to show business actors over processes:
1) Build relation entities with fields `business_actor` and `process`.
2) Call tool `selectable_matrix` with:
   - title = "Business Actors × Processes"
   - entities_json = JSON array of relation entities
   - row_field = "business_actor"
   - column_field = "process"
3) The user's checkbox selections in the matrix become chat selection context
   (via selection_received), so follow-up actions can target selected relations.
```