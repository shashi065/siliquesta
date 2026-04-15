# Async Task System - Quick Reference

## Quick Start (5 minutes)

### 1. Start Redis
```bash
# Check it's running
redis-cli ping
# Should return: PONG

# If not, start it:
redis-server  # macOS/Linux
# Or via WSL for Windows
```

### 2. Start Celery Workers
```bash
# Bash/macOS/Linux
bash start_worker.sh --concurrency 4

# PowerShell/Windows
.\start_worker.ps1 -Concurrency 4

# Direct command
cd services/api
celery -A app.celery_app worker --concurrency=4 --loglevel=info
```

### 3. Start API
```bash
cd services/api
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Done! ✅

## Submit Async Job

```bash
# Optimization
curl -X POST http://localhost:8000/ts/optimizer/ \
  -H "Content-Type: application/json" \
  -d '{"wn": 1.0, "wp": 2.0, "vdd": 1.8, "temp": 27.0, "cl_ff": 10.0}'

# Response (immediate!)
{
  "job_id": "abc123...",
  "status": "queued"
}
```

## Check Job Status

```bash
# Save job_id from above
JOB_ID="abc123..."

# Check status
curl http://localhost:8000/status/task/$JOB_ID/status
# Response: {"status": "pending|started|success|failure"}

# Get result (once complete)
curl http://localhost:8000/status/task/$JOB_ID/result
# Response: {...complete result...}
```

## Available Tasks

| Task | Endpoint | Duration | Example |
|------|----------|----------|---------|
| Optimization | `POST /ts/optimizer/` | 30-120s | NSGA-II search |
| ML Optimization | `POST /ts/optimizer/ml-optimize` | 10-60s | Digital twin search |
| Training | `POST /ts/digital_twin/train` | 60-180s | Model training |
| Simulation | `POST /ts/simulation/` | 5-30s | SPICE sim |

## Status Values

```
pending   - Waiting in queue
started   - Worker picked it up
success   - ✅ Complete, check result
failure   - ❌ Error occurred
retry     - Retrying after error
```

## Common Curl Commands

```bash
# Submit job
curl -X POST http://localhost:8000/ts/optimizer/ \
  -H "Content-Type: application/json" \
  -d '{...}'

# Check status (poll every 5-10 seconds)
curl http://localhost:8000/status/task/{JOB_ID}/status

# Get final result
curl http://localhost:8000/status/task/{JOB_ID}/result

# Cancel task
curl -X POST http://localhost:8000/status/task/{JOB_ID}/cancel

# Queue health
curl http://localhost:8000/status/tasks/queue/status
```

## Python Examples

```python
import requests
import time

# Submit job
resp = requests.post("http://localhost:8000/ts/optimizer/", json={
    "wn": 1.0, "wp": 2.0, "vdd": 1.8, "temp": 27.0
})
job_id = resp.json()["job_id"]

# Poll for result (timeout after 5 minutes)
for i in range(300):
    status_resp = requests.get(f"http://localhost:8000/status/task/{job_id}/status")
    status = status_resp.json()
    
    if status["successful"]:
        result = requests.get(f"http://localhost:8000/status/task/{job_id}/result").json()
        print("Result:", result)
        break
    
    print(f"Status: {status['status']}")
    time.sleep(1)
```

## Monitoring

### Option 1: Flower Web UI
```bash
# Install
pip install flower

# Start
cd services/api
celery -A app.celery_app flower --port=5555

# View: http://localhost:5555
```

### Option 2: Redis CLI
```bash
# Check queue depth
redis-cli LLEN celery

# Monitor in real-time
redis-cli monitor

# Check connection
redis-cli ping
```

### Option 3: Celery Inspect
```bash
# Active tasks
celery -A app.celery_app inspect active

# Worker stats
celery -A app.celery_app inspect stats

