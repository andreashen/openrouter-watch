import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { isBatchModel, matchesBatchFilter } from "./batchFilter.js";
import {
  composeVisibleModels,
  matchesPointerFilter,
  matchesRemovedFilter,
  rowPassesFilters,
} from "./modelVisibility.js";

function toSearchText(model) {
  return `${model.model_id} ${model.vendor_name ?? ""} ${model.name ?? ""}`.toLowerCase();
}

function identityDisplay(model) {
  return model;
}

const normal = {
  model_id: "openai/gpt-4o",
  vendor_name: "OpenAI",
  name: "GPT-4o",
  supports_reasoning: false,
  supports_tools: true,
  supports_vision: true,
  officially_removed: false,
  is_pointer: false,
};
const batch = {
  ...normal,
  model_id: "openai/gpt-4o:batch",
  name: "GPT-4o Batch",
};
const batchUpper = {
  ...normal,
  model_id: "openai/gpt-4o:BATCH",
};
const removed = {
  ...normal,
  model_id: "openai/old",
  officially_removed: true,
};
const pointer = {
  ...normal,
  model_id: "openai/gpt-4o-latest",
  is_pointer: true,
};

describe("production modelVisibility uses shared batch predicate", () => {
  it("shares isBatchModel / matchesBatchFilter with batchFilter.js", () => {
    assert.equal(isBatchModel(batch), true);
    assert.equal(isBatchModel(batchUpper), true);
    assert.equal(isBatchModel({ model_id: "foo/batch-helper" }), false);
    assert.equal(matchesBatchFilter(batch, "hide"), false);
    assert.equal(matchesBatchFilter(batch, "show"), true);
    assert.equal(matchesBatchFilter(batch, "only"), true);
    assert.equal(matchesBatchFilter(normal, "only"), false);
  });

  it("hide/show/only truth table for rowPassesFilters", () => {
    const base = {
      pinSet: new Set(),
      search: "",
      toSearchText,
      removedMode: "show",
      pointerMode: "show",
      selectedVendors: [],
    };
    assert.equal(
      rowPassesFilters({ ...base, model: normal, display: normal, batchMode: "hide" }),
      true,
    );
    assert.equal(
      rowPassesFilters({ ...base, model: batch, display: batch, batchMode: "hide" }),
      false,
    );
    assert.equal(
      rowPassesFilters({ ...base, model: batchUpper, display: batchUpper, batchMode: "hide" }),
      false,
    );
    assert.equal(
      rowPassesFilters({ ...base, model: batch, display: batch, batchMode: "show" }),
      true,
    );
    assert.equal(
      rowPassesFilters({ ...base, model: normal, display: normal, batchMode: "only" }),
      false,
    );
    assert.equal(
      rowPassesFilters({ ...base, model: batch, display: batch, batchMode: "only" }),
      true,
    );
  });

  it("rejects suffix false positives", () => {
    const base = {
      pinSet: new Set(),
      search: "",
      toSearchText,
      removedMode: "show",
      pointerMode: "show",
      batchMode: "only",
      selectedVendors: [],
    };
    for (const id of ["foo/batch-helper", "vendor/batch:preview", "foo:batch:preview"]) {
      const model = { ...normal, model_id: id };
      assert.equal(rowPassesFilters({ ...base, model, display: model }), false, id);
    }
  });

  it("ANDs batch with removed/pointer/search/vendor", () => {
    const base = {
      pinSet: new Set(),
      search: "",
      toSearchText,
      removedMode: "hide",
      pointerMode: "hide",
      batchMode: "show",
      selectedVendors: ["OpenAI"],
    };
    assert.equal(
      rowPassesFilters({ ...base, model: removed, display: removed }),
      false,
      "removed hidden",
    );
    assert.equal(
      rowPassesFilters({ ...base, model: pointer, display: pointer }),
      false,
      "pointer hidden",
    );
    assert.equal(
      rowPassesFilters({
        ...base,
        model: batch,
        display: batch,
        search: "claude",
      }),
      false,
      "search miss",
    );
    assert.equal(
      rowPassesFilters({
        ...base,
        model: { ...batch, vendor_name: "Anthropic" },
        display: { ...batch, vendor_name: "Anthropic" },
      }),
      false,
      "vendor miss",
    );
    assert.equal(
      rowPassesFilters({ ...base, model: batch, display: batch, batchMode: "show" }),
      true,
    );
  });

  it("Pin exemption: pinned batch stays visible under hide and leads composeVisibleModels", () => {
    const models = [normal, batch, removed];
    const result = composeVisibleModels({
      models,
      pinnedIds: [batch.model_id],
      resolveDisplayModel: identityDisplay,
      toSearchText,
      filters: {
        search: "",
        removedMode: "hide",
        pointerMode: "hide",
        batchMode: "hide",
        selectedVendors: [],
      },
    });
    assert.equal(result.pinnedCount, 1);
    assert.equal(result.visible[0].model_id, batch.model_id);
    assert.ok(result.visible.every((m) => m.model_id !== removed.model_id));
    // Non-pinned batch still filtered out under hide.
    assert.equal(
      result.visible.filter((m) => m.model_id.endsWith(":batch")).length,
      1,
    );
  });

  it("matchesRemovedFilter / matchesPointerFilter keep prior semantics", () => {
    assert.equal(matchesRemovedFilter(removed, "hide"), false);
    assert.equal(matchesRemovedFilter(removed, "only"), true);
    assert.equal(matchesPointerFilter(pointer, "hide"), false);
    assert.equal(matchesPointerFilter(normal, "only"), false);
    assert.equal(matchesPointerFilter(pointer, "show"), true);
  });
});
