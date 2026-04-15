# Async Task System - Complete Guide

## Overview

The async task system uses **Celery + Redis** to execute long-running operations (optimization, training, simulation) in background workers, keeping the API responsive and enabling true scalability.

## Architecture

```
FastAPI Endpoints
    ↓
SaaS Manager (auth, rate limiting, cost)
    ↓
JobDispatcher (Celery)
    ↓
Redis (broker + result backend)
    ↓
Celery Workers (execution pool)
    ↓
Database (job status, results, audit)
```

## Components

### 1. Redis (Message Broker & Result Backend)
- **Broker:** Tasks queued here before workers pick them up
- **Backend:** Results stored here after task completion
- **Port:** 6379 (default)

### 2. Celery (Task Queue)
- **App:** `app.celery_app` (configured in `services/api/app/celery_app.py`)
- **Tasks:** Defined in `services/api/app/tasks/compute.py`
- **Config:** Job serialization, time limits, task acknowledgment

### 3. API Endpoints
- **Async endpoints** return immediately with `job_id`
- **Status endpoints** check job progress
- **Result endpoints** retrieve completed results

### 4. Workers
- **Process:** Background Python processes running Celery
- **Concurrency:** Configurable number of parallel tasks
- **Timeout:** 5 minutes (hard), 4 minutes (soft)

## Available Tasks

### Optimization Tasks

#### `siliquesta.run_optimizer`
Multi-objective evolutionary optimization using NSGA-II.

```python
# Endpoint request
POST /ts/optimizer/
{
    "wn": 1.0,
    "wp": 2.0,
    "vdd": 1.8,
    "temp": 27.0,
    ...
}

# Immediate response
{
    "job_id": "abc123...",
    "job_key": "job_2024_001",
    "status": "queued"
}

# Later check status
GET /status/task/abc123.../status
# When complete
GET /status/task/abc123.../result
```

#### `siliquesta.run_ml_optimizer`
ML-powered optimization using digital twin surrogate model.

```python
POST /ts/optimizer/ml-optimize
{
    "wn": 1.0,
    "wp": 2.0,
    "vdd": 1.8,
    "objective": "performance",  # "performance", "power", "efficiency", "balanced"
    "iterations": 100,
    "method": "two_stage"  # "two_stage", "evolutionary", "bayesian"
}
```

### Training Tasks

#### `siliquesta.train_digital_twin`
Train ML models (XGBoost) for power, frequency, delay prediction.

```python
POST /ts/digital_twin/train
{
    "sample_count": 5000,
    "prefer_spice": false  # Use SPICE simulation or fast physics-based models
}
```

**Duration:** 30-120 seconds depending on sample count

### Simulation Tasks

#### `siliquesta.run_spice_simulation`
SPICE transient simulation of inverter circuit.

#### `siliquesta.run_pvt_sweep`
Process-Voltage-Temperature parameter sweep.

#### `siliquesta.run_batch_simulations`
Batch multiple SPICE simulations in parallel.

## Setup Instructions

### 1. Install Redis

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
redis-server --daemonize yes
redis-cli ping  # Should return PONG
```

**macOS:**
```bash
brew install redis
brew services start redis
redis-cli ping
```

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL: `wsl -- sudo apt-get install redis-server`

### 2. Install Dependencies

```bash
cd services/api
pip install celery[redis]==5.3.0 redis==5.0.0
```

### 3. Configure Environment

Create `.env` in `services/api/`:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false  # Set to true for testing (synchronous)
```

### 4. Start Workers

**Option A: bash (Linux/macOS)**
```bash
bash start_worker.sh --concurrency 4 --loglevel info
```

**Option B: PowerShell (Windows)**
```powershell
.\start_worker.ps1 -Concurrency 4 -Loglevel info
```

**Option C: Direct Celery command**
```bash
cd services/api
celery -A app.celery_app worker --concurrency=4 --loglevel=info
```

### 5. Start API Server

```bash
cd services/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage Examples

### Example 1: Submit Optimization Job

```bash
# Submit optimization
curl -X POST http://localhost:8000/ts/optimizer/ \
  -H "Content-Type: application/json" \
  -d '{
    "wn": 1.0,
    "wp": 2.0,
    "vdd": 1.8,
    "temp": 27.0,
    "cl_ff": 10.0,
    "max_power": 5.0,
    "population_size": 48,
    "generations": 10
  }' | jq .

