# NSGA-II Quick Reference Card

Quick lookup guide for the NSGA-II multi-objective optimizer API.

---

## 🚀 Quick Start (30 seconds)

```bash
# Start API (from services/api)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test it
curl http://localhost:8000/api/v1/nsga2/health

# Run optimization
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json" \
  -d '{"population_size": 30, "generations": 10}'
```

---

## 📋 Endpoints at a Glance

### POST /api/v1/nsga2/optimize
**Run multi-objective optimization**

Request:
```json
{
  "population_size": 50,
  "generations": 30,
  "use_ml": false,
  "seed": 42
}
```

Response: `{ "status", "pareto_front", "metrics", "best_solutions" }`

---

### GET /api/v1/nsga2/health
**Check optimizer availability**

Response:
```json
{
  "status": "healthy",
  "nsga2_available": true,
  "deap_requirement": "deap>=1.4.1",
  "timestamp": "ISO8601"
}
```

---

### POST /api/v1/nsga2/compare
**Compare two circuit designs**

Request:
```json
{
  "design1": {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
  "design2": {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
}
```

Response: `{ "design1", "design2", "comparison" }`

---

### GET /api/v1/nsga2/info
**Get optimizer capabilities**

Response: `{ "name", "description", "objectives", "parameters", "algorithm", "outputs" }`

---

## 🔧 Parameters Reference

### Optimization Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `population_size` | int | 10-1000 | 50 | Individuals per generation |
| `generations` | int | 5-500 | 30 | Evolution cycles |
| `use_ml` | bool | - | false | Use ML prediction model |
| `seed` | int | ≥0 | 42 | Random seed (reproducibility) |

### Design Parameters

| Parameter | Type | Range | Unit | Description |
|-----------|------|-------|------|-------------|
| `wn` | float | 0.5-10.0 | µm | NMOS width |
| `wp` | float | 0.5-10.0 | µm | PMOS width |
| `vdd` | float | 1.0-5.0 | V | Supply voltage |

---

## 📊 Response Fields

### Pareto Front Solution
```
{
  "parameters": {
    "wn": 2.5,
    "wp": 5.0,
    "vdd": 2.8
  },
  "performance": {
    "frequency": 0.8,        // GHz
    "power": 15.2,            // mW
    "delay": 1.25,            // ns
    "efficiency": 0.0526      // GHz/mW
  },
  "rank": 1                   // Pareto rank
}
```

### Metrics
```
{
  "generations": 30,
  "population_size": 50,
  "execution_time": 12.34,           // seconds
  "pareto_front_size": 15,
  "hypervolume": 2850.5,             // quality metric
  "spread": 0.78,                    // diversity metric
  "timestamp": "ISO8601"
}
```

---

## 🐍 Python Examples

### Using REST API
```python
import requests

# Optimize
response = requests.post(
    "http://localhost:8000/api/v1/nsga2/optimize",
    json={"population_size": 50, "generations": 30}
)
result = response.json()

# Extract Pareto front
pareto = result["pareto_front"]
metrics = result["metrics"]
```

### Using Python Client
```python
from nsga2_client import NSGAIIClient

client = NSGAIIClient("http://localhost:8000")

# Optimize
result = client.optimize(population_size=50, generations=30)

# Access results
best_power = result.get_best_power_solution()
best_freq = result.get_best_frequency_solution()
```

### Direct Module Usage
```python
from app.nsga2_optimizer import run_optimization

pareto_front, metrics = run_optimization(
    population_size=50,
    generations=30,
    use_ml=False,
    seed=42
)
```

---

## ⏱️ Performance Guide

| Use Case | Population | Generations | Time |
|----------|-----------|------------|------|
| **Testing** | 30 | 10 | 3-5s |
| **Development** | 50 | 30 | 10-15s |
| **Production** | 100 | 50 | 30-60s |
| **Research** | 200 | 100 | 2-5m |

---

## 🧪 Testing

```bash
# Full test suite with colored output
python test_nsga2_api.py

# Test specific endpoint
curl http://localhost:8000/api/v1/nsga2/health
curl http://localhost:8000/api/v1/nsga2/info

# Run custom optimization
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json" \
  -d '{"population_size": 50, "generations": 30}'
```

---

## 🔍 Troubleshooting

