const { contextBridge } = require("electron");

const apiArgument = process.argv.find((arg) => arg.startsWith("--siliquesta-api-base="));
const apiBase = apiArgument
  ? apiArgument.replace("--siliquesta-api-base=", "")
  : "https://siliquesta-backend.onrender.com/api/v1";

contextBridge.exposeInMainWorld("SILIQUESTA_SHARED_CONFIG", {
  API_BASE: apiBase,
  PLATFORM: "desktop",
});