# Response (immediate)
{
  "job_id": "5f8c9b0a-1234-5678-abcd-ef1234567890",
  "job_key": "job_2024_001",
  "status": "queued",
  "scope": "optimizer.run"
}
```

### Example 2: Check Job Status

```bash
# Poll for status (can do immediately or after 30 seconds)
curl http://localhost:8000/status/task/5f8c9b0a.../status | jq .

# Response (still processing)
{
  "task_id": "5f8c9b0a...",
  "status": "started",
  "successful": false,
  "result": null
}

# After completion
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

### Example 3: Retrieve Results

```bash
# Get results (once complete)
curl http://localhost:8000/status/task/5f8c9b0a.../result | jq .

# Response (once task completes)
{
  "pareto_front": [...],
  "best_design": {...}
}
```

### Example 4: Train Digital Twin

```bash
# Submit training job
curl -X POST http://localhost:8000/ts/digital_twin/train \
  -H "Content-Type: application/json" \
  -d '{
    "sample_count": 5000,
    "prefer_spice": false
  }' | jq .

# Response
{
  "job_id": "7a9f1c2d-...",
  "status": "queued"
}

# Check status after ~60-90 seconds
curl http://localhost:8000/status/task/7a9f1c2d.../status | jq .
```

## Monitoring

### 1. Task Status API

```bash
# Check specific task
curl http://localhost:8000/status/task/{task_id}/status

# Get results
curl http://localhost:8000/status/task/{task_id}/result

# Queue status
curl http://localhost:8000/status/tasks/queue/status
```

### 2. Flower Web UI (Optional)

```bash
# Install Flower
pip install flower

# Start Flower
cd services/api
celery -A app.celery_app flower --port=5555
```

**Access:** http://localhost:5555

Features:
- ✓ Real-time task monitoring
- ✓ Worker status and health
- ✓ Task history and results
- ✓ Performance graphs
- ✓ Task execution timeline

### 3. Redis CLI

```bash
# Check Redis connection
redis-cli ping

# Monitor all operations
redis-cli monitor

# Check message queue depth
redis-cli LLEN celery  # Key length

# Flush all (DANGER - clears all data)
redis-cli FLUSHDB
```

### 4. Logs

**Worker logs:**
```bash
tail -f /var/log/celery/worker.log
```

**API logs:**
```bash
# If running locally with --reload
# Logs appear in terminal
```

## Task Lifecycle

```
1. CLIENT SUBMITS JOB
   POST /ts/optimizer/
   └─ Returns: job_id immediately

2. API QUEUES TASK
   JobDispatcher.dispatch("task_name", job_key, payload)
   └─ Stores in Redis queue

3. WORKER PICKS UP TASK
   Worker: "OK, I'll process this"
   └─ Updates job status: "started"

4. TASK EXECUTES
   Worker: Running optimization/training...
   └─ May take seconds to minutes

5. TASK COMPLETES
   Worker: "Done! Here's the result"
   └─ Updates job status: "completed"
   └─ Stores result in Redis backend

6. CLIENT RETRIEVES RESULT
   GET /status/task/{job_id}/result
   └─ Returns: Full result data
```

## Performance Tips

### 1. Concurrency Tuning

```bash
# CPU-bound tasks (optimization, training)
#   Use: # of CPU cores
concurrency = $(nproc)

# I/O-bound tasks (simulation)
#   Use: 2-3x # of CPU cores
concurrency = $(( $(nproc) * 2 ))

# Mixed workload
#   Start with: # of CPU cores + 2
```

### 2. Queue Configuration

```python
# In celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=1,    # Grab 1 task at a time (good for long tasks)
    task_acks_late=True,             # Acknowledge only after completion
    task_time_limit=300,             # Hard limit: 5 minutes
    task_soft_time_limit=240,        # Soft limit: 4 minutes
)
```

### 3. Result Backend Tuning

```bash
# Save results for 24 hours (86400 seconds)
result_expires=86400

# Or use:
# - Memory-only: Less reliable but fastest
# - Disk-backed: More reliable but slower
# - Database: Most reliable but requires cleanup
```

## Troubleshooting

### Worker Won't Start

**Error:** "Connection refused"
```bash
# Check Redis is running
redis-cli ping

# If not running
redis-server
```

**Error:** "Celery app not found"
```bash
# Check you're in correct directory
cd services/api

# Check imports
python -c "from app.celery_app import celery_app; print(celery_app)"

# Check app.tasks.compute exists
ls -la app/tasks/
```

### Tasks Stuck in Pending

