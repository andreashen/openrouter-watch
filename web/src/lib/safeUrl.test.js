import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveSafeModelUrl, sanitizeModelUrl } from "./safeUrl.js";

describe("sanitizeModelUrl", () => {
  it("allows https openrouter.ai links", () => {
    assert.equal(
      sanitizeModelUrl("https://openrouter.ai/acme/alpha"),
      "https://openrouter.ai/acme/alpha",
    );
    assert.equal(
      sanitizeModelUrl("https://www.openrouter.ai/acme/alpha"),
      "https://www.openrouter.ai/acme/alpha",
    );
  });

  it("rejects javascript: and non-allowlisted hosts/protocols", () => {
    assert.equal(sanitizeModelUrl("javascript:alert(1)"), null);
    assert.equal(sanitizeModelUrl("JAVASCRIPT:alert(1)"), null);
    assert.equal(sanitizeModelUrl("http://openrouter.ai/acme/alpha"), null);
    assert.equal(sanitizeModelUrl("https://evil.example/acme"), null);
    assert.equal(sanitizeModelUrl("https://openrouter.ai.evil.com/x"), null);
    assert.equal(sanitizeModelUrl("https://user:pass@openrouter.ai/x"), null);
  });
});

describe("resolveSafeModelUrl", () => {
  it("falls back to openrouter path for missing/invalid field URLs", () => {
    assert.equal(
      resolveSafeModelUrl({ model_id: "acme/alpha" }),
      "https://openrouter.ai/acme/alpha",
    );
    assert.equal(
      resolveSafeModelUrl({
        model_id: "acme/alpha",
        openrouter_model_url: "javascript:alert(1)",
      }),
      "https://openrouter.ai/acme/alpha",
    );
  });
});
