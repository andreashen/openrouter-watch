import { isPointerModel, rowPassesFilters } from "./modelVisibility.js";
import {
  applySortDirectionSelection,
  applySortFieldSelection,
  formatSortTriggerLabel,
  shouldCloseSortPanelOnOutsideClick,
  toggleSortPanelOpen,
} from "./sortPanel.js";
import {
  compareFetchedAt,
  compareNullableNumber,
  compareNullableText,
} from "./modelTableCompare.js";
import { initModelIdColResize } from "./modelTableColumnResize.js";
import { getNumericValue, resolveDisplayModel, toSearchText } from "./modelTableDisplay.js";
import {
  createModelIdHTML,
  formatCapabilities,
  formatCompact,
  formatIndex,
  formatKnowledgeCutoff,
  formatPrice,
  formatReleasedAt,
  formatTimestamp,
  getKnowledgeCutoffMonth,
  getUpdatedAtValue,
} from "./modelTableFormat.js";
import { initCapabilityTips, initPriceUnitTips } from "./modelTableTips.js";
import {
  bindExclusiveRadioButtons,
  syncExclusiveRadioButtons,
} from "./segmentedFilterControl.js";

/** @typedef {import("./modelTableTypes.js").ModelRow} ModelRow */
/** @typedef {import("./modelTableTypes.js").ModelTableBoot} ModelTableBoot */
/** @typedef {import("./modelTableTypes.js").TriFilterMode} TriFilterMode */
/** @typedef {import("./modelTableTypes.js").SortDirection} SortDirection */

const PIN_BOOKMARK_OUTLINE = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4h10a1 1 0 011 1v15l-6-3.5L6 20V5a1 1 0 011-1z"/></svg>`;
const PIN_BOOKMARK_FILLED = `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4h10a1 1 0 011 1v15l-6-3.5L6 20V5a1 1 0 011-1z"/></svg>`;
const PIN_GRIP = `<svg viewBox="0 0 12 16" fill="currentColor" aria-hidden="true"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/><circle cx="3" cy="8" r="1.4"/><circle cx="9" cy="8" r="1.4"/><circle cx="3" cy="13" r="1.4"/><circle cx="9" cy="13" r="1.4"/></svg>`;

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

const NUMERIC_RANGE_KEYS = [
  "context_length",
  "max_completion_tokens",
  "input_price_usd_per_1m",
  "weighted_avg_input_price_usd_per_1m",
  "output_price_usd_per_1m",
  "intelligence_index",
  "coding_index",
  "agentic_index",
];

/**
 * @param {HTMLInputElement|null} input
 * @returns {number|null}
 */
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

/**
 * @param {string} key
 * @returns {{ min: number|null, max: number|null }}
 */
function getRangeByKey(key) {
  const minInput = /** @type {HTMLInputElement|null} */ (
    document.querySelector(`input[data-range-key="${key}"][data-range-bound="min"]`)
  );
  const maxInput = /** @type {HTMLInputElement|null} */ (
    document.querySelector(`input[data-range-key="${key}"][data-range-bound="max"]`)
  );
  return {
    min: parseRangeValue(minInput),
    max: parseRangeValue(maxInput),
  };
}

/**
 * @param {string} html
 * @param {string} className
 * @param {Record<string, string>} [dataset]
 * @returns {HTMLTableCellElement}
 */
function createCellHTML(html, className, dataset = {}) {
  const cell = document.createElement("td");
  cell.className = className;
  for (const [key, value] of Object.entries(dataset)) {
    cell.dataset[key] = value;
  }
  cell.innerHTML = html;
  return cell;
}

/**
 * @param {ModelTableBoot} [boot]
 */
