/**
 * Batch model id helpers.
 *
 * OpenRouter batch endpoints use a `:batch` suffix on `model_id`
 * (e.g. `openai/gpt-4o:batch`). Matching is case-insensitive and suffix-only.
 */

/**
 * @param {{ model_id?: string } | null | undefined} model
 * @returns {boolean}
 */
export function isBatchModel(model) {
  const id = model?.model_id;
  if (typeof id !== "string" || id.length === 0) {
    return false;
  }
  return id.toLowerCase().endsWith(":batch");
}

/**
 * @param {{ model_id?: string } | null | undefined} model
 * @param {"hide" | "show" | "only"} mode
 * @returns {boolean}
 */
export function matchesBatchFilter(model, mode) {
  const isBatch = isBatchModel(model);
  if (mode === "show") {
    return true;
  }
  if (mode === "only") {
    return isBatch;
  }
  return !isBatch;
}
