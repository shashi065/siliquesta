# Cloud Execution Quick Start

**Setup & Usage in 10 Minutes**

---

## What You Get

✅ **Async Jobs** - Submit jobs, get instant response  
✅ **Parallel Processing** - 4-100 concurrent simulations  
✅ **Smart Caching** - Skip redundant calculations  
✅ **User Isolation** - Multi-tenant support  
✅ **Automatic Scaling** - Add workers as needed  

---

## Step 1: Start Redis (2 minutes)

**Option A: Docker (Recommended)**

```bash
docker run -d -p 6379:6379 redis:latest
```

**Option B: Local Redis**

```bash
# Macintosh
brew install redis
redis-server

# Ubuntu
sudo apt install redis-server
redis-server

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
redis-server.exe
```

**Option C: Skip Redis (Uses in-memory queue)**

```bash
# System automatically fallback to in-memory queue
# (Less persistent, but works for development)
```

---

## Step 2: Start Backend (2 minutes)

Terminal 1 - FastAPI Server:

```bash
cd backend

# Install if needed (already done)
# pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Job Worker:

```bash
cd backend

# Create and run worker script
python -c "
import asyncio
import logging
from app.services.job_worker import get_job_worker

logging.basicConfig(level=logging.INFO)
async def main():
    worker = get_job_worker(num_workers=4)
    await worker.start()

asyncio.run(main())
"
```

Or create `backend/scripts/start_worker.py`:

```python
#!/usr/bin/env python3
"""Start job worker process."""

import asyncio
import logging
from app.services.job_worker import get_job_worker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting SILIQUESTA Job Worker (4 parallel workers)")
    worker = get_job_worker(num_workers=4)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python backend/scripts/start_worker.py
```

---

## Step 3: Test Single Job (2 minutes)

```bash
# Submit a job
curl -X POST http://localhost:8000/api/v1/jobs/enqueue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "job_type": "simulate",
    "params": {
      "wn": 500,
      "wp": 1000,
      "vdd": 1.2,
      "cl": 1e-12,
      "temp": 27
    },
    "priority": "normal"
  }' | jq .

# Response (202 Accepted)
# {
#   "job_id": "job_abc123def456",
#   "status": "queued",
#   "created_at": "now",
#   "message": "Job queued. Poll GET /jobs/job_abc123def456 for status"
# }
```

Check job status:

```bash
# Replace with actual job_id from above
JOB_ID="job_abc123def456"

# Check status (keep running until completed)
watch -n 2 "curl -s http://localhost:8000/api/v1/jobs/$JOB_ID \
  -H 'Authorization: Bearer YOUR_TOKEN' | jq ."

# Or manually
curl http://localhost:8000/api/v1/jobs/$JOB_ID \
  -H "Authorization: Bearer YOUR_TOKEN" | jq .
```

Expected progression:

```
# Status 1: Queued
{
  "job_id": "job_abc123",
  "status": "queued",
  "progress_percent": 0
}

# Status 2: Running
{
  "job_id": "job_abc123",
  "status": "running",
  "started_at": "2024-04-12T10:30:45",
  "progress_percent": 50
}

# Status 3: Completed
{
  "job_id": "job_abc123",
  "status": "completed",
  "finished_at": "2024-04-12T10:30:52",
  "progress_percent": 100,
  "result": {
    "frequency": 2.45,
    "delay": 145.3,
    "power": 0.78,
    ...
  }
}
```

---

## Step 4: Batch Job (Parameter Sweep)

Submit 10 jobs at once:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/batch-enqueue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "jobs": [
      {"job_type": "simulate", "params": {"wn": 300, "wp": 600, ...}, "priority": "normal"},
      {"job_type": "simulate", "params": {"wn": 400, "wp": 800, ...}, "priority": "normal"},
      {"job_type": "simulate", "params": {"wn": 500, "wp": 1000, ...}, "priority": "normal"},
      {"job_type": "simulate", "params": {"wn": 600, "wp": 1200, ...}, "priority": "normal"},
      {"job_type": "simulate", "params": {"wn": 700, "wp": 1400, ...}, "priority": "high"}
    ]
  }' | jq .
```

Response:

```json
{
  "total_requested": 5,
  "enqueued": 5,
  "failed": 0,
  "job_ids": [
    "job_abc123",
    "job_def456",
    "job_ghi789",
    "job_jkl012",
    "job_mno345"
  ],
  "message": "Submitted 5 jobs to queue"
}
```

---

## Step 5: Monitor Queue

Check current queue status:

```bash
curl http://localhost:8000/api/v1/queue/stats \
  -H "Authorization: Bearer YOUR_TOKEN" | jq .
```

Response:

```json
{
  "total_jobs": 8,
  "queued": 3,
  "running": 2,
  "completed": 3,
  "failed": 0,
  "estimated_wait_minutes": 1.5
}
```

Interpret results:

```
queued: 3              → 3 jobs waiting to run
running: 2            → 2 jobs currently executing
estimated_wait_minutes: 1.5  → New job will start in ~1.5 min
                             (3 queued ÷ 4 workers × 5 sec/job ÷ 60)
```

---

## Step 6: Python API Usage

```python
import requests
import time
import json

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Submit a job
response = requests.post(
    f"{API_URL}/jobs/enqueue",
    json={
        "job_type": "simulate",
        "params": {
            "wn": 500,
            "wp": 1000,
            "vdd": 1.2,
            "cl": 1e-12,
            "temp": 27,
            "tech_node": 7.0,
            "corner": "TT"
        },
        "priority": "normal"
    },
    headers=headers
)

job_id = response.json()["job_id"]
print(f"📤 Submitted job: {job_id}")

# Poll for completion
while True:
    status_resp = requests.get(
        f"{API_URL}/jobs/{job_id}",
        headers=headers
    )
    
    status = status_resp.json()
    print(f"Status: {status['status']} ({status.get('progress_percent', 0)}%)")
    
    if status["status"] == "completed":
        print(f"✅ Result: {json.dumps(status['result'], indent=2)}")
        break
    elif status["status"] == "failed":
        print(f"❌ Error: {status['error']}")
        break
    
    time.sleep(2)
```

