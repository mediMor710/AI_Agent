// main.js — NexusAI Desktop
// Starts python app.py as a background process, then opens the window.

const { app, BrowserWindow, shell, dialog } = require("electron");
const { spawn } = require("child_process");
const http      = require("http");
const path      = require("path");
const fs        = require("fs");

let mainWindow   = null;
let flaskProcess = null;


// ════════════════════════════════════════════════════════════════
// WHERE ARE THE PYTHON FILES?
//
// Dev  (npm start):  right next to main.js  →  __dirname
// Built (.exe):      copied by extraResources into  resources/python/
// ════════════════════════════════════════════════════════════════
function getPythonDir() {
  if (app.isPackaged) {
    // process.resourcesPath = dist\win-unpacked\resources
    // extraResources copies files to:  resources\python\
    return path.join(process.resourcesPath, "python");
  }
  // In dev mode main.js sits in the project root alongside app.py
  return path.join(__dirname);
}


// ════════════════════════════════════════════════════════════════
// START FLASK
// ════════════════════════════════════════════════════════════════
function startFlask() {
  const pythonDir = getPythonDir();
  const appScript = path.join(pythonDir, "app.py");

  // Log paths so you can debug in the console
  console.log("[NexusAI] isPackaged  :", app.isPackaged);
  console.log("[NexusAI] pythonDir   :", pythonDir);
  console.log("[NexusAI] appScript   :", appScript);

  // Show a clear error if app.py is missing
  if (!fs.existsSync(appScript)) {
    const contents = fs.existsSync(pythonDir)
      ? fs.readdirSync(pythonDir).join("\n")
      : "(folder does not exist)";
    dialog.showErrorBox(
      "NexusAI — app.py not found",
      `Expected app.py at:\n${appScript}\n\nFolder contents:\n${contents}`
    );
    app.quit();
    return;
  }

  // Use "python" on Windows, "python3" on Mac/Linux
  const pythonCmd = process.platform === "win32" ? "python" : "python3";

  // Spawn:  python app.py
  // cwd is the folder containing app.py so all relative imports work
  flaskProcess = spawn(pythonCmd, ["app.py"], {
    cwd:  pythonDir,
    stdio: "pipe",
    env:  { ...process.env, PYTHONUNBUFFERED: "1" },
  });

  flaskProcess.stdout.on("data", d => process.stdout.write("[Flask] " + d));
  flaskProcess.stderr.on("data", d => process.stdout.write("[Flask] " + d));

  flaskProcess.on("error", err => {
    dialog.showErrorBox(
      "NexusAI — Python not found",
      `Could not start Python.\n\nError: ${err.message}\n\n` +
      `Make sure Python is installed and "python" works in your terminal.\n` +
      `Download Python: https://python.org`
    );
    app.quit();
  });

  flaskProcess.on("close", code =>
    console.log(`[NexusAI] Flask exited with code ${code}`)
  );
}


// ════════════════════════════════════════════════════════════════
// WAIT FOR FLASK TO BE READY
// ════════════════════════════════════════════════════════════════
function waitForFlask(callback) {
  let attempts = 0;
  const MAX    = 40;

  const check = () => {
    attempts++;
    http.get("http://127.0.0.1:5000", () => {
      console.log(`[NexusAI] Flask ready after ${attempts}s`);
      callback(null);
    }).on("error", () => {
      if (attempts >= MAX) {
        callback(new Error("Flask did not respond after 40 seconds."));
      } else {
        setTimeout(check, 1000);
      }
    });
  };

  // Give Flask 2.5 seconds to start before first check
  setTimeout(check, 2500);
}


// ════════════════════════════════════════════════════════════════
// CREATE THE WINDOW
// ════════════════════════════════════════════════════════════════
function createWindow() {
  mainWindow = new BrowserWindow({
    width:     1280,
    height:    800,
    minWidth:  900,
    minHeight: 600,
    title:     "NexusAI — Sales Intelligence Agent",
    backgroundColor: "#0f1117",
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadURL("http://127.0.0.1:5000");

  // Show only once the page is fully loaded (avoids white flash)
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    console.log("[NexusAI] Window shown");
  });

  // Open links in the real browser, not inside the app window
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => { mainWindow = null; });
}


// ════════════════════════════════════════════════════════════════
// APP LIFECYCLE
// ════════════════════════════════════════════════════════════════
app.whenReady().then(() => {
  startFlask();

  waitForFlask(err => {
    if (err) {
      dialog.showErrorBox(
        "NexusAI — Startup Failed",
        `Flask/Python did not start.\n\n${err.message}\n\n` +
        `Make sure all Python packages are installed:\n` +
        `  pip install flask boto3 pandas matplotlib reportlab python-dotenv`
      );
      app.quit();
      return;
    }
    createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// Kill Flask when the app closes — no orphan processes
app.on("before-quit", () => {
  if (flaskProcess) {
    console.log("[NexusAI] Shutting down Flask...");
    flaskProcess.kill();
  }
});