"""Embedded HTML View for the selectable matrix (React + MCP Apps SDK)."""

from ...resources.styles import VSCODE_CSS

_VIEW_TEMPLATE = (
    r"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Selectable Matrix</title>
  <style>"""
    + VSCODE_CSS
    + r"""
    .vsc-matrix-wrap { display: grid; grid-template-columns: 1fr 360px; gap: 12px; }
    .vsc-matrix-cell { min-width: 130px; }
    .vsc-matrix-cell .cell-top { display: flex; align-items: center; gap: 6px; }
    .vsc-matrix-cell .cell-meta { font-size: 11px; opacity: .75; margin-top: 4px; }
    .vsc-json-panel { border: 1px solid var(--vscode-editorWidget-border); border-radius: 6px; overflow: hidden; }
    .vsc-json-head { padding: 8px 10px; border-bottom: 1px solid var(--vscode-editorWidget-border); font-weight: 600; }
    .vsc-json-body { max-height: 520px; overflow: auto; padding: 8px 10px; }
    .vsc-rel-row { border: 1px solid var(--vscode-editorWidget-border); border-radius: 6px; padding: 6px; margin-bottom: 8px; }
    .vsc-rel-row pre { margin: 6px 0 0; white-space: pre-wrap; word-break: break-word; }
    @media (max-width: 1100px) {
      .vsc-matrix-wrap { grid-template-columns: 1fr; }
    }
  </style>
</head>"""
)

EMBEDDED_VIEW_HTML = _VIEW_TEMPLATE + r"""
<body>
  <div id="root">
    <div class="vsc-empty">Waiting for data…</div>
  </div>

  <script type="module">
    import React, { useEffect, useMemo, useState } from "https://esm.sh/react@18.3.1";
    import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";
    import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

    const app = new App({ name: "Selectable Matrix", version: "1.0.0" });
    const root = createRoot(document.getElementById("root"));

    let setPayloadExternal = null;
    let lastPayloadText = null;

    function getEntityKey(entity, index) {
      if (entity && (entity.id || entity.relationship_id || entity.uuid)) {
        return String(entity.id || entity.relationship_id || entity.uuid);
      }
      return `idx:${index}`;
    }

    function MatrixApp() {
      const [payload, setPayload] = useState(null);
      const [searchQuery, setSearchQuery] = useState("");
      const [rowSort, setRowSort] = useState("asc");
      const [columnSort, setColumnSort] = useState("asc");
      const [hiddenColumns, setHiddenColumns] = useState(new Set());
      const [selectedKeys, setSelectedKeys] = useState(new Set());
      const [activeCell, setActiveCell] = useState(null);
      const [columnsPanelOpen, setColumnsPanelOpen] = useState(false);

      setPayloadExternal = (next) => {
        setPayload(next);
        setSearchQuery("");
        setRowSort("asc");
        setColumnSort("asc");
        setHiddenColumns(new Set());
        setSelectedKeys(new Set());
        setActiveCell(null);
        setColumnsPanelOpen(false);
      };

      const matrixData = useMemo(() => {
        if (!payload || !payload.entities) {
          return { rows: [], columns: [], cellMap: new Map(), selectedEntities: [], activeEntities: [] };
        }

        const { entities, rowField, columnField } = payload;
        const q = searchQuery.trim().toLowerCase();

        const rowsSet = new Set();
        const colsSet = new Set();
        const cellMap = new Map();

        entities.forEach((entity, idx) => {
          const rowVal = String(entity?.[rowField] ?? "").trim();
          const colVal = String(entity?.[columnField] ?? "").trim();
          if (!rowVal || !colVal) return;

          const haystack = JSON.stringify(entity).toLowerCase();
          if (q && !haystack.includes(q) && !rowVal.toLowerCase().includes(q) && !colVal.toLowerCase().includes(q)) {
            return;
          }

          rowsSet.add(rowVal);
          colsSet.add(colVal);
          const key = `${rowVal}\u0000${colVal}`;
          if (!cellMap.has(key)) cellMap.set(key, []);
          cellMap.get(key).push({ entity, idx, key: getEntityKey(entity, idx) });
        });

        let rows = [...rowsSet];
        let columns = [...colsSet];

        rows.sort((a, b) => (rowSort === "asc" ? a.localeCompare(b) : b.localeCompare(a)));
        columns.sort((a, b) => (columnSort === "asc" ? a.localeCompare(b) : b.localeCompare(a)));

        columns = columns.filter((col) => !hiddenColumns.has(col));

        const selectedEntities = [];
        entities.forEach((entity, idx) => {
          const key = getEntityKey(entity, idx);
          if (selectedKeys.has(key)) selectedEntities.push(entity);
        });

        let activeEntities = [];
        if (activeCell) {
          activeEntities = cellMap.get(`${activeCell.row}\u0000${activeCell.col}`) || [];
        }

        return { rows, columns, cellMap, selectedEntities, activeEntities };
      }, [payload, searchQuery, rowSort, columnSort, hiddenColumns, selectedKeys, activeCell]);

      useEffect(() => {
        if (!payload) return;
        const timer = setTimeout(async () => {
          try {
            const pretty = JSON.stringify(matrixData.selectedEntities, null, 2);
            await app.updateModelContext({
              content: [{
                type: "text",
                text: `Current matrix selection (${matrixData.selectedEntities.length} relations):\n${pretty}`,
              }],
            });
          } catch (err) {
            console.warn("updateModelContext failed", err);
          }

          try {
            await app.callServerTool({
              name: "selection_received",
              arguments: { selection: matrixData.selectedEntities },
            });
          } catch (err) {
            console.warn("selection_received failed", err);
          }
        }, 250);
        return () => clearTimeout(timer);
      }, [payload, matrixData.selectedEntities]);

      const allColumns = useMemo(() => {
        if (!payload || !payload.entities) return [];
        const set = new Set();
        payload.entities.forEach((entity) => {
          const val = String(entity?.[payload.columnField] ?? "").trim();
          if (val) set.add(val);
        });
        return [...set].sort((a, b) => a.localeCompare(b));
      }, [payload]);

      if (!payload) {
        return React.createElement("div", { className: "vsc-empty" }, "Waiting for data…");
      }

      function toggleCellSelection(row, col, checked) {
        const entries = matrixData.cellMap.get(`${row}\u0000${col}`) || [];
        const next = new Set(selectedKeys);
        entries.forEach((entry) => {
          if (checked) next.add(entry.key);
          else next.delete(entry.key);
        });
        setSelectedKeys(next);
      }

      function toggleSingleSelection(key, checked) {
        const next = new Set(selectedKeys);
        if (checked) next.add(key);
        else next.delete(key);
        setSelectedKeys(next);
      }

      function cellState(row, col) {
        const entries = matrixData.cellMap.get(`${row}\u0000${col}`) || [];
        if (entries.length === 0) return { checked: false, indeterminate: false, count: 0 };
        const selectedCount = entries.filter((entry) => selectedKeys.has(entry.key)).length;
        return {
          checked: selectedCount === entries.length,
          indeterminate: selectedCount > 0 && selectedCount < entries.length,
          count: entries.length,
        };
      }

      const toolbar = React.createElement(
        "div",
        { className: "vsc-toolbar" },
        React.createElement(
          "div",
          { className: "vsc-toolbar-left" },
          React.createElement("input", {
            type: "search",
            placeholder: "Filter matrix…",
            value: searchQuery,
            onChange: (e) => setSearchQuery(e.target.value),
            style: { width: "240px" },
          }),
          React.createElement(
            "span",
            { className: "vsc-status" },
            `${matrixData.selectedEntities.length} relation(s) selected`
          )
        ),
        React.createElement(
          "div",
          { className: "vsc-toolbar-right", style: { display: "flex", gap: "8px", alignItems: "center" } },
          React.createElement(
            "button",
            {
              className: "btn",
              onClick: () => setRowSort((v) => (v === "asc" ? "desc" : "asc")),
              type: "button",
            },
            `Sort rows ${rowSort === "asc" ? "▲" : "▼"}`
          ),
          React.createElement(
            "button",
            {
              className: "btn",
              onClick: () => setColumnSort((v) => (v === "asc" ? "desc" : "asc")),
              type: "button",
            },
            `Sort columns ${columnSort === "asc" ? "▲" : "▼"}`
          ),
          React.createElement(
            "details",
            {
              className: "vsc-col-panel",
              open: columnsPanelOpen,
              onToggle: (e) => setColumnsPanelOpen(e.currentTarget.open),
            },
            React.createElement("summary", { className: "btn" }, "Columns"),
            React.createElement(
              "div",
              { className: "vsc-col-menu" },
              allColumns.map((column) => {
                const visible = !hiddenColumns.has(column);
                return React.createElement(
                  "label",
                  { key: column, className: "vsc-col-item" },
                  React.createElement("input", {
                    type: "checkbox",
                    checked: visible,
                    onChange: (e) => {
                      const next = new Set(hiddenColumns);
                      if (e.target.checked) next.delete(column);
                      else next.add(column);
                      setHiddenColumns(next);
                    },
                  }),
                  " ",
                  column
                );
              })
            )
          )
        )
      );

      const tableHead = React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("th", null, payload.rowField),
          ...matrixData.columns.map((column) => React.createElement("th", { key: column }, column))
        )
      );

      const tableBody = React.createElement(
        "tbody",
        null,
        matrixData.rows.length === 0 || matrixData.columns.length === 0
          ? React.createElement(
              "tr",
              null,
              React.createElement(
                "td",
                { className: "vsc-empty", colSpan: Math.max(2, matrixData.columns.length + 1) },
                "No matrix entries for current filter"
              )
            )
          : matrixData.rows.map((row) =>
              React.createElement(
                "tr",
                { key: row },
                React.createElement("th", { style: { textAlign: "left" } }, row),
                ...matrixData.columns.map((column) => {
                  const state = cellState(row, column);
                  return React.createElement(
                    "td",
                    {
                      key: `${row}::${column}`,
                      className: "vsc-matrix-cell",
                      onClick: () => setActiveCell({ row, col: column }),
                    },
                    state.count === 0
                      ? React.createElement("span", { className: "vsc-empty" }, "—")
                      : React.createElement(
                          "div",
                          null,
                          React.createElement(
                            "div",
                            { className: "cell-top" },
                            React.createElement("input", {
                              type: "checkbox",
                              checked: state.checked,
                              ref: (el) => {
                                if (el) el.indeterminate = state.indeterminate;
                              },
                              onChange: (e) => toggleCellSelection(row, column, e.target.checked),
                              onClick: (e) => e.stopPropagation(),
                            }),
                            React.createElement("span", null, `${state.count} rel`)
                          ),
                          React.createElement("div", { className: "cell-meta" }, "Open for details")
                        )
                  );
                })
              )
            )
      );

      const table = React.createElement(
        "div",
        { className: "vsc-table-container" },
        React.createElement("table", { className: "vsc-table" }, tableHead, tableBody)
      );

      const detailPanel = React.createElement(
        "div",
        { className: "vsc-json-panel" },
        React.createElement(
          "div",
          { className: "vsc-json-head" },
          activeCell
            ? `${activeCell.row} × ${activeCell.col}`
            : "Select a matrix cell"
        ),
        React.createElement(
          "div",
          { className: "vsc-json-body" },
          !activeCell
            ? React.createElement("div", { className: "vsc-empty" }, "Select a cell to inspect relation objects")
            : matrixData.activeEntities.length === 0
              ? React.createElement("div", { className: "vsc-empty" }, "No relations in this cell")
              : matrixData.activeEntities.map((entry, idx) =>
                  React.createElement(
                    "div",
                    { key: `${entry.key}-${idx}`, className: "vsc-rel-row" },
                    React.createElement(
                      "label",
                      null,
                      React.createElement("input", {
                        type: "checkbox",
                        checked: selectedKeys.has(entry.key),
                        onChange: (e) => toggleSingleSelection(entry.key, e.target.checked),
                      }),
                      " Select relation"
                    ),
                    React.createElement("pre", null, JSON.stringify(entry.entity, null, 2))
                  )
                )
        )
      );

      return React.createElement(
        "div",
        null,
        React.createElement("h2", null, payload.title || "Selectable Matrix"),
        React.createElement(
          "div",
          { className: "vsc-panel" },
          toolbar,
          React.createElement(
            "div",
            { className: "vsc-matrix-wrap" },
            table,
            detailPanel
          )
        )
      );
    }

    app.ontoolresult = (result) => {
      try {
        const textItem = (result.content || []).find((c) => c.type === "text");
        if (!textItem) return;
        if (textItem.text === lastPayloadText) return;

        const parsed = JSON.parse(textItem.text);
        if (parsed && parsed._kind === "selectable_matrix" && parsed.entities && parsed.rowField && parsed.columnField) {
          lastPayloadText = textItem.text;
          if (setPayloadExternal) setPayloadExternal(parsed);
        }
      } catch (e) {
        root.render(React.createElement("div", { className: "vsc-empty" }, `Error: ${String(e)}`));
      }
    };

    app.onhostcontextchanged = (ctx) => {
      if (ctx.safeAreaInsets) {
        document.body.style.paddingTop = ctx.safeAreaInsets.top + "px";
        document.body.style.paddingRight = ctx.safeAreaInsets.right + "px";
        document.body.style.paddingBottom = ctx.safeAreaInsets.bottom + "px";
        document.body.style.paddingLeft = ctx.safeAreaInsets.left + "px";
      }
    };

    root.render(React.createElement(MatrixApp));
    await app.connect();

    const ctx = app.getHostContext();
    if (ctx && ctx.safeAreaInsets) {
      document.body.style.paddingTop = ctx.safeAreaInsets.top + "px";
    }
  </script>
</body>
</html>"""
