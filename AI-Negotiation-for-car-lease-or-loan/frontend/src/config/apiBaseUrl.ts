const rawApiBaseUrl =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "");

/**
 * Single source of truth for backend API base URL.
 * In production, fail fast when the env variable is missing.
 */
export const API_BASE_URL = (() => {
  const normalized = rawApiBaseUrl.trim().replace(/\/$/, "");
  if (!normalized && !import.meta.env.DEV) {
    throw new Error(
      "Missing API base URL. Set VITE_API_URL (or VITE_API_BASE_URL) in Vercel environment variables.",
    );
  }
  return normalized;
})();
