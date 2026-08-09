/**
 * S4 sort panel behavior helpers (production-path, unit-testable).
 */

/**
 * @param {string} field
 * @param {"asc"|"desc"} direction
 * @param {Record<string, string>} labels
 */
export function formatSortTriggerLabel(field, direction, labels = {}) {
  if (!field) {
    return "不排序";
  }
  const fieldLabel = labels[field] ?? field;
  return `${fieldLabel} · ${direction === "asc" ? "↑" : "↓"}`;
}

/**
 * @param {{ field: string, direction: "asc"|"desc" }} state
 * @param {string} nextField
 */
export function applySortFieldSelection(state, nextField) {
  if (!nextField) {
    return { field: "", direction: state.direction || "desc", closePanel: true };
  }
  return {
    field: nextField,
    direction: "desc",
    closePanel: false,
  };
}

/**
 * @param {{ field: string, direction: "asc"|"desc" }} state
 * @param {"asc"|"desc"} nextDir
 */
export function applySortDirectionSelection(state, nextDir) {
  if (!state.field) {
    return { ...state, closePanel: false };
  }
  return {
    field: state.field,
    direction: nextDir === "asc" ? "asc" : "desc",
    closePanel: true,
  };
}

/**
 * @param {boolean} currentlyOpen
 * @returns {boolean}
 */
export function toggleSortPanelOpen(currentlyOpen) {
  return !currentlyOpen;
}

/**
 * Decide whether an outside click should close the panel.
 * @param {EventTarget | null} target
 * @param {{ contains: (node: unknown) => boolean } | null} controlEl
 */
export function shouldCloseSortPanelOnOutsideClick(target, controlEl) {
  if (!controlEl || target == null || typeof controlEl.contains !== "function") {
    return false;
  }
  return !controlEl.contains(target);
}
