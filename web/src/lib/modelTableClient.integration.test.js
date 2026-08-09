/**
 * Executable production-client integration coverage (happy-dom).
 * Exercises initModelTable against a real DOM fixture — not source regex mirrors.
 */
import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, it } from "node:test";
import { Window } from "happy-dom";

import { initModelTable } from "./modelTableClient.js";

/** @type {Window|null} */
let windowRef = null;

function mountFixture() {
  const window = new Window({ url: "https://example.test/" });
  const { document } = window;
  document.body.innerHTML = `
    <div id="sort-control">
      <button type="button" id="sort-trigger" aria-expanded="false">
        <span id="sort-trigger-label">不排序</span>
      </button>
      <div id="sort-panel" hidden>
        <button type="button" data-sort-field="" aria-pressed="true">不排序</button>
        <button type="button" data-sort-field="input_price_usd_per_1m" aria-pressed="false">输入价</button>
        <button type="button" data-sort-dir="desc" aria-pressed="true">降序</button>
        <button type="button" data-sort-dir="asc" aria-pressed="false">升序</button>
      </div>
    </div>
    <div id="removed-filter" role="radiogroup" aria-label="已下架">
      <button type="button" role="radio" data-removed-filter="hide" aria-checked="true">不显示</button>
      <button type="button" role="radio" data-removed-filter="show" aria-checked="false">显示</button>
      <button type="button" role="radio" data-removed-filter="only" aria-checked="false">只显示</button>
    </div>
    <div id="pointer-filter" role="radiogroup" aria-label="latest">
      <button type="button" role="radio" data-pointer-filter="hide" aria-checked="true">不显示</button>
      <button type="button" role="radio" data-pointer-filter="show" aria-checked="false">显示</button>
      <button type="button" role="radio" data-pointer-filter="only" aria-checked="false">只显示</button>
    </div>
    <div id="batch-filter" role="radiogroup" aria-label="Batch">
      <button type="button" role="radio" data-batch-filter="hide" aria-checked="true">不显示</button>
      <button type="button" role="radio" data-batch-filter="show" aria-checked="false">显示</button>
      <button type="button" role="radio" data-batch-filter="only" aria-checked="false">只显示</button>
    </div>
    <input id="model-search" type="search" />
    <input id="cap-reasoning" type="checkbox" />
    <input id="cap-tools" type="checkbox" />
    <input id="cap-vision" type="checkbox" />
    <button type="button" id="vendor-filter-clear">清除</button>
    <button type="button" data-vendor-filter="OpenAI" aria-pressed="false">OpenAI</button>
    <p id="model-count"></p>
    <button type="button" id="pin-clear-all" disabled>清除 Pin</button>
    <table id="model-table">
      <thead><tr><th id="model-id-col-header"><span id="model-id-col-resizer"></span></th></tr></thead>
      <tbody id="model-table-body"></tbody>
    </table>
  `;

  // @ts-expect-error happy-dom window assignment for browser globals used by client
  globalThis.window = window;
  globalThis.document = document;
  globalThis.HTMLElement = window.HTMLElement;
  globalThis.HTMLButtonElement = window.HTMLButtonElement;
  globalThis.HTMLInputElement = window.HTMLInputElement;
  globalThis.DocumentFragment = window.DocumentFragment;
  globalThis.requestAnimationFrame = (cb) => window.setTimeout(() => cb(0), 0);
  globalThis.cancelAnimationFrame = (id) => window.clearTimeout(id);

  windowRef = window;
  return { window, document };
}

function fixtureModels() {
  return [
    {
      model_id: "acme/alpha",
      name: "Alpha",
      vendor_name: "OpenAI",
      officially_removed: false,
      is_pointer: false,
      input_price_usd_per_1m: 2,
      fetched_at: "2026-01-01T00:00:00Z",
    },
    {
      model_id: "acme/alpha:batch",
      name: "Alpha Batch",
      vendor_name: "OpenAI",
      officially_removed: false,
      is_pointer: false,
      input_price_usd_per_1m: 1,
      fetched_at: "2026-01-01T00:00:00Z",
    },
    {
      model_id: "acme/gone",
      name: "Gone",
      vendor_name: "Other",
      officially_removed: true,
      is_pointer: false,
      input_price_usd_per_1m: 3,
      fetched_at: "2026-01-01T00:00:00Z",
    },
    {
      model_id: "acme/beta-latest",
      name: "Beta Latest",
      vendor_name: "Other",
      officially_removed: false,
      is_pointer: true,
      pointer_target_id: "acme/alpha",
      input_price_usd_per_1m: 4,
      fetched_at: "2026-01-01T00:00:00Z",
    },
  ];
}

/**
 * @returns {string[]}
 */
function visibleIds() {
  return [...document.querySelectorAll("#model-table-body tr")]
    .map((row) => row.getAttribute("data-model-id") || "")
    .filter(Boolean);
}

/**
 * @returns {number}
 */
function visibleCount() {
  const text = document.querySelector("#model-count")?.textContent || "";
  const match = text.match(/显示\s*(\d+)/);
  return match ? Number(match[1]) : -1;
}

beforeEach(() => {
  mountFixture();
});

afterEach(() => {
  windowRef?.close();
  windowRef = null;
});

