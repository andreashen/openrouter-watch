/**
 * URL allowlist for model deep links rendered in the table.
 * Only https://openrouter.ai (and www) are accepted.
 */

const ALLOWED_HOSTS = new Set(["openrouter.ai", "www.openrouter.ai"]);

/**
 * @param {string|null|undefined} raw
 * @returns {string|null} sanitized absolute https URL, or null when rejected
 */
export function sanitizeModelUrl(raw) {
  if (typeof raw !== "string" || !raw.trim()) {
    return null;
  }
  let url;
  try {
    url = new URL(raw.trim());
  } catch {
    return null;
  }
  if (url.protocol !== "https:") {
    return null;
  }
  if (!ALLOWED_HOSTS.has(url.hostname.toLowerCase())) {
    return null;
  }
  // Block credentials / unexpected userinfo
  if (url.username || url.password) {
    return null;
  }
  return url.href;
}

/**
 * Prefer allowlisted openrouter_model_url; else build https://openrouter.ai/{model_id}.
 *
 * @param {{ model_id?: string, openrouter_model_url?: string }} model
 * @returns {string|null}
 */
export function resolveSafeModelUrl(model) {
  const fromField = sanitizeModelUrl(model?.openrouter_model_url);
  if (fromField) {
    return fromField;
  }
  const modelId = typeof model?.model_id === "string" ? model.model_id : "";
  if (!modelId) {
    return null;
  }
  try {
    const fallback = new URL("https://openrouter.ai/");
    fallback.pathname = `/${modelId.replace(/^\/+/, "")}`;
    return sanitizeModelUrl(fallback.href);
  } catch {
    return null;
  }
}