export function initModelTable(boot = {}) {
  /** @type {ModelRow[]} */
  const models = Array.isArray(boot.models) ? boot.models : [];
  /** @type {Record<string, string[]>} */
  const vendorMatchByChip =
    boot.vendorMatchByChip && typeof boot.vendorMatchByChip === "object"
      ? boot.vendorMatchByChip
      : {};

  const tableBody = /** @type {HTMLElement|null} */ (document.querySelector("#model-table-body"));
  const modelTable = /** @type {HTMLElement|null} */ (document.querySelector("#model-table"));
  const modelIdColHeader = /** @type {HTMLElement|null} */ (
    document.querySelector("#model-id-col-header")
  );
  const modelIdColResizer = /** @type {HTMLElement|null} */ (
    document.querySelector("#model-id-col-resizer")
  );
  const count = document.querySelector("#model-count");
  const pinClearAll = /** @type {HTMLButtonElement|null} */ (
    document.querySelector("#pin-clear-all")
  );
  const searchInput = /** @type {HTMLInputElement|null} */ (
    document.querySelector("#model-search")
  );
  const capReasoning = /** @type {HTMLInputElement|null} */ (
    document.querySelector("#cap-reasoning")
  );
  const capTools = /** @type {HTMLInputElement|null} */ (document.querySelector("#cap-tools"));
  const capVision = /** @type {HTMLInputElement|null} */ (document.querySelector("#cap-vision"));
  const removedFilterButtons = /** @type {HTMLElement[]} */ (
    Array.from(document.querySelectorAll("[data-removed-filter]"))
  );
  const pointerFilterButtons = /** @type {HTMLElement[]} */ (
    Array.from(document.querySelectorAll("[data-pointer-filter]"))
  );
  const batchFilterButtons = /** @type {HTMLElement[]} */ (
    Array.from(document.querySelectorAll("[data-batch-filter]"))
  );
  const vendorFilterButtons = /** @type {HTMLElement[]} */ (
    Array.from(document.querySelectorAll("[data-vendor-filter]"))
  );
  const vendorFilterClear = document.querySelector("#vendor-filter-clear");
  const sortControl = document.querySelector("#sort-control");
  const sortTrigger = /** @type {HTMLButtonElement|null} */ (
    document.querySelector("#sort-trigger")
  );
  const sortTriggerLabel = document.querySelector("#sort-trigger-label");
  const sortPanel = /** @type {HTMLElement|null} */ (document.querySelector("#sort-panel"));
  const sortFieldButtons = /** @type {HTMLElement[]} */ (
    Array.from(document.querySelectorAll("[data-sort-field]"))
  );
  const sortDirButtons = /** @type {HTMLButtonElement[]} */ (
    Array.from(document.querySelectorAll("[data-sort-dir]"))
  );
  const rangeInputs = /** @type {HTMLInputElement[]} */ (
    Array.from(document.querySelectorAll("input[data-range-key][data-range-bound]"))
  );

  const totalRows = models.length;
  /** @type {Map<string, ModelRow>} */
  const modelsById = new Map(models.map((model) => [model.model_id, model]));

  /** @type {TriFilterMode} */
  let removedFilterMode = "hide";
  /** @type {TriFilterMode} */
  let pointerFilterMode = "hide";
  /** @type {TriFilterMode} */
  let batchFilterMode = "hide";
  /** @type {string} */
  let sortFieldValue = "";
  /** @type {SortDirection} */
  let sortDirectionValue = "desc";
  /** @type {Set<string>} */
  const selectedVendors = new Set();
  /** @type {string[]} */
  const pinnedIds = [];
  /** @type {string|null} */
  let pinDragId = null;

  const columnResize = initModelIdColResize({
    modelTable,
    modelIdColHeader,
    modelIdColResizer,
    storageKey: "openrouter-watch.model-id-column-width",
    minWidth: 140,
    maxWidth: 480,
  });

  /**
   * @param {TriFilterMode} mode
   */
  function setRemovedFilterMode(mode) {
    removedFilterMode = mode;
    syncExclusiveRadioButtons(removedFilterButtons, "removedFilter", mode);
  }

  /**
   * @param {TriFilterMode} mode
   */
  function setPointerFilterMode(mode) {
    pointerFilterMode = mode;
    syncExclusiveRadioButtons(pointerFilterButtons, "pointerFilter", mode);
  }

  /**
   * @param {TriFilterMode} mode
   */
  function setBatchFilterMode(mode) {
    batchFilterMode = mode;
    syncExclusiveRadioButtons(batchFilterButtons, "batchFilter", mode);
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

  /**
   * @param {boolean} open
   */
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

  function syncPinClearButton() {
    if (!pinClearAll) {
      return;
    }
    const disabled = pinnedIds.length === 0;
    pinClearAll.disabled = disabled;
    pinClearAll.setAttribute("aria-disabled", disabled ? "true" : "false");
  }

  /**
   * @param {string} modelId
   */
  function pinModel(modelId) {
    if (!modelId || pinnedIds.includes(modelId)) {
      return;
    }
    pinnedIds.push(modelId);
    applyFiltersAndSort();
  }

  /**
   * @param {string} modelId
   */
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

  /**
   * @param {DragEvent} event
   * @param {HTMLElement} row
   * @returns {"before"|"after"}
   */
  function pinDropPlace(event, row) {
    const rect = row.getBoundingClientRect();
    return event.clientY < rect.top + rect.height / 2 ? "before" : "after";
  }

  function clearPinDropIndicators() {
    tableBody?.querySelectorAll("tr.ow-row-pin-drop, tr.ow-row-pin-drop-after").forEach((el) => {
      el.classList.remove("ow-row-pin-drop", "ow-row-pin-drop-after");
    });
  }

  /**
   * @param {string} fromId
   * @param {string} toId
   * @param {"before"|"after"} [place]
   */
  function reorderPinned(fromId, toId, place = "before") {
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

  /**
   * @param {ModelRow} model
   * @param {ModelRow} display
   * @param {boolean} pinned
   * @returns {HTMLTableCellElement}
   */
  function createModelIdCell(model, display, pinned) {
    const cell = document.createElement("td");
    cell.className = "px-5 py-3 font-mono text-xs";
    cell.dataset.col = "model-id";

    const inner = document.createElement("div");
    inner.className = "model-id-cell-inner";

    if (pinned) {
      const handle = document.createElement("span");
      handle.className = "pin-drag-handle";
      handle.setAttribute("aria-hidden", "true");
      handle.title = "拖拽排序";
      handle.draggable = true;
      handle.innerHTML = PIN_GRIP;
      handle.addEventListener("dragstart", (event) => {
        pinDragId = model.model_id;
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", model.model_id);
        }
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
    linkWrap.innerHTML = createModelIdHTML(display, isPointerModel(display));
    inner.appendChild(linkWrap);

    cell.appendChild(inner);
    return cell;
  }

  /**
   * @param {ModelRow[]} rows
   * @param {number} [pinnedCount]
   */
  function renderRows(rows, pinnedCount = 0) {
    if (!tableBody) {
      return;
    }
    tableBody.textContent = "";
    const fragment = document.createDocumentFragment();
    const pinSet = new Set(pinnedIds);

    for (const model of rows) {
      const display = resolveDisplayModel(model, modelsById);
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
          const fromId = pinDragId || event.dataTransfer?.getData("text/plain");
          if (!fromId || fromId === model.model_id) {
            return;
          }
          reorderPinned(fromId, model.model_id, place);
        });
      }

      row.appendChild(createModelIdCell(model, display, pinned));
      row.appendChild(
        createCellHTML(
          formatCompact(display.context_length ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatCompact(display.max_completion_tokens ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatPrice(display.input_price_usd_per_1m ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatPrice(display.weighted_avg_input_price_usd_per_1m ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatPrice(display.output_price_usd_per_1m ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatIndex(display.intelligence_index ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatIndex(display.coding_index ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatIndex(display.agentic_index ?? null),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatCapabilities(
            Boolean(display.supports_reasoning),
            Boolean(display.supports_tools),
            Boolean(display.supports_vision),
          ),
          "whitespace-nowrap px-5 py-3",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatKnowledgeCutoff(display.knowledge_cutoff),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatReleasedAt(display.released_at),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      row.appendChild(
        createCellHTML(
          formatTimestamp(getUpdatedAtValue(display)),
          "whitespace-nowrap px-5 py-3 tabular-nums font-mono text-xs",
        ),
      );
      fragment.appendChild(row);
    }
    tableBody.appendChild(fragment);
    columnResize.apply(columnResize.getWidth());
    syncPinClearButton();

    if (count) {
      const pinPart =
        pinnedCount > 0
          ? `（含 <span style="color: var(--ow-ink)">${pinnedCount}</span> 个 Pin）`
          : "";
      count.innerHTML = `显示 <span style="color: var(--ow-ink)">${rows.length}</span>${pinPart} / ${totalRows} 个模型`;
    }
  }

  function applyFiltersAndSort() {
    const search = searchInput?.value.trim().toLowerCase() ?? "";
    const needsReasoning = capReasoning?.checked ?? false;
    const needsTools = capTools?.checked ?? false;
    const needsVision = capVision?.checked ?? false;
    const field = sortFieldValue;
    /** @type {SortDirection} */
    const direction = sortDirectionValue === "asc" ? "asc" : "desc";
    /** @type {Record<string, { min: number|null, max: number|null }>} */
    const numericRanges = Object.fromEntries(
      NUMERIC_RANGE_KEYS.map((key) => [key, getRangeByKey(key)]),
    );

    const pinSet = new Set(pinnedIds);
    for (let i = pinnedIds.length - 1; i >= 0; i -= 1) {
      const id = pinnedIds[i];
      if (!modelsById.has(id)) {
        pinnedIds.splice(i, 1);
        pinSet.delete(id);
      }
    }

    const filtered = models
      .map((model, index) => ({ model, display: resolveDisplayModel(model, modelsById), index }))
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
          vendorMatchByChip,
          toSearchText,
          numericRanges,
          getNumericValue,
          numericRangeKeys: NUMERIC_RANGE_KEYS,
        }),
      );

    if (field) {
      filtered.sort((left, right) => {
        let result = 0;
        if (field === "updated_at") {
          result = compareFetchedAt(
            getUpdatedAtValue(left.display),
            getUpdatedAtValue(right.display),
            direction,
          );
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
          result = compareNullableNumber(
            getNumericValue(left.display, field),
            getNumericValue(right.display, field),
            direction,
          );
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
    renderRows(/** @type {ModelRow[]} */ (visible), pinnedModels.length);
  }

  function syncVendorChipPressedState() {
    for (const button of vendorFilterButtons) {
      const vendor = button.dataset.vendorFilter;
      const isActive = Boolean(vendor && selectedVendors.has(vendor));
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    }
  }

  searchInput?.addEventListener("input", applyFiltersAndSort);
  capReasoning?.addEventListener("change", applyFiltersAndSort);
  capTools?.addEventListener("change", applyFiltersAndSort);
  capVision?.addEventListener("change", applyFiltersAndSort);

  bindExclusiveRadioButtons(removedFilterButtons, "removedFilter", (mode) => {
    if (mode === removedFilterMode) return;
    setRemovedFilterMode(/** @type {TriFilterMode} */ (mode));
    applyFiltersAndSort();
  });
  bindExclusiveRadioButtons(pointerFilterButtons, "pointerFilter", (mode) => {
    if (mode === pointerFilterMode) return;
    setPointerFilterMode(/** @type {TriFilterMode} */ (mode));
    applyFiltersAndSort();
  });
  bindExclusiveRadioButtons(batchFilterButtons, "batchFilter", (mode) => {
    if (mode === batchFilterMode) return;
    setBatchFilterMode(/** @type {TriFilterMode} */ (mode));
    applyFiltersAndSort();
  });

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

  setRemovedFilterMode("hide");
  setPointerFilterMode("hide");
  setBatchFilterMode("hide");
  updateSortControlUi();
  initCapabilityTips(tableBody);
  initPriceUnitTips(modelTable);
  applyFiltersAndSort();
}
