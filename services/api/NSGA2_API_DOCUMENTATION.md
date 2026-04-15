# NSGA-II Multi-Objective Optimization API

Complete REST API documentation for the NSGA-II multi-objective circuit optimization service.

## Overview

The NSGA-II (Non-dominated Sorting Genetic Algorithm II) multi-objective optimizer finds optimal trade-offs between power consumption and operating frequency for CMOS circuits.

**Optimization Objectives:**
- Minimize: Power consumption (mW)
- Maximize: Operating frequency (GHz)

**Design Parameters:**
- WN: NMOS transistor width (µm) - Range: 0.5 to 10.0
- WP: PMOS transistor width (µm) - Range: 0.5 to 10.0
- VDD: Supply voltage (V) - Range: 1.0 to 5.0

## Endpoints

### 1. POST /api/v1/nsga2/optimize

**Description:** Run NSGA-II multi-objective optimization

**Request Body:**
```json
{
  "population_size": 50,
  "generations": 30,
  "use_ml": false,
  "seed": 42
}
```

**Parameters:**
- `population_size` (int, default=50): Number of individuals per generation (10-1000)
- `generations` (int, default=30): Number of generations to evolve (5-500)
- `use_ml` (bool, default=false): Use ML model for performance prediction
- `seed` (int, default=42): Random seed for reproducibility

**Response (200 OK):**
```json
{
  "status": "success",
  "pareto_front": [
    {
      "parameters": {
        "wn": 2.5,
        "wp": 5.0,
        "vdd": 2.8
      },
      "performance": {
        "frequency": 0.8,
        "power": 15.2,
        "delay": 1.25,
        "efficiency": 0.0526
      },
      "rank": 1
    },
    {
      "parameters": {
        "wn": 5.0,
        "wp": 8.0,
        "vdd": 3.5
      },
      "performance": {
        "frequency": 1.2,
        "power": 22.8,
        "delay": 0.83,
        "efficiency": 0.0526
      },
      "rank": 1
    }
  ],
  "metrics": {
    "generations": 30,
    "population_size": 50,
    "execution_time": 12.34,
    "pareto_front_size": 15,
    "hypervolume": 2850.5,
    "spread": 0.78,
    "timestamp": "2024-12-19T10:30:45.123Z"
  },
  "best_solutions": {
    "best_power": {
      "wn": 0.8,
      "wp": 1.5,
      "vdd": 1.2,
      "power": 5.3,
      "frequency": 0.2
    },
    "best_frequency": {
      "wn": 9.5,
      "wp": 9.8,
      "vdd": 4.8,
      "power": 89.2,
      "frequency": 2.5
    },
    "best_efficiency": {
      "wn": 4.2,
      "wp": 6.1,
      "vdd": 2.5,
      "power": 18.5,
      "frequency": 0.95,
      "efficiency": 0.0514
    }
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/nsga2/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "population_size": 50,
    "generations": 30,
    "use_ml": false,
    "seed": 42
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/nsga2/optimize",
    json={
        "population_size": 50,
        "generations": 30,
        "use_ml": False,
        "seed": 42
    }
)

result = response.json()
pareto_front = result["pareto_front"]
metrics = result["metrics"]
best_solutions = result["best_solutions"]

print(f"Pareto front size: {metrics['pareto_front_size']}")
print(f"Execution time: {metrics['execution_time']:.2f}s")
print(f"Hypervolume: {metrics['hypervolume']:.2f}")
print(f"Spread: {metrics['spread']:.4f}")
```

---

### 2. GET /api/v1/nsga2/health

**Description:** Check if NSGA-II optimizer is available

**Response (200 OK):**
```json
{
  "status": "healthy",
  "nsga2_available": true,
  "deap_requirement": "deap>=1.4.1",
  "timestamp": "2024-12-19T10:30:45.123Z"
}
```

**Example cURL:**
```bash
curl http://localhost:8000/api/v1/nsga2/health
```

---

### 3. POST /api/v1/nsga2/compare

**Description:** Compare two circuit designs

**Request Body:**
```json
{
  "design1": {
    "wn": 2.5,
    "wp": 5.0,
    "vdd": 2.8
  },
  "design2": {
    "wn": 5.0,
    "wp": 8.0,
    "vdd": 3.5
  }
}
```

**Response (200 OK):**
```json
{
  "design1": {
    "parameters": {
      "wn": 2.5,
      "wp": 5.0,
      "vdd": 2.8
    },
    "performance": {
      "frequency": 0.8,
      "power": 15.2,
      "delay": 1.25,
      "efficiency": 0.0526
    }
  },
  "design2": {
    "parameters": {
      "wn": 5.0,
      "wp": 8.0,
      "vdd": 3.5
    },
    "performance": {
      "frequency": 1.2,
      "power": 22.8,
      "delay": 0.83,
      "efficiency": 0.0526
    }
  },
  "comparison": {
    "frequency_ratio": 1.5,
    "power_ratio": 1.5,
    "efficiency_ratio": 1.0
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/nsga2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "design1": {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
    "design2": {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
  }'
```

---

