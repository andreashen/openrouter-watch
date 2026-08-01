import assert from "node:assert/strict";
import test from "node:test";
import { reorderPinnedIds } from "./pinReorder.js";

test("downward: drop A on B top-line inserts A before B (not after)", () => {
  // Andriy SIT bug: visual top insert line on B must keep A above B.
  const result = reorderPinnedIds(["A", "B", "C"], "A", "B", "before");
  assert.deepEqual(result, ["A", "B", "C"]);
  assert.ok(result.indexOf("A") < result.indexOf("B"));
});

test("downward: drop A on C top-line places A immediately before C", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "A", "C", "before");
  assert.deepEqual(result, ["B", "A", "C"]);
});

test("upward: drop C on B top-line inserts C before B (symmetric)", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "C", "B", "before");
  assert.deepEqual(result, ["A", "C", "B"]);
  assert.ok(result.indexOf("C") < result.indexOf("B"));
});

test("upward: drop C on A top-line places C first", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "C", "A", "before");
  assert.deepEqual(result, ["C", "A", "B"]);
});

test("end: drop A on last row bottom-line places A after last (group end)", () => {
  // Residual bug: any pinned model must be able to land below the last pin.
  const result = reorderPinnedIds(["A", "B", "C"], "A", "C", "after");
  assert.deepEqual(result, ["B", "C", "A"]);
  assert.equal(result[result.length - 1], "A");
});

test("end: drop B on last row bottom-line places B last", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "B", "C", "after");
  assert.deepEqual(result, ["A", "C", "B"]);
});

test("after mid: drop A on B bottom-line places A immediately after B", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "A", "B", "after");
  assert.deepEqual(result, ["B", "A", "C"]);
});

test("default place is before (back-compat)", () => {
  assert.deepEqual(reorderPinnedIds(["A", "B", "C"], "A", "C"), ["B", "A", "C"]);
});

test("no-op when fromId === toId or missing ids", () => {
  assert.deepEqual(reorderPinnedIds(["A", "B"], "A", "A"), ["A", "B"]);
  assert.deepEqual(reorderPinnedIds(["A", "B"], "Z", "B"), ["A", "B"]);
});
