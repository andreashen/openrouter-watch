/**
 * Exclusive segmented control helpers (radiogroup + radio semantics).
 * Implements APG-style roving tabindex with Arrow keys plus Home/End
 * to move focus and select.
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
 * @param {number} fromIndex
 * @param {number} delta
 * @returns {number}
 */
export function nextRadioIndex(buttons, fromIndex, delta) {
  const len = buttons.length;
  if (len === 0) {
    return -1;
  }
  return (fromIndex + delta + len * 10) % len;
}

/**
 * @param {string} key
 * @returns {"next"|"prev"|"first"|"last"|null}
 */
export function radioKeyboardAction(key) {
  switch (key) {
    case "ArrowRight":
    case "ArrowDown":
      return "next";
    case "ArrowLeft":
    case "ArrowUp":
      return "prev";
    case "Home":
      return "first";
    case "End":
      return "last";
    default:
      return null;
  }
}

/**
 * @param {HTMLElement[]} buttons
 * @param {string} dataKey
 * @param {(mode: string) => void} onSelect
 */
export function bindExclusiveRadioButtons(buttons, dataKey, onSelect) {
  /**
   * @param {HTMLElement} button
   */
  const selectButton = (button) => {
    const mode = button.dataset[dataKey];
    if (!mode) {
      return;
    }
    onSelect(mode);
    button.focus();
  };

  for (const button of buttons) {
    button.addEventListener("click", () => {
      selectButton(button);
    });

    button.addEventListener("keydown", (event) => {
      const action = radioKeyboardAction(event.key);
      if (!action) {
        return;
      }
      event.preventDefault();
      const currentIndex = buttons.indexOf(button);
      if (currentIndex < 0) {
        return;
      }
      let nextIndex = currentIndex;
      if (action === "next") {
        nextIndex = nextRadioIndex(buttons, currentIndex, 1);
      } else if (action === "prev") {
        nextIndex = nextRadioIndex(buttons, currentIndex, -1);
      } else if (action === "first") {
        nextIndex = 0;
      } else if (action === "last") {
        nextIndex = buttons.length - 1;
      }
      const next = buttons[nextIndex];
      if (next) {
        selectButton(next);
      }
    });
  }
}
