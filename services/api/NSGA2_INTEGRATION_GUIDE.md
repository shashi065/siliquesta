# NSGA-II Integration Guide

Complete integration guide for the NSGA-II multi-objective optimizer with the SILIQUESTA platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ ML Prediction│  │ Simulation   │  │ NSGA-II Optimizer│  │
│  │   Model      │  │   Engine     │  │   (NEW)          │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                  │                    │             │
│         └──────────────────┼────────────────────┘             │
│                            ▼                                  │
│                 ┌──────────────────────┐                      │
│                 │ Performance Predictor│                      │
│                 │  (Hybrid ML + Physics)                      │
│                 └──────────────────────┘                      │
│                            │                                  │
│         ┌──────────────────┼──────────────────┐               │
│         ▼                  ▼                  ▼               │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────┐   │
│  │ /api/v1/   │  │ /api/v1/    │  │ /api/v1/nsga2/     │   │
│  │ predict    │  │ simulate    │  │ optimize (NEW)     │   │
│  │ (ML)       │  │             │  │ compare (NEW)      │   │
│  │            │  │             │  │ health (NEW)       │   │
│  │            │  │             │  │ info (NEW)         │   │
│  └────────────┘  └─────────────┘  └────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
   [ML Model]                          [Optimization]
   XGBoost                             Results
   Predictions                         Pareto Front
```

## Component Breakdown

### 1. NSGA-II Optimizer Module
**File:** `services/api/app/nsga2_optimizer.py` (500+ lines)

**Key Classes:**
- `CircuitParameters`: Input parameters (WN, WP, VDD)
- `CircuitPerformance`: Performance metrics (frequency, power, delay, efficiency)
- `ParetoSolution`: Single solution with rank
- `OptimizationMetrics`: Convergence and quality metrics

**Key Classes:**
- `PerformancePredictor`: Dual-mode prediction (ML + equations)
- `NSGAII_Optimizer`: Core evolutionary algorithm

### 2. API Routes Module
**File:** `services/api/app/api/nsga2_routes.py` (400+ lines)

**Endpoints:**
- `POST /api/v1/nsga2/optimize` - Run optimization
- `GET /api/v1/nsga2/health` - Health check
- `POST /api/v1/nsga2/compare` - Compare designs
- `GET /api/v1/nsga2/info` - Optimizer info

### 3. FastAPI Integration
**File:** `services/api/app/main.py` (modified)

**Changes:**
```python
# Import
from app.api import ... nsga2_routes ...

# Register route
router.include_router(nsga2_routes.router, tags=["NSGA-II Optimization"])
```

### 4. Dependencies
**File:** `services/api/requirements.txt` (modified)

**Addition:**
```
deap==1.4.1  # NSGA-II evolutionary algorithm
```

---

## Data Flow

### Optimization Flow

```
1. User Request
   └─ POST /api/v1/nsga2/optimize
      ├─ population_size: 50
      ├─ generations: 30
      ├─ use_ml: false
      └─ seed: 42
            │
            ▼
2. Route Handler (nsga2_routes.py)
   └─ validate request
      └─ call run_optimization()
            │
            ▼
3. NSGA-II Optimizer (nsga2_optimizer.py)
   ├─ initialize population
   ├─ evaluate fitness (30 generations × 50 population)
   │   ├─ generate random parameters
   │   │   (WN: 0.5-10, WP: 0.5-10, VDD: 1-5)
   │   └─ predict performance
   │       (via PerformancePredictor)
   ├─ apply genetic operators
   │   ├─ crossover: blend parameters
   │   ├─ mutation: add Gaussian noise
   │   └─ selection: NSGA-II sorting
   └─ extract Pareto front (non-dominated solutions)
            │
            ▼
4. Metrics Computation
   ├─ hypervolume (optimization quality)
   ├─ spread (solution diversity)
   ├─ execution time
   └─ convergence statistics
            │
            ▼
5. Response Construction
   ├─ Pareto front (15-30 solutions typically)
   ├─ Best power design
   ├─ Best frequency design
   ├─ Best efficiency design
   └─ Metrics
            │
            ▼
6. User Response
   └─ JSON with complete optimization results
```

### Performance Prediction Flow

```
User provides circuit parameters
(WN, WP, VDD)
      │
      ▼
