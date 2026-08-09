/**
 * Model ID column resize behavior.
 */

/**
 * @param {object} opts
 * @param {HTMLElement|null} opts.modelTable
 * @param {HTMLElement|null} opts.modelIdColHeader
 * @param {HTMLElement|null} opts.modelIdColResizer
 * @param {string} opts.storageKey
 * @param {number} opts.minWidth
 * @param {number} opts.maxWidth
 * @returns {{ apply: (width: number|null) => void, getWidth: () => number|null }}
 */
export function initModelIdColResize({
  modelTable,
  modelIdColHeader,
  modelIdColResizer,
  storageKey,
  minWidth,
  maxWidth,
}) {
  /** @type {number|null} */
  let modelIdColWidth = null;

  /**
   * @param {number} width
   */
  const clamp = (width) => Math.min(maxWidth, Math.max(minWidth, width));

  const readStored = () => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        return null;
      }
      const parsed = Number(raw);
      return Number.isFinite(parsed) ? clamp(parsed) : null;
    } catch {
      return null;
    }
  };

  /**
   * @param {number|null} width
   */
  const persist = (width) => {
    try {
      if (width === null) {
        window.localStorage.removeItem(storageKey);
        return;
      }
      window.localStorage.setItem(storageKey, String(width));
    } catch {
      // Ignore storage failures.
    }
  };

  /**
   * @param {number|null} width
   */
  const apply = (width) => {
    modelIdColWidth = width;
    if (!modelTable || !modelIdColHeader) {
      return;
    }
    if (width === null) {
      modelTable.classList.remove("model-id-col-sized");
      modelIdColHeader.style.width = "";
      modelIdColHeader.style.maxWidth = "";
      modelIdColHeader.style.minWidth = "";
      return;
    }
    modelTable.classList.add("model-id-col-sized");
    const widthStyle = `${width}px`;
    modelIdColHeader.style.width = widthStyle;
    modelIdColHeader.style.maxWidth = widthStyle;
    modelIdColHeader.style.minWidth = widthStyle;
  };

  apply(readStored());

  if (!modelIdColResizer || !modelIdColHeader) {
    return {
      apply,
      getWidth: () => modelIdColWidth,
    };
  }

  let startX = 0;
  let startWidth = 0;
  /** @type {number|null} */
  let pendingWidth = null;
  /** @type {number|null} */
  let rafId = null;

  const flushPendingWidth = () => {
    rafId = null;
    if (pendingWidth === null) {
      return;
    }
    apply(pendingWidth);
    pendingWidth = null;
  };

  const stopResize = () => {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      flushPendingWidth();
    }
    document.body.classList.remove("model-id-col-resizing");
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", stopResize);
    if (modelIdColWidth !== null) {
      persist(modelIdColWidth);
    }
  };

  /**
   * @param {MouseEvent} event
   */
  const onMouseMove = (event) => {
    const delta = event.clientX - startX;
    pendingWidth = clamp(startWidth + delta);
    if (rafId !== null) {
      return;
    }
    rafId = requestAnimationFrame(flushPendingWidth);
  };

  /**
   * @param {number} clientX
   */
  const startResize = (clientX) => {
    const measuredWidth = modelIdColHeader.getBoundingClientRect().width;
    startX = clientX;
    startWidth = modelIdColWidth ?? measuredWidth;
    pendingWidth = null;
    document.body.classList.add("model-id-col-resizing");
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", stopResize);
  };

  modelIdColResizer.addEventListener("mousedown", (event) => {
    event.preventDefault();
    startResize(event.clientX);
  });

  modelIdColResizer.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const measuredWidth = modelIdColHeader.getBoundingClientRect().width;
    const currentWidth = modelIdColWidth ?? measuredWidth;
    const delta = event.key === "ArrowLeft" ? -8 : 8;
    const nextWidth = clamp(currentWidth + delta);
    apply(nextWidth);
    persist(nextWidth);
  });

  return {
    apply,
    getWidth: () => modelIdColWidth,
  };
}
