/**
 * Safe DOM cell builders for the model table.
 * Model-sourced strings always go through textContent / setAttribute — never string HTML.
 */

import { resolveSafeModelUrl } from "./safeUrl.js";

/**
 * @param {number} value
 * @returns {string}
 */
export function truncateToOneDecimal(value) {
  return (Math.trunc(value * 10) / 10).toFixed(1);
}

/**
 * @param {string} className
 * @param {string} text
 * @returns {HTMLSpanElement}
 */
function textSpan(className, text) {
  const span = document.createElement("span");
  span.className = className;
  span.textContent = text;
  return span;
}

/**
 * @param {number|null} value
 * @returns {HTMLSpanElement}
 */
export function formatCompact(value) {
  if (value === null) {
    return textSpan("text-slate-400 dark:text-slate-600", "—");
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
  return textSpan("text-slate-700 dark:text-slate-300", formatted);
}

/**
 * @param {number|null} value
 * @returns {HTMLSpanElement}
 */
export function formatPrice(value) {
  if (value === null) {
    return textSpan("text-slate-400 dark:text-slate-600", "—");
  }
  if (value === 0) {
    return textSpan("text-slate-700 dark:text-slate-300", "0");
  }
  const formatted = value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  return textSpan("text-slate-700 dark:text-slate-300", formatted);
}

/**
 * @param {number|null} value
 * @returns {HTMLSpanElement}
 */
export function formatIndex(value) {
  if (value === null) {
    return textSpan("text-slate-400 dark:text-slate-600", "—");
  }
  const num = value.toFixed(1);
  let colorClass = "text-slate-700 dark:text-slate-300";
  if (value >= 80) colorClass = "text-emerald-600 dark:text-emerald-400 font-medium";
  else if (value >= 50) colorClass = "ow-accent-text";
  return textSpan(colorClass, num);
}

/**
 * @param {string} letter
 * @param {boolean} supported
 * @param {string} tip
 * @param {string} onClass
 * @returns {HTMLSpanElement}
 */
export function formatCapabilityBadge(letter, supported, tip, onClass) {
  const badge = document.createElement("span");
  badge.className = supported ? `cap-badge cap-badge--on ${onClass}` : "cap-badge";
  badge.dataset.capTip = tip;
  badge.tabIndex = 0;
  badge.setAttribute("role", "img");
  badge.setAttribute("aria-label", `${tip}: ${supported ? "yes" : "no"}`);
  badge.textContent = letter;
  return badge;
}

/**
 * @param {boolean} reasoning
 * @param {boolean} tools
 * @param {boolean} vision
 * @returns {HTMLSpanElement}
 */
export function formatCapabilities(reasoning, tools, vision) {
  const wrap = document.createElement("span");
  wrap.className = "cap-cell";
  wrap.append(
    formatCapabilityBadge("R", reasoning, "Reasoning", "cap-badge--r"),
    formatCapabilityBadge("T", tools, "Tools", "cap-badge--t"),
    formatCapabilityBadge("V", vision, "Vision", "cap-badge--v"),
  );
  return wrap;
}

/**
 * @param {string} value
 * @returns {HTMLSpanElement}
 */
export function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return textSpan("text-slate-500 dark:text-slate-400", String(value ?? ""));
  }
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return textSpan("text-slate-500 dark:text-slate-400", `${year}-${month}-${day} ${hour}:${minute}`);
}

/**
 * @param {string|null|undefined} value
 * @returns {HTMLSpanElement}
 */
export function formatKnowledgeCutoff(value) {
  if (value == null || value === "") {
    return textSpan("text-slate-400 dark:text-slate-600", "—");
  }
  const text = String(value);
  const month = /^\d{4}-\d{2}/.test(text) ? text.slice(0, 7) : text;
  return textSpan("text-slate-700 dark:text-slate-300", month);
}

/**
 * @param {string|null|undefined} value
 * @returns {HTMLSpanElement}
 */
export function formatReleasedAt(value) {
  if (value == null || value === "") {
    return textSpan("text-slate-400 dark:text-slate-600", "—");
  }
  return textSpan("text-slate-700 dark:text-slate-300", String(value));
}

/**
 * @param {string|null|undefined} value
 * @returns {string|null}
 */
export function getKnowledgeCutoffMonth(value) {
  if (value == null || value === "") {
    return null;
  }
  const text = String(value);
  return /^\d{4}-\d{2}/.test(text) ? text.slice(0, 7) : text;
}

/**
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @returns {string}
 */
export function getUpdatedAtValue(model) {
  return model.updated_at || model.fetched_at || "";
}

/**
 * Build the model-id link/badge cluster with safe DOM APIs.
 *
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @param {boolean} isPointer
 * @returns {HTMLElement}
 */
export function createModelIdContent(model, isPointer) {
  const safeHref = resolveSafeModelUrl(model);
  const root = document.createElement(safeHref ? "a" : "span");
  root.className =
    "model-id-link rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--ow-accent)]/40";

  if (safeHref) {
    root.setAttribute("href", safeHref);
    root.setAttribute("target", "_blank");
    root.setAttribute("rel", "noopener noreferrer");
  }
  root.setAttribute("title", model.model_id ?? "");

  const idText = document.createElement("span");
  idText.className = "model-id-text font-semibold ow-accent-text transition-colors";
  idText.textContent = model.model_id ?? "";
  root.appendChild(idText);

  if (isPointer) {
    const pointerBadge = document.createElement("span");
    pointerBadge.className =
      "model-id-badge rounded-full bg-violet-100 px-2 py-0.5 text-[11px] font-semibold text-violet-700 ring-1 ring-inset ring-violet-200 dark:bg-violet-500/15 dark:text-violet-300 dark:ring-violet-500/30";
    pointerBadge.textContent = "Latest";
    pointerBadge.title = model.pointer_target_id ? `→ ${model.pointer_target_id}` : "Latest";
    root.appendChild(pointerBadge);
  }

  if (model.officially_removed) {
    const removedBadge = document.createElement("span");
    removedBadge.className =
      "model-id-badge rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700 ring-1 ring-inset ring-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:ring-amber-500/30";
    removedBadge.textContent = "已下架";
    root.appendChild(removedBadge);
  }

  return root;
}
