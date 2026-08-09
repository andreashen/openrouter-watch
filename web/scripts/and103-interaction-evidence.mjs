/**
 * Reproducible AND-103 interaction evidence for S4 + Batch filter.
 *
 * Requires pinned Playwright from package.json (devDependency).
 * Prefer: npm run test:and103-evidence  (builds, serves preview, runs checks)
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { rowPassesFilters } from "../src/lib/modelVisibility.js";
import { getNumericValue, resolveDisplayModel, toSearchText } from "../src/lib/modelTableDisplay.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  process.env.EVIDENCE_OUT_DIR || path.join(__dirname, "../../../artifacts/and103-evidence"),
);
mkdirSync(outDir, { recursive: true });

const baseUrl = process.env.EVIDENCE_BASE_URL || "http://127.0.0.1:4331/";
const evidence = { baseUrl, steps: [], failures: [], ok: true };

function step(name, data = {}) {
  evidence.steps.push({ name, ...data, at: new Date().toISOString() });
}

function fail(name, reason, data = {}) {
  evidence.failures.push({ name, reason, ...data });
  evidence.ok = false;
}

function nearlyEqual(a, b, tolerancePx = 2) {
  return Math.abs(a - b) <= tolerancePx;
}

/**
 * @param {string} text
 * @returns {number|null}
 */
function parseVisibleCount(text) {
  const match = text.match(/显示\s*(\d+)/);
  return match ? Number(match[1]) : null;
}

/**
 * @param {import("playwright").Page} page
 * @param {{ batchMode: "hide"|"show"|"only" }} opts
 * @returns {Promise<number>}
 */
async function expectedVisibleCount(page, { batchMode }) {
  const boot = await page.evaluate(() => {
    const raw = document.getElementById("model-table-boot")?.textContent || "{}";
    return JSON.parse(raw);
  });
  const models = Array.isArray(boot.models) ? boot.models : [];
  const modelsById = new Map(models.map((m) => [m.model_id, m]));
  const pinSet = new Set();
  return models.filter((model) =>
    rowPassesFilters({
      model,
      display: resolveDisplayModel(model, modelsById),
      pinSet,
      search: "",
      needsReasoning: false,
      needsTools: false,
      needsVision: false,
      removedMode: "hide",
      pointerMode: "hide",
      batchMode,
      selectedVendors: [],
      vendorMatchByChip: boot.vendorMatchByChip || {},
      toSearchText,
      numericRanges: {},
      getNumericValue,
      numericRangeKeys: [],
    }),
  ).length;
}

/**
 * @param {import("playwright").Page} page
 * @param {string} previousCountText
 */
