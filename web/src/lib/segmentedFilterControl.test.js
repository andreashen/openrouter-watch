import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, it } from "node:test";
import { Window } from "happy-dom";

import {
  bindExclusiveRadioButtons,
  nextRadioIndex,
  radioKeyboardAction,
  syncExclusiveRadioButtons,
} from "./segmentedFilterControl.js";

/** @type {Window|null} */
let windowRef = null;

beforeEach(() => {
  const window = new Window({ url: "https://example.test/" });
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.HTMLElement = window.HTMLElement;
  windowRef = window;
});

afterEach(() => {
  windowRef?.close();
  windowRef = null;
});

describe("radioKeyboardAction / nextRadioIndex", () => {
  it("maps arrow and home/end keys", () => {
    assert.equal(radioKeyboardAction("ArrowRight"), "next");
    assert.equal(radioKeyboardAction("ArrowDown"), "next");
    assert.equal(radioKeyboardAction("ArrowLeft"), "prev");
    assert.equal(radioKeyboardAction("ArrowUp"), "prev");
    assert.equal(radioKeyboardAction("Home"), "first");
    assert.equal(radioKeyboardAction("End"), "last");
    assert.equal(radioKeyboardAction("Enter"), null);
  });

  it("wraps indices for roving navigation", () => {
    const buttons = [{}, {}, {}];
    assert.equal(nextRadioIndex(/** @type {any} */ (buttons), 2, 1), 0);
    assert.equal(nextRadioIndex(/** @type {any} */ (buttons), 0, -1), 2);
  });
});

describe("bindExclusiveRadioButtons keyboard", () => {
  it("moves focus, selects mode, and syncs aria-checked via Arrow/Home/End", () => {
    document.body.innerHTML = `
      <div role="radiogroup" id="batch-filter">
        <button type="button" role="radio" data-batch-filter="hide" aria-checked="true" tabindex="0">不显示</button>
        <button type="button" role="radio" data-batch-filter="show" aria-checked="false" tabindex="-1">显示</button>
        <button type="button" role="radio" data-batch-filter="only" aria-checked="false" tabindex="-1">只显示</button>
      </div>
    `;
    const buttons = /** @type {HTMLElement[]} */ (
      Array.from(document.querySelectorAll("[data-batch-filter]"))
    );
    /** @type {string} */
    let mode = "hide";
    bindExclusiveRadioButtons(buttons, "batchFilter", (next) => {
      mode = next;
      syncExclusiveRadioButtons(buttons, "batchFilter", mode);
    });
    syncExclusiveRadioButtons(buttons, "batchFilter", mode);

    buttons[0].focus();
    buttons[0].dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
    );
    assert.equal(mode, "show");
    assert.equal(buttons[1].getAttribute("aria-checked"), "true");
    assert.equal(buttons[0].getAttribute("aria-checked"), "false");
    assert.equal(buttons[1].tabIndex, 0);
    assert.equal(buttons[0].tabIndex, -1);
    assert.equal(document.activeElement, buttons[1]);

    buttons[1].dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }),
    );
    assert.equal(mode, "only");
    assert.equal(buttons[2].getAttribute("aria-checked"), "true");
    assert.equal(document.activeElement, buttons[2]);

    buttons[2].dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }),
    );
    assert.equal(mode, "show");

    buttons[1].dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "Home", bubbles: true }),
    );
    assert.equal(mode, "hide");
    assert.equal(document.activeElement, buttons[0]);

    buttons[0].dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "End", bubbles: true }),
    );
    assert.equal(mode, "only");
    assert.equal(document.activeElement, buttons[2]);
    assert.equal(buttons[2].tabIndex, 0);
  });
});
