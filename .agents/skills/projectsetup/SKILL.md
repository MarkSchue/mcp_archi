---
name: projectsetup
description: Explains how this MCP-server project is structured, scaffolded, and run. Use this skill when onboarding, when setting up a new MCP server, or when debugging import/path issues. Covers directory layout, virtual-environment conventions, tool registration, VS Code integration, and common pitfalls.
license: Complete terms in LICENSE.txt
---

# Project Setup — MCP Server Workspace

This skill documents how the **mcp_archi** workspace is organised, why each
piece exists, and how to scaffold a new MCP server from scratch.  Follow this
guide when onboarding, debugging import problems, or adding a new server.

---

## 1  Directory layout

```
mcp_archi/                          ← workspace root (git repo root)
├── .agents/skills/                 ← agent skills (this file lives here)
├── .github/agents/                 ← GitHub Copilot agent policies
├── .venv/                          ← Python virtual environment (git-ignored)
├── .vscode/
│   ├── mcp.json                    ← MCP server launch config for VS Code
│   └── settings.json               ← workspace-level VS Code settings
├── exports/                        ← runtime export artefacts
├── output/                         ← generated diagrams (draw.io, CSV, …)
├── requirements/                   ← human-readable requirements docs
│   └── mcp/servers/<name>/tools/<tool>/requirements.md
├── src/
│   └── mcp/                        ← NOT a Python package (no __init__.py)
│       └── servers/                ← top-level Python package
│           ├── __init__.py
│           ├── common/             ← shared utilities (available to all servers)
│           ├── archimate/          ← ArchiMate MCP server
│           └── export_csv/         ← CSV-export MCP server
├── .gitignore
├── pyproject.toml                  ← project metadata, tool config, deps
├── requirements.txt                ← direct dependencies (human-editable)
└── requirements-lock.txt           ← full pip freeze (reproducible installs)
```

### Key insight: `src/mcp/` is NOT a Python package

There is **no `__init__.py`** in `src/mcp/`.  The `mcp` name belongs to the
**MCP SDK** installed in the virtualenv (`pip install mcp`).  The local
directory `src/mcp/` is just a filesystem grouping — Python never imports it
as a package.

The actual importable package root is `src/mcp/servers/`, which contains:

```
servers/
├── __init__.py           ← "# Top-level package for all MCP servers"
├── common/               ← shared code
├── archimate/            ← one MCP server
│   ├── __init__.py
│   ├── __main__.py       ← entry point: `python -m servers.archimate`
│   ├── server.py         ← FastMCP instance + tool registration
│   ├── db.py             ← metamodel SQLite access
│   ├── model_db.py       ← model CRUD SQLite access
│   ├── data/             ← SQLite databases, seed data
│   ├── resources/        ← HTML views, CSS
│   └── tools/            ← one sub-package per tool
│       ├── archimate_model_query/
│       │   ├── __init__.py
│       │   └── tool.py   ← @mcp.tool() decorated function
│       ├── drawio/
│       └── …
└── export_csv/           ← another MCP server (same pattern)
```

---

## 2  Virtual environment

```bash
# Create (once)
python3 -m venv .venv

# Activate
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Or install from pyproject.toml
pip install -e ".[dev]"
```

The `.venv/` directory is git-ignored.  All commands assume `.venv/bin/python`
as the interpreter.

---

## 3  Import resolution — the PYTHONPATH trick

Because `src/mcp/` is not a package, the import root must be set explicitly.

| What you want to import       | Required PYTHONPATH     |
|-------------------------------|-------------------------|
| `from mcp.server.fastmcp …`  | (none — site-packages)  |
| `import servers.archimate`    | `src/mcp`               |
| `from servers.archimate …`   | `src/mcp`               |

### How it works

1. `PYTHONPATH=src/mcp` adds `src/mcp/` to `sys.path`.
2. Python finds `servers/` there (it has `__init__.py`) → regular package.
3. Python finds `mcp` in site-packages → the MCP SDK, not the local dir.
4. Because `src/mcp/` has **no** `__init__.py`, Python never confuses it
   with the SDK's `mcp` package.

### Running a server from the terminal

```bash
# From workspace root:
PYTHONPATH=src/mcp .venv/bin/python -m servers.archimate

# Or equivalently (setting cwd):
cd src/mcp && PYTHONPATH=. ../../.venv/bin/python -m servers.archimate
```

### Running ad-hoc scripts

```bash
PYTHONPATH=src/mcp .venv/bin/python -c "
from servers.archimate.tools.drawio.tool import drawio
print(type(drawio))  # <class 'function'>
"
```

> **Common mistake:** importing `servers.archimate.tools.drawio` gives you
> the *module*, not the function.  The callable lives at
> `servers.archimate.tools.drawio.tool.drawio`.

---

## 4  VS Code MCP integration (`.vscode/mcp.json`)

```jsonc
{
    "servers": {
        "archimate": {
            "type": "stdio",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["-m", "servers.archimate"],
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src/mcp"
            }
        }
    }
}
```

**Rules:**
- Use `${workspaceFolder}` — never hardcode absolute paths.
- Use `env.PYTHONPATH` — never rely on `cwd` to set the import root.
- Each server gets its own entry (archimate, export-csv, …).

---

## 5  Anatomy of an MCP server

### 5.1  `server.py` — the hub

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ArchiMate")

# Initialize databases
init_db()
init_model_db()

