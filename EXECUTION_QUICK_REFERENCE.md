# Execution-Based AI System - Quick Reference

## What It Does (NOT Chatbot)

**4-Step Constraint-Based Execution Pipeline:**

1. **Parse** natural language input
2. **Extract** optimization constraints
3. **Call** NSGA-II optimizer
4. **Return** Pareto front results

## Input

Natural language optimization requests:
```
"optimize for low power under 1GHz"
"maximize frequency with power budget 20mW"
"high efficiency design, keep voltage low"
"balance power and efficiency"
```

## Output

```json
{
  "status": "success",
  "objectives": ["minimize_power"],
  "constraints": {"max_frequency": 1.0},
  "solutions": {
    "best_power": {"wn": 2.15, "wp": 4.30, "vdd": 2.50, ...},
    "best_frequency": {...},
    "best_efficiency": {...}
  }
}
```

## Parsing Keywords

### Power
- "low power", "reduce power", "minimal power"
- "power under X mW", "power below X"

### Frequency  
- "high frequency", "maximize frequency"
- "frequency under X GHz", "at least X GHz"

### Efficiency
- "high efficiency", "improve efficiency"
- "efficiency above X"

### Voltage
- "low voltage", "high voltage"
- "voltage = X V"

### Transistor
- "small transistor", "large transistor"

## CLI Usage

```bash
python execution_cli.py "optimize for low power under 1GHz"
```

## API Usage

**POST** `/api/v1/execution/execute`
```json
{"request": "optimize for low power under 1GHz"}
```

**GET** `/api/v1/execution/supported-keywords`

**GET** `/api/v1/execution/health`

## Design Space

- **WN**: 0.5 - 10.0 µm (NMOS width)
- **WP**: 0.5 - 10.0 µm (PMOS width)
- **VDD**: 1.0 - 5.0 V (Supply voltage)

## Performance Metrics

- **Frequency**: GHz (maximize for performance)
- **Power**: mW (minimize for efficiency)
- **Efficiency**: GHz/mW (maximize for balance)

## Optimization Strategy

1. **Parse** constraints from natural language
2. **Adapt** optimizer parameters based on constraint tightness
3. **Run** NSGA-II evolutionary algorithm
4. **Filter** solutions by constraints
5. **Return** best designs for each metric

## System Files

| File | Purpose |
|------|---------|
| `execution_engine.py` | Core engine |
| `execution_cli.py` | Command-line interface |
| `test_execution_engine.py` | Test suite (10 tests) |
| `services/api/app/api/execution_routes.py` | FastAPI routes |
| `EXECUTION_SYSTEM_DOCUMENTATION.md` | Full documentation |

## Testing

```bash
# Run 10 comprehensive tests
python test_execution_engine.py

# Test specific request
python execution_cli.py "your request here"
```

## Key Features

✓ **Natural Language Parsing**: Uses regex patterns to extract constraints  
✓ **Multi-Objective Optimization**: NSGA-II with power/frequency objectives  
✓ **Adaptive Parameters**: Optimizer parameters adjust to constraint severity  
✓ **Solution Filtering**: All returned solutions meet constraints  
✓ **Three-Solution Return**: Best power, best frequency, best efficiency  
✓ **REST API Integration**: Fully integrated with FastAPI backend  
✓ **No Chatbot UI**: Pure execution engine, no conversation  

## Example Flow

```
Input: "optimize for low power under 1GHz"
  ↓
Parse: objective=MINIMIZE_POWER, max_frequency=1.0GHz
  ↓
Adapt: population=50, generations=30
  ↓
Optimize: NSGA-II evolutionary algorithm
  ↓
Filter: Keep only solutions with frequency ≤ 1.0 GHz
  ↓
Output: 3 best designs (power, frequency, efficiency)
```

## Constraint Examples

| Request | Objective | Constraints |
|---------|-----------|-------------|
| "low power" | Minimize power | None |
| "power under 10mW" | Minimize power | max_power=10mW |
| "high frequency" | Maximize frequency | None |
| "freq under 2GHz" | Maximize frequency | max_frequency=2GHz |
| "at least 1.5GHz" | Maximize frequency | min_frequency=1.5GHz |
| "low voltage" | Flexible | vdd_range=(1.0,2.5)V |
| "balanced design" | Multi-objective | None |

## Integration with NSGA-II

```python
# Under the hood:
from app.nsga2_optimizer import run_optimization

pareto_front, metrics = run_optimization(
    population_size=50,
    generations=30,
    use_ml=False,
    seed=42,
    verbose=False
)

# Filter results
filtered = [s for s in pareto_front if s.performance.frequency <= max_freq]

# Return best solutions
```

## Performance

- **Parse time**: ~5-10 ms
- **Optimization time**: ~5-30 seconds
- **Filter time**: ~1 ms
- **Total latency**: ~5-30 seconds per request

## Requirements

- Python 3.8+
- DEAP 1.4.1 (for NSGA-II)
- NumPy
- Pydantic
- FastAPI (for API)

## See Also

- Full documentation: [EXECUTION_SYSTEM_DOCUMENTATION.md](EXECUTION_SYSTEM_DOCUMENTATION.md)
- NSGA-II details: [NSGA2_API_DOCUMENTATION.md](services/api/NSGA2_API_DOCUMENTATION.md)
- Backend integration: [services/api/app/main.py](services/api/app/main.py)
