"""Embedded HTML View for the selectable table (Vanilla JS, MCP Apps SDK).

CSS is loaded from the archimate resources package (styles.css) via
`resources.styles.VSCODE_CSS`.
"""

from ...resources.styles import VSCODE_CSS

_VIEW_TEMPLATE = (
    r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Selectable Table</title>
  <style>"""
    + VSCODE_CSS
    + r"""</style>
</head>"""
)

EMBEDDED_VIEW_HTML = _VIEW_TEMPLATE + r"""
<body>
  <div id="root">
    <div class="vsc-empty">Waiting for data…</div>
  </div>

  <script type="module">
    import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

    const app = new App({ name: "Selectable Table", version: "1.0.0" });

    let data = null;
    let selected = new Set();
    let sortKey = null;
    let sortDir = "asc";
    let searchQuery = "";
    let lastTablePayloadText = null;
    let hiddenColumns = new Set();
    let columnOrder = [];
    let columnsPanelOpen = false;
    let outsideClickHandler = null;
    let enhancedObjectColumns = new Set();
    let columnsMenuScrollTop = 0;

    let _updateDebounce = null;

    function flattenObject(value, prefix = "") {
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
      }
      const flat = {};
      for (const [key, nested] of Object.entries(value)) {
        const nextKey = prefix ? `${prefix}.${key}` : key;
        if (nested && typeof nested === "object" && !Array.isArray(nested)) {
          Object.assign(flat, flattenObject(nested, nextKey));
        } else {
          flat[nextKey] = nested;
        }
      }
      return flat;
    }

    function isPlainObject(value) {
      return !!value && typeof value === "object" && !Array.isArray(value);
    }

    function getViewData() {
      if (!data) return { columns: [], entities: [] };
      const baseColumns = data.columns || [];
      const baseEntities = data.entities || [];

      const objectColumns = baseColumns.filter((col) =>
        baseEntities.some((entity) => isPlainObject(entity[col]))
      );

      enhancedObjectColumns = new Set(
        [...enhancedObjectColumns].filter((col) => objectColumns.includes(col))
      );

      if (enhancedObjectColumns.size === 0) {
        return { columns: baseColumns, entities: baseEntities, objectColumns };
      }

      const discovered = [];
      const discoveredSet = new Set();
      const enhancedEntities = baseEntities.map((entity) => {
        const next = { ...entity };
        for (const col of enhancedObjectColumns) {
          const value = entity[col];
          if (isPlainObject(value)) {
            const flattened = flattenObject(value, col);
            for (const [k, v] of Object.entries(flattened)) {
              next[k] = v;
              if (!discoveredSet.has(k)) {
                discoveredSet.add(k);
                discovered.push(k);
              }
            }
          }
        }
        return next;
      });

      return {
        columns: [...baseColumns, ...discovered],
        entities: enhancedEntities,
        objectColumns,
      };
    }

    async function sendSelectionAutomatic() {
      if (!data) return;
      const viewData = getViewData();
      const columns = viewData.columns;
      let items = viewData.entities;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        items = items.filter(e => columns.some(c => String(e[c] || "").toLowerCase().includes(q)));
      }
      if (sortKey) {
        items = [...items].sort((a, b) => {
          const av = a[sortKey] || "", bv = b[sortKey] || "";
          if (av < bv) return sortDir === "asc" ? -1 : 1;
          if (av > bv) return sortDir === "asc" ? 1 : -1;
          return 0;
        });
      }

      const selItems = items.filter((_, i) => selected.has(i));

      clearTimeout(_updateDebounce);
      _updateDebounce = setTimeout(async () => {
        try {
          const pretty = JSON.stringify(selItems, null, 2);
          await app.updateModelContext({
            content: [{
              type: 'text',
              text: `Current table selection (${selItems.length} rows):\n${pretty}`
            }]
          });
          const statusEl = document.querySelector('.vsc-status');
          if (statusEl) statusEl.textContent = `${selItems.length} row(s) in context`;
        } catch (err) {
          console.warn('updateModelContext failed', err);
          const statusEl = document.querySelector('.vsc-status');
          if (statusEl) statusEl.textContent = `Context update failed: ${String(err)}`;
        }

        try {
          await app.callServerTool({ name: 'selection_received', arguments: { selection: selItems } });
        } catch (err) {
          console.warn('callServerTool(selection_received) failed', err);
        }
      }, 300);
    }

    function render() {
      const root = document.getElementById("root");
      if (!data) { root.innerHTML = '<div class="empty">Waiting for data…</div>'; return; }

      const { title } = data;
      const viewData = getViewData();
      const sourceColumns = viewData.columns;
      const entities = viewData.entities;
      const objectColumns = viewData.objectColumns || [];

      if (sortKey && !sourceColumns.includes(sortKey)) {
        sortKey = null;
      }

      if (columnOrder.length === 0) {
        columnOrder = [...sourceColumns];
      } else {
        const existing = new Set(sourceColumns);
        columnOrder = columnOrder.filter(c => existing.has(c));
        for (const col of sourceColumns) {
          if (!columnOrder.includes(col)) columnOrder.push(col);
        }
      }
      hiddenColumns = new Set([...hiddenColumns].filter(c => sourceColumns.includes(c)));
      const visibleColumns = columnOrder.filter(c => !hiddenColumns.has(c));

      let items = entities;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        items = items.filter(e => sourceColumns.some(c => String(e[c] || "").toLowerCase().includes(q)));
      }

      if (sortKey) {
        items = [...items].sort((a, b) => {
          const av = a[sortKey] || "", bv = b[sortKey] || "";
          if (av < bv) return sortDir === "asc" ? -1 : 1;
          if (av > bv) return sortDir === "asc" ? 1 : -1;
          return 0;
        });
      }

      const allSelected = items.length > 0 && items.every((_, i) => selected.has(i));

      let html = '<h2>' + esc(title) + '</h2>';
      html += '<div class="vsc-panel">';
      html += '<div class="vsc-toolbar">';
      html += '<div class="vsc-toolbar-left">';
      html += '<input type="search" placeholder="Search…" value="' + esc(searchQuery) + '" style="width:220px" />';
      html += '<span class="vsc-status">' + selected.size + ' of ' + items.length + ' selected</span>';
      html += '</div>';
      html += '<div class="vsc-toolbar-right">';
      html += '<details class="vsc-col-panel" ' + (columnsPanelOpen ? 'open' : '') + '>';
      html += '<summary class="btn">Columns</summary>';
      html += '<div class="vsc-col-menu">';
      for (const c of columnOrder) {
        const checked = hiddenColumns.has(c) ? '' : 'checked';
        html += '<label class="vsc-col-item"><input type="checkbox" data-col-toggle="' + esc(c) + '" ' + checked + ' /> ' + esc(c) + '</label>';
      }
      html += '</div>';
      html += '</details>';
      html += '</div>';
      html += '</div>';
      html += '<div class="vsc-table-container"><table class="vsc-table">';

      html += '<thead><tr>';
      html += '<th class="col-checkbox"><input type="checkbox" class="select-all" ' + (allSelected ? 'checked' : '') + ' /></th>';
      for (const c of visibleColumns) {
        const arrow = sortKey === c ? (sortDir === "asc" ? " ▲" : " ▼") : "";
        html += '<th draggable="true" data-col="' + esc(c) + '"><span class="th-title">' + esc(c) + '</span>';
        if (objectColumns.includes(c)) {
          const checkedEnhance = enhancedObjectColumns.has(c) ? 'checked' : '';
          html += '<label class="vsc-head-enhance"><input type="checkbox" data-enhance-col="' + esc(c) + '" ' + checkedEnhance + ' /></label>';
        }
        html += '<span class="sort-arrow">' + arrow + '</span></th>';
      }
      html += '</tr></thead>';

      html += '<tbody>';
      if (items.length === 0) {
        html += '<tr><td colspan="' + (visibleColumns.length + 1) + '" class="vsc-empty">No entries found</td></tr>';
      } else {
        for (let i = 0; i < items.length; i++) {
          const e = items[i];
          const isSel = selected.has(i);
          html += '<tr data-idx="' + i + '" class="' + (isSel ? 'selected' : '') + '">';
          html += '<td class="col-checkbox"><input type="checkbox" ' + (isSel ? 'checked' : '') + ' /></td>';
          for (const c of visibleColumns) {
            html += '<td>' + esc(String(e[c] || "")) + '</td>';
          }
          html += '</tr>';
        }
      }
      html += '</tbody></table></div>';

      if (selected.size > 0) {
        const selItems = [...selected].sort().map(i => items[i]).filter(Boolean);
        const leadCol = visibleColumns[0] || sourceColumns[0] || "name";
        const names = selItems.map(e => e[leadCol]).join(", ");
        html += '<div class="vsc-status">' + selected.size + ' selected: ' + esc(names) + '</div>';
      } else {
        html += '<div class="vsc-status">Click rows to select</div>';
      }
      html += '</div>';

      /* actions removed — selection is sent automatically */

      // remember how far the table and page were scrolled so we don't jump
      let prevScroll = 0;
      const oldContainer = root.querySelector('.vsc-table-container');
      if (oldContainer) prevScroll = oldContainer.scrollTop;
      const oldColMenu = root.querySelector('.vsc-col-menu');
      if (oldColMenu && columnsPanelOpen) columnsMenuScrollTop = oldColMenu.scrollTop;
      const prevPage = window.scrollY || document.documentElement.scrollTop || 0;

      root.innerHTML = html;

      const newContainer = root.querySelector('.vsc-table-container');
      if (newContainer) newContainer.scrollTop = prevScroll;
      if (prevPage) window.scrollTo(0, prevPage);
      const newColMenu = root.querySelector('.vsc-col-menu');
      if (newColMenu && columnsPanelOpen && columnsMenuScrollTop > 0) {
        newColMenu.scrollTop = columnsMenuScrollTop;
      }

      root.querySelector("input[type=search]").addEventListener("input", (ev) => {
        searchQuery = ev.target.value;
        selected.clear();
        render();
        sendSelectionAutomatic();
      });

      root.querySelectorAll('input[data-enhance-col]').forEach(cb => {
        cb.addEventListener('click', (ev) => {
          ev.stopPropagation();
        });
        cb.addEventListener('mousedown', (ev) => {
          ev.stopPropagation();
        });
        cb.addEventListener('change', (ev) => {
          const col = ev.target.getAttribute('data-enhance-col');
          if (!col) return;
          if (ev.target.checked) enhancedObjectColumns.add(col);
          else enhancedObjectColumns.delete(col);
          render();
          sendSelectionAutomatic();
        });
      });

      const colMenu = root.querySelector('.vsc-col-menu');
      if (colMenu) {
        colMenu.querySelectorAll('input[data-col-toggle]').forEach(cb => {
          cb.addEventListener('change', (ev) => {
            const col = ev.target.getAttribute('data-col-toggle');
            const wantVisible = !!ev.target.checked;
            const currentlyVisible = columnOrder.filter(c => !hiddenColumns.has(c));
            if (!wantVisible && currentlyVisible.length <= 1 && currentlyVisible.includes(col)) {
              ev.target.checked = true;
              return;
            }
            if (wantVisible) hiddenColumns.delete(col);
            else hiddenColumns.add(col);
            columnsMenuScrollTop = colMenu.scrollTop;
            render();
          });
        });
      }

      const colPanel = root.querySelector('.vsc-col-panel');
      if (colPanel) {
        colPanel.addEventListener('toggle', () => {
          columnsPanelOpen = colPanel.open;
          if (!columnsPanelOpen) columnsMenuScrollTop = 0;
        });
      }

      if (outsideClickHandler) {
        document.removeEventListener('click', outsideClickHandler, true);
      }
      outsideClickHandler = (ev) => {
        const panel = root.querySelector('.vsc-col-panel');
        if (!panel || !panel.open) return;
        if (panel.contains(ev.target)) return;
        panel.removeAttribute('open');
        columnsPanelOpen = false;
      };
      document.addEventListener('click', outsideClickHandler, true);

      /* action buttons removed — no-op */

      /* send-to-chat handler removed (functionality is automatic) */

      /* send-to-server handler removed (functionality is automatic) */

      root.querySelector(".select-all").addEventListener("change", () => {
        if (selected.size === items.length) {
          selected.clear();
        } else {
          selected = new Set(items.map((_, i) => i));
        }
        render();
        sendSelectionAutomatic();
      });

      root.querySelectorAll("th[data-col]").forEach(th => {
        th.addEventListener("click", () => {
          const col = th.dataset.col;
          if (sortKey === col) { sortDir = sortDir === "asc" ? "desc" : "asc"; }
          else { sortKey = col; sortDir = "asc"; }
          render();
        });

        th.addEventListener('dragstart', (ev) => {
          ev.dataTransfer.effectAllowed = 'move';
          ev.dataTransfer.setData('text/plain', th.dataset.col || '');
          th.classList.add('dragging-col');
        });
        th.addEventListener('dragover', (ev) => {
          ev.preventDefault();
          th.classList.add('drag-over-col');
        });
        th.addEventListener('dragleave', () => {
          th.classList.remove('drag-over-col');
        });
        th.addEventListener('drop', (ev) => {
          ev.preventDefault();
          th.classList.remove('drag-over-col');
          const fromCol = ev.dataTransfer.getData('text/plain');
          const toCol = th.dataset.col || '';
          if (!fromCol || !toCol || fromCol === toCol) return;
          const fromIdx = columnOrder.indexOf(fromCol);
          const toIdx = columnOrder.indexOf(toCol);
          if (fromIdx < 0 || toIdx < 0) return;
          columnOrder.splice(fromIdx, 1);
          columnOrder.splice(toIdx, 0, fromCol);
          render();
        });
        th.addEventListener('dragend', () => {
          root.querySelectorAll('th[data-col]').forEach(h => h.classList.remove('dragging-col', 'drag-over-col'));
        });
      });

      root.querySelectorAll("tbody tr[data-idx]").forEach(tr => {
        tr.addEventListener("click", (ev) => {
          if (ev.target && ev.target.closest("input[type=checkbox]")) return;
          const idx = parseInt(tr.dataset.idx);
          if (selected.has(idx)) selected.delete(idx); else selected.add(idx);
          // update only the clicked row and status rather than re-rendering
          const rowEl = tr;
          if (rowEl) {
            rowEl.classList.toggle("selected", selected.has(idx));
            const cb = rowEl.querySelector("input[type=checkbox]");
            if (cb) cb.checked = selected.has(idx);
          }
          const statusEl = document.querySelector('.vsc-status');
          if (statusEl) statusEl.textContent = `${selected.size} of ${items.length} selected`;
          const allCheckbox = document.querySelector('.select-all');
          if (allCheckbox) {
            const allSelected = items.length > 0 && items.every((_, i) => selected.has(i));
            allCheckbox.checked = allSelected;
          }
          sendSelectionAutomatic();
        });

        const rowCheckbox = tr.querySelector("input[type=checkbox]");
        if (rowCheckbox) {
          rowCheckbox.addEventListener("change", (ev) => {
            ev.stopPropagation();
            const idx = parseInt(tr.dataset.idx);
            const isChecked = !!ev.target.checked;
            if (isChecked) selected.add(idx); else selected.delete(idx);
            tr.classList.toggle("selected", isChecked);
            const statusEl = document.querySelector('.vsc-status');
            if (statusEl) statusEl.textContent = `${selected.size} of ${items.length} selected`;
            const allCheckbox = document.querySelector('.select-all');
            if (allCheckbox) {
              const allSelected = items.length > 0 && items.every((_, i) => selected.has(i));
              allCheckbox.checked = allSelected;
            }
            sendSelectionAutomatic();
          });
        }
      });
    }

    function esc(s) {
      const d = document.createElement("div");
      d.textContent = s;
      return d.innerHTML;
    }

    app.ontoolresult = (result) => {
      try {
        const textItem = (result.content || []).find(c => c.type === "text");
        if (textItem) {
          if (textItem.text === lastTablePayloadText) {
            return;
          }
          const parsed = JSON.parse(textItem.text);
          // only treat proper table payloads as new data.  selection_received
          // and other tools also return text, so check shape.
          if (parsed && parsed._kind === "selectable_table" && parsed.columns && parsed.entities) {
            lastTablePayloadText = textItem.text;
            data = parsed;
            selected.clear();
            sortKey = null;
            searchQuery = "";
            hiddenColumns = new Set();
            columnOrder = [...parsed.columns];
            columnsPanelOpen = false;
            enhancedObjectColumns = new Set();
            columnsMenuScrollTop = 0;
            render();
          } else {
            // ignore non-table responses
          }
        }
      } catch (e) {
        document.getElementById("root").innerHTML =
          '<div class="vsc-empty">Error: ' + esc(String(e)) + '</div>';
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

    await app.connect();

    const ctx = app.getHostContext();
    if (ctx && ctx.safeAreaInsets) {
      document.body.style.paddingTop = ctx.safeAreaInsets.top + "px";
    }
  </script>
</body>
</html>"""