### 4. GET /api/v1/nsga2/info

**Description:** Get optimizer information and capabilities

**Response (200 OK):**
```json
{
  "name": "NSGA-II Multi-Objective Optimizer",
  "description": "Non-dominated Sorting Genetic Algorithm II for CMOS circuit optimization",
  "objectives": [
    {
      "name": "Power",
      "type": "minimize",
      "unit": "mW"
    },
    {
      "name": "Frequency",
      "type": "maximize",
      "unit": "GHz"
    }
  ],
  "parameters": [
    {
      "name": "WN",
      "description": "NMOS width",
      "unit": "µm",
      "range": [0.5, 10.0]
    },
    {
      "name": "WP",
      "description": "PMOS width",
      "unit": "µm",
      "range": [0.5, 10.0]
    },
    {
      "name": "VDD",
      "description": "Supply voltage",
      "unit": "V",
      "range": [1.0, 5.0]
    }
  ],
  "algorithm": "NSGA-II (DEAP implementation)",
  "outputs": ["Pareto front", "Optimization metrics", "Best solutions"]
}
```

**Example cURL:**
```bash
curl http://localhost:8000/api/v1/nsga2/info
```

---

## Response Fields Explained

### Pareto Front Solutions

Each solution in the Pareto front represents a non-dominated design:

- **parameters**: Circuit design parameters (WN, WP, VDD)
- **performance**: Predicted performance metrics
  - `frequency`: Operating frequency in GHz
  - `power`: Power consumption in mW
  - `delay`: Propagation delay in ns
  - `efficiency`: Energy efficiency (GHz/mW)
- **rank**: Pareto rank (1 = Pareto-optimal, higher = dominated)

### Optimization Metrics

- **generations**: Number of generations evolved
- **population_size**: Population size per generation
- **execution_time**: Total optimization time (seconds)
- **pareto_front_size**: Number of non-dominated solutions found
- **hypervolume**: Multi-objective quality metric (higher = better)
- **spread**: Solution diversity metric (higher = more diverse)
- **timestamp**: ISO 8601 timestamp of optimization

### Best Solutions

Special highlighted solutions:

- **best_power**: Design minimizing power consumption
- **best_frequency**: Design maximizing operating frequency
- **best_efficiency**: Design maximizing energy efficiency

---

## Usage Patterns

### Pattern 1: Quick Optimization

Find Pareto front with default settings:

```python
response = requests.post("http://localhost:8000/api/v1/nsga2/optimize")
pareto = response.json()["pareto_front"]
best = response.json()["best_solutions"]
```

### Pattern 2: Fine-Tuned Search

Run larger optimization with more generations:

```python
response = requests.post(
    "http://localhost:8000/api/v1/nsga2/optimize",
    json={
        "population_size": 100,
        "generations": 50,
        "seed": 12345
    }
)
```

### Pattern 3: Compare Designs

Evaluate two specific designs:

```python
response = requests.post(
    "http://localhost:8000/api/v1/nsga2/compare",
    json={
        "design1": {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
        "design2": {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
    }
)
comparison = response.json()
print(f"Design 2 is {comparison['comparison']['frequency_ratio']:.2f}x faster")
```

### Pattern 4: Monitor Optimization Progress

Check if optimizer is available before running:

```python
health = requests.get("http://localhost:8000/api/v1/nsga2/health").json()
if health["nsga2_available"]:
    # Run optimization
    pass
```

---

## Integration with ML Predictions

The optimizer can optionally use the advanced ML prediction model:

```python
response = requests.post(
    "http://localhost:8000/api/v1/nsga2/optimize",
    json={
        "population_size": 50,
        "generations": 30,
        "use_ml": True  # Use ML model for faster predictions
    }
)
```

**Note:** ML mode requires a trained XGBoost model. Falls back to physics equations if unavailable.

---

## Performance Guidelines

| Setting | Time | Quality | Diversity |
|---------|------|---------|-----------|
| Small (pop=30, gen=10) | < 5s | Low | Low |
| Medium (pop=50, gen=30) | 10-15s | Good | Good |
| Large (pop=100, gen=50) | 30-60s | Very Good | Very Good |
| XL (pop=200, gen=100) | 2-5m | Excellent | Excellent |

---

## Error Handling

### 503 Service Unavailable
```json
{
  "detail": "NSGA-II optimizer not available. Install DEAP: pip install deap"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Optimization error: <error message>"
}
```

---

## Integration with Other APIs

**Related endpoints:**
- `/api/v1/predict` - ML predictions (single design)
- `/api/v1/simulate` - CMOS simulation
- `/api/v1/optimize` - ADA optimizer (single-objective)

---

## Technology Stack

- **Algorithm**: NSGA-II via DEAP library
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Performance Prediction**: XGBoost (optional) or physics equations
- **Database**: PostgreSQL (for persistent optimization history)

---

## Changelog

### v1.0.0 (2024-12-19)

- Initial NSGA-II API release
- Support for multi-objective optimization
- Pareto front extraction
- Integration with ML prediction model
- Health checks and monitoring
- ✅ API fully functional and tested
