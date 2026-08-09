/**
 * Sorting / comparison helpers for the model table.
 */

/**
 * @param {string|null} left
 * @param {string|null} right
 * @param {"asc"|"desc"} direction
 * @returns {number}
 */
export function compareNullableText(left, right, direction) {
  if (left === null && right === null) {
    return 0;
  }
  if (left === null) {
    return 1;
  }
  if (right === null) {
    return -1;
  }
  const result = left.localeCompare(right);
  return direction === "asc" ? result : -result;
}

/**
 * @param {number|null} left
 * @param {number|null} right
 * @param {"asc"|"desc"} direction
 * @returns {number}
 */
export function compareNullableNumber(left, right, direction) {
  if (left === null && right === null) {
    return 0;
  }
  if (left === null) {
    return 1;
  }
  if (right === null) {
    return -1;
  }
  return direction === "asc" ? left - right : right - left;
}

/**
 * @param {string} value
 * @returns {{ valid: boolean, timestamp: number, text: string }}
 */
export function parseFetchedAtValue(value) {
  if (!value) {
    return { valid: false, timestamp: 0, text: "" };
  }
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) {
    return { valid: false, timestamp: 0, text: value };
  }
  return { valid: true, timestamp, text: value };
}

/**
 * @param {string} left
 * @param {string} right
 * @param {"asc"|"desc"} direction
 * @returns {number}
 */
export function compareFetchedAt(left, right, direction) {
  const parsedLeft = parseFetchedAtValue(left);
  const parsedRight = parseFetchedAtValue(right);

  if (!parsedLeft.valid && !parsedRight.valid) {
    return direction === "asc"
      ? parsedLeft.text.localeCompare(parsedRight.text)
      : parsedRight.text.localeCompare(parsedLeft.text);
  }
  if (!parsedLeft.valid) {
    return 1;
  }
  if (!parsedRight.valid) {
    return -1;
  }
  return direction === "asc"
    ? parsedLeft.timestamp - parsedRight.timestamp
    : parsedRight.timestamp - parsedLeft.timestamp;
}
