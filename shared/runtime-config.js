//  Runtime Configuration (Browser-safe)

window.SILIQUESTA_API_BASE =
  window.SILIQUESTA_API_BASE ||
  (/^(localhost|127\.0\.0\.1|0\.0\.0\.0)$/i.test(window.location.hostname)
    ? window.location.origin.replace(/\/+$/, "") + "/api/v1"
    : "https://siliquesta-backend.onrender.com/api/v1");

// Platform identifier
window.SILIQUESTA_PLATFORM = window.SILIQUESTA_PLATFORM || "web";