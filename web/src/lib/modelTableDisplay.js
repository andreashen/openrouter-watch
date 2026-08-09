/**
 * Resolve display row for pointer/latest models.
 */

import { isPointerModel } from "./modelVisibility.js";

/**
 * @param {import("./modelTableTypes.js").ModelRow} row
 * @param {Map<string, import("./modelTableTypes.js").ModelRow>} modelsById
 * @returns {import("./modelTableTypes.js").ModelRow}
 */
export function resolveDisplayModel(row, modelsById) {
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

/**
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @returns {string}
 */
export function toSearchText(model) {
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

/**
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @param {string} key
 * @returns {number|null}
 */
export function getNumericValue(model, key) {
  const rawValue = /** @type {Record<string, unknown>} */ (model)[key];
  return typeof rawValue === "number" ? rawValue : null;
}
