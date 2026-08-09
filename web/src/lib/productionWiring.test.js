import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

describe("production wiring", () => {
  it("modelTableClient imports shared modelVisibility / sortPanel helpers", () => {
    const src = readFileSync(join(root, "modelTableClient.js"), "utf8");
    assert.match(src, /from\s+["']\.\/modelVisibility\.js["']/);
    assert.match(src, /rowPassesFilters/);
    assert.match(src, /from\s+["']\.\/sortPanel\.js["']/);
    assert.match(src, /formatSortTriggerLabel/);
    assert.doesNotMatch(src, /function isBatchModel/);
    assert.doesNotMatch(src, /endsWith\(":batch"\)/);
  });

  it("modelVisibility imports shared batchFilter predicate", () => {
    const src = readFileSync(join(root, "modelVisibility.js"), "utf8");
    assert.match(src, /from\s+["']\.\/batchFilter\.js["']/);
    assert.match(src, /matchesBatchFilter/);
  });
});
