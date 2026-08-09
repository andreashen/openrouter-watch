import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  applySortDirectionSelection,
  applySortFieldSelection,
  formatSortTriggerLabel,
  shouldCloseSortPanelOnOutsideClick,
  toggleSortPanelOpen,
} from "./sortPanel.js";

describe("sortPanel S4 behavior", () => {
  it("formats trigger label for none / field+direction", () => {
    assert.equal(formatSortTriggerLabel("", "desc", {}), "不排序");
    assert.equal(
      formatSortTriggerLabel("input_price_usd_per_1m", "desc", {
        input_price_usd_per_1m: "输入价",
      }),
      "输入价 · ↓",
    );
    assert.equal(
      formatSortTriggerLabel("input_price_usd_per_1m", "asc", {
        input_price_usd_per_1m: "输入价",
      }),
      "输入价 · ↑",
    );
  });

  it("field selection resets direction to desc and keeps panel open", () => {
    const next = applySortFieldSelection({ field: "", direction: "asc" }, "context_length");
    assert.deepEqual(next, { field: "context_length", direction: "desc", closePanel: false });
  });

  it("clearing field closes panel", () => {
    const next = applySortFieldSelection({ field: "context_length", direction: "asc" }, "");
    assert.equal(next.field, "");
    assert.equal(next.closePanel, true);
  });

  it("direction selection closes panel when a field is active", () => {
    const next = applySortDirectionSelection(
      { field: "context_length", direction: "desc" },
      "asc",
    );
    assert.deepEqual(next, { field: "context_length", direction: "asc", closePanel: true });
  });

  it("toggles open state and outside-click close detection", () => {
    assert.equal(toggleSortPanelOpen(false), true);
    assert.equal(toggleSortPanelOpen(true), false);

    const control = {
      contains(node) {
        return node === "inside";
      },
    };
    assert.equal(shouldCloseSortPanelOnOutsideClick("inside", control), false);
    assert.equal(shouldCloseSortPanelOnOutsideClick("outside", control), true);
    assert.equal(shouldCloseSortPanelOnOutsideClick(null, control), false);
  });
});
