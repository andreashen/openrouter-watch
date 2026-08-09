/**
 * Shared typedefs for the model table client (JSDoc / check).
 */

/**
 * @typedef {"hide" | "show" | "only"} TriFilterMode
 */

/**
 * @typedef {"asc" | "desc"} SortDirection
 */

/**
 * @typedef {object} ModelRow
 * @property {string} model_id
 * @property {string} [name]
 * @property {string} [vendor_name]
 * @property {string} [author]
 * @property {string} [slug]
 * @property {string} [openrouter_model_url]
 * @property {boolean} [officially_removed]
 * @property {boolean} [is_pointer]
 * @property {string|null} [pointer_target_id]
 * @property {string|null} [pointer_kind]
 * @property {string} [fetched_at]
 * @property {string} [updated_at]
 * @property {number|null} [context_length]
 * @property {number|null} [max_completion_tokens]
 * @property {number|null} [input_price_usd_per_1m]
 * @property {number|null} [weighted_avg_input_price_usd_per_1m]
 * @property {number|null} [output_price_usd_per_1m]
 * @property {number|null} [intelligence_index]
 * @property {number|null} [coding_index]
 * @property {number|null} [agentic_index]
 * @property {boolean} [supports_reasoning]
 * @property {boolean} [supports_tools]
 * @property {boolean} [supports_vision]
 * @property {string|null} [knowledge_cutoff]
 * @property {string|null} [released_at]
 */

/**
 * @typedef {object} ModelTableBoot
 * @property {ModelRow[]} [models]
 * @property {Record<string, string[]>} [vendorMatchByChip]
 */

export {};
