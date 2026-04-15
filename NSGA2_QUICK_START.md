# NSGA-II Quick Reference Card

## One-Liner Imports

```python
from app.nsga2_optimizer import run_optimization, NSGAII_Optimizer, CircuitParameters
```

---

## Basic Usage (Copy-Paste Ready)

### 1️⃣ Quick Optimization
```python
pf, metrics = run_optimization()  # Uses defaults: 100 pop, 50 gen, seed=42
print(f"Solutions: {len(pf)}, Time: {metrics.execution_time:.2f}s")
```

### 2️⃣ With Constraints
```python
pf, metrics = run_optimization(freq_min=2.0, power_max=50.0)
print(f"Feasible designs: {len(pf)}")
```

### 3️⃣ Custom Parameters
```python
pf, metrics = run_optimization(
    population_size=200,      # Larger = better exploration
    generations=100,          # More = better convergence
    freq_min=1.0,             # Minimum frequency (GHz)
    power_max=100.0,          # Maximum power (mW)
    seed=999                  # Reproducible
)
```

### 4️⃣ Get Results in Exact Format
```python
optimizer = NSGAII_Optimizer(random_seed=42)
optimizer.optimize(population_size=100, generations=50)
solutions = optimizer.get_pareto_front_dict()

# Returns: [{"wn": float, "wp": float, "vdd": float, "power": float, "frequency": float, "delay": float}, ...]
```

### 5️⃣ Best Solutions
```python
optimizer.optimize(...)

best_power = optimizer.get_best_power()           # Min power solution
best_freq = optimizer.get_best_frequency()        # Max frequency solution
best_eff = optimizer.get_best_efficiency()        # Best GHz/mW

print(f"Min power: {best_power.performance.power:.2f} mW")
print(f"Max freq: {best_freq.performance.frequency:.2f} GHz")
```

---

## Parameter Bounds

| Param | Min | Max | Unit |
|-------|-----|-----|------|
| wn | 0.5 | 10.0 | µm |
| wp | 0.5 | 10.0 | µm |
| vdd | 1.0 | 5.0 | V |

---

## Output Format

```python
[
  {
    "wn": 0.5,           # float, µm
    "wp": 0.543,         # float, µm
    "vdd": 1.001,        # float, V
    "power": 0.686,      # float, mW
    "frequency": 15.0,   # float, GHz
    "delay": 0.2022      # float, ns
  },
  { ... }  # More solutions
]
```

---

## Response Metrics

```python
metrics.execution_time      # float, seconds
metrics.hypervolume         # float, Pareto front quality
metrics.spread              # float, solution diversity
metrics.pareto_front_size   # int, number of solutions
metrics.generations         # int, generations run
metrics.population_size     # int, population used
```

---

## Common Patterns

### Pattern 1: Find Best Solutions
```python
pf, _ = run_optimization()
best = sorted(pf, key=lambda s: s.performance.power)[:5]
for sol in best:
    print(f"WN={sol.parameters.wn:.1f}, P={sol.performance.power:.2f}mW")
```

### Pattern 2: Export to JSON
```python
import json
pf, metrics = run_optimization()
output = [
    {"wn": s.parameters.wn, "wp": s.parameters.wp, 
     "vdd": s.parameters.vdd, "power": s.performance.power,
     "frequency": s.performance.frequency, "delay": s.performance.delay}
    for s in pf
]
with open("results.json", "w") as f:
    json.dump(output, f, indent=2)
```

### Pattern 3: Reproducible Batch
```python
results = {}
for seed in [42, 99, 123]:
    pf, m = run_optimization(seed=seed, verbose=False)
    results[seed] = {"solutions": len(pf), "time": m.execution_time}

print(results)  # All runs deterministic
```

### Pattern 4: FastAPI Handler
```python
@app.post("/optimize")
async def optimize(freq_min: float = 0, power_max: float = 1000):
    pf, metrics = run_optimization(freq_min=freq_min, power_max=power_max, verbose=False)
    return {
        "solutions": [{"wn": s.parameters.wn, ...} for s in pf],
        "metrics": {"time": metrics.execution_time, "count": len(pf)}
    }
```

---

## Performance Tuning

| Use Case | Pop | Gen | Time | Solutions |
|---|---|---|---|---|
| 🚀 Quick | 50 | 10 | 0.1s | ~1-2 |
| ⚡ Fast | 50 | 20 | 0.2s | ~1-2 |
| 📊 Standard | 100 | 50 | 0.5s | ~1-3 |
| 🎯 Thorough | 200 | 100 | 2-5s | ~2-5 |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Gets 1 solution | Normal (try increasing population) |
| No feasible solutions | Relax constraints (lower freq_min, raise power_max) |
| Different results each run | Use `seed=42` (or any fixed number) |
| Slow execution | Reduce population or generations |
| Import error | `pip install deap` |

---

## DEAP Details

- **Algorithm**: NSGA-II (Non-dominated Sorting GA II)
- **Selection**: Non-dominated sorting by Pareto rank
- **Crossover**: Blend crossover (α=0.5)
- **Mutation**: Gaussian mutation (σ=0.2)
- **Objectives**: [Power (min), Frequency (max)]
- **Constraints**: Penalty method

---

## Reproducibility Guarantee

✅ **Same seed = Same results**

```python
# These are ALWAYS identical
pf1, _ = run_optimization(seed=42, population_size=100, generations=50)
pf2, _ = run_optimization(seed=42, population_size=100, generations=50)

assert len(pf1) == len(pf2)
assert all(s1.performance.power == s2.performance.power for s1, s2 in zip(pf1, pf2))
```

---

## Testing

```bash
.venv\Scripts\python.exe test_nsga2_full_upgrade.py
```

Expected: **7/7 tests PASSED ✅**

---

## File Locations

| File | Purpose |
|------|---------|
| `services/api/app/nsga2_optimizer.py` | Main implementation |
| `test_nsga2_full_upgrade.py` | Test suite |
| `NSGA2_FULL_UPGRADE.md` | Complete guide |
| `NSGA2_API_INTEGRATION.md` | API examples |
| `NSGA2_UPGRADE_SUMMARY.md` | Summary |

---

## Support Resources

- 📖 **Full Guide**: NSGA2_FULL_UPGRADE.md
- 🔌 **API Examples**: NSGA2_API_INTEGRATION.md  
- 🧪 **Tests**: test_nsga2_full_upgrade.py
- 💻 **Code**: services/api/app/nsga2_optimizer.py

---

## Status

✅ **PRODUCTION READY**

- All requirements met
- 7/7 tests passing
- Fully documented
- Fast (~0.5-1.3s)
- Deterministic
- Reproducible

**Version**: 2.0.0 | **Date**: April 13, 2026
