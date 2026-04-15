import { mkdir, copyFile, rm, cp, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const distDir = path.join(rootDir, "dist", "web");
const sharedDir = path.join(rootDir, "shared");
const webAppDir = path.join(rootDir, "apps", "web");

const runtimeApiBase = (process.env.SILIQUESTA_API_BASE || "").replace(/\/+$/, "");
const runtimePlatform = process.env.SILIQUESTA_PLATFORM || "web";

await rm(distDir, { recursive: true, force: true });
await mkdir(path.join(distDir, "shared"), { recursive: true });
await mkdir(path.join(distDir, "downloads"), { recursive: true });
await mkdir(path.join(distDir, "assets"), { recursive: true });

await copyFile(path.join(webAppDir, "app.html"), path.join(distDir, "app.html"));
await copyFile(path.join(webAppDir, "pricing.html"), path.join(distDir, "pricing.html"));
await copyFile(path.join(rootDir, "sw.js"), path.join(distDir, "sw.js"));
await copyFile(path.join(rootDir, "manifest.json"), path.join(distDir, "manifest.json"));
await copyFile(path.join(webAppDir, "landing.html"), path.join(distDir, "index.html"));
await copyFile(path.join(webAppDir, "favicon.ico"), path.join(distDir, "favicon.ico"));
await cp(sharedDir, path.join(distDir, "shared"), { recursive: true, force: true });
await cp(path.join(webAppDir, "downloads"), path.join(distDir, "downloads"), { recursive: true, force: true });
await cp(path.join(webAppDir, "assets"), path.join(distDir, "assets"), { recursive: true, force: true });

const runtimeApiBaseScript = runtimeApiBase
  ? JSON.stringify(runtimeApiBase)
  : "(/^(localhost|127\\\\.0\\\\.0\\\\.1|0\\\\.0\\\\.0\\\\.0)$/i.test(window.location.hostname) ? window.location.origin.replace(/\\\\/$/, '') + '/api/v1' : 'https://siliquesta-backend.onrender.com/api/v1')";

await writeFile(
  path.join(distDir, "shared", "runtime-config.js"),
  `window.SILIQUESTA_API_BASE = ${runtimeApiBaseScript};\nwindow.SILIQUESTA_PLATFORM = ${JSON.stringify(runtimePlatform)};\n`,
  "utf8"
);

console.log(`Built web bundle at ${distDir}`);
