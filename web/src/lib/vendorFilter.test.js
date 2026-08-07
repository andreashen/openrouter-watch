import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  VENDOR_QUICK_FILTERS,
  buildVendorMatchByChip,
  expandSelectedVendorNames,
  matchesVendorSelection,
} from "./vendorFilter.js";

describe("vendorFilter", () => {
  it("keeps xAI chip matching both xAI and SpaceXAI display names", () => {
    const matchByChip = buildVendorMatchByChip();
    assert.deepEqual(matchByChip.xAI, ["xAI", "SpaceXAI"]);
    assert.equal(matchesVendorSelection("SpaceXAI", ["xAI"], matchByChip), true);
    assert.equal(matchesVendorSelection("xAI", ["xAI"], matchByChip), true);
    assert.equal(matchesVendorSelection("OpenAI", ["xAI"], matchByChip), false);
  });

  it("defaults chips without matchNames to exact name only", () => {
    const matchByChip = buildVendorMatchByChip();
    assert.deepEqual(matchByChip.OpenAI, ["OpenAI"]);
    assert.equal(matchesVendorSelection("OpenAI", ["OpenAI"], matchByChip), true);
    assert.equal(matchesVendorSelection("openai", ["OpenAI"], matchByChip), false);
  });

  it("ORs multiple selected chips including aliases", () => {
    const allowed = expandSelectedVendorNames(["xAI", "Meta"]);
    assert.equal(allowed.has("xAI"), true);
    assert.equal(allowed.has("SpaceXAI"), true);
    assert.equal(allowed.has("Meta"), true);
    assert.equal(allowed.has("Google"), false);
  });

  it("treats empty selection as pass-through", () => {
    assert.equal(matchesVendorSelection("SpaceXAI", []), true);
    assert.equal(matchesVendorSelection(null, new Set()), true);
  });

  it("exposes the expected quick-filter chip order", () => {
    assert.deepEqual(
      VENDOR_QUICK_FILTERS.map((v) => v.name),
      [
        "Anthropic",
        "OpenAI",
        "xAI",
        "Meta",
        "Google",
        "Z.ai",
        "Xiaomi",
        "MoonshotAI",
        "Qwen",
        "MiniMax",
        "DeepSeek",
      ],
    );
  });
});