PerformancePredictor.predict()
      │
      ├─────────────┬─────────────┐
      │             │             │
      ▼             ▼             ▼
  use_ml=True   use_ml=False   [Fallback]
      │             │             │
      ▼             ▼             ▼
  ML Model    Physics Eq.    Physics Eq.
  (XGBoost)   (Available)     (Default)
      │             │             │
      └─────────────┴─────────────┘
              │
              ▼
    CircuitPerformance
    ├─ frequency (GHz)
    ├─ power (mW)
    ├─ delay (ns)
    └─ efficiency (GHz/mW)
```

---

## Integration Points

### 1. With ML Prediction API ✓

The optimizer can use predictions from `/api/v1/predict`:

```python
# In nsga2_optimizer.py
class PerformancePredictor:
    def predict(self, params: CircuitParameters):
        if self.use_ml:
            # Use XGBoost model
            return self.model.predict(params)
        else:
            # Use physics equations
            return self._predict_with_equations(params)
```

**Integration achieved:** ✅
- Both endpoints can coexist
- ML model is optional
- Equations provide fallback

### 2. With CMOS Simulation ✓

Uses same parameter space:

```
Simulation Engine        NSGA-II Optimizer
─────────────────        ─────────────────
WN: 0.5-10 µm      ↔     WN: 0.5-10 µm
WP: 0.5-10 µm      ↔     WP: 0.5-10 µm
VDD: 1.0-5.0 V     ↔     VDD: 1.0-5.0 V
```

**Integration potential:** Can chain simulations with optimization

### 3. With Existing API Routes ✓

New endpoints don't conflict:
- `/api/v1/predict` - Single design prediction (ML)
- `/api/v1/simulate` - Single design simulation
- `/api/v1/optimize` - Old optimizer (single-objective ADA)
- `/api/v1/nsga2/*` - New NSGA-II (multi-objective) ← NEW

**Benefits:**
- Both optimizers coexist
- Users choose optimal tool
- No backward compatibility issues

---

## Usage Patterns

### Pattern 1: Development/Testing

Minimal configuration:

```bash
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json"
```

Uses defaults: pop=50, gen=30, no ML

### Pattern 2: Production Optimization

Tuned for quality:

```python
requests.post(
    "http://localhost:8000/api/v1/nsga2/optimize",
    json={
        "population_size": 100,
        "generations": 50,
        "use_ml": True,
        "seed": None
    }
)
```

### Pattern 3: Batch Analysis

Compare multiple designs:

```python
designs = [
    {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
    {"wn": 5.0, "wp": 8.0, "vdd": 3.5},
    {"wn": 7.5, "wp": 9.0, "vdd": 4.2},
]

for design in designs:
    response = requests.post(
        "http://localhost:8000/api/v1/nsga2/compare",
        json={
            "design1": design,
            "design2": designs[0]  # Compare to baseline
        }
    )
```

### Pattern 4: Monitoring

Check optimizer availability:

```python
health = requests.get("http://localhost:8000/api/v1/nsga2/health").json()
if health["nsga2_available"]:
    # Run optimization
else:
    # Fall back to single-objective
```

---

## Configuration

### Environment Variables

None currently required. Optional:

```bash
# Enable ML model (if set up)
USE_ML_MODEL=true

# Parallel evaluation (future enhancement)
NSGA2_WORKERS=4

# Random seed for reproducibility
NSGA2_SEED=42
```

### Runtime Parameters

Controlled via API request:

```json
{
  "population_size": 50,    // 10-1000
  "generations": 30,         // 5-500
  "use_ml": false,           // true/false
  "seed": 42                 // any positive int
}
```

---

## Performance Characteristics

### Execution Time

| Config | Time | Quality | Notes |
|--------|------|---------|-------|
| pop=30, gen=10 | 3-5s | Low | Testing |
| pop=50, gen=30 | 10-15s | Good | Default |
| pop=100, gen=50 | 30-60s | Very Good | Production |
| pop=200, gen=100 | 2-5m | Excellent | Heavy |

### Memory Usage

```
Population Size × Individuals × Data per Individual
= 50 × 50 × ~1KB
≈ 2.5 MB (modest)

Typical: 10-100 MB depending on population
```

### Scalability

- **Horizontal:** Multiple API instances (load balanced)
- **Vertical:** Increase population for better solutions
- **Temporal:** Longer runs converge to better Pareto fronts

---

## Error Handling

### Missing DEAP Library

```json
// Response: 503 Service Unavailable
{
  "detail": "NSGA-II optimizer not available. Install DEAP: pip install deap"
}
```

**Fix:**
```bash
pip install deap==1.4.1
```

### Invalid Parameters

```json
// Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "population_size"],
      "msg": "ensure this value is greater than or equal to 10",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Fix:** Ensure population_size ∈ [10, 1000]

### Optimization Timeout

```json
// Response: 504 Gateway Timeout (if API gateway timeout < optimization time)
{
  "detail": "Request timeout"
}
```

**Fix:** Increase HTTP timeout or reduce generations

---

## Testing

### Automated Tests

Run comprehensive test suite:

```bash
chmod +x test_nsga2_api.py
python test_nsga2_api.py
```

Tests: health check, info, basic optimization, large optimization, comparison, multiple runs, edge cases

### Manual Testing

Via cURL:

```bash
# Health check
curl http://localhost:8000/api/v1/nsga2/health

# Optimizer info
curl http://localhost:8000/api/v1/nsga2/info

# Quick optimization
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json" \
  -d '{"population_size": 30, "generations": 10}'

# Design comparison
curl -X POST http://localhost:8000/api/v1/nsga2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "design1": {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
    "design2": {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
  }'
```

---

## Deployment

### Development

```bash
# 1. Install dependencies
pip install fastapi uvicorn deap numpy xgboost pydantic

# 2. Run API server
cd services/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Test endpoints
python test_nsga2_api.py
```

### Production

```bash
# Using Docker (ensure deap in requirements.txt)
docker build -t siliquesta-api .
docker run -p 8000:8000 siliquesta-api

# Using uvicorn with workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: siliquesta-api
spec:
  ports:
  - port: 8000
    name: nsga2-optimizer
  selector:
    app: siliquesta-api
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: siliquesta-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: siliquesta-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: USE_ML_MODEL
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

---

## Monitoring & Observability

### Metrics Collected

Each optimization run provides:
- Execution time
- Pareto front size
- Hypervolume (quality)
- Spread (diversity)
- Convergence rate

### Health Monitoring

```bash
# Via health endpoint
curl http://localhost:8000/api/v1/nsga2/health

# Expected response
{
  "status": "healthy",
  "nsga2_available": true,
  "deap_requirement": "deap>=1.4.1",
  "timestamp": "2024-12-19T10:30:45.123Z"
}
```

### Logging

Check API logs:

```bash
# Docker logs
docker logs siliquesta-api

# File logs (if configured)
tail -f logs/siliquesta-api.log
```

---

## Future Enhancements

### Phase 2

- [ ] Persistent optimization history (PostgreSQL)
- [ ] Batch optimization jobs (Celery workers)
- [ ] Real-time progress streaming (WebSocket)
- [ ] Visualization endpoint (Pareto front plots)

### Phase 3

- [ ] Multi-objective constraint handling
- [ ] Advanced fitness weighted aggregation
- [ ] Surrogate model integration (Gaussian Process)
- [ ] Parallel population evaluation

### Phase 4

- [ ] Hardware acceleration (GPU-based evaluation)
- [ ] Custom genetic operators
- [ ] Interactive Pareto front explorer (3D visualization)
- [ ] Export to CAD tools (GDS, LEF/DEF)

---

## References

### External Documentation

- **DEAP Documentation:** https://deap.readthedocs.io/
- **NSGA-II Paper:** Deb et al. (2002) - "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"
- **FastAPI:** https://fastapi.tiangolo.com/

### Internal Documentation

- [NSGA2_API_DOCUMENTATION.md](NSGA2_API_DOCUMENTATION.md) - API endpoint details
- [ML_API_REFERENCE.md](ML_API_REFERENCE.md) - ML prediction integration
- [README.md](README.md) - General backend setup

---

## Changelog

### v1.0.0 (2024-12-19)

- ✅ NSGA-II optimizer core implementation
- ✅ Multi-objective fitness (power, frequency)
- ✅ Pareto front extraction
- ✅ FastAPI route wrapper
- ✅ Comprehensive documentation
- ✅ Test suite
- ✅ Health checks and monitoring

---

## Support

For issues or questions:

1. Check health endpoint: `/api/v1/nsga2/health`
2. Review API documentation: [NSGA2_API_DOCUMENTATION.md](NSGA2_API_DOCUMENTATION.md)
3. Run test suite: `python test_nsga2_api.py`
4. Check logs: `docker logs <container>` or `/logs/siliquesta-api.log`

---

**Document Version:** 1.0.0
**Last Updated:** 2024-12-19
**Status:** ✅ Complete and Production-Ready
