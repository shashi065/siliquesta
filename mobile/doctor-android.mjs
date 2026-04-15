import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const androidDir = path.join(__dirname, "android");
const gradleHome = path.join(__dirname, ".gradle-user-home");
const localPropertiesPath = path.join(androidDir, "local.properties");

fs.mkdirSync(gradleHome, { recursive: true });

const candidateSdkDirs = [
  process.env.ANDROID_SDK_ROOT,
  process.env.ANDROID_HOME,
  process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, "Android", "Sdk") : null,
  process.env.ProgramFiles ? path.join(process.env.ProgramFiles, "Android", "Android Studio", "sdk") : null,
].filter(Boolean);

const sdkDir = candidateSdkDirs.find((candidate) => fs.existsSync(candidate));

if (sdkDir) {
  const escaped = sdkDir.replace(/\\/g, "\\\\");
  fs.writeFileSync(localPropertiesPath, `sdk.dir=${escaped}\n`, "utf8");
  console.log(`Android SDK configured: ${sdkDir}`);
} else {
  console.log("Android SDK not found automatically.");
  console.log("Install Android Studio SDK or set ANDROID_SDK_ROOT, then rerun `npm run doctor:android`.");
}

console.log(`Gradle user home ready: ${gradleHome}`);
