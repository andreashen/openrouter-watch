/**
 * Clean-checkout runner for AND-103 evidence:
 * build → install Chromium (pinned Playwright) → preview → boot safety → interaction evidence.
 *
 * Pinned runner: package.json devDependency `playwright@1.62.1` (exact).
 */
import { spawn } from "node:child_process";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const astroBin = path.join(root, "node_modules", ".bin", "astro");

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      cwd: root,
      stdio: "inherit",
      shell: false,
      ...opts,
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${cmd} ${args.join(" ")} exited ${code}`));
    });
  });
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      server.close((err) => (err ? reject(err) : resolve(port)));
    });
    server.on("error", reject);
  });
}

async function waitForHttp(url, { timeoutMs = 60000 } = {}) {
  const start = Date.now();
  let lastErr;
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return;
      lastErr = new Error(`HTTP ${res.status}`);
    } catch (err) {
      lastErr = err;
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`preview not reachable at ${url}: ${lastErr}`);
}

await run("npm", ["run", "build"]);
await run("npx", ["playwright", "install", "chromium"]);

const port = await freePort();
const baseUrl = `http://127.0.0.1:${port}/`;
const preview = spawn(
  process.execPath,
  [astroBin, "preview", "--host", "127.0.0.1", "--port", String(port)],
  { cwd: root, stdio: ["ignore", "pipe", "pipe"], shell: false },
);

let previewReady = false;
const ready = new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("preview startup timeout")), 60000);
  const onData = (buf) => {
    const text = buf.toString();
    process.stdout.write(text);
    if (/localhost|127\.0\.0\.1|Local/.test(text)) {
      previewReady = true;
      clearTimeout(timer);
      resolve();
    }
  };
  preview.stdout.on("data", onData);
  preview.stderr.on("data", onData);
  preview.on("exit", (code) => {
    if (!previewReady) {
      clearTimeout(timer);
      reject(new Error(`preview exited early: ${code}`));
    }
  });
});

try {
  await ready;
  await waitForHttp(baseUrl);
  await run("node", ["scripts/check-boot-json-safety.mjs"]);
  await run("node", ["scripts/and103-dom-security.mjs"]);
  await run("node", ["scripts/and103-interaction-evidence.mjs"], {
    env: {
      ...process.env,
      EVIDENCE_BASE_URL: baseUrl,
    },
  });
} finally {
  preview.kill("SIGTERM");
}
