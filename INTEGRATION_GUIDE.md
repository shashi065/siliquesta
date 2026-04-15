# SILIQUESTA End-to-End Integration Guide

## Overview

This document describes how all components of the SILIQUESTA system integrate together:
- Frontend (React/Next.js)
- Backend API (FastAPI)
- Job Queue (Celery + Redis)
- Database (SQLAlchemy)
- ML Services (XGBoost + PyTorch)

## System Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React/Next)   │
│   Port 3000     │
└────────┬────────┘
         │ HTTP/HTTPS
         │ JWT Bearer Token
         ↓
┌─────────────────┐         ┌─────────────┐
│   FastAPI       │◄────────┤   Database  │
│   Backend       │  ORM    │ PostgreSQL  │
│   Port 8000     │◄────────┤   / SQLite  │
└────────┬────────┘         └─────────────┘
         │
    ┌────┴────┐
    │          │
    ↓          ↓
┌────────┐  ┌──────────┐
│ Celery │  │   Redis  │
│ Tasks  │  │  Broker  │
└────────┘  └──────────┘
    │           ↑
    └───────┬───┘
        ┌───┴───┐
        │       │
        ↓       ↓
    ┌────────────────┐
    │  ML Services   │
    │ (XGBoost, etc) │
    └────────────────┘
```

## Data Flow: Complete User Journey

### 1. Authentication Flow
```
User Login
    ↓
POST /auth/login (email, password)
    ↓
Backend: Verify credentials → Generate JWT
    ↓
API returns: { access_token, token_type: "bearer" }
    ↓
Frontend: Store token in localStorage
    ↓
All subsequent requests include:
  Authorization: Bearer <token>
```

### 2. Project Management Flow
```
Frontend: User creates new project
    ↓
POST /projects (name, description, tags)
    ↓
Backend: Create project record in database
    ↓
API returns: { id, slug, name, description, created_at, ... }
    ↓
Frontend: Store project ID
    ↓
User saves design within project
    ↓
POST /projects/{id}/save-design (design_state_json)
    ↓
Backend: Update project.design_state_json
    ↓
API returns: { success, updated_at }
    ↓
Design is now persisted and can be retrieved later
```

### 3. Simulation Execution Flow
```
Frontend: User clicks "Run Simulation"
    ↓
POST /simulate (wn, wp, vdd, temp, cl_ff, corner, tech_node)
    ↓
Backend: Validate parameters
    ↓
Backend: Create ComputeJob record in database
    ↓
Backend: Submit Celery task "siliquesta.run_spice_simulation"
    ↓
API returns: { job_id, status: "queued" }
    ↓
Frontend: Start polling job status (every 1.2 seconds)
    │
    ├─→ GET /jobs/{job_id}
    │      or
    └─→ GET /results/{job_id}
    ↓
Backend: Check Celery task status
    ↓
When task completes:
    ├─→ Store results in ComputeJob.results_json
    ├─→ Update status to "completed"
    └─→ Return results to frontend
    ↓
Frontend: Display results
    (freq, delay, power, timing, energy metrics, etc.)
```

### 4. ML Optimization Execution Flow
```
Frontend: User clicks "ML Optimize"
    ↓
POST /optimize/ml-optimize (
    wp, vdd, temp, cl_ff, tech_node,
    [objective], [constraints], [baseline_metrics]
)
    ↓
Backend: Validate parameters
    ↓
Backend: Create ComputeJob record
    ↓
Backend: Load trained ML model (XGBoost + PyTorch)
    ↓
Backend: Submit Celery task "siliquesta.run_ml_optimizer"
    ↓
API returns: { job_id, status: "queued" }
    ↓
Celery Task Execution:
    1. Load ML model from disk
    2. Generate parameter candidates
    3. Use model to predict metrics for each candidate
    4. Score candidates against objective + constraints
    5. Select top-N candidates
    6. (Optional) Run SPICE on best candidates to verify
    7. Store results with confidence scores
    ↓
Frontend: Poll /jobs/{job_id}
    ↓
Frontend: When complete, display:
    - optimized_params (Wn, Wp, VDD, temp adjustments)
    - predicted_metrics (frequency, power, delay)
    - confidence_score (0-1, reliability of predictions)
    - improvement_percent (vs baseline)
    - comparison_table (baseline vs optimized)
```

## API Endpoints Summary

### Authentication
- `POST /auth/login` - Login with email/password → JWT token
- `POST /auth/signup` - Create new user account
- `GET /users/me` - Get current user profile

### Projects (NEW - CRUD)
- `POST /projects` - Create project
- `GET /projects` - List all projects
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/save-design` - Save design state
- `GET /projects/{id}/design-state` - Retrieve design state

### Simulation
- `POST /simulate` - Run single simulation
- `POST /simulate/sweep` - Run parameter sweep
- `POST /simulate/batch` - Run batch simulations