### "NSGA-II optimizer not available" (503)
```bash
# Install DEAP
pip install deap==1.4.1

# Verify installation
python -c "import deap; print(deap.__version__)"
```

### "Invalid parameter value" (422)
Check parameter ranges:
- `population_size`: 10-1000
- `generations`: 5-500
- `wn`, `wp`: 0.5-10.0
- `vdd`: 1.0-5.0

### API not responding
```bash
# Check API health
curl http://localhost:8000/health

# Check NSGA-II specifically
curl http://localhost:8000/api/v1/nsga2/health

# Restart server
pkill -f uvicorn
python -m uvicorn app.main:app --port 8000
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `NSGA2_API_DOCUMENTATION.md` | Complete endpoint reference |
| `NSGA2_INTEGRATION_GUIDE.md` | Architecture & integration |
| `NSGA2_IMPLEMENTATION_SUMMARY.md` | Feature overview |
| `test_nsga2_api.py` | Automated test suite |
| `nsga2_client.py` | Python client library |
| `app/nsga2_optimizer.py` | Core implementation |
| `app/api/nsga2_routes.py` | FastAPI routes |

---

## 🎯 Common Tasks

### Run Basic Optimization
```bash
curl -X POST http://localhost:8000/api/v1/nsga2/optimize
```

### Run with Custom Parameters
```bash
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "population_size": 100,
    "generations": 50,
    "use_ml": true,
    "seed": 12345
  }'
```

### Compare Two Designs
```bash
curl -X POST http://localhost:8000/api/v1/nsga2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "design1": {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
    "design2": {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
  }'
```

### Get Optimizer Status
```bash
curl http://localhost:8000/api/v1/nsga2/info
curl http://localhost:8000/api/v1/nsga2/health
```

---

## 🔐 Security Notes

- ✅ All inputs validated via Pydantic
- ✅ CORS configured (adjust in `main.py` if needed)
- ✅ Rate limiting ready (configure as needed)
- ✅ Error messages sanitized
- ✅ No sensitive data in logs

---

## 📞 Support Chain

1. **Check health:** `/api/v1/nsga2/health`
2. **Review docs:** `NSGA2_API_DOCUMENTATION.md`
3. **Run tests:** `python test_nsga2_api.py`
4. **Check logs:** `docker logs <container>` or `tail -f logs/siliquesta-api.log`
5. **Review code:** `app/nsga2_optimizer.py` and `app/api/nsga2_routes.py`

---

## 🚀 Deployment Checklist

- [ ] `deap==1.4.1` in `requirements.txt`
- [ ] `nsga2_routes` imported in `main.py`
- [ ] Router registered in `main.py`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] API server started
- [ ] Health check passes: `/api/v1/nsga2/health`
- [ ] Optimization test passes: `/api/v1/nsga2/optimize` (POST)
- [ ] Comparison test passes: `/api/v1/nsga2/compare` (POST)

---

## 🔗 API Integration with Other Services

```
┌─────────────────────────────────────┐
│        SILIQUESTA Backend           │
├─────────────────────────────────────┤
│                                     │
│  /api/v1/predict ──────┐           │
│  (ML Model)            │           │
│                        ▼           │
│  /api/v1/nsga2/optimize            │
│  (Multi-Objective)                  │
│                        ▲           │
│  /api/v1/simulate ─────┘           │
│  (CMOS Simulation)                  │
│                                     │
└─────────────────────────────────────┘
```

---

## 📝 Response Time Reference

- Small optimization (pop=30, gen=10): **3-5 seconds**
- Default optimization (pop=50, gen=30): **10-15 seconds**
- Large optimization (pop=100, gen=50): **30-60 seconds**
- XL optimization (pop=200, gen=100): **2-5 minutes**

---

## 🎓 Learning Resources

1. **DEAP Framework:** https://deap.readthedocs.io/
2. **NSGA-II Algorithm:** https://ieeexplore.ieee.org/document/996017
3. **FastAPI Guide:** https://fastapi.tiangolo.com/
4. **Pydantic Validation:** https://pydantic-docs.helpmanual.io/

---

## 📅 Version Info

- **Version:** 1.0.0
- **Status:** Production Ready ✅
- **DEAP Version:** 1.4.1
- **Python:** 3.8+
- **Last Updated:** 2024-12-19

---

**Keep this card handy for quick reference!** 🚀
