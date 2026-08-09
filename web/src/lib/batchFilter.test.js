import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { isBatchModel, matchesBatchFilter } from "./batchFilter.js";

describe("isBatchModel", () => {
  it("matches model ids ending with :batch (case-insensitive)", () => {
    assert.equal(isBatchModel({ model_id: "openai/gpt-4o:batch" }), true);
    assert.equal(isBatchModel({ model_id: "anthropic/claude-sonnet-4.5:Batch" }), true);
    assert.equal(isBatchModel({ model_id: "google/gemini-2.5-pro:BATCH" }), true);
  });

  it("rejects non-batch ids and substring false positives", () => {
    assert.equal(isBatchModel({ model_id: "openai/gpt-4o" }), false);
    assert.equal(isBatchModel({ model_id: "foo/batch-helper" }), false);
    assert.equal(isBatchModel({ model_id: "vendor/batch:preview" }), false);
    assert.equal(isBatchModel({ model_id: "" }), false);
    assert.equal(isBatchModel({}), false);
    assert.equal(isBatchModel(null), false);
  });
});

describe("matchesBatchFilter", () => {
  const batch = { model_id: "openai/gpt-4o:batch" };
  const normal = { model_id: "openai/gpt-4o" };

  it("hide keeps non-batch and drops batch", () => {
    assert.equal(matchesBatchFilter(normal, "hide"), true);
    assert.equal(matchesBatchFilter(batch, "hide"), false);
  });

  it("show keeps both", () => {
    assert.equal(matchesBatchFilter(normal, "show"), true);
    assert.equal(matchesBatchFilter(batch, "show"), true);
  });

  it("only keeps batch rows", () => {
    assert.equal(matchesBatchFilter(normal, "only"), false);
    assert.equal(matchesBatchFilter(batch, "only"), true);
  });
});
