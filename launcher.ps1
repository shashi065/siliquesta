# SILIQUESTA Local Development Launcher (Windows)
# ==================================================
# Starts backend service without Docker
# 
# Usage: .\launcher.ps1 [-Port 8000] [-BackendOnly] [-Debug] [-NoReload]

param(
    [int]$Port = 8000,
    [switch]$BackendOnly = $false,
    [switch]$Debug = $false,
    [switch]$NoReload = $false
)

$ErrorActionPreference = "Stop"

# Colors
$Colors = @{
    Header = "`e[95m"
    Blue = "`e[94m"
    Cyan = "`e[96m"
    Green = "`e[92m"
    Yellow = "`e[93m"
    Red = "`e[91m"
    Reset = "`e[0m"
    Bold = "`e[1m"
}

function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch($Level) {
        "INFO" { $Colors.Blue }
        "SUCCESS" { $Colors.Green }
        "WARN" { $Colors.Yellow }
        "ERROR" { $Colors.Red }
        default { $Colors.Reset }
    }
    
    Write-Host "[$timestamp] $Level`t$Message" -ForegroundColor White
}

function Test-PythonVersion {
    try {
        $version = python --version 2>&1
        Write-Log "SUCCESS" "Python found: $version"
        return $true
    }
    catch {
        Write-Log "ERROR" "Python not found. Install Python 3.10+ and add to PATH"
        return $false
    }
}

function Test-Dependencies {
    $required = @("fastapi", "uvicorn", "sqlalchemy", "pydantic", "numpy", "scipy")
    $missing = @()
    
    Write-Log "INFO" "Checking dependencies..."
    
    foreach ($pkg in $required) {
        try {
            python -c "import $($pkg.Replace('-', '_'))" 2>&1 | Out-Null
        }
        catch {
            $missing += $pkg
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Log "ERROR" "Missing packages: $($missing -join ', ')"
        Write-Log "INFO" "Install with: pip install -r services/api/requirements.txt"
        return $false
    }
    
    Write-Log "SUCCESS" "All dependencies installed"
    return $true
}

function Start-FastAPIBackend {
    param(
        [int]$Port,
        [bool]$Reload,
        [bool]$Debug
    )
    
    $backendDir = Join-Path (Get-Location) "services" "api"
    Write-Log "INFO" "Starting FastAPI backend on port $Port..."
    
    $uvicornArgs = @(
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", $Port.ToString()
    )
    
    if ($Reload) {
        $uvicornArgs += "--reload"
    }
    
    if ($Debug) {
        $uvicornArgs += "--log-level", "debug"
    }
    else {
        $uvicornArgs += "--log-level", "info"
    }
    
    Push-Location $backendDir
    
    try {
        Write-Log "SUCCESS" "Backend starting..."
        python -m uvicorn $uvicornArgs
    }
    finally {
        Pop-Location
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )
    
    $startTime = Get-Date
    $timeout = New-TimeSpan -Seconds $TimeoutSeconds
    
    while ((Get-Date) - $startTime -lt $timeout) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Log "SUCCESS" "Service ready: $Url"
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
        
        Start-Sleep -Milliseconds 500
    }
    
    Write-Log "WARN" "Service did not become ready within ${TimeoutSeconds}s: $Url"
    return $false
}

# Main execution
Write-Host "`n$($Colors.Bold)$($Colors.Header)" -NoNewline
Write-Host @"
╔═══════════════════════════════════════════╗
║  SILIQUESTA - Local Development Launcher  ║
║    Windows/PowerShell Edition             ║
╚═══════════════════════════════════════════╝
"@
Write-Host $Colors.Reset

# Pre-flight checks
Write-Log "INFO" "Running pre-flight checks..."

if (-not (Test-PythonVersion)) {
    exit 1
}

if (-not (Test-Dependencies)) {
    exit 1
}

# Check .env
if (Test-Path ".env") {
    Write-Log "SUCCESS" ".env file loaded"
}
else {
    Write-Log "WARN" ".env file not found, using defaults"
}

# Start services
Write-Log "INFO" "Starting services..."

# Register cleanup on exit
$onExit = {
    Write-Log "INFO" "Cleaning up..."
}
trap {
    & $onExit
}

# Start backend
try {
    Start-FastAPIBackend -Port $Port -Reload (-not $NoReload) -Debug $Debug
}
catch {
    Write-Log "ERROR" "Failed to start backend: $_"
    exit 1
}

Write-Log "SUCCESS" "All services started successfully!"
Write-Log "INFO" "Backend: http://localhost:$Port"
Write-Log "INFO" "Docs: http://localhost:$Port/docs"