# Import tools — their @mcp.tool() decorators register automatically
from .tools.archimate_model_query import tool as _t1  # noqa: E402, F401
from .tools.drawio import tool as _t2                 # noqa: E402, F401
```

The `mcp` object is the single FastMCP instance shared across all tools.
Tools import it via relative imports: `from ...server import mcp`.

### 5.2  `__main__.py` — entry point

```python
"""Entry point: python -m servers.archimate"""
from .server import mcp
mcp.run()
```

### 5.3  `__init__.py` — package export

```python
from .server import mcp
__all__ = ["mcp"]
```

---

## 6  Anatomy of a tool

Each tool lives in its own sub-package under `tools/`:

```
tools/
└── my_new_tool/
    ├── __init__.py    ← typically just: from . import tool
    └── tool.py        ← contains the @mcp.tool() function
```

### `tool.py` template

```python
"""Tool: my_new_tool – one-line description."""
from __future__ import annotations

import json
from mcp import types
from ...server import mcp  # ← relative import to the shared FastMCP instance


@mcp.tool()
def my_new_tool(
    action: str,
    payload_json: str = "{}",
) -> list[types.TextContent]:
    """Docstring shown to the LLM as tool description."""
    payload = json.loads(payload_json) if payload_json else {}

    if action == "do_something":
        result = {"status": "ok"}
    else:
        result = {"error": f"Unknown action: {action}"}

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
```

### `__init__.py`

```python
from . import tool  # noqa: F401 – registers @mcp.tool()
```

### Registering the tool

Add one line to `server.py`:

```python
from .tools.my_new_tool import tool as _tN  # noqa: E402, F401
```

---

## 7  Adding a new MCP server

To add a completely new server (e.g. `servers.reporting`):

1. **Create the package:**
   ```
   src/mcp/servers/reporting/
   ├── __init__.py
   ├── __main__.py
   ├── server.py
   └── tools/
       ├── __init__.py
       └── some_tool/
           ├── __init__.py
           └── tool.py
   ```

2. **`server.py`:**
   ```python
   from mcp.server.fastmcp import FastMCP
   mcp = FastMCP("Reporting")
   from .tools.some_tool import tool as _t1  # noqa: E402, F401
   ```

3. **`__main__.py`:**
   ```python
   from .server import mcp
   mcp.run()
   ```

4. **Register in `.vscode/mcp.json`:**
   ```jsonc
   "reporting": {
       "type": "stdio",
       "command": "${workspaceFolder}/.venv/bin/python",
       "args": ["-m", "servers.reporting"],
       "env": { "PYTHONPATH": "${workspaceFolder}/src/mcp" }
   }
   ```

5. **Test:**
   ```bash
   PYTHONPATH=src/mcp .venv/bin/python -c "
   from servers.reporting import mcp
   print(mcp.name, len(mcp._tool_manager._tools), 'tools')
   "
   ```

---

## 8  `pyproject.toml` highlights

```toml
[project]
name = "mcp-archi"
requires-python = ">=3.12"
dependencies = ["fastmcp>=2.14,<3", "mcp>=1.26,<2"]

[tool.ruff]
src = ["src/mcp"]           # tells ruff where the import root is

[tool.pytest.ini_options]
pythonpath = ["src/mcp"]    # tells pytest where the import root is
```

Both `ruff` and `pytest` need the same `src/mcp` path so they resolve
imports the same way the runtime does.

---

## 9  Database conventions

- **Metamodel DB** (`data/archimate_3_2.sqlite`) — read-only reference data
  (elements, relationships, metamodel rules).  Initialised by `db.init_db()`.
- **Model DB** (`data/archimate_models.sqlite`) — user model data (elements,
  relationships, versions, tags, attributes).  Initialised by
  `model_db.init_model_db()`.
- Both are SQLite files stored alongside the code under `data/`.
- Path resolution uses `Path(__file__).resolve().parents[N]` — never
  hardcoded absolute paths.

---

## 10  Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'servers'` | Missing `PYTHONPATH=src/mcp` | Set `PYTHONPATH` or `cwd` |
| `ModuleNotFoundError: No module named 'mcp.servers'` | Wrong PYTHONPATH (`src` instead of `src/mcp`) | Use `src/mcp` not `src` |
| `TypeError: 'module' object is not callable` | Importing the tool *module* instead of the *function* | Import `from ….tool import my_func` |
| `duplicate column name: tags_json` | DB migration already applied | Safe to ignore; schema is idempotent |
| Hardcoded `/home/…` path breaks on another machine | Absolute path in code | Use `Path(__file__).parents[N]` or `${workspaceFolder}` |

---

## 11  Scaffolding checklist for a new project

- [ ] `python3 -m venv .venv`
- [ ] `pip install fastmcp mcp`
- [ ] Create `src/mcp/servers/<name>/` with `__init__.py`, `__main__.py`, `server.py`
- [ ] Create at least one tool under `tools/<tool_name>/`
- [ ] Add `pyproject.toml` with `[tool.ruff] src = ["src/mcp"]` and `[tool.pytest.ini_options] pythonpath = ["src/mcp"]`
- [ ] Add `.vscode/mcp.json` with `env.PYTHONPATH`
- [ ] Add `.gitignore` (pycache, venv, output artefacts)
- [ ] Add `requirements.txt` (direct deps) and `requirements-lock.txt` (full freeze)
- [ ] Smoke test: `PYTHONPATH=src/mcp .venv/bin/python -c "from servers.<name> import mcp; print(mcp.name)"`