### Optimization
- `POST /optimize` - Traditional ADA optimizer
- `POST /optimize/ml-optimize` - ML-powered optimization (NEW)
- `POST /optimize/predict` - Quick ML prediction (NEW)

### Job Management
- `GET /jobs/{job_id}` - Get Celery task status
- `GET /results/{job_id}` - Get job results from database

### Other Services
- `POST /pvt/corner-summary` - PVT analysis
- `POST /twin/compute-aging` - Digital twin aging simulation
- `POST /ai/chat` - AI chatbot
- `POST /ai/generate-code` - AI code generation

## Response Format Standardization

### Job Submission Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "success": true,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Job Status Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "result": { ... },
  "error": null,
  "timestamp": "2024-01-15T10:35:45.123456",
  "completed_at": "2024-01-15T10:35:40.123456"
}
```

### Simulation Results
```json
{
  "freq": 1250.5,          // MHz
  "delay": 0.45,           // ns
  "dynamic_power": 2.3,    // mW
  "static_power": 0.1,     // mW
  "total_power": 2.4,      // mW
  "power_delay_product": 1.08,
  "corner": "tt",
  "vdd": 1.2,
  "temp": 25,
  "tech_node": 5,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Optimization Results
```json
{
  "optimized_params": {
    "wn": 12.5,
    "wp": 25.3,
    "vdd": 1.15
  },
  "predicted_metrics": {
    "freq": 1350.2,
    "delay": 0.40,
    "dynamic_power": 2.0,
    "static_power": 0.08
  },
  "confidence_score": 0.92,
  "baseline_metrics": {
    "freq": 1250.5,
    "delay": 0.45,
    "dynamic_power": 2.3
  },
  "improvement_percent": 8.0,
  "algorithm": "ml",
  "iterations": 500,
  "execution_time_ms": 2345,
  "timestamp": "2024-01-15T10:35:45.123456"
}
```

## Frontend API Integration

### Using the API Client

```typescript
import { 
  projectsAPI, 
  simulationAPI, 
  optimizerAPI,
  projectsAPI 
} from '@/utils/api';

// 1. Create a project
const project = await projectsAPI.create({
  name: 'My Circuit',
  description: 'Optimization test',
  tags: ['test']
});
// Returns: { id: 1, slug: 'my-circuit', name: '...', ... }

// 2. Save design
await projectsAPI.saveDesign(project.id, {
  components: [...],
  parameters: { wn: 5, wp: 10 }
});

// 3. Run simulation
const simResults = await simulationAPI.run({
  wn: 5,
  wp: 10,
  vdd: 1.2,
  temp: 25,
  cl_ff: 1.0,
  corner: 'tt',
  tech_node: 5
});
// Returns: { freq, delay, power, ... }

// 4. Run ML optimization
const optResults = await optimizerAPI.run({
  wp: 10,
  vdd: 1.2,
  temp: 25,
  cl_ff: 1.0,
  tech_node: 5
});
// Returns: { optimized_params, predicted_metrics, confidence_score, ... }
```

### Error Handling

All API errors include proper HTTP status codes and error messages:

```typescript
try {
  await projectsAPI.create({ name: 'Test' });
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login - handled automatically by interceptor
  } else if (error.response?.status === 400) {
    // Validation error
    console.log(error.response.data.detail);
  } else if (error.response?.status === 500) {
    // Server error
    console.log('Server error');
  }
}
```

## Database Integration

### Key Tables

**users**
- id, email, password_hash, full_name, created_at

**projects**
- id, user_id, slug, name, description, tags_json, design_state_json, created_at, updated_at

**compute_jobs**
- id, user_id, job_key (Celery task ID), backend_task_id, compute_type, input_params_json, results_json, status, error_message, created_at, completed_at

**design_dna_records**
- id, project_id, metrics_json, timestamp

### Async/ORM Integration

All database operations use SQLAlchemy async:

```python
from app.database import get_db
from app.models import Project

@app.get("/projects/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    # Async query
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    return project
```

## Celery Task Integration

### Tasks in `backend/app/tasks/compute.py`

```python
@celery_app.task(name='siliquesta.run_spice_simulation')
def run_spice_simulation(params: dict) -> dict:
    """Execute SPICE simulation"""
    # 1. Validate parameters
    # 2. Generate netlist
    # 3. Run ngspice
    # 4. Parse results
    # 5. Return: { freq, delay, power, ... }
    return results

@celery_app.task(name='siliquesta.run_ml_optimizer')
def run_ml_optimizer(params: dict) -> dict:
    """Run ML-powered optimization"""
    # 1. Load ML model
    # 2. Generate candidates
    # 3. Predict metrics
    # 4. Score and rank
    # 5. Return: { optimized_params, predictions, confidence, ... }
    return results
```

### Backend Task Submission

```python
from app.celery_app import celery_app

# Submit simulation task
task = celery_app.send_task(
    'siliquesta.run_spice_simulation',
    args=(params,),
    task_id=job_key
)

# Check status
status = task.status  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'
result = task.result   # Task result dict or exception

# Store in database
job.backend_task_id = task.id
job.results_json = result
job.status = 'completed'
await db.commit()
```

## Complete User Flow: "Save Design → Simulate → Optimize"

```
1. USER LOGS IN
   └─ POST /auth/login → Get JWT token

2. USER CREATES PROJECT
   └─ POST /projects → Project created
   └─ ID: 42, Name: "Inverter Design"

3. USER DRAWS CIRCUIT
   └─ State kept in React (not persisted yet)

4. USER SAVES DESIGN
   └─ POST /projects/42/save-design
   └─ design_state_json updated in DB

5. USER RUNS SIMULATION
   ├─ POST /simulate with Wn=5, Wp=10
   ├─ Backend creates ComputeJob
   ├─ Celery task queued
   ├─ API returns job_id = "abc123"
   ├─ Frontend polls GET /jobs/abc123
   │  Stats: queued → started → running → completed
   ├─ Results retrieved
   └─ Frontend displays: Freq=1.25GHz, Delay=0.45ns, Power=2.4mW

6. USER CLICKS "OPTIMIZE WITH AI"
   ├─ POST /optimize/ml-optimize with same Wn, Wp
   ├─ Backend loads XGBoost model
   ├─ Predicts 500 candidates in 2.3 seconds
   ├─ ML returns job_id = "def456"
   ├─ Frontend polls GET /jobs/def456
   ├─ Results retrieved
   └─ Frontend displays:
      - New Wn: 12.5 (+150%)
      - New Wp: 25.3 (+153%)
      - Predicted Freq: 1.35GHz (+8%)
      - Predicted Power: 2.0mW (-17%)
      - Confidence: 92%

7. USER UPDATES DESIGN WITH OPTIMIZED PARAMS
   └─ POST /projects/42/save-design with updated design_state

8. USER RUNS VERIFICATION SIMULATION
   └─ POST /simulate with Wn=12.5, Wp=25.3
   └─ Actual results match predictions within 2%
```

## Integration Testing

Run end-to-end tests:

```bash
# From backend directory
pytest tests/test_e2e_integration.py -v

# Test specific flow
pytest tests/test_e2e_integration.py::TestEndToEndFlows::test_save_and_simulate_flow -v
```

## Performance Considerations

### Frontend → Backend
- JWT tokens cached in localStorage (1 hour)
- JSON responses compressed automatically
- Job polling: 1.2 second intervals, 120 second timeout

### Backend → Database
- Async SQLAlchemy for non-blocking I/O
- Connection pooling (10 connections by default)
- Indexes on user_id, job_key, created_at

### Backend → Celery
- Redis broker in-memory caching
- Tasks timeout after 3600 seconds
- Failures automatically retry (up to 3 times)

### ML Model
- Model loaded once on startup (cached in memory)
- Prediction on single candidate: ~5ms
- Prediction on 500 candidates: ~2-3 seconds

## Deployment Checklist

- [ ] Database migrations run (if using PostgreSQL)
- [ ] Redis server started and accessible
- [ ] Celery workers started (`celery -A app.celery_app worker`)
- [ ] Backend API running on port 8000 (or configured port)
- [ ] Frontend built and running on port 3000
- [ ] JWT_SECRET_KEY configured
- [ ] CORS origins configured for production domains
- [ ] ML models downloaded and cached
- [ ] Health checks passing: `GET /health`
- [ ] Monitoring dashboards connected
- [ ] Error logging configured (Sentry, etc.)

## Troubleshooting

### Frontend can't reach backend
- Check CORS configuration in main.py
- Verify origins list includes frontend URL
- Check firewall/network rules

### Jobs stuck in "queued"
- Check Redis is running: `redis-cli ping`
- Check Celery workers are running
- Check Celery logs for errors

### ML predictions are wrong
- Check ML model file exists: `ai-engine/models/digital_twin_model.py`
- Verify training data was loaded correctly
- Check model accuracy on test set

### Authentication failing
- Verify JWT_SECRET_KEY is set consistently
- Check token expiration (default 30 minutes)
- Verify token is sent in Authorization header

## Next Steps

1. **Test the integration** - Run integration tests to verify all endpoints work
2. **Load testing** - Test with concurrent users and jobs
3. **Production deployment** - Deploy to staging/production environment
4. **Monitoring setup** - Configure logs, metrics, alerts
5. **Documentation** - User guide, API documentation, deployment guide

## Support & Issues

For issues or questions:
1. Check `/health` endpoint for system status
2. Review logs in `backend/app/` directory
3. Check Celery worker logs
4. Review database schema with `SELECT * FROM compute_jobs LIMIT 10;`
