/**
 * Production visibility pipeline for the model table.
 * Uses the shared batch predicate so unit tests cover the shipped path.
 */

import { matchesBatchFilter } from "./batchFilter.js";
import { matchesVendorSelection } from "./vendorFilter.js";

/**
 * @param {{ model_id?: string, is_pointer?: boolean }} model
 * @returns {boolean}
 */
export function isPointerModel(model) {
  if (typeof model?.is_pointer === "boolean") {
    return model.is_pointer;
  }
  const modelId = model?.model_id ?? "";
  if (modelId.startsWith("~")) {
    return true;
  }
  const slugPart = modelId.split("/", 2)[1] ?? "";
  return slugPart.includes("-latest");
}

/**
 * @param {{ officially_removed?: boolean }} model
 * @param {"hide" | "show" | "only"} mode
 */
export function matchesRemovedFilter(model, mode) {
  if (mode === "show") {
    return true;
  }
  if (mode === "only") {
    return Boolean(model.officially_removed);
  }
  return !model.officially_removed;
}

/**
 * @param {{ model_id?: string, is_pointer?: boolean }} model
 * @param {"hide" | "show" | "only"} mode
 */
export function matchesPointerFilter(model, mode) {
  const isPointer = isPointerModel(model);
  if (!isPointer) {
    return mode !== "only";
  }
  if (mode === "hide") {
    return false;
  }
  return true;
}

/**
 * @param {object} args
 * @param {object} args.model
 * @param {object} args.display
 * @param {Set<string>} args.pinSet
 * @param {string} args.search lowercase trimmed
 * @param {boolean} args.needsReasoning
 * @param {boolean} args.needsTools
 * @param {boolean} args.needsVision
 * @param {"hide"|"show"|"only"} args.removedMode
 * @param {"hide"|"show"|"only"} args.pointerMode
 * @param {"hide"|"show"|"only"} args.batchMode
 * @param {Iterable<string>} args.selectedVendors
 * @param {Record<string, string[]>} [args.vendorMatchByChip]
 * @param {(model: object) => string} args.toSearchText
 * @param {Record<string, { min: number|null, max: number|null }>} [args.numericRanges]
 * @param {(display: object, key: string) => number|null} [args.getNumericValue]
 * @param {string[]} [args.numericRangeKeys]
 * @returns {boolean}
 */
export function rowPassesFilters({
  model,
  display,
  pinSet,
  search,
  needsReasoning = false,
  needsTools = false,
  needsVision = false,
  removedMode = "hide",
  pointerMode = "hide",
  batchMode = "hide",
  selectedVendors = [],
  vendorMatchByChip,
  toSearchText,
  numericRanges = {},
  getNumericValue,
  numericRangeKeys = [],
}) {
  if (pinSet?.has(model.model_id)) {
    return false;
  }
  if (search && !toSearchText(model).includes(search)) {
    return false;
  }
  if (needsReasoning && !display.supports_reasoning) {
    return false;
  }
  if (needsTools && !display.supports_tools) {
    return false;
  }
  if (needsVision && !display.supports_vision) {
    return false;
  }
  if (!matchesRemovedFilter(model, removedMode)) {
    return false;
  }
  if (!matchesPointerFilter(model, pointerMode)) {
    return false;
  }
  if (!matchesBatchFilter(model, batchMode)) {
    return false;
  }
  if (!matchesVendorSelection(display.vendor_name, selectedVendors, vendorMatchByChip)) {
    return false;
  }
  if (getNumericValue && numericRangeKeys.length > 0) {
    for (const key of numericRangeKeys) {
      const range = numericRanges[key] ?? { min: null, max: null };
      const value = getNumericValue(display, key);
      if ((range.min !== null || range.max !== null) && value === null) {
        return false;
      }
      if (range.min !== null && value !== null && value < range.min) {
        return false;
      }
      if (range.max !== null && value !== null && value > range.max) {
        return false;
      }
    }
  }
  return true;
}

/**
 * Compose final visible rows: pinned (filter-exempt) first, then filtered others.
 *
 * @param {object} args
 * @param {object[]} args.models
 * @param {string[]} args.pinnedIds
 * @param {(row: object) => object} args.resolveDisplayModel
 * @param {(model: object) => string} args.toSearchText
 * @param {Omit<Parameters<typeof rowPassesFilters>[0], "model"|"display"|"pinSet"|"toSearchText">} args.filters
 * @returns {{ visible: object[], pinnedCount: number, filteredCount: number }}
 */
export function composeVisibleModels({ models, pinnedIds, resolveDisplayModel, toSearchText, filters }) {
  const modelsById = new Map(models.map((model) => [model.model_id, model]));
  const livePinnedIds = pinnedIds.filter((id) => modelsById.has(id));
  const pinSet = new Set(livePinnedIds);

  const filtered = models.filter((model) =>
    rowPassesFilters({
      model,
      display: resolveDisplayModel(model),
      pinSet,
      toSearchText,
      ...filters,
    }),
  );

  const pinnedModels = livePinnedIds.map((id) => modelsById.get(id)).filter(Boolean);
  return {
    visible: [...pinnedModels, ...filtered],
    pinnedCount: pinnedModels.length,
    filteredCount: filtered.length,
  };
}
