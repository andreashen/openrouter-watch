/**
 * Vendor quick-filter chip config and matching helpers.
 *
 * Chip `name` is the selection key / accessible label. `matchNames` lists the
 * `vendor_name` values that chip should accept (defaults to `[name]`).
 *
 * OpenRouter may rename a brand's display prefix (e.g. xAI → SpaceXAI) while
 * older / removed rows keep the previous label; aliases keep the chip usable.
 */

/** @typedef {{ name: string, icon: string, mono: boolean, matchNames?: string[] }} VendorQuickFilter */

/** @type {readonly VendorQuickFilter[]} */
export const VENDOR_QUICK_FILTERS = Object.freeze([
  { name: "Anthropic", icon: "anthropic.svg", mono: true },
  { name: "OpenAI", icon: "openai.svg", mono: true },
  { name: "xAI", icon: "xai.svg", mono: true, matchNames: ["xAI", "SpaceXAI"] },
  { name: "Meta", icon: "meta.svg", mono: true },
  { name: "Google", icon: "google.png", mono: false },
  { name: "Z.ai", icon: "zai.svg", mono: false },
  { name: "Xiaomi", icon: "xiaomi.png", mono: false },
  { name: "MoonshotAI", icon: "moonshotai.png", mono: false },
  { name: "Qwen", icon: "qwen.svg", mono: false },
  { name: "MiniMax", icon: "minimax.png", mono: false },
  { name: "DeepSeek", icon: "deepseek.svg", mono: false },
]);

/**
 * @param {readonly VendorQuickFilter[]} filters
 * @returns {Record<string, string[]>}
 */
export function buildVendorMatchByChip(filters = VENDOR_QUICK_FILTERS) {
  /** @type {Record<string, string[]>} */
  const map = {};
  for (const filter of filters) {
    const names = filter.matchNames?.length ? filter.matchNames : [filter.name];
    map[filter.name] = [...names];
  }
  return map;
}

/**
 * Expand selected chip keys into the set of acceptable `vendor_name` values.
 *
 * @param {Iterable<string>} selectedChips
 * @param {Record<string, string[]>} [matchByChip]
 * @returns {Set<string>}
 */
export function expandSelectedVendorNames(
  selectedChips,
  matchByChip = buildVendorMatchByChip(),
) {
  const names = new Set();
  for (const chip of selectedChips) {
    const aliases = matchByChip[chip];
    if (aliases?.length) {
      for (const name of aliases) {
        names.add(name);
      }
    } else {
      names.add(chip);
    }
  }
  return names;
}

/**
 * @param {string | null | undefined} vendorName
 * @param {Iterable<string>} selectedChips
 * @param {Record<string, string[]>} [matchByChip]
 * @returns {boolean}
 */
export function matchesVendorSelection(
  vendorName,
  selectedChips,
  matchByChip = buildVendorMatchByChip(),
) {
  const selected = selectedChips instanceof Set ? selectedChips : new Set(selectedChips);
  if (selected.size === 0) {
    return true;
  }
  if (vendorName == null || vendorName === "") {
    return false;
  }
  return expandSelectedVendorNames(selected, matchByChip).has(vendorName);
}
