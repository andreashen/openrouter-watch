/**
 * Reorder session-level pinned model ids.
 * Drop indicator is a top insert line → always insert BEFORE toId.
 *
 * @param {string[]} ids
 * @param {string} fromId
 * @param {string} toId
 * @returns {string[]}
 */
export function reorderPinnedIds(ids, fromId, toId) {
  const from = ids.indexOf(fromId);
  const to = ids.indexOf(toId);
  if (from < 0 || to < 0 || from === to) {
    return ids.slice();
  }
  const next = ids.slice();
  const [item] = next.splice(from, 1);
  // Re-resolve target after removal so downward moves still insert *before* toId
  // (top insert-line semantics). Using the pre-removal `to` index would place
  // the item after toId when from < to.
  const insertAt = next.indexOf(toId);
  if (insertAt < 0) {
    return ids.slice();
  }
  next.splice(insertAt, 0, item);
  return next;
}
