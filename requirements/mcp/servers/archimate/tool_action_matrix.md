# ArchiMate MCP Tool Action Matrix (LLM-Compact)

Compact reference of ArchiMate MCP tools, actions/query types, and payload requirements.

## Invocation Discipline (critical)

- Use MCP tool calls over configured `stdio` transport.
- Resolve `model_id` context first (`archimate_current_model`) before model-scoped actions.
- Validate required payload fields before invocation.
- Do not mix transport styles (MCP + ad-hoc HTTP + direct module imports) in one workflow.
- For deterministic usage guidance, see `.github/agents/archimate architect.agent.md`.

## Conventions

- Router-style tools use `action` + `payload_json`.
- `none` means no field is required.
- `id OR at least one filter` means one of those selectors must be provided.
- `<...>` values are placeholders.

## 1) `archimate_metamodel_info`

- **Input style:** function arguments (not action router)
- **Function args:** `query_type`, `name?`, `layer?`, `category?`, `search?`, `limit?`

| query_type | Required fields | Notes |
|---|---|---|
| `db_info` | none | Returns metamodel/model DB paths + existence |
| `overview` | none | Dataset metadata + counts + layers/categories |
| `elements` | none | Optional filters: `layer`, `search`, `limit` |
| `relationships` | none | Optional filters: `category`, `search`, `limit` |
| `element` | `name` | Exact element lookup |
| `relationship` | `name` | Exact relationship lookup |
| `rules` | none | Optional filter: `search`, `limit` |

---

## 2) `archimate_metamodel_enhance`

- **Input style:** `action` + `payload_json`

| action | Required payload fields | Optional payload fields |
|---|---|---|
| `db_info` | none | none |
| `upsert_element` | `name`, `layer`, `aspect`, `definition` | `attributes`, `constraints` |
| `upsert_relationship` | `name`, `category`, `directed`, `definition` | `attributes`, `constraints` |
| `add_rule` | `rule_type`, `source`, `relationship`, `target`, `notes` | none |
| `add_annotation` | `target_type`, `target_name`, `note` | `source` |
| `list_annotations` | none | `target_type`, `target_name`, `limit` |
| `delete_annotation` | `id` OR at least one filter | `target_type`, `target_name`, `note`, `source` |
| `delete_rule` | `id` OR at least one filter | `rule_type`, `source`, `relationship`, `target`, `notes` |

---

## 3) `archimate_model_management`

- **Input style:** `action` + `payload_json`

| action | Required payload fields | Optional payload fields |
|---|---|---|
| `db_info` | none | none |
| `create_model` | `name` | `description`, `attributes`, `model_id`, `author` |
| `list_models` | none | `limit`, `search` |
| `get_model` | `model_id` | `include_graph` |
| `update_model` | `model_id` | `name`, `description`, `attributes`, `expected_version`, `author`, `message` |
| `delete_model` | `model_id` | none |
| `upsert_element` | `model_id`, `type_name`, `name` | `element_id`, `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `list_elements` | `model_id` | `type_name`, `search`, `valid_at`, `limit` |
| `delete_element` | `model_id`, `element_id` | `expected_version`, `author`, `message` |
| `upsert_relationship` | `model_id`, `type_name`, `source_element_id`, `target_element_id` | `relationship_id`, `name`, `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `list_relationships` | `model_id` | `type_name`, `source_element_id`, `target_element_id`, `valid_at`, `limit` |
| `delete_relationship` | `model_id`, `relationship_id` | `expected_version`, `author`, `message` |
| `list_versions` | `model_id` | `limit` |
| `get_version` | `model_id`, `version` | none |
| `revert_version` | `model_id`, `version` | `expected_version`, `author` |
| `validate_model` | `model_id` | none |
| `generate_report` | `model_id` | none |
| `generate_insights` | `model_id` | none |
| `generate_view_mermaid` | `model_id` | `direction`, `limit` |
| `export_csv` | `model_id` | `filename_prefix` |
| `import_csv` | `model_id`, `elements_csv`, `relationships_csv` | `replace`, `expected_version`, `author` |
| `export_xml` | `model_id` | none |
| `import_xml` | `model_id`, `xml` | `replace`, `expected_version`, `author` |
| `acquire_lock` | `model_id`, `owner` | `force` |
| `release_lock` | `model_id` | `owner`, `force` |
| `get_lock` | `model_id` | none |

---

## 4) `archimate_model_query`

- **Input style:** `action` + `payload_json`

