import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  containsRawScriptBreaker,
  htmlSafeJsonStringify,
} from "./htmlSafeJson.js";

describe("htmlSafeJsonStringify", () => {
  it("escapes script-breaking payloads so raw </script> cannot appear", () => {
    const payload = {
      models: [
        {
          model_id: "evil/</script><script>alert(1)</script>:batch",
          name: "x<script>y</script>&z",
        },
      ],
      note: "a < b & c > d",
    };
    const embedded = htmlSafeJsonStringify(payload);
    assert.equal(containsRawScriptBreaker(embedded), false);
    assert.equal(embedded.includes("<"), false);
    assert.equal(embedded.includes(">"), false);
    assert.equal(embedded.includes("&"), false);
    assert.match(embedded, /\\u003c/);
    assert.match(embedded, /\\u003e/);
    assert.match(embedded, /\\u0026/);

    const parsed = JSON.parse(embedded);
    assert.equal(parsed.models[0].model_id, payload.models[0].model_id);
    assert.equal(parsed.models[0].name, payload.models[0].name);
    assert.equal(parsed.note, payload.note);
  });

  it("escapes U+2028 and U+2029 line/paragraph separators", () => {
    const payload = { text: `line\u2028break\u2029end` };
    const embedded = htmlSafeJsonStringify(payload);
    assert.equal(embedded.includes("\u2028"), false);
    assert.equal(embedded.includes("\u2029"), false);
    assert.match(embedded, /\\u2028/);
    assert.match(embedded, /\\u2029/);
    assert.equal(JSON.parse(embedded).text, payload.text);
  });
});
