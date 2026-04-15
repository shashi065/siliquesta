import packager from "@electron/packager";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const iconCandidates = [
  path.join(__dirname, "..", "web", "public", "siliquesta.ico"),
  path.join(__dirname, "..", "web", "public", "favicon.ico"),
  path.join(__dirname, "..", "web", "favicon.ico"),
];

const existingIcon = iconCandidates.find((candidate) => fs.existsSync(candidate));

const commonOptions = {
  dir: __dirname,
  out: path.join(__dirname, "dist"),
  overwrite: true,
  prune: false,
  asar: false,
  name: "SILIQUESTA",
  executableName: "SILIQUESTA",
  ignore: [
    /^\/dist($|\/)/,
    /^\/node_modules\/\.cache($|\/)/,
  ],
};

const targets = [
  { platform: "win32", arch: "x64" },
  { platform: "linux", arch: "x64" },
  { platform: "darwin", arch: "x64" },
];

for (const target of targets) {
  const options = {
    ...commonOptions,
    ...target,
  };
  if (existingIcon && target.platform === "win32") {
    options.icon = existingIcon;
  }
  const appPaths = await packager(options);
  for (const appPath of appPaths) {
    console.log(`Packaged ${target.platform}/${target.arch}: ${appPath}`);
  }
}