describe("modelTableClient integration", () => {
  it("defaults to hide batch/removed/pointer and uses radio semantics", () => {
    initModelTable({ models: fixtureModels(), vendorMatchByChip: { OpenAI: ["OpenAI"] } });

    assert.deepEqual(visibleIds(), ["acme/alpha"]);
    assert.equal(visibleCount(), 1);

    const hide = document.querySelector('[data-batch-filter="hide"]');
    const show = document.querySelector('[data-batch-filter="show"]');
    assert.equal(hide?.getAttribute("role"), "radio");
    assert.equal(hide?.getAttribute("aria-checked"), "true");
    assert.equal(show?.getAttribute("aria-checked"), "false");
    assert.equal(hide?.hasAttribute("aria-pressed"), false);
  });

  it("applies Batch show/only through the production client path", () => {
    initModelTable({ models: fixtureModels() });

    document.querySelector('[data-batch-filter="show"]')?.dispatchEvent(new window.Event("click"));
    assert.deepEqual(visibleIds().sort(), ["acme/alpha", "acme/alpha:batch"]);
    assert.equal(
      document.querySelector('[data-batch-filter="show"]')?.getAttribute("aria-checked"),
      "true",
    );

    document.querySelector('[data-batch-filter="only"]')?.dispatchEvent(new window.Event("click"));
    assert.deepEqual(visibleIds(), ["acme/alpha:batch"]);
  });

  it("runs S4 field/direction selection via production sort panel wiring", () => {
    initModelTable({ models: fixtureModels() });
    /** @type {HTMLElement} */ (document.querySelector('[data-batch-filter="show"]')).click();

    /** @type {HTMLElement} */ (document.querySelector("#sort-trigger")).click();
    assert.equal(document.querySelector("#sort-panel")?.hidden, false);

    /** @type {HTMLElement} */ (
      document.querySelector('[data-sort-field="input_price_usd_per_1m"]')
    ).click();
    assert.match(document.querySelector("#sort-trigger-label")?.textContent || "", /输入价/);

    /** @type {HTMLElement} */ (document.querySelector('[data-sort-dir="asc"]')).click();
    assert.match(document.querySelector("#sort-trigger-label")?.textContent || "", /↑/);
    assert.equal(document.querySelector("#sort-panel")?.hidden, true);
    assert.deepEqual(visibleIds(), ["acme/alpha:batch", "acme/alpha"]);
  });

  it("keeps pinned rows visible across Batch hide and clears via pin control", () => {
    initModelTable({ models: fixtureModels() });
    /** @type {HTMLElement} */ (document.querySelector('[data-batch-filter="only"]')).click();
    assert.deepEqual(visibleIds(), ["acme/alpha:batch"]);

    const pinBtn = /** @type {HTMLElement} */ (
      document.querySelector('.pin-toggle[aria-label^="Pin "]')
    );
    assert.ok(pinBtn);
    pinBtn.click();
    assert.equal(visibleCount(), 1);

    /** @type {HTMLElement} */ (document.querySelector('[data-batch-filter="hide"]')).click();
    // Pin keeps batch row visible even when Batch=hide
    assert.ok(visibleIds().includes("acme/alpha:batch"));
    assert.ok(visibleIds().includes("acme/alpha"));

    const clear = /** @type {HTMLButtonElement} */ (document.querySelector("#pin-clear-all"));
    assert.equal(clear.disabled, false);
    clear.click();
    assert.deepEqual(visibleIds(), ["acme/alpha"]);
  });

  it("combines vendor chip filter with Batch show", () => {
    initModelTable({
      models: fixtureModels(),
      vendorMatchByChip: { OpenAI: ["OpenAI"] },
    });
    /** @type {HTMLElement} */ (document.querySelector('[data-batch-filter="show"]')).click();
    /** @type {HTMLElement} */ (document.querySelector('[data-vendor-filter="OpenAI"]')).click();
    assert.deepEqual(visibleIds().sort(), ["acme/alpha", "acme/alpha:batch"]);
    assert.equal(
      document.querySelector('[data-vendor-filter="OpenAI"]')?.getAttribute("aria-pressed"),
      "true",
    );
  });

  it("renders hostile model fields via textContent/setAttribute without XSS sinks", () => {
    const evilId = `acme/x"><img src=x onerror=window.__xss=1>`;
    initModelTable({
      models: [
        {
          model_id: evilId,
          name: `<img src=x>`,
          vendor_name: "OpenAI",
          openrouter_model_url: "javascript:alert(1)",
          pointer_target_id: `tgt"><img src=x>`,
          is_pointer: true,
          knowledge_cutoff: `2024"><img src=x>`,
          released_at: `</script><script>alert(1)</script>`,
          fetched_at: `bad"><img src=x>`,
          officially_removed: false,
          input_price_usd_per_1m: 1,
        },
      ],
    });
    /** @type {HTMLElement} */ (document.querySelector('[data-pointer-filter="show"]')).click();

    const body = document.querySelector("#model-table-body");
    assert.ok(body);
    assert.equal(body.querySelectorAll("img").length, 0);
    assert.equal(body.querySelectorAll("script").length, 0);
    assert.equal(Boolean(window.__xss), false);
    const href = body.querySelector("a")?.getAttribute("href") || "";
    assert.equal(/^\s*javascript:/i.test(href), false);
    assert.match(href, /^https:\/\/openrouter\.ai\//);
    assert.equal(body.querySelector(".model-id-text")?.textContent, evilId);
    assert.equal(body.querySelectorAll("[onerror]").length, 0);
  });
});
