import { rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

const targets = [
  path.join(rootDir, ".venv_siliquesta"),
  path.join(rootDir, "apps", "web", ".next"),
  path.join(rootDir, "apps", "web", "node_modules"),
  path.join(rootDir, "apps", "web", "tsconfig.tsbuildinfo"),
  path.join(rootDir, "services", "api", "app", "__pycache__"),
  path.join(rootDir, "services", "api", "app", "api", "__pycache__"),
  path.join(rootDir, "services", "api", "app", "services", "__pycache__"),
  path.join(rootDir, "services", "api", "spice_debug"),
  path.join(rootDir, "services", "api", "spice_debug_low"),
  path.join(rootDir, "services", "api", "spice_debug_real"),
  path.join(rootDir, "services", "api", "spice_debug_real_abs"),
  path.join(rootDir, "services", "api", "spice_work"),
  path.join(rootDir, "services", "api", "spice_work_py"),
  path.join(rootDir, "backend_storage"),
  path.join(rootDir, "apps", "desktop", "node_modules"),
  path.join(rootDir, "mobile", "node_modules"),
  path.join(rootDir, "mobile", ".gradle-user-home"),
  path.join(rootDir, "output"),
  path.join(rootDir, "runtime_vendor"),
];

for (const target of targets) {
  try {
    await rm(target, { recursive: true, force: true });
  } catch (error) {
    console.warn(`Skipped locked path: ${target} (${error.code || "unknown"})`);
  }
}

console.log("Removed generated caches, vendor directories, local envs, and scratch outputs.");
