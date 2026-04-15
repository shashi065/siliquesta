// Single source of truth for browser and Node consumers.

const FALLBACK_API_BASE = "https://siliquesta-backend.onrender.com/api/v1";

function resolveApiBase(globalScope) {
  if (globalScope && typeof globalScope.SILIQUESTA_API_BASE === "string" && globalScope.SILIQUESTA_API_BASE.trim()) {
    return globalScope.SILIQUESTA_API_BASE.replace(/\/+$/, "");
  }

  const envBase = process.env.NEXT_PUBLIC_API_URL || process.env.SILIQUESTA_API_BASE;
  if (typeof envBase === "string" && envBase.trim()) {
    return envBase.replace(/\/+$/, "");
  }

  return FALLBACK_API_BASE;
}

const browserScope = typeof window !== "undefined" ? window : undefined;
const API_BASE = resolveApiBase(browserScope);

if (browserScope) {
  browserScope.SILIQUESTA_API_BASE = API_BASE;
}

module.exports = {
  FALLBACK_API_BASE,
  API_BASE,
  resolveApiBase,
};
