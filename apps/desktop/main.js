const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const fs = require("node:fs");

const apiBase = process.env.SILIQUESTA_API_BASE || "https://siliquesta-backend.onrender.com/api/v1";
const externalUrl = process.env.SILIQUESTA_WEB_URL || "";

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1600,
    height: 980,
    minWidth: 1280,
    minHeight: 800,
    backgroundColor: "#020209",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: false,
      additionalArguments: apiBase ? [`--siliquesta-api-base=${apiBase}`] : [],
    },
  });

  if (externalUrl) {
    mainWindow.loadURL(externalUrl);
    return;
  }

  const localBundle = path.resolve(__dirname, "..", "..", "dist", "web", "index.html");
  if (!fs.existsSync(localBundle)) {
    throw new Error(`Missing web bundle at ${localBundle}. Run npm run build-web first.`);
  }

  mainWindow.loadFile(localBundle);
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