# Registered tasks
celery -A app.celery_app inspect registered
```

## Troubleshooting

### "Connection refused"
```bash
# Redis not running
redis-cli ping  # Should return PONG
redis-server    # Start if not running
```

### "Celery is required for optimization"
```bash
# Workers not running
cd services/api
celery -A app.celery_app worker --concurrency=4
```

### Job stuck in "pending"
```bash
# Check queue
redis-cli LLEN celery

# Check workers
celery -A app.celery_app inspect stats

# Restart workers if needed
```

### Task timeout (taking too long)
```bash
# Check task isn't hung
celery -A app.celery_app inspect active

# Increase timeout if needed (in celery_app.py)
task_time_limit = 600  # 10 minutes
```

## Environment Variables

```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0

# For testing (synchronous execution)
export CELERY_TASK_ALWAYS_EAGER=false
```

## Performance Tips

```bash
# CPU-bound (optimization, training)
# Use: number of CPU cores
celery -A app.celery_app worker --concurrency=4

# I/O-bound (simulation)
# Use: 2-3x CPU cores
celery -A app.celery_app worker --concurrency=8

# Check CPU cores
nproc  # Linux/macOS
Get-ComputerInfo | Select-Object CsProcessors  # PowerShell
```

## Architecture

```
Client
  ↓
API Endpoint (FastAPI)
  ↓
JobDispatcher
  ↓
Redis Queue
  ↓
Celery Workers (3, 4, 5, ...)
  ↓
Results stored in Redis
  ↓
Client polls status/result
```

## File Locations

```
services/
├── api/
│   ├── app/
│   │   ├── celery_app.py          # Celery config
│   │   ├── tasks/
│   │   │   └── compute.py         # All task definitions
│   │   ├── api/
│   │   │   ├── optimizer.py       # Async dispatch
│   │   │   ├── digital_twin.py    # Async dispatch
│   │   │   └── async_status.py    # Status endpoints (NEW)
│   │   └── services/
│   │       └── task_monitor.py    # Monitoring helpers (NEW)
│   └── requirements.txt
├── start_worker.sh                  # Worker startup (NEW)
└── start_worker.ps1                 # Worker startup PS1 (NEW)
```

## Task Status Polling Pattern

**Recommended approach:**

```python
import time

def wait_for_job(job_id, timeout=300, poll_interval=5):
    start = time.time()
    
    while time.time() - start < timeout:
        status = get_status(job_id)
        
        if status["successful"]:
            return get_result(job_id)
        
        if status["status"] == "failure":
            raise Exception(f"Job failed: {status['error']}")
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Job did not complete in {timeout}s")

# Usage
result = wait_for_job(job_id)
print(result)
```

## Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ts/optimizer/` | Submit optimization job |
| POST | `/ts/optimizer/ml-optimize` | Submit ML optimization |
| POST | `/ts/digital_twin/train` | Submit training job |
| GET | `/status/task/{id}/status` | Check job status |
| GET | `/status/task/{id}/result` | Get completed result |
| POST | `/status/task/{id}/cancel` | Cancel task |
| GET | `/status/tasks/queue/status` | Queue health |

## Response Examples

### Immediate (job submitted)
```json
{
  "job_id": "5f8c9b0a-1234-5678-abcd-ef1234567890",
  "job_key": "job_2024_001",
  "status": "queued"
}
```

### Status check (pending)
```json
{
  "task_id": "5f8c9b0a...",
  "status": "started",
  "successful": false,
  "result": null
}
```

### Status check (complete)
```json
{
  "task_id": "5f8c9b0a...",
  "status": "success",
  "successful": true,
  "result": {
    "pareto_front": [...],
    "best_design": {...}
  }
}
```

## Scaling Options

### Single Machine
```bash
# Increase workers
celery -A app.celery_app worker --concurrency=16

# Monitor
celery -A app.celery_app flower
```

### Multiple Machines
```bash
# All point to same Redis
export CELERY_BROKER_URL=redis://redis-host:6379/0

# Start workers on each machine
celery -A app.celery_app worker
```

---

**Save this file!** Reference it when submitting async jobs.

Last Updated: April 13, 2026
