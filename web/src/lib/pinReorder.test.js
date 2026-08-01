import assert from "node:assert/strict";
import test from "node:test";
import { reorderPinnedIds } from "./pinReorder.js";

test("downward: drop A on B top-line inserts A before B (not after)", () => {
  // Andriy SIT bug: visual top insert line on B must keep A above B.
  const result = reorderPinnedIds(["A", "B", "C"], "A", "B");
  assert.deepEqual(result, ["A", "B", "C"]);
  assert.ok(result.indexOf("A") < result.indexOf("B"));
});

test("downward: drop A on C top-line places A immediately before C", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "A", "C");
  assert.deepEqual(result, ["B", "A", "C"]);
});

test("upward: drop C on B top-line inserts C before B (symmetric)", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "C", "B");
  assert.deepEqual(result, ["A", "C", "B"]);
  assert.ok(result.indexOf("C") < result.indexOf("B"));
});

test("upward: drop C on A top-line places C first", () => {
  const result = reorderPinnedIds(["A", "B", "C"], "C", "A");
  assert.deepEqual(result, ["C", "A", "B"]);
});

test("no-op when fromId === toId or missing ids", () => {
  assert.deepEqual(reorderPinnedIds(["A", "B"], "A", "A"), ["A", "B"]);
  assert.deepEqual(reorderPinnedIds(["A", "B"], "Z", "B"), ["A", "B"]);
});
