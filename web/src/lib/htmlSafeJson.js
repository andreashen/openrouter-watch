/**
 * Serialize JSON for safe embedding inside an HTML <script> element.
 *
 * JSON.stringify alone is not HTML-safe: a model string containing
 * `</script>` can break out of the script tag. Also escape U+2028/U+2029
 * which are valid in JSON/HTML but terminate ECMAScript statements.
 *
 * @param {unknown} value
 * @returns {string}
 */
export function htmlSafeJsonStringify(value) {
  const json = JSON.stringify(value);
  if (typeof json !== "string") {
    return "null";
  }
  return json
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}

/**
 * @param {string} embedded
 * @returns {boolean} true when the payload still contains a raw script breaker
 */
export function containsRawScriptBreaker(embedded) {
  return /<\/script/i.test(embedded);
}
