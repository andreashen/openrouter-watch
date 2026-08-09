/**
 * Exclusive segmented control helpers (radiogroup + radio semantics).
 */

/**
 * Sync buttons that belong to a radiogroup of exclusive options.
 * Uses `role="radio"` + `aria-checked` (not aria-pressed).
 *
 * @param {HTMLElement[]} buttons
 * @param {string} dataKey camelCase dataset key, e.g. "batchFilter"
 * @param {string} mode active value
 */
export function syncExclusiveRadioButtons(buttons, dataKey, mode) {
  for (const button of buttons) {
    const value = button.dataset[dataKey] ?? "";
    const isActive = value === mode;
    if (button.getAttribute("role") !== "radio") {
      button.setAttribute("role", "radio");
    }
    button.setAttribute("aria-checked", isActive ? "true" : "false");
    button.tabIndex = isActive ? 0 : -1;
  }
}

/**
 * @param {HTMLElement[]} buttons
 * @param {string} dataKey
 * @param {(mode: string) => void} onSelect
 */
export function bindExclusiveRadioButtons(buttons, dataKey, onSelect) {
  for (const button of buttons) {
    button.addEventListener("click", () => {
      const mode = button.dataset[dataKey];
      if (!mode) {
        return;
      }
      onSelect(mode);
    });
  }
}