---

## Step 7: Parameter Sweep (Batch)

```python
import requests

# Generate parameter sweep
params_sweep = [
    {"wn": wn, "wp": wn*2, "vdd": vdd, "cl": 1e-12}
    for wn in range(200, 1000, 100)
    for vdd in [1.0, 1.2, 1.5]
]

print(f"Sweeping {len(params_sweep)} parameter combinations...")

# Submit all at once
response = requests.post(
    f"{API_URL}/jobs/batch-enqueue",
    json={"jobs": [
        {"job_type": "simulate", "params": p, "priority": "normal"}
        for p in params_sweep
    ]},
    headers=headers
)

job_ids = response.json()["job_ids"]
print(f"📤 Submitted {len(job_ids)} jobs")

# Collect results
results = {}

for job_id in job_ids:
    while True:
        status = requests.get(
            f"{API_URL}/jobs/{job_id}",
            headers=headers
        ).json()
        
        if status["status"] in ["completed", "failed"]:
            results[job_id] = status
            break
        
        time.sleep(1)

# Analyze
successful = sum(1 for r in results.values() if r["status"] == "completed")
print(f"✅ {successful}/{len(job_ids)} completed successfully")

# Find best design
if successful > 0:
    best = max(
        [r for r in results.values() if r["status"] == "completed"],
        key=lambda r: r["result"]["frequency"]
    )
    print(f"🏆 Best (highest freq): {best['result']['frequency']} GHz")
```

---

## Cheatsheet

### Submit Jobs

```bash
# Single job
curl -X POST /jobs/enqueue \
  -d '{"job_type": "simulate", "params": {...}}'

# Batch (10 jobs)
curl -X POST /jobs/batch-enqueue \
  -d '{"jobs": [...]}'
```

### Check Status

```bash
# Single job
curl GET /jobs/{job_id}

# Queue depth
curl GET /queue/stats

# Worker health (admin)
curl GET /worker/stats
```

### Job Priorities

```
"priority": "urgent"   # Run first (0 wait)
"priority": "high"     # Run soon (< 1 min)
"priority": "normal"   # Normal queue (default)
"priority": "low"      # Run when idle
```

### Job Statuses

```
"queued"    → Waiting for worker
"running"   → Currently executing
"completed" → Done, check result
"failed"    → Error, check error field
"cancelled" → User cancelled it
```

### Response Status Codes

```
202 Accepted       → Job submitted (async)
200 OK            → Got status or queue stats
400 Bad Request   → Invalid parameters
401 Unauthorized  → Missing/invalid token
403 Forbidden     → Permission denied
404 Not Found     → Job doesn't exist
500 Server Error  → Internal error
```

---

## Common Workflows

### Workflow 1: Quick Simulation

```
1. POST /jobs/enqueue
   └─ Get job_id
   
2. GET /jobs/{job_id} (poll)
   └─ Wait for status="completed"
   
3. Extract result → Done!
```

**Time:** 5-10 seconds

### Workflow 2: Parameter Sweep

```
1. POST /jobs/batch-enqueue (100 jobs)
   └─ Get job_ids[]
   
2. GET /queue/stats
   └─ See estimated wait time
   
3. GET /jobs/{job_id} (poll all)
   └─ Collect results
   
4. Analyze all results → Done!
```

**Time:** 5 minutes (100 jobs ÷ 4 workers)

### Workflow 3: Real-Time Optimization

```
1. User adjusts parameters (frontend)
   
2. Auto-submit job (background)
   └─ Job queued immediately
   
3. Show queue status
   └─ "Your job is #5 in queue"
   
4. As results arrive
   └─ Update UI with findings
   
5. Cache hits for similar params → Instant!
```

---

## Troubleshooting

### Jobs not executing?

```bash
# Check worker is running
ps aux | grep "start_worker"

# Restart worker
python backend/scripts/start_worker.py

# Check Redis
redis-cli ping
# Should show: PONG
```

### Queue stuck?

```bash
# Check queue stats
curl /queue/stats | jq .

# Force process 10 jobs sync
python backend/scripts/process_jobs.py --count 10

# Clear failed jobs
python -c "
from app.services.job_queue import get_job_queue
queue = get_job_queue()
# Manual inspection needed
"
```

### Cache not working?

```bash
# Check cache stats
curl /worker/stats | jq '.cache_stats'

# Should show > 0 hits if cache working

# Manually test cache
python -c "
from app.services.cache import get_cache
cache = get_cache()
cache.set('test_key', {'data': 123})
assert cache.get('test_key') == {'data': 123}
print('✅ Cache working')
"
```

---

## Performance Tips

1. **Use batch-enqueue for sweeps** (not individual jobs)
2. **Set priority=high for urgent work**
3. **Monitor cache hit rate** (target: >50%)
4. **Scale workers as needed** (default: 4, can go to 20+)
5. **Keep Redis restarting** (auto-recovery on failure)

---

## Next Steps

- ✅ Try single job (Step 3)
- ✅ Try batch jobs (Step 4)
- ✅ Monitor queue (Step 5)
- 📖 Read full guide: `PHASE_4_CLOUD_UPGRADE.md`
- 🚀 Deploy to production with Docker

---

**Done!** 🎉 You now have async job processing with caching and parallel execution!
