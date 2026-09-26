/**
 * Display rules for AA scores. The public table does not import this module
 * until a written grant allows the cutover.
 */

export const AA_SORT_NOTE =
  "排序只比较与列名版本相同的分数。旧版本徽章和空值不参与排序。";

/**
 * @param {string} metricLabel
 * @param {string} majorMinor
 * @returns {string}
 */
export function columnVersionLabel(metricLabel, majorMinor) {
  return `${metricLabel} v${majorMinor}`;
}

/**
 * @param {number|null|undefined} value
 * @param {string|null|undefined} cellVersion
 * @param {string} columnVersion
 * @returns {{ text: string, badge: string|null, comparable: boolean, hint: string|null }}
 */
export function formatAaScoreCell(value, cellVersion, columnVersion) {
  if (value === null || value === undefined) {
    return { text: "—", badge: null, comparable: false, hint: "不可比" };
  }
  if (cellVersion !== columnVersion) {
    return { text: String(value), badge: `v${cellVersion}`, comparable: false, hint: null };
  }
  return { text: String(value), badge: null, comparable: true, hint: null };
}

/**
 * @param {number|null|undefined} value
 * @param {string|null|undefined} cellVersion
 * @param {string} columnVersion
 * @returns {number|null}
 */
export function aaSortValue(value, cellVersion, columnVersion) {
  if (value === null || value === undefined) {
    return null;
  }
  if (cellVersion !== columnVersion) {
    return null;
  }
  return value;
}
