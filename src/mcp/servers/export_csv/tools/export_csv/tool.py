"""Tool: export_csv – Export selection (list of dicts) to a CSV file."""

import csv
import json
import re
from pathlib import Path
from mcp import types

from ...server import mcp

# Exports directory (fixed to workspace exports folder)
EXPORTS_DIR = Path("/home/markus/Workspace/mcp_archi/exports")
FNAME_RE = re.compile(r"^[\w\-. ]+\.csv$", flags=re.I)


@mcp.tool()
def export_csv(filename: str, selection: list | None = None) -> list[types.TextContent]:
    """Export `selection` (list of dicts) to `exports/<filename>`.

    - `filename` must be a simple basename ending with .csv
    - If `selection` is None or empty, returns an error message
    """
    # validate filename
    safe = Path(filename).name
    if safe != filename or not FNAME_RE.match(filename):
        return [types.TextContent(type="text", text="Error: invalid filename — use a simple name ending with .csv")]

    if not selection:
        return [types.TextContent(type="text", text="Error: no selection provided to export")]

    try:
        # ensure exports dir
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = EXPORTS_DIR / safe

        # compute header columns (union of all keys, stable order)
        keys: list[str] = []
        for row in selection:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)

        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in selection:
                writer.writerow({k: row.get(k, "") for k in keys})

        return [types.TextContent(type="text", text=f"Exported {len(selection)} rows to {out_path}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Export failed: {e}")]
