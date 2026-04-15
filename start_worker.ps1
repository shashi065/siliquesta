# Start Celery Worker for Background Tasks (Windows PowerShell)
#
# Prerequisites:
# - Redis running
# - Python environment activated: .\venv\Scripts\Activate.ps1
# - Dependencies: celery, redis
#
# Usage:
#   .\start_worker.ps1 [-Concurrency 4] [-Loglevel "info"] [-Monitor]

param(
    [int]$Concurrency = 4,
    [string]$Queues = "celery",
    [string]$Loglevel = "info",
    [switch]$Monitor
)

# Color outputs
function Write-Header {
    param([string]$Message)
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error_ {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning_ {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

Write-Header "Celery Worker Startup (Windows)"
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Concurrency: $Concurrency processes"
Write-Host "  Queues: $Queues"
Write-Host "  Log Level: $Loglevel"
Write-Host ""

# Check prerequisites
Write-Warning_ "Checking prerequisites..."

# Check Redis
$redisRunning = $false
try {
    $redisCheck = redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        $redisRunning = $true
    }
} catch {
}

if (-not $redisRunning) {
    Write-Error_ "Redis server not running"
    Write-Host "  Start Redis: redis-server"
    exit 1
}
Write-Success "Redis is running"

# Check Python environment
if (-not (Test-Path ".venv\Scripts\Activate.ps1") -and -not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Error_ "Virtual environment not found"
    Write-Host "  Create environment: python -m venv .venv"
    exit 1
}

# Activate venv
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
}
Write-Success "Virtual environment activated"

# Check Celery
try {
    $null = python -c "import celery" 2>$null
    Write-Success "Celery is installed"
} catch {
    Write-Error_ "Celery not installed"
    Write-Host "  Install: pip install celery[redis]"
    exit 1
}

Write-Host ""
Write-Header "Starting Celery Worker"
Write-Host ""

# Set environment variables
$env:CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Change to API directory
Push-Location services\api

# Start Celery worker
Write-Host "Starting Celery worker with the following settings:"
Write-Host "  Broker: $($env:CELERY_BROKER_URL)"
Write-Host "  Backend: $($env:CELERY_RESULT_BACKEND)"
Write-Host ""

celery -A app.celery_app worker `
    --concurrency=$Concurrency `
    --queues=$Queues `
    --loglevel=$Loglevel `
    --time-limit=300 `
    --soft-time-limit=240 `
    --prefetch-multiplier=1 `
    --task-events `
    --without-gossip `
    --without-mingle `
    --without-heartbeat

# Optional: Start Flower monitoring
if ($Monitor) {
    Write-Host ""
    Write-Warning_ "Starting Flower monitoring at http://localhost:5555"
    celery -A app.celery_app flower --port=5555
}

Pop-Location