async function waitForCountChange(page, previousCountText) {
  await page.waitForFunction(
    (prev) => {
      const text = document.querySelector("#model-count")?.textContent || "";
      return Boolean(text) && text !== prev && /显示\s+\d+/.test(text);
    },
    previousCountText,
    { timeout: 10000 },
  );
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
await page.goto(baseUrl, { waitUntil: "networkidle" });

const row = page.locator("#batch-filter").locator("xpath=ancestor::div[contains(@class,'grid')][1]");
await row.waitFor();

// --- Four equal columns (actual geometry) ---
const colBoxes = await page.evaluate(() => {
  const ids = ["sort-control", "removed-filter", "pointer-filter", "batch-filter"];
  return ids.map((id) => {
    const el = document.getElementById(id);
    const cell = id === "sort-control" ? el : el?.parentElement;
    const rect = (cell || el)?.getBoundingClientRect();
    return rect
      ? { id, x: rect.x, y: rect.y, width: rect.width, height: rect.height }
      : { id, missing: true };
  });
});
const present = colBoxes.filter((b) => !b.missing);
const widths = present.map((b) => b.width);
const widthOk =
  present.length === 4 &&
  widths.every((w) => nearlyEqual(w, widths[0], 2));
step("four-controls-geometry", { present: present.length, widths, widthOk });
if (!widthOk) {
  fail("four-controls-geometry", "expected 4 equal-width columns", { widths });
}

// Default hide: no :batch in body
const hideText = await page.locator("#model-table-body").innerText();
const hideCount = await page.locator("#model-count").innerText();
const hideOk = hideText.toLowerCase().includes(":batch") === false;
step("default-hide", { hideCount, hasBatch: !hideOk, hideOk });
if (!hideOk) fail("default-hide", "batch rows visible under default hide");
await row.screenshot({ path: path.join(outDir, "01-default-four-col.png") });

// S4 open + full panel bounds vs viewport
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
const openGeom = await page.evaluate(() => {
  const panel = document.getElementById("sort-panel");
  const trigger = document.getElementById("sort-trigger");
  const pr = panel.getBoundingClientRect();
  const tr = trigger.getBoundingClientRect();
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  return {
    panel: { x: pr.x, y: pr.y, right: pr.right, bottom: pr.bottom, width: pr.width, height: pr.height },
    trigger: { x: tr.x, y: tr.y, bottom: tr.bottom },
    viewport: { width: vw, height: vh },
    fullyInViewport: pr.top >= 0 && pr.left >= 0 && pr.right <= vw + 1 && pr.bottom <= vh + 1,
    belowTrigger: pr.top >= tr.bottom - 1,
  };
});
step("s4-open-bounds", openGeom);
if (!openGeom.fullyInViewport || !openGeom.belowTrigger) {
  fail("s4-open-bounds", "S4 panel not fully visible / clipped", openGeom);
}
await page.screenshot({
  path: path.join(outDir, "02-s4-panel.png"),
  clip: {
    x: Math.max(0, openGeom.trigger.x - 12),
    y: Math.max(0, openGeom.trigger.y - 12),
    width: Math.min(520, openGeom.viewport.width),
    height: Math.min(360, openGeom.viewport.height),
  },
});

const listboxCount = await page.locator('#sort-panel [role="listbox"], #sort-panel [role="option"]').count();
step("s4-button-group-semantics", { listboxOrOptionRoles: listboxCount });
if (listboxCount !== 0) {
  fail("s4-button-group-semantics", "listbox/option roles still present");
}

await page.locator('[data-sort-field="input_price_usd_per_1m"]').click();
await page.locator('[data-sort-dir="asc"]').click();
const label = await page.locator("#sort-trigger-label").innerText();
const panelHiddenAfterDir = await page.locator("#sort-panel").isHidden();
step("s4-field-dir", { label, panelHiddenAfterDir });
if (!(label.includes("输入价") && label.includes("↑") && panelHiddenAfterDir)) {
  fail("s4-field-dir", "field/direction transition failed", { label, panelHiddenAfterDir });
}

// Escape + focus restore
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
await page.keyboard.press("Escape");
const focused = await page.evaluate(() => document.activeElement?.id || "");
const escHidden = await page.locator("#sort-panel").isHidden();
step("s4-escape-focus", { panelHidden: escHidden, focused });
if (!(escHidden && focused === "sort-trigger")) {
  fail("s4-escape-focus", "Escape did not close panel and restore focus", { escHidden, focused });
}

// Outside click
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
await page.locator("#model-search").click();
const outsideHidden = await page.locator("#sort-panel").isHidden();
step("s4-outside-click", { panelHidden: outsideHidden });
if (!outsideHidden) fail("s4-outside-click", "outside click did not close panel");

// Batch show / only — wait on count text, assert against production filter expected values
const expectedShow = await expectedVisibleCount(page, { batchMode: "show" });
const expectedOnly = await expectedVisibleCount(page, { batchMode: "only" });
const beforeShow = await page.locator("#model-count").innerText();
await page.locator('[data-batch-filter="show"]').click();
await waitForCountChange(page, beforeShow);
const showCountText = await page.locator("#model-count").innerText();
const showCount = parseVisibleCount(showCountText);
const showOk = showCount === expectedShow;
step("batch-show", { showCountText, showCount, expectedShow, showOk });
if (!showOk) {
  fail("batch-show", "visible count did not match expected Batch=show", {
    showCount,
    expectedShow,
  });
}
await row.screenshot({ path: path.join(outDir, "03-batch-show.png") });

const beforeOnly = showCountText;
await page.locator('[data-batch-filter="only"]').click();
await waitForCountChange(page, beforeOnly);
const onlyCountText = await page.locator("#model-count").innerText();
const onlyCount = parseVisibleCount(onlyCountText);
const onlyText = await page.locator("#model-table-body").innerText();
const sampleHasBatch = onlyText.toLowerCase().includes(":batch");
const nonBatchLeak = onlyText
  .split("\n")
  .filter((l) => l.includes("/"))
  .some((l) => l.includes("/") && !l.toLowerCase().includes(":batch"));
const onlyOk = onlyCount === expectedOnly && sampleHasBatch && !nonBatchLeak;
step("batch-only", { onlyCountText, onlyCount, expectedOnly, sampleHasBatch, nonBatchLeak, onlyOk });
if (!onlyOk) {
  fail("batch-only", "Batch=only count/content failed", {
    onlyCount,
    expectedOnly,
    sampleHasBatch,
    nonBatchLeak,
  });
}
await page.locator("#model-table").screenshot({ path: path.join(outDir, "04-batch-only-table.png") });

// Responsive narrow viewport: panel in bounds + no page horizontal overflow
await page.setViewportSize({ width: 390, height: 844 });
await page.locator("#sort-trigger").scrollIntoViewIfNeeded();
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
const narrow = await page.evaluate(() => {
  const panel = document.getElementById("sort-panel");
  const pr = panel.getBoundingClientRect();
  const doc = document.documentElement;
  return {
    panel: { top: pr.top, left: pr.left, right: pr.right, bottom: pr.bottom },
    viewport: { width: window.innerWidth, height: window.innerHeight },
    scrollWidth: doc.scrollWidth,
    clientWidth: doc.clientWidth,
    fullyInViewport: pr.top >= 0 && pr.left >= 0 && pr.right <= window.innerWidth + 1 && pr.bottom <= window.innerHeight + 1,
    noHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 1,
  };
});
step("responsive-s4", narrow);
if (!narrow.fullyInViewport || !narrow.noHorizontalOverflow) {
  fail("responsive-s4", "narrow viewport panel clipped or page overflows horizontally", narrow);
}
await page.screenshot({ path: path.join(outDir, "05-mobile-s4-panel.png") });

writeFileSync(path.join(outDir, "evidence.json"), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
await browser.close();
process.exit(evidence.ok ? 0 : 1);
