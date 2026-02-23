"""ExportCSV MCP Server – entry point.

Creates the FastMCP instance and imports tool modules so that their
@mcp.tool() decorators register with this server.
"""

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP("ExportCSV")

# ---------------------------------------------------------------------------
# Import tool modules so their decorators register with `mcp`
# ---------------------------------------------------------------------------
from .tools.export_csv import tool as _t1  # noqa: E402, F401
