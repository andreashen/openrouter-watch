/**
 * Post-build check: model-table-boot payload in dist must be HTML-safe.
 * Run after `npm run build`.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { containsRawScriptBreaker } from "../src/lib/htmlSafeJson.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const distIndex = join(root, "dist/index.html");
const html = readFileSync(distIndex, "utf8");
const match = html.match(
  /<script[^>]*id="model-table-boot"[^>]*>([\s\S]*?)<\/script>/i,
);
assert.ok(match, "model-table-boot script not found in dist/index.html");
const body = match[1];
assert.equal(
  containsRawScriptBreaker(body),
  false,
  "dist boot JSON still contains a raw </script> breaker",
);
const parsed = JSON.parse(body);
assert.ok(Array.isArray(parsed.models), "boot JSON models must be an array");
console.log(
  JSON.stringify({
    ok: true,
    models: parsed.models.length,
    hasEscapedLt: body.includes("\\u003c") || !body.includes("<"),
  }),
);
