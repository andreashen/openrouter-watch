/**
 * Reorder session-level pinned model ids.
 * Visual insert line: top → place 'before'; bottom → place 'after'.
 *
 * @param {string[]} ids
 * @param {string} fromId
 * @param {string} toId
 * @param {'before'|'after'} [place='before']
 * @returns {string[]}
 */
export function reorderPinnedIds(ids, fromId, toId, place = "before") {
  const from = ids.indexOf(fromId);
  const to = ids.indexOf(toId);
  if (from < 0 || to < 0 || from === to) {
    return ids.slice();
  }
  const next = ids.slice();
  const [item] = next.splice(from, 1);
  // Re-resolve target after removal so downward moves keep the intended
  // before/after relationship to toId (not a stale pre-removal index).
  const targetAt = next.indexOf(toId);
  if (targetAt < 0) {
    return ids.slice();
  }
  const insertAt = place === "after" ? targetAt + 1 : targetAt;
  next.splice(insertAt, 0, item);
  return next;
}
