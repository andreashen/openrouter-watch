import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { aaSortValue, columnVersionLabel, formatAaScoreCell } from "./aaScoreDisplay.js";

describe("AA score display stays comparable only inside the column version", () => {
  it("labels the three columns with one major.minor", () => {
    assert.equal(columnVersionLabel("Intelligence", "4.3"), "Intelligence v4.3");
    assert.equal(columnVersionLabel("Coding", "4.3"), "Coding v4.3");
  });

  it("renders a blank cell as incomparable", () => {
    assert.deepEqual(formatAaScoreCell(null, "4.3", "4.3"), {
      text: "—",
      badge: null,
      comparable: false,
      hint: "不可比",
    });
  });

  it("badges an older full-row snapshot and drops it from the sort key", () => {
    assert.deepEqual(formatAaScoreCell(51, "4.1", "4.3"), {
      text: "51",
      badge: "v4.1",
      comparable: false,
      hint: null,
    });
    assert.equal(aaSortValue(51, "4.1", "4.3"), null);
    assert.equal(aaSortValue(null, "4.3", "4.3"), null);
    assert.equal(aaSortValue(53, "4.3", "4.3"), 53);
  });
});