| action | Required payload fields | Optional payload fields |
|---|---|---|
| `db_info` | none | none |
| `search_elements` | `model_id` | `type_name`, `layer`, `aspect`, `attribute_key`, `attribute_value`, `search`, `valid_at`, `limit` |
| `search_relationships` | `model_id` | `type_name`, `category`, `source_element_id`, `target_element_id`, `valid_at`, `limit` |
| `neighbors` | `model_id`, `element_id` | `direction`, `relationship_type`, `limit` |
| `path_exists` | `model_id`, `source_element_id`, `target_element_id` | `max_depth` |
| `temporal_slice` | `model_id`, `valid_at` | `layer`, `element_limit`, `relationship_limit` |
| `model_stats` | `model_id` | none |

---

## 5) `archimate_model_cud`

- **Input style:** `action` + `payload_json`
- **Purpose:** dedicated create/update/delete for elements and relationships

| action | Required payload fields | Optional payload fields |
|---|---|---|
| `db_info` | none | none |
| `create_element` | `model_id`, `type_name`, `name` | `element_id`, `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `update_element` | `model_id`, `element_id`, `type_name`, `name` | `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `delete_element` | `model_id`, `element_id` | `expected_version`, `author`, `message` |
| `create_relationship` | `model_id`, `type_name`, `source_element_id`, `target_element_id` | `relationship_id`, `name`, `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `update_relationship` | `model_id`, `relationship_id`, `type_name`, `source_element_id`, `target_element_id` | `name`, `attributes`, `valid_from`, `valid_to`, `expected_version`, `author`, `message` |
| `delete_relationship` | `model_id`, `relationship_id` | `expected_version`, `author`, `message` |

### Aliases (same behavior)

- `create_el` → `create_element`
- `update_el` → `update_element`
- `delete_el` → `delete_element`
- `create_rel` → `create_relationship`
- `update_rel` → `update_relationship`
- `delete_rel` → `delete_relationship`

---

## 6) Example Payloads

Use these directly as `payload_json` for router-style tools.

### 6.1 `archimate_model_management`

- **create_model**

```json
{
	"name": "Order Platform",
	"description": "Baseline architecture model",
	"author": "architect-a"
}
```

- **upsert_element**

```json
{
	"model_id": "<model-id>",
	"type_name": "Business Actor",
	"name": "Customer",
	"attributes": {"criticality": "high"},
	"expected_version": 1,
	"author": "architect-a"
}
```

- **upsert_relationship**

```json
{
	"model_id": "<model-id>",
	"type_name": "Serving",
	"source_element_id": "<element-a>",
	"target_element_id": "<element-b>",
	"expected_version": 2,
	"author": "architect-a"
}
```

- **validate_model**

```json
{
	"model_id": "<model-id>"
}
```

### 6.2 `archimate_model_query`

- **search_elements**

```json
{
	"model_id": "<model-id>",
	"layer": "Business",
	"search": "customer",
	"limit": 50
}
```

- **path_exists**

```json
{
	"model_id": "<model-id>",
	"source_element_id": "<element-a>",
	"target_element_id": "<element-b>",
	"max_depth": 4
}
```

### 6.3 `archimate_model_cud`

- **create_el**

```json
{
	"model_id": "<model-id>",
	"type_name": "Application Service",
	"name": "Checkout Service",
	"expected_version": 3,
	"author": "architect-a"
}
```

- **update_rel**

```json
{
	"model_id": "<model-id>",
	"relationship_id": "<rel-id>",
	"type_name": "Serving",
	"source_element_id": "<element-a>",
	"target_element_id": "<element-b>",
	"name": "serves",
	"expected_version": 4,
	"author": "architect-a"
}
```

- **delete_el**

```json
{
	"model_id": "<model-id>",
	"element_id": "<element-id>",
	"expected_version": 5,
	"author": "architect-a"
}
```

### 6.4 `archimate_metamodel_info`

- **query_type=element** (`name` argument required)

```json
{
	"query_type": "element",
	"name": "Business Actor"
}
```

- **query_type=rules**

```json
{
	"query_type": "rules",
	"search": "serv",
	"limit": 20
}
```

### 6.5 `archimate_metamodel_enhance`

- **upsert_element**

```json
{
	"name": "Policy",
	"layer": "Motivation",
	"aspect": "Motivation",
	"definition": "A directive that constrains behavior",
	"attributes": {"status": "custom"}
}
```

- **add_rule**

```json
{
	"rule_type": "custom",
	"source": "Policy",
	"relationship": "Influence",
	"target": "Requirement",
	"notes": "Policies can influence requirements"
}
```

---

## 7) Minimal End-to-End Workflow

Use this sequence to go from an empty workspace model to a validated/exported model.

1. **Create model** (`archimate_model_management`, `create_model`)
2. **Create elements** (`archimate_model_cud`, `create_el`) for core business/application/technology objects
3. **Create relationships** (`archimate_model_cud`, `create_rel`) between those elements
4. **Check structure** (`archimate_model_query`, `model_stats` and `path_exists`)
5. **Validate** (`archimate_model_management`, `validate_model`) and fix any errors
6. **Generate report/insights** (`generate_report`, `generate_insights`)
7. **Export**
   - CSV: `archimate_model_management` + `export_csv`
   - XML: `archimate_model_management` + `export_xml`

### Example sequence payloads

- **Step 1 – create_model**

```json
{
	"name": "Minimal Example",
	"author": "architect-a"
}
```

- **Step 2 – create_el**

```json
{
	"model_id": "<model-id>",
	"type_name": "Business Actor",
	"name": "Customer",
	"expected_version": 1,
	"author": "architect-a"
}
```

- **Step 3 – create_rel**

```json
{
	"model_id": "<model-id>",
	"type_name": "Serving",
	"source_element_id": "<element-a>",
	"target_element_id": "<element-b>",
	"expected_version": 3,
	"author": "architect-a"
}
```

- **Step 5 – validate_model**

```json
{
	"model_id": "<model-id>"
}
```

- **Step 7 – export_csv**

```json
{
	"model_id": "<model-id>",
	"filename_prefix": "minimal_example"
}
```

---

## 8) Workflow Variant: Versioned Collaborative Editing

Use this pattern when multiple clients may modify the same model.

1. **Acquire lock** (`archimate_model_management`, `acquire_lock`)
2. **Read current model/version** (`get_model` or `list_versions`)
3. **Perform changes with optimistic concurrency** (`expected_version` on every write)
4. **Handle conflicts**: if version mismatch occurs, re-read latest version and retry
5. **Validate + report** (`validate_model`, `generate_report`)
6. **Release lock** (`release_lock`)
7. **Optional rollback** (`revert_version`) if a bad change was committed

### Example payloads

- **Acquire lock**

```json
{
	"model_id": "<model-id>",
	"owner": "user-a"
}
```

- **Write with expected version (`create_el`)**

```json
{
	"model_id": "<model-id>",
	"type_name": "Application Component",
	"name": "Order API",
	"expected_version": 12,
	"author": "user-a"
}
```

- **Conflict retry pattern (`update_rel`)**

```json
{
	"model_id": "<model-id>",
	"relationship_id": "<rel-id>",
	"type_name": "Serving",
	"source_element_id": "<source-id>",
	"target_element_id": "<target-id>",
	"name": "serves-v2",
	"expected_version": 13,
	"author": "user-a"
}
```

- **Release lock**

```json
{
	"model_id": "<model-id>",
	"owner": "user-a"
}
```

- **Rollback (`revert_version`)**

```json
{
	"model_id": "<model-id>",
	"version": 10,
	"expected_version": 14,
	"author": "user-a"
}
```

### Notes

- `expected_version` protects against lost updates.
- Locking prevents simultaneous writers from stepping on each other.
- `revert_version` creates a new version; it does not delete history.

---

## 9) Troubleshooting

| Error text (example) | Likely cause | Fix |
|---|---|---|
| `Error: missing required field 'model_id'` | Required payload key not provided | Add the missing key in `payload_json` |
| `Error: payload_json is invalid JSON` | Malformed JSON string | Validate JSON syntax before calling the tool |
| `Error: Model '<id>' not found` | Wrong/old model ID | Call `list_models` and use a valid `model_id` |
| `Version conflict: expected X, but current version is Y` | Stale writer version | Re-read model/version, then retry with latest `expected_version` |
| `Error: update_element requires 'element_id'` | Update called without target ID | Provide `element_id` for update actions |
| `Error: update_relationship requires 'relationship_id'` | Update called without target relationship | Provide `relationship_id` for update actions |
| `Error: Source element '<id>' not found...` | Relationship endpoint doesn’t exist | Create/fix referenced element IDs first |
| `Error: relationship '<name>' not found` (metamodel) | Querying unknown metamodel relation | Use `query_type='relationships'` to inspect available names |
| `Error: element '<name>' not found` (metamodel) | Querying unknown metamodel element | Use `query_type='elements'` to inspect available names |
| `Error: delete_annotation requires id or at least one filter field` | Delete called without selector | Provide `id` or one/more filter fields |
| `Error: Model '<id>' is locked by '<owner>'` | Another client owns the lock | Wait, use lock owner, or call `acquire_lock` with `force=true` if appropriate |
| `Error: Lock owner mismatch...` | Unlock attempted by different owner | Use correct `owner` or `force=true` when releasing lock |

### Quick diagnostics

- Run `db_info` in any tool to verify SQLite file paths and existence.
- Run `model_stats` to confirm model has expected elements/relationships.
- Run `validate_model` after each write batch before export.