```bash
# Check queue depth
redis-cli LLEN celery

# Monitor tasks in real-time
celery -A app.celery_app inspect active

# Force purge queue (DANGER)
celery -A app.celery_app purge
```

### Memory Leaks

```bash
# Worker uses too much memory
# Solution: Set worker max tasks per child

celery -A app.celery_app worker \
    --max-tasks-per-child=1000  # Restart after 1000 tasks
```

### Slow Task Execution

```bash
# Check worker utilization
celery -A app.celery_app inspect stats

# If CPU-bound: Reduce concurrency
# If I/O-bound: Increase concurrency
# Check: redis-cli monitor (for queue volume)
```

## Test Mode (Synchronous)

For testing without Redis:

```bash
# Set in environment
export CELERY_TASK_ALWAYS_EAGER=true

# Or in code
from app.config import settings
settings.CELERY_TASK_ALWAYS_EAGER = True

# Now tasks execute synchronously (blocks until complete)
```

## Production Deployment

### Quick Start

```bash
# 1. Install
pip install celery[redis] redis

# 2. Start Redis (as service)
sudo systemctl start redis

# 3. Start workers (as service)
sudo systemctl start celery-worker

# 4. Monitor
celery -A app.celery_app flower

# 5. View logs
journalctl -u celery-worker -f
```

### Systemd Service (Linux)

**File:** `/etc/systemd/system/celery-worker.service`
```ini
[Unit]
Description=Celery Worker
After=redis.service

[Service]
Type=forking
User=celery
Group=celery
Environment="CELERY_BROKER_URL=redis://localhost:6379/0"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/0"
ExecStart=/usr/local/bin/celery -A app.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker
```

## Integration with API

### Existing Endpoints Using Async

All these endpoints NOW return immediately with job_id:

- `POST /ts/optimizer/` - NSGA-II optimization
- `POST /ts/optimizer/ml-optimize` - ML optimization
- `POST /ts/digital_twin/train` - Model training
- `POST /ts/simulation/` - SPICE simulation

### Status Checking

- `GET /status/task/{job_id}/status` - Current status
- `GET /status/task/{job_id}/result` - Get result (if ready)
- `GET /status/tasks/queue/status` - Queue health

### Error Handling

```python
# If Redis/Celery not available
GET /ts/optimizer/
Response: 503 Service Unavailable
Detail: "Celery is required for optimization execution"

# If task fails
GET /status/task/{job_id}/status
Response:
{
    "status": "failure",
    "successful": false,
    "error": "NSGA-II optimization failed: population size must be > 2"
}
```

## Scaling

### Vertical Scaling (Single Machine)
```bash
# Increase worker concurrency
celery -A app.celery_app worker --concurrency=16

# Increase Redis memory
redis-server --maxmemory 2gb
```

### Horizontal Scaling (Multiple Machines)

```bash
# Machine 1: Redis + API
redis-server
python -m uvicorn app.main:app

# Machine 2: Worker
celery -A app.celery_app worker

# Machine 3: Worker
celery -A app.celery_app worker

# Machines point to same Redis broker
CELERY_BROKER_URL=redis://redis-host:6379/0
```

## Monitoring & Alerting

### Metrics to Track

1. **Queue Depth:** Number of pending tasks
2. **Worker Health:** Active/idle workers
3. **Task Duration:** Time to complete tasks
4. **Error Rate:** Failed vs. successful tasks
5. **Redis Memory:** Broker/backend memory usage

### Sample Monitoring Query

```python
from celery_app import celery_app

# Get stats
stats = celery_app.control.inspect().stats()
active = celery_app.control.inspect().active()

print(f"Workers: {len(stats)}")
print(f"Active tasks: {sum(len(t) for t in active.values())}")
```

## FAQ

**Q: How long do results persist?**
A: By default 24 hours. Change in `celery_app.py`: `result_expires=86400`

**Q: Can I cancel a running task?**
A: Yes, if not already executing:
```bash
curl -X POST /status/task/{job_id}/cancel
```

**Q: What if Redis goes down?**
A: Tasks will be lost if not yet processed. Use `broker_connection_retry_on_startup=True` to reconnect.

**Q: Can I have multiple queues?**
A: Yes! Use `--queues` to assign workers to specific queues.

**Q: How do I debug a failing task?**
A: Check logs in Flower or worker console. Set `--loglevel=debug` for verbose output.

---

**Last Updated:** April 13, 2026
**Status:** ✅ Production Ready
**Version:** 1.0
