/**
 * Chromium regression: initModelTable must not create XSS sinks from model fields.
 */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixtureDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "dom-security-fixture");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
};

/**
 * @param {string} urlPath
 */
function resolvePath(urlPath) {
  if (urlPath === "/" || urlPath === "/harness.html") {
    return path.join(fixtureDir, "harness.html");
  }
  if (urlPath.startsWith("/src/")) {
    return path.join(root, urlPath.slice(1));
  }
  return path.join(fixtureDir, urlPath.replace(/^\//, ""));
}

const server = createServer(async (req, res) => {
  try {
    const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
    const filePath = path.resolve(resolvePath(urlPath));
    const allowedRoots = [path.resolve(root), path.resolve(fixtureDir)];
    if (!allowedRoots.some((base) => filePath === base || filePath.startsWith(base + path.sep))) {
      res.writeHead(403);
      res.end("forbidden");
      return;
    }
    const data = await readFile(filePath);
    const ext = path.extname(filePath);
    res.writeHead(200, { "content-type": MIME[ext] || "application/octet-stream" });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end("not found");
  }
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const { port } = /** @type {import('node:net').AddressInfo} */ (server.address());
const base = `http://127.0.0.1:${port}/harness.html`;

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  page.on("pageerror", (err) => console.error("pageerror", err));
  page.on("console", (msg) => {
    if (msg.type() === "error") console.error("console", msg.text());
  });
  await page.goto(base, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__domSecurityResult != null, null, {
    timeout: 15000,
  });
  const result = await page.evaluate(() => window.__domSecurityResult);
  const failures = [];
  if (result.imgCount !== 0) failures.push(`imgCount=${result.imgCount}`);
  if (result.scriptCount !== 0) failures.push(`scriptCount=${result.scriptCount}`);
  if (result.handlerAttrs) failures.push("inline on* handler present");
  if (result.unsafeHref) failures.push("javascript: href present");
  if (Object.values(result.xssFlags).some(Boolean)) {
    failures.push(`xss flags fired: ${JSON.stringify(result.xssFlags)}`);
  }
  if (!result.modelIdText.includes('"><img')) {
    failures.push("evil model_id was not preserved as text");
  }
  if (result.rowCount < 1) failures.push("expected rendered rows");
  if (!result.hrefs.every((h) => typeof h === "string" && h.startsWith("https://openrouter.ai/"))) {
    failures.push(`unexpected hrefs: ${JSON.stringify(result.hrefs)}`);
  }

  console.log(JSON.stringify({ ok: failures.length === 0, result, failures }, null, 2));
  if (failures.length > 0) {
    process.exitCode = 1;
  }
} finally {
  await browser.close();
  server.close();
}
