/**
 * Pure HTML formatters for model table cells.
 */

/**
 * @param {number} value
 * @returns {string}
 */
export function truncateToOneDecimal(value) {
  return (Math.trunc(value * 10) / 10).toFixed(1);
}

/**
 * @param {number|null} value
 * @returns {string}
 */
export function formatCompact(value) {
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

/**
 * @param {number|null} value
 * @returns {string}
 */
export function formatPrice(value) {
  if (value === null) {
    return '<span class="text-slate-400 dark:text-slate-600">—</span>';
  }
  if (value === 0) {
    return '<span class="text-slate-700 dark:text-slate-300">0</span>';
  }
  const formatted = value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  return `<span class="text-slate-700 dark:text-slate-300">${formatted}</span>`;
}

/**
 * @param {number|null} value
 * @returns {string}
 */
export function formatIndex(value) {
  if (value === null) return '<span class="text-slate-400 dark:text-slate-600">—</span>';
  const num = value.toFixed(1);
  let colorClass = "text-slate-700 dark:text-slate-300";
  if (value >= 80) colorClass = "text-emerald-600 dark:text-emerald-400 font-medium";
  else if (value >= 50) colorClass = "ow-accent-text";
  return `<span class="${colorClass}">${num}</span>`;
}

/**
 * @param {string} letter
 * @param {boolean} supported
 * @param {string} tip
 * @param {string} onClass
 * @returns {string}
 */
export function formatCapabilityBadge(letter, supported, tip, onClass) {
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

/**
 * @param {boolean} reasoning
 * @param {boolean} tools
 * @param {boolean} vision
 * @returns {string}
 */
export function formatCapabilities(reasoning, tools, vision) {
  return `<span class="cap-cell">
      ${formatCapabilityBadge("R", reasoning, "Reasoning", "cap-badge--r")}
      ${formatCapabilityBadge("T", tools, "Tools", "cap-badge--t")}
      ${formatCapabilityBadge("V", vision, "Vision", "cap-badge--v")}
    </span>`;
}

/**
 * @param {string} value
 * @returns {string}
 */
export function formatTimestamp(value) {
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

/**
 * @param {string|null|undefined} value
 * @returns {string}
 */
export function formatKnowledgeCutoff(value) {
  if (value == null || value === "") {
    return '<span class="text-slate-400 dark:text-slate-600">—</span>';
  }
  const text = String(value);
  const month = /^\d{4}-\d{2}/.test(text) ? text.slice(0, 7) : text;
  return `<span class="text-slate-700 dark:text-slate-300">${month}</span>`;
}

/**
 * @param {string|null|undefined} value
 * @returns {string}
 */
export function formatReleasedAt(value) {
  if (value == null || value === "") {
    return '<span class="text-slate-400 dark:text-slate-600">—</span>';
  }
  return `<span class="text-slate-700 dark:text-slate-300">${value}</span>`;
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
export function getModelUrl(model) {
  return model.openrouter_model_url || `https://openrouter.ai/${model.model_id}`;
}

/**
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @returns {string}
 */
export function getUpdatedAtValue(model) {
  return model.updated_at || model.fetched_at || "";
}

/**
 * @param {import("./modelTableTypes.js").ModelRow} model
 * @param {boolean} isPointer
 * @returns {string}
 */
export function createModelIdHTML(model, isPointer) {
  const removedBadge = model.officially_removed
    ? '<span class="model-id-badge rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700 ring-1 ring-inset ring-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:ring-amber-500/30">已下架</span>'
    : "";
  const pointerBadge = isPointer
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
