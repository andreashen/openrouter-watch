/**
 * Floating tooltip helpers for capability / price-unit info.
 */

/**
 * @param {string} text
 * @param {{ wrap?: boolean }} [opts]
 * @returns {HTMLDivElement}
 */
export function createFloatingTip(text, { wrap = false } = {}) {
  const tip = document.createElement("div");
  tip.className = wrap ? "cap-tip cap-tip--wrap" : "cap-tip";
  tip.textContent = text;
  tip.setAttribute("role", "tooltip");
  return tip;
}

/**
 * @param {HTMLElement} tipEl
 * @param {Element} anchor
 */
export function positionFloatingTip(tipEl, anchor) {
  const rect = anchor.getBoundingClientRect();
  tipEl.style.left = `${rect.left + rect.width / 2}px`;
  tipEl.style.top = `${rect.top}px`;
}

/**
 * @param {Element|null} tableBody
 */
export function initCapabilityTips(tableBody) {
  /** @type {HTMLDivElement|null} */
  let tipEl = null;

  const hideTip = () => {
    if (tipEl) {
      tipEl.remove();
      tipEl = null;
    }
  };

  /**
   * @param {HTMLElement} badge
   */
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
    const target = /** @type {Element|null} */ (event.target);
    const badge = /** @type {HTMLElement|null} */ (target?.closest?.(".cap-badge"));
    if (!badge || !tableBody.contains(badge)) {
      return;
    }
    showTip(badge);
  });

  tableBody.addEventListener("pointerout", (event) => {
    const target = /** @type {Element|null} */ (event.target);
    const badge = target?.closest?.(".cap-badge");
    if (!badge) {
      return;
    }
    const next = /** @type {Node|null} */ (/** @type {PointerEvent} */ (event).relatedTarget);
    if (next && badge.contains(next)) {
      return;
    }
    hideTip();
  });

  tableBody.addEventListener("focusin", (event) => {
    const target = /** @type {Element|null} */ (event.target);
    const badge = /** @type {HTMLElement|null} */ (target?.closest?.(".cap-badge"));
    if (badge) {
      showTip(badge);
    }
  });

  tableBody.addEventListener("focusout", () => {
    hideTip();
  });

  window.addEventListener("scroll", hideTip, true);
}

/**
 * @param {HTMLElement|null} modelTable
 */
export function initPriceUnitTips(modelTable) {
  /** @type {HTMLDivElement|null} */
  let tipEl = null;
  const headerRow = modelTable?.querySelector("thead tr");

  const hideTip = () => {
    if (tipEl) {
      tipEl.remove();
      tipEl = null;
    }
  };

  /**
   * @param {HTMLElement} button
   */
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
    const target = /** @type {Element|null} */ (event.target);
    const button = /** @type {HTMLElement|null} */ (target?.closest?.(".price-unit-info"));
    if (!button || !headerRow.contains(button)) {
      return;
    }
    showTip(button);
  });

  headerRow.addEventListener("pointerout", (event) => {
    const target = /** @type {Element|null} */ (event.target);
    const button = target?.closest?.(".price-unit-info");
    if (!button) {
      return;
    }
    const next = /** @type {Node|null} */ (/** @type {PointerEvent} */ (event).relatedTarget);
    if (next && button.contains(next)) {
      return;
    }
    hideTip();
  });

  headerRow.addEventListener("focusin", (event) => {
    const target = /** @type {Element|null} */ (event.target);
    const button = /** @type {HTMLElement|null} */ (target?.closest?.(".price-unit-info"));
    if (button) {
      showTip(button);
    }
  });

  headerRow.addEventListener("focusout", () => {
    hideTip();
  });

  window.addEventListener("scroll", hideTip, true);
}
