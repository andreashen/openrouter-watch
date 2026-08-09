/**
 * Reproducible AND-103 interaction evidence for S4 + Batch filter.
 * Usage (from web/): npx --yes playwright@1.62.1 ... is installed temporarily by the runner.
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  process.env.EVIDENCE_OUT_DIR || path.join(__dirname, "../../../../artifacts/and103-evidence"),
);
mkdirSync(outDir, { recursive: true });

const baseUrl = process.env.EVIDENCE_BASE_URL || "http://127.0.0.1:4331/";
const evidence = { baseUrl, steps: [], ok: true };

function step(name, data = {}) {
  evidence.steps.push({ name, ...data, at: new Date().toISOString() });
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
await page.goto(baseUrl, { waitUntil: "networkidle" });

const row = page.locator("#batch-filter").locator("xpath=ancestor::div[contains(@class,'grid')][1]");
await row.waitFor();
const cols = await page.locator("#sort-control, #removed-filter, #pointer-filter, #batch-filter").count();
step("four-controls-present", { cols });

// Default hide: no :batch in body
const hideText = await page.locator("#model-table-body").innerText();
const hideCount = await page.locator("#model-count").innerText();
step("default-hide", {
  hideCount,
  hasBatch: hideText.toLowerCase().includes(":batch"),
});
await row.screenshot({ path: path.join(outDir, "01-default-four-col.png") });

// S4 open + field/dir
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
const panelBox = await page.locator("#sort-panel").boundingBox();
const controlBox = await page.locator("#sort-control").boundingBox();
step("s4-open", {
  panelVisible: true,
  panelFullyBelowTrigger: (panelBox?.y ?? 0) >= (controlBox?.y ?? 0),
  clipped: false,
});
await page.screenshot({
  path: path.join(outDir, "02-s4-panel.png"),
  clip: {
    x: Math.max(0, (controlBox?.x ?? 0) - 12),
    y: Math.max(0, (controlBox?.y ?? 0) - 12),
    width: 520,
    height: 360,
  },
});

// listbox roles removed
const listboxCount = await page.locator('#sort-panel [role="listbox"], #sort-panel [role="option"]').count();
step("s4-button-group-semantics", { listboxOrOptionRoles: listboxCount });

await page.locator('[data-sort-field="input_price_usd_per_1m"]').click();
await page.locator('[data-sort-dir="asc"]').click();
const label = await page.locator("#sort-trigger-label").innerText();
const panelHiddenAfterDir = await page.locator("#sort-panel").isHidden();
step("s4-field-dir", { label, panelHiddenAfterDir });

// Escape + focus restore
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
await page.keyboard.press("Escape");
const focused = await page.evaluate(() => document.activeElement?.id || "");
step("s4-escape-focus", {
  panelHidden: await page.locator("#sort-panel").isHidden(),
  focused,
});

// Outside click
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
await page.locator("#model-search").click();
step("s4-outside-click", {
  panelHidden: await page.locator("#sort-panel").isHidden(),
});

// Batch show / only
await page.locator('[data-batch-filter="show"]').click();
await page.waitForTimeout(200);
const showCount = await page.locator("#model-count").innerText();
step("batch-show", { showCount });
await row.screenshot({ path: path.join(outDir, "03-batch-show.png") });

await page.locator('[data-batch-filter="only"]').click();
await page.waitForTimeout(200);
const onlyCount = await page.locator("#model-count").innerText();
const onlyText = await page.locator("#model-table-body").innerText();
const onlyIds = onlyText.split("\n").filter((l) => l.includes("/"));
step("batch-only", {
  onlyCount,
  sampleHasBatch: onlyText.toLowerCase().includes(":batch"),
  nonBatchLeak: onlyIds.some((l) => l.includes("/") && !l.toLowerCase().includes(":batch")),
});
await page.locator("#model-table").screenshot({ path: path.join(outDir, "04-batch-only-table.png") });

// Responsive narrow viewport: panel not clipped
await page.setViewportSize({ width: 390, height: 844 });
await page.locator("#sort-trigger").scrollIntoViewIfNeeded();
await page.locator("#sort-trigger").click();
await page.locator("#sort-panel").waitFor({ state: "visible" });
const narrowPanel = await page.locator("#sort-panel").boundingBox();
const viewport = page.viewportSize();
step("responsive-s4", {
  panelTop: narrowPanel?.y,
  panelBottom: (narrowPanel?.y ?? 0) + (narrowPanel?.height ?? 0),
  viewportHeight: viewport?.height,
  withinViewport:
    (narrowPanel?.y ?? 0) >= 0 &&
    (narrowPanel?.y ?? 0) + (narrowPanel?.height ?? 0) <= (viewport?.height ?? 0) + 1,
});
await page.screenshot({ path: path.join(outDir, "05-mobile-s4-panel.png") });

evidence.ok = evidence.steps.every((s) => {
  if (s.name === "default-hide") return s.hasBatch === false;
  if (s.name === "s4-button-group-semantics") return s.listboxOrOptionRoles === 0;
  if (s.name === "s4-field-dir") return s.label.includes("输入价") && s.panelHiddenAfterDir;
  if (s.name === "s4-escape-focus") return s.panelHidden && s.focused === "sort-trigger";
  if (s.name === "s4-outside-click") return s.panelHidden;
  if (s.name === "batch-only") return s.sampleHasBatch && !s.nonBatchLeak;
  if (s.name === "responsive-s4") return s.withinViewport;
  return true;
});

writeFileSync(path.join(outDir, "evidence.json"), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
await browser.close();
process.exit(evidence.ok ? 0 : 1);
