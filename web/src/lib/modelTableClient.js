// @ts-nocheck
import { rowPassesFilters } from "./modelVisibility.js";
import {
  applySortDirectionSelection,
  applySortFieldSelection,
  formatSortTriggerLabel,
  shouldCloseSortPanelOnOutsideClick,
  toggleSortPanelOpen,
} from "./sortPanel.js";

/** @param {{ models?: any[], vendorMatchByChip?: Record<string, string[]> }} boot */
export function initModelTable(boot = {}) {
  const models = Array.isArray(boot.models) ? boot.models : [];
  const vendorMatchByChip =
    boot.vendorMatchByChip && typeof boot.vendorMatchByChip === "object"
      ? boot.vendorMatchByChip
      : {};

  const tableBody = document.querySelector("#model-table-body");
  const modelTable = document.querySelector("#model-table");
  const modelIdColHeader = document.querySelector("#model-id-col-header");
  const modelIdColResizer = document.querySelector("#model-id-col-resizer");
  const count = document.querySelector("#model-count");
  const pinClearAll = document.querySelector("#pin-clear-all");
  const searchInput = document.querySelector("#model-search");
  const capReasoning = document.querySelector("#cap-reasoning");
  const capTools = document.querySelector("#cap-tools");
  const capVision = document.querySelector("#cap-vision");
  const removedFilterButtons = Array.from(document.querySelectorAll("[data-removed-filter]"));
  const pointerFilterButtons = Array.from(document.querySelectorAll("[data-pointer-filter]"));
  const batchFilterButtons = Array.from(document.querySelectorAll("[data-batch-filter]"));
  const vendorFilterButtons = Array.from(document.querySelectorAll("[data-vendor-filter]"));
  const vendorFilterClear = document.querySelector("#vendor-filter-clear");
  const sortControl = document.querySelector("#sort-control");
  const sortTrigger = document.querySelector("#sort-trigger");
  const sortTriggerLabel = document.querySelector("#sort-trigger-label");
  const sortPanel = document.querySelector("#sort-panel");
  const sortFieldButtons = Array.from(document.querySelectorAll("[data-sort-field]"));
  const sortDirButtons = Array.from(document.querySelectorAll("[data-sort-dir]"));
  const rangeInputs = Array.from(document.querySelectorAll("input[data-range-key][data-range-bound]"));
  const totalRows = models.length;
  const modelsById = new Map(models.map((model) => [model.model_id, model]));
  const MODEL_ID_COL_WIDTH_KEY = "openrouter-watch.model-id-column-width";
  const MODEL_ID_COL_MIN_WIDTH = 140;
  const MODEL_ID_COL_MAX_WIDTH = 480;
  let removedFilterMode = "hide";
  let pointerFilterMode = "hide";
  let batchFilterMode = "hide";
  /** @type {string} */
  let sortFieldValue = "";
  /** @type {"asc" | "desc"} */
  let sortDirectionValue = "desc";
  const SORT_FIELD_LABELS = {
    context_length: "上下文",
    max_completion_tokens: "最大输出",
    input_price_usd_per_1m: "输入价",
    weighted_avg_input_price_usd_per_1m: "加权输入价",
    output_price_usd_per_1m: "输出价",
    intelligence_index: "Intelligence",
    coding_index: "Coding",
    agentic_index: "Agentic",
    knowledge_cutoff: "知识截止",
    released_at: "发布日期",
    updated_at: "更新时间",
  };
  /** @type {Set<string>} 多选厂商并集（OR）；空集表示不过滤厂商；值为芯片 name */
  const selectedVendors = new Set();
  /** @type {Record<string, string[]>} 芯片 name → 可匹配的 vendor_name（含改名前缀别名） */
  const vendorMatchMap =
    vendorMatchByChip && typeof vendorMatchByChip === "object" ? vendorMatchByChip : {};

  let modelIdColWidth = null;
  /** @type {string[]} 会话级 Pin 顺序（先 Pin 的更靠上）；不写 storage */
  const pinnedIds = [];
  let pinDragId = null;
  const PIN_BOOKMARK_OUTLINE = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4h10a1 1 0 011 1v15l-6-3.5L6 20V5a1 1 0 011-1z"/></svg>`;
  const PIN_BOOKMARK_FILLED = `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4h10a1 1 0 011 1v15l-6-3.5L6 20V5a1 1 0 011-1z"/></svg>`;
  const PIN_GRIP = `<svg viewBox="0 0 12 16" fill="currentColor" aria-hidden="true"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/><circle cx="3" cy="8" r="1.4"/><circle cx="9" cy="8" r="1.4"/><circle cx="3" cy="13" r="1.4"/><circle cx="9" cy="13" r="1.4"/></svg>`;
  const numericRangeKeys = [
    "context_length",
    "max_completion_tokens",
    "input_price_usd_per_1m",
    "weighted_avg_input_price_usd_per_1m",
    "output_price_usd_per_1m",
    "intelligence_index",
    "coding_index",
    "agentic_index",
  ];

  function clampModelIdColWidth(width) {
    return Math.min(MODEL_ID_COL_MAX_WIDTH, Math.max(MODEL_ID_COL_MIN_WIDTH, width));
  }

  function readStoredModelIdColWidth() {
    try {
      const raw = window.localStorage.getItem(MODEL_ID_COL_WIDTH_KEY);
      if (!raw) {
        return null;
      }
      const parsed = Number(raw);
      return Number.isFinite(parsed) ? clampModelIdColWidth(parsed) : null;
    } catch {
      return null;
    }
  }

  function persistModelIdColWidth(width) {
    try {
      if (width === null) {
        window.localStorage.removeItem(MODEL_ID_COL_WIDTH_KEY);
        return;
      }
      window.localStorage.setItem(MODEL_ID_COL_WIDTH_KEY, String(width));
    } catch {
      // Ignore storage failures.
    }
  }

  function applyModelIdColWidth(width) {
    modelIdColWidth = width;
    if (!modelTable || !modelIdColHeader) {
      return;
    }
    if (width === null) {
      modelTable.classList.remove("model-id-col-sized");
      modelIdColHeader.style.width = "";
      modelIdColHeader.style.maxWidth = "";
      modelIdColHeader.style.minWidth = "";
      return;
    }
    // table-layout:fixed takes column width from the first row only.
    // Writing header styles is O(1); do NOT touch every td on each drag frame
    // (that was the primary jank source with ~300+ Model ID cells + ellipsis).
    modelTable.classList.add("model-id-col-sized");
    const widthStyle = `${width}px`;
    modelIdColHeader.style.width = widthStyle;
    modelIdColHeader.style.maxWidth = widthStyle;
    modelIdColHeader.style.minWidth = widthStyle;
  }

  function initModelIdColResize() {
    modelIdColWidth = readStoredModelIdColWidth();
    applyModelIdColWidth(modelIdColWidth);

    if (!modelIdColResizer || !modelIdColHeader) {
      return;
    }

    let startX = 0;
    let startWidth = 0;
    let pendingWidth = null;
    let rafId = null;

    const flushPendingWidth = () => {
      rafId = null;
      if (pendingWidth === null) {
        return;
      }
      applyModelIdColWidth(pendingWidth);
      pendingWidth = null;
    };

    const stopResize = () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        flushPendingWidth();
      }
      document.body.classList.remove("model-id-col-resizing");
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", stopResize);
      if (modelIdColWidth !== null) {
        persistModelIdColWidth(modelIdColWidth);
      }
    };

    const onMouseMove = (event) => {
      const delta = event.clientX - startX;
      pendingWidth = clampModelIdColWidth(startWidth + delta);
      if (rafId !== null) {
        return;
      }
      rafId = requestAnimationFrame(flushPendingWidth);
    };

    const startResize = (clientX) => {
      const measuredWidth = modelIdColHeader.getBoundingClientRect().width;
      startX = clientX;
      startWidth = modelIdColWidth ?? measuredWidth;
      pendingWidth = null;
      document.body.classList.add("model-id-col-resizing");
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", stopResize);
    };

    modelIdColResizer.addEventListener("mousedown", (event) => {
      event.preventDefault();
      startResize(event.clientX);
    });

    modelIdColResizer.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
        return;
      }
      event.preventDefault();
      const measuredWidth = modelIdColHeader.getBoundingClientRect().width;
      const currentWidth = modelIdColWidth ?? measuredWidth;
      const delta = event.key === "ArrowLeft" ? -8 : 8;
      const nextWidth = clampModelIdColWidth(currentWidth + delta);
      applyModelIdColWidth(nextWidth);
      persistModelIdColWidth(nextWidth);
    });
  }

  function setRemovedFilterMode(mode) {
    removedFilterMode = mode;
    for (const button of removedFilterButtons) {
      const isActive = button.dataset.removedFilter === mode;
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    }
  }

  function setPointerFilterMode(mode) {
    pointerFilterMode = mode;
    for (const button of pointerFilterButtons) {
      const isActive = button.dataset.pointerFilter === mode;
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    }
  }

  function setBatchFilterMode(mode) {
    batchFilterMode = mode;
    for (const button of batchFilterButtons) {
      const isActive = button.dataset.batchFilter === mode;
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    }
  }

  function isPointerModel(model) {
    if (typeof model.is_pointer === "boolean") {
      return model.is_pointer;
    }
    const modelId = model.model_id;
    if (modelId.startsWith("~")) {
      return true;
    }
    const slugPart = modelId.split("/", 2)[1] ?? "";
    return slugPart.includes("-latest");
  }

  function resolveDisplayModel(row) {
    if (!isPointerModel(row) || !row.pointer_target_id) {
      return row;
    }
    const target = modelsById.get(row.pointer_target_id);
    if (!target) {
      return row;
    }
    return {
      ...target,
      model_id: row.model_id,
      name: row.name ?? target.name,
      openrouter_model_url: row.openrouter_model_url ?? target.openrouter_model_url,
      is_pointer: true,
      pointer_target_id: row.pointer_target_id,
      pointer_kind: row.pointer_kind ?? null,
      officially_removed: row.officially_removed,
      fetched_at: row.fetched_at,
      updated_at: row.updated_at ?? row.fetched_at,
    };
  }

  function updateSortControlUi() {
    if (sortTriggerLabel) {
      sortTriggerLabel.textContent = formatSortTriggerLabel(
        sortFieldValue,
        sortDirectionValue,
        SORT_FIELD_LABELS,
      );
    }
    for (const button of sortFieldButtons) {
      const value = button.dataset.sortField ?? "";
      button.setAttribute("aria-pressed", value === sortFieldValue ? "true" : "false");
    }
    for (const button of sortDirButtons) {
      const dir = button.dataset.sortDir;
      const isActive = Boolean(sortFieldValue) && dir === sortDirectionValue;
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
      button.disabled = !sortFieldValue;
    }
  }

  function setSortPanelOpen(open) {
    if (!sortPanel || !sortTrigger) {
      return;
    }
    if (open) {
      sortPanel.hidden = false;
      sortTrigger.setAttribute("aria-expanded", "true");
    } else {
      sortPanel.hidden = true;
      sortTrigger.setAttribute("aria-expanded", "false");
    }
  }

  function updateSortDirectionState({ resetDirection = false } = {}) {
    if (resetDirection) {
      sortDirectionValue = "desc";
    }
    updateSortControlUi();
  }

  function truncateToOneDecimal(value) {
    return (Math.trunc(value * 10) / 10).toFixed(1);
  }

  function formatCompact(value) {
    if (value === null) {
      return '<span class="text-slate-400 dark:text-slate-600">—</span>';
    }
    const absValue = Math.abs(value);
    let formatted = "";
    if (absValue >= 1_000_000) {
      formatted = `${truncateToOneDecimal(value / 1_000_000)}M`;
    } else if (absValue >= 1_000) {
      formatted = `${truncateToOneDecimal(value / 1_000)}K`;
    } else {
      formatted = new Intl.NumberFormat("en-US").format(value);
    }
    return `<span class="text-slate-700 dark:text-slate-300">${formatted}</span>`;
  }

  function formatPrice(value) {
    if (value === null) {
      return '<span class="text-slate-400 dark:text-slate-600">—</span>';
    }
    if (value === 0) {
      return '<span class="text-slate-700 dark:text-slate-300">0</span>';
    }
    const formatted = value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
    return `<span class="text-slate-700 dark:text-slate-300">${formatted}</span>`;
  }

  function formatIndex(value) {
    if (value === null) return '<span class="text-slate-400 dark:text-slate-600">—</span>';
    const num = value.toFixed(1);
    // Add a subtle color based on value for index
    let colorClass = "text-slate-700 dark:text-slate-300";
    if (value >= 80) colorClass = "text-emerald-600 dark:text-emerald-400 font-medium";
    else if (value >= 50) colorClass = "ow-accent-text";
    return `<span class="${colorClass}">${num}</span>`;
  }

  function formatCapabilityBadge(letter, supported, tip, onClass) {
    const aria = `${tip}: ${supported ? "yes" : "no"}`;
    const stateClass = supported ? `cap-badge--on ${onClass}` : "";
    return `<span
      class="cap-badge ${stateClass}"
      data-cap-tip="${tip}"
      tabindex="0"
      role="img"
      aria-label="${aria}"
    >${letter}</span>`;
  }

  function formatCapabilities(reasoning, tools, vision) {
    return `<span class="cap-cell">
      ${formatCapabilityBadge("R", reasoning, "Reasoning", "cap-badge--r")}
      ${formatCapabilityBadge("T", tools, "Tools", "cap-badge--t")}
      ${formatCapabilityBadge("V", vision, "Vision", "cap-badge--v")}
    </span>`;
  }

  function formatTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return `<span class="text-slate-500 dark:text-slate-400">${value}</span>`;
    }
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, "0");
    const day = String(date.getUTCDate()).padStart(2, "0");
    const hour = String(date.getUTCHours()).padStart(2, "0");
    const minute = String(date.getUTCMinutes()).padStart(2, "0");
    return `<span class="text-slate-500 dark:text-slate-400">${year}-${month}-${day} ${hour}:${minute}</span>`;
  }

  function formatKnowledgeCutoff(value) {
    if (value == null || value === "") {
      return '<span class="text-slate-400 dark:text-slate-600">—</span>';
    }
    const text = String(value);
    const month = /^\d{4}-\d{2}/.test(text) ? text.slice(0, 7) : text;
    return `<span class="text-slate-700 dark:text-slate-300">${month}</span>`;
  }

  function formatReleasedAt(value) {
    if (value == null || value === "") {
      return '<span class="text-slate-400 dark:text-slate-600">—</span>';
    }
    return `<span class="text-slate-700 dark:text-slate-300">${value}</span>`;
  }

  function getKnowledgeCutoffMonth(value) {
    if (value == null || value === "") {
      return null;
    }
    const text = String(value);
    return /^\d{4}-\d{2}/.test(text) ? text.slice(0, 7) : text;
  }

  function compareNullableText(left, right, direction) {
    if (left === null && right === null) {
      return 0;
    }
    if (left === null) {
      return 1;
    }
    if (right === null) {
      return -1;
    }
    const result = left.localeCompare(right);
    return direction === "asc" ? result : -result;
  }

  function getModelUrl(model) {
    return model.openrouter_model_url || `https://openrouter.ai/${model.model_id}`;
  }

  function getUpdatedAtValue(model) {
    return model.updated_at || model.fetched_at || "";
  }

  function createModelIdHTML(model) {
    const removedBadge = model.officially_removed
      ? '<span class="model-id-badge rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700 ring-1 ring-inset ring-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:ring-amber-500/30">已下架</span>'
      : "";
    const pointerBadge = isPointerModel(model)
      ? `<span
          class="model-id-badge rounded-full bg-violet-100 px-2 py-0.5 text-[11px] font-semibold text-violet-700 ring-1 ring-inset ring-violet-200 dark:bg-violet-500/15 dark:text-violet-300 dark:ring-violet-500/30"
          title="${model.pointer_target_id ? `→ ${model.pointer_target_id}` : "Latest"}"
        >Latest</span>`
      : "";
    const url = getModelUrl(model);
    return `
      <a
        href="${url}"
        target="_blank"
        rel="noopener noreferrer"
        title="${model.model_id}"
        class="model-id-link rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--ow-accent)]/40"
      >
        <span class="model-id-text font-semibold ow-accent-text transition-colors">${model.model_id}</span>
        ${pointerBadge}
        ${removedBadge}
      </a>
    `;
  }

  function parseRangeValue(input) {
    if (!input) {
      return null;
    }
    const value = input.value.trim();
    if (!value) {
      return null;
    }
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return null;
    }
    const scaleRaw = Number(input.dataset.rangeScale ?? "1");
    const scale = Number.isFinite(scaleRaw) && scaleRaw > 0 ? scaleRaw : 1;
    return parsed * scale;
  }

  function getRangeByKey(key) {
    const minInput = document.querySelector(
      `input[data-range-key="${key}"][data-range-bound="min"]`,
    );
    const maxInput = document.querySelector(
      `input[data-range-key="${key}"][data-range-bound="max"]`,
    );
    return {
      min: parseRangeValue(minInput),
      max: parseRangeValue(maxInput),
    };
  }

  function toSearchText(model) {
    return [
      model.model_id,
      model.vendor_name,
      model.name,
      model.author,
      model.slug,
      model.pointer_target_id,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  function compareNullableNumber(left, right, direction) {
    if (left === null && right === null) {
      return 0;
    }
    if (left === null) {
      return 1;
    }
    if (right === null) {
      return -1;
    }
    return direction === "asc" ? left - right : right - left;
  }

  function parseFetchedAtValue(value) {
    if (!value) {
      return { valid: false, timestamp: 0, text: "" };
    }
    const timestamp = Date.parse(value);
    if (!Number.isFinite(timestamp)) {
      return { valid: false, timestamp: 0, text: value };
    }
    return { valid: true, timestamp, text: value };
  }

  function compareFetchedAt(left, right, direction) {
    const parsedLeft = parseFetchedAtValue(left);
    const parsedRight = parseFetchedAtValue(right);

    if (!parsedLeft.valid && !parsedRight.valid) {
      return direction === "asc"
        ? parsedLeft.text.localeCompare(parsedRight.text)
        : parsedRight.text.localeCompare(parsedLeft.text);
    }
    if (!parsedLeft.valid) {
      return 1;
    }
    if (!parsedRight.valid) {
      return -1;
    }
    return direction === "asc"
      ? parsedLeft.timestamp - parsedRight.timestamp
      : parsedRight.timestamp - parsedLeft.timestamp;
  }

  function createCellHTML(html, className, dataset = {}) {
    const cell = document.createElement("td");
    cell.className = className;
    for (const [key, value] of Object.entries(dataset)) {
      cell.dataset[key] = value;
    }
    cell.innerHTML = html;
    return cell;
  }

  function syncPinClearButton() {
    if (!pinClearAll) {
      return;
    }
    const disabled = pinnedIds.length === 0;
    pinClearAll.disabled = disabled;
    pinClearAll.setAttribute("aria-disabled", disabled ? "true" : "false");
  }

  function pinModel(modelId) {
    if (!modelId || pinnedIds.includes(modelId)) {
      return;
    }
    pinnedIds.push(modelId);
    applyFiltersAndSort();
  }

  function unpinModel(modelId) {
    const index = pinnedIds.indexOf(modelId);
    if (index < 0) {
      return;
    }
    pinnedIds.splice(index, 1);
    applyFiltersAndSort();
  }

  function clearAllPins() {
    if (pinnedIds.length === 0) {
      return;
    }
    pinnedIds.length = 0;
    applyFiltersAndSort();
  }

  function pinDropPlace(event, row) {
    const rect = row.getBoundingClientRect();
    return event.clientY < rect.top + rect.height / 2 ? "before" : "after";
  }

  function clearPinDropIndicators() {
    tableBody?.querySelectorAll("tr.ow-row-pin-drop, tr.ow-row-pin-drop-after").forEach((el) => {
      el.classList.remove("ow-row-pin-drop", "ow-row-pin-drop-after");
    });
  }

  function reorderPinned(fromId, toId, place = "before") {
    // Keep algorithm aligned with web/src/lib/pinReorder.js (node:test).
    // Top insert line ⇒ before; bottom insert line ⇒ after (incl. group end).
    const from = pinnedIds.indexOf(fromId);
    const to = pinnedIds.indexOf(toId);
    if (from < 0 || to < 0 || from === to) {
      return;
    }
    const [item] = pinnedIds.splice(from, 1);
    const targetAt = pinnedIds.indexOf(toId);
    if (targetAt < 0) {
      pinnedIds.splice(from, 0, item);
      return;
    }
    const insertAt = place === "after" ? targetAt + 1 : targetAt;
    pinnedIds.splice(insertAt, 0, item);
    applyFiltersAndSort();
  }

  function createModelIdCell(model, display, pinned) {
    const cell = document.createElement("td");
    cell.className = "px-5 py-3 font-mono text-xs";
    cell.dataset.col = "model-id";

    const inner = document.createElement("div");
    inner.className = "model-id-cell-inner";

    if (pinned) {
      // Decorative pointer-only grip: not in tab order, not announced as a control
      // (RFC / Lens B1: no keyboard reorder).
      const handle = document.createElement("span");
      handle.className = "pin-drag-handle";
      handle.setAttribute("aria-hidden", "true");
      handle.title = "拖拽排序";
      handle.draggable = true;
      handle.innerHTML = PIN_GRIP;
      handle.addEventListener("dragstart", (event) => {
        pinDragId = model.model_id;
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", model.model_id);
        const row = cell.closest("tr");
        row?.classList.add("pin-dragging");
      });
      handle.addEventListener("dragend", () => {
        pinDragId = null;
        tableBody?.querySelectorAll("tr.pin-dragging").forEach((el) => {
          el.classList.remove("pin-dragging");
        });
        clearPinDropIndicators();
      });
      inner.appendChild(handle);
    }

    const pinBtn = document.createElement("button");
    pinBtn.type = "button";
    pinBtn.className = "pin-toggle ow-press";
    pinBtn.setAttribute("aria-pressed", pinned ? "true" : "false");
    pinBtn.setAttribute(
      "aria-label",
      pinned ? `取消 Pin ${model.model_id}` : `Pin ${model.model_id}`,
    );
    pinBtn.innerHTML = pinned ? PIN_BOOKMARK_FILLED : PIN_BOOKMARK_OUTLINE;
    pinBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (pinned) {
        unpinModel(model.model_id);
      } else {
        pinModel(model.model_id);
      }
    });
    inner.appendChild(pinBtn);

    const linkWrap = document.createElement("div");
    linkWrap.className = "model-id-link-wrap";
    linkWrap.innerHTML = createModelIdHTML(display);
    inner.appendChild(linkWrap);

    cell.appendChild(inner);
    return cell;
  }

  function renderRows(rows, pinnedCount = 0) {
    if (!tableBody) {
      return;
    }
    tableBody.textContent = "";
    const fragment = document.createDocumentFragment();
    const pinSet = new Set(pinnedIds);

    for (const model of rows) {
      const display = resolveDisplayModel(model);
      const pinned = pinSet.has(model.model_id);
      const row = document.createElement("tr");
      row.className = `ow-row group transition-colors${display.officially_removed ? " opacity-70" : ""}${pinned ? " ow-row-pinned" : ""}`;
      row.dataset.modelId = model.model_id;
      row.dataset.pinned = pinned ? "true" : "false";

      if (pinned) {
        row.addEventListener("dragover", (event) => {
          if (!pinDragId || pinDragId === model.model_id) {
            return;
          }
          event.preventDefault();
          const place = pinDropPlace(event, row);
          clearPinDropIndicators();
          row.classList.add(place === "after" ? "ow-row-pin-drop-after" : "ow-row-pin-drop");
        });
        row.addEventListener("dragleave", () => {
          row.classList.remove("ow-row-pin-drop", "ow-row-pin-drop-after");
        });
        row.addEventListener("drop", (event) => {
          event.preventDefault();
          const place = pinDropPlace(event, row);
          clearPinDropIndicators();
          const fromId = pinDragId || event.dataTransfer.getData("text/plain");
          if (!fromId || fromId === model.model_id) {
            return;
          }
          reorderPinned(fromId, model.model_id, place);
        });
      }

      row.appendChild(createModelIdCell(model, display, pinned));
      row.appendChild(
        createCellHTML(formatCompact(display.context_length), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatCompact(display.max_completion_tokens), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatPrice(display.input_price_usd_per_1m), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(
          formatPrice(display.weighted_avg_input_price_usd_per_1m ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(formatPrice(display.output_price_usd_per_1m), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatIndex(display.intelligence_index), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatIndex(display.coding_index), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatIndex(display.agentic_index), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(
          formatCapabilities(
            display.supports_reasoning,
            display.supports_tools,
            display.supports_vision,
          ),
          "whitespace-nowrap px-5 py-3",
        ),
      );
      row.appendChild(
        createCellHTML(formatKnowledgeCutoff(display.knowledge_cutoff), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatReleasedAt(display.released_at), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      row.appendChild(
        createCellHTML(formatTimestamp(getUpdatedAtValue(display)), "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs"),
      );
      fragment.appendChild(row);
    }
    tableBody.appendChild(fragment);
    applyModelIdColWidth(modelIdColWidth);
    syncPinClearButton();

    if (count) {
      const pinPart =
        pinnedCount > 0
          ? `（含 <span style="color: var(--ow-ink)">${pinnedCount}</span> 个 Pin）`
          : "";
      count.innerHTML = `显示 <span style="color: var(--ow-ink)">${rows.length}</span>${pinPart} / ${totalRows} 个模型`;
    }
  }

  function getNumericValue(model, key) {
    const rawValue = model[key];
    return typeof rawValue === "number" ? rawValue : null;
  }

  function applyFiltersAndSort() {
    const search = searchInput?.value.trim().toLowerCase() ?? "";
    const needsReasoning = capReasoning?.checked ?? false;
    const needsTools = capTools?.checked ?? false;
    const needsVision = capVision?.checked ?? false;
    const directionValue = sortDirectionValue;
    const field = sortFieldValue;
    const direction = directionValue === "asc" ? "asc" : "desc";
    const numericRanges = {
      context_length: getRangeByKey("context_length"),
      max_completion_tokens: getRangeByKey("max_completion_tokens"),
      input_price_usd_per_1m: getRangeByKey("input_price_usd_per_1m"),
      weighted_avg_input_price_usd_per_1m: getRangeByKey("weighted_avg_input_price_usd_per_1m"),
      output_price_usd_per_1m: getRangeByKey("output_price_usd_per_1m"),
      intelligence_index: getRangeByKey("intelligence_index"),
      coding_index: getRangeByKey("coding_index"),
      agentic_index: getRangeByKey("agentic_index"),
    };

    const pinSet = new Set(pinnedIds);
    // Drop stale ids that no longer exist in the dataset.
    for (let i = pinnedIds.length - 1; i >= 0; i -= 1) {
      const id = pinnedIds[i];
      if (!modelsById.has(id)) {
        pinnedIds.splice(i, 1);
        pinSet.delete(id);
      }
    }

    const filtered = models
      .map((model, index) => ({ model, display: resolveDisplayModel(model), index }))
      .filter(({ model, display }) =>
        rowPassesFilters({
          model,
          display,
          pinSet,
          search,
          needsReasoning,
          needsTools,
          needsVision,
          removedMode: removedFilterMode,
          pointerMode: pointerFilterMode,
          batchMode: batchFilterMode,
          selectedVendors,
          vendorMatchByChip: vendorMatchMap,
          toSearchText,
          numericRanges,
          getNumericValue,
          numericRangeKeys,
        }),
      );

    if (field) {
      filtered.sort((left, right) => {
        let result = 0;
        if (field === "updated_at") {
          result = compareFetchedAt(getUpdatedAtValue(left.display), getUpdatedAtValue(right.display), direction);
        } else if (field === "knowledge_cutoff") {
          result = compareNullableText(
            getKnowledgeCutoffMonth(left.display.knowledge_cutoff),
            getKnowledgeCutoffMonth(right.display.knowledge_cutoff),
            direction,
          );
        } else if (field === "released_at") {
          result = compareNullableText(
            left.display.released_at ?? null,
            right.display.released_at ?? null,
            direction,
          );
        } else {
          const leftValue = getNumericValue(left.display, field);
          const rightValue = getNumericValue(right.display, field);
          result = compareNullableNumber(leftValue, rightValue, direction);
        }
        if (result !== 0) {
          return result;
        }
        const modelIdCompare = left.model.model_id.localeCompare(right.model.model_id);
        if (modelIdCompare !== 0) {
          return modelIdCompare;
        }
        return left.index - right.index;
      });
    }

    const pinnedModels = pinnedIds.map((id) => modelsById.get(id)).filter(Boolean);
    const visible = [...pinnedModels, ...filtered.map((entry) => entry.model)];
    renderRows(visible, pinnedModels.length);
  }

  searchInput?.addEventListener("input", applyFiltersAndSort);
  capReasoning?.addEventListener("change", applyFiltersAndSort);
  capTools?.addEventListener("change", applyFiltersAndSort);
  capVision?.addEventListener("change", applyFiltersAndSort);
  for (const button of removedFilterButtons) {
    button.addEventListener("click", () => {
      const mode = button.dataset.removedFilter;
      if (!mode || mode === removedFilterMode) {
        return;
      }
      setRemovedFilterMode(mode);
      applyFiltersAndSort();
    });
  }
  for (const button of pointerFilterButtons) {
    button.addEventListener("click", () => {
      const mode = button.dataset.pointerFilter;
      if (!mode || mode === pointerFilterMode) {
        return;
      }
      setPointerFilterMode(mode);
      applyFiltersAndSort();
    });
  }

  for (const button of batchFilterButtons) {
    button.addEventListener("click", () => {
      const mode = button.dataset.batchFilter;
      if (!mode || mode === batchFilterMode) {
        return;
      }
      setBatchFilterMode(mode);
      applyFiltersAndSort();
    });
  }

  function syncVendorChipPressedState() {
    for (const button of vendorFilterButtons) {
      const vendor = button.dataset.vendorFilter;
      const isActive = Boolean(vendor && selectedVendors.has(vendor));
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    }
  }

  for (const button of vendorFilterButtons) {
    button.addEventListener("click", () => {
      const vendor = button.dataset.vendorFilter;
      if (!vendor) {
        return;
      }
      if (selectedVendors.has(vendor)) {
        selectedVendors.delete(vendor);
      } else {
        selectedVendors.add(vendor);
      }
      syncVendorChipPressedState();
      applyFiltersAndSort();
    });
  }

  vendorFilterClear?.addEventListener("click", () => {
    if (selectedVendors.size === 0) {
      return;
    }
    selectedVendors.clear();
    syncVendorChipPressedState();
    applyFiltersAndSort();
  });

  sortTrigger?.addEventListener("click", (event) => {
    event.stopPropagation();
    const currentlyOpen = Boolean(sortPanel && !sortPanel.hidden);
    setSortPanelOpen(toggleSortPanelOpen(currentlyOpen));
  });

  for (const button of sortFieldButtons) {
    button.addEventListener("click", () => {
      const nextField = button.dataset.sortField ?? "";
      const next = applySortFieldSelection(
        { field: sortFieldValue, direction: sortDirectionValue },
        nextField,
      );
      sortFieldValue = next.field;
      sortDirectionValue = next.direction;
      updateSortControlUi();
      applyFiltersAndSort();
      if (next.closePanel) {
        setSortPanelOpen(false);
      }
    });
  }

  for (const button of sortDirButtons) {
    button.addEventListener("click", () => {
      const nextDir = button.dataset.sortDir === "asc" ? "asc" : "desc";
      const next = applySortDirectionSelection(
        { field: sortFieldValue, direction: sortDirectionValue },
        nextDir,
      );
      sortFieldValue = next.field;
      sortDirectionValue = next.direction;
      updateSortControlUi();
      applyFiltersAndSort();
      if (next.closePanel) {
        setSortPanelOpen(false);
      }
    });
  }

  document.addEventListener("click", (event) => {
    if (!sortControl || sortPanel?.hidden) {
      return;
    }
    if (!shouldCloseSortPanelOnOutsideClick(event.target, sortControl)) {
      return;
    }
    setSortPanelOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || sortPanel?.hidden) {
      return;
    }
    setSortPanelOpen(false);
    sortTrigger?.focus();
  });

  for (const input of rangeInputs) {
    input.addEventListener("input", applyFiltersAndSort);
  }

  pinClearAll?.addEventListener("click", () => {
    clearAllPins();
  });

  initModelIdColResize();
  updateSortDirectionState();
  initCapabilityTips();
  initPriceUnitTips();
  applyFiltersAndSort();

  function createFloatingTip(text, { wrap = false } = {}) {
    const tip = document.createElement("div");
    tip.className = wrap ? "cap-tip cap-tip--wrap" : "cap-tip";
    tip.textContent = text;
    tip.setAttribute("role", "tooltip");
    return tip;
  }

  function positionFloatingTip(tipEl, anchor) {
    const rect = anchor.getBoundingClientRect();
    tipEl.style.left = `${rect.left + rect.width / 2}px`;
    tipEl.style.top = `${rect.top}px`;
  }

  function initCapabilityTips() {
    let tipEl = null;

    const hideTip = () => {
      if (tipEl) {
        tipEl.remove();
        tipEl = null;
      }
    };

    const showTip = (badge) => {
      const text = badge.dataset.capTip;
      if (!text) {
        return;
      }
      hideTip();
      tipEl = createFloatingTip(text);
      document.body.appendChild(tipEl);
      positionFloatingTip(tipEl, badge);
    };

    if (!tableBody) {
      return;
    }

    tableBody.addEventListener("pointerover", (event) => {
      const badge = event.target.closest?.(".cap-badge");
      if (!badge || !tableBody.contains(badge)) {
        return;
      }
      showTip(badge);
    });

    tableBody.addEventListener("pointerout", (event) => {
      const badge = event.target.closest?.(".cap-badge");
      if (!badge) {
        return;
      }
      const next = event.relatedTarget;
      if (next && badge.contains(next)) {
        return;
      }
      hideTip();
    });

    tableBody.addEventListener("focusin", (event) => {
      const badge = event.target.closest?.(".cap-badge");
      if (badge) {
        showTip(badge);
      }
    });

    tableBody.addEventListener("focusout", () => {
      hideTip();
    });

    window.addEventListener("scroll", hideTip, true);
  }

  function initPriceUnitTips() {
    let tipEl = null;
    const headerRow = modelTable?.querySelector("thead tr");

    const hideTip = () => {
      if (tipEl) {
        tipEl.remove();
        tipEl = null;
      }
    };

    const showTip = (button) => {
      const text = button.dataset.tip;
      if (!text) {
        return;
      }
      hideTip();
      tipEl = createFloatingTip(text, { wrap: true });
      document.body.appendChild(tipEl);
      positionFloatingTip(tipEl, button);
    };

    if (!headerRow) {
      return;
    }

    headerRow.addEventListener("pointerover", (event) => {
      const button = event.target.closest?.(".price-unit-info");
      if (!button || !headerRow.contains(button)) {
        return;
      }
      showTip(button);
    });

    headerRow.addEventListener("pointerout", (event) => {
      const button = event.target.closest?.(".price-unit-info");
      if (!button) {
        return;
      }
      const next = event.relatedTarget;
      if (next && button.contains(next)) {
        return;
      }
      hideTip();
    });

    headerRow.addEventListener("focusin", (event) => {
      const button = event.target.closest?.(".price-unit-info");
      if (button) {
        showTip(button);
      }
    });

    headerRow.addEventListener("focusout", () => {
      hideTip();
    });

    window.addEventListener("scroll", hideTip, true);
  }
}
