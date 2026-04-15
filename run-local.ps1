$ErrorActionPreference = "Stop"

$root = "C:\Users\SHASHI\OneDrive\Desktop\siliquesta"
$venvPython = Join-Path $root ".venv_siliquesta\Scripts\python.exe"
$backendDir = Join-Path $root "services" "api"
$logDir = Join-Path $root "output\logs"
$backendLog = Join-Path $logDir "backend_web.log"
$staticLog = Join-Path $logDir "static_web.log"

New-Item -ItemType Directory -Force $logDir | Out-Null

if (-not (Test-Path $venvPython)) {
  throw "Missing virtualenv at $venvPython. Ask me to recreate the local runtime."
}

Write-Host "Starting SILIQUESTA backend on http://127.0.0.1:8000 ..."
Start-Process -FilePath pwsh -ArgumentList @(
  "-NoProfile",
  "-Command",
  "Set-Location '$backendDir'; & '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 *> '$backendLog'"
)

Write-Host "Starting SILIQUESTA product shell on http://127.0.0.1:8080 ..."
Start-Process -FilePath pwsh -ArgumentList @(
  "-NoProfile",
  "-Command",
  "Set-Location '$root'; & '$venvPython' -m http.server 8080 -d '$root' *> '$staticLog'"
)

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "SILIQUESTA is launching without Docker."
Write-Host "Product UI:  http://127.0.0.1:8080/index.html"
Write-Host "Backend API: http://127.0.0.1:8000"
Write-Host ""
Write-Host "Logs:"
Write-Host "  $backendLog"
Write-Host "  $staticLog"
