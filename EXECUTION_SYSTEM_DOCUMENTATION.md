# Execution-Based AI System Documentation

## Overview

The Execution-Based AI System is a constraint-based optimization engine that:

1. **Parses** natural language optimization requests
2. **Extracts** design constraints and objectives
3. **Calls** the NSGA-II multi-objective optimizer
4. **Returns** Pareto front solutions meeting all constraints

This is NOT a chatbot - it's a direct execution system that interprets requirements and produces results.

## System Architecture

```
User Request (Natural Language)
        ↓
   ConstraintParser
   ├─ Power keywords
   ├─ Frequency keywords
   ├─ Efficiency keywords
   ├─ Transistor sizing
   └─ Supply voltage
        ↓
   ConstraintSet (Extracted constraints + objectives)
        ↓
   ExecutionEngine
   └─ Parameter adaptation
        ↓
   NSGA-II Optimizer
   ├─ Multi-objective genetic algorithm
   ├─ Population-based search
   └─ Pareto front extraction
        ↓
   Result Formatting
   └─ Best solutions (power, frequency, efficiency)
        ↓
   Return to User
```

## Key Components

### 1. ConstraintParser

Extracts optimization constraints and objectives from natural language.

**Pattern Categories:**

#### Power Keywords
- "low power", "reduced power", "minimal power"
- "power under X mW", "power below X mW"
- "keep power under X", "maintain power under X"

#### Frequency Keywords
- "high frequency", "maximum frequency", "peak frequency"
- "frequency under X GHz", "up to X GHz"
- "at least X GHz", "minimum X GHz frequency"

#### Efficiency Keywords
- "high efficiency", "maximum efficiency", "improve efficiency"
- "efficiency above X", "efficiency at least X"

#### Transistor Keywords
- "small transistor", "narrow gate width", "thin transistor"
- "large transistor", "wide gate width", "thick transistor"

#### Voltage Keywords
- "low voltage", "reduced voltage", "minimal voltage"
- "high voltage", "maximum voltage"
- "voltage = X V", "voltage is X V"

### 2. ConstraintSet

Data structure containing extracted constraints:

```python
@dataclass
class ConstraintSet:
    max_power: Optional[float] = None  # mW
    min_frequency: Optional[float] = None  # GHz
    max_frequency: Optional[float] = None  # GHz
    min_efficiency: Optional[float] = None  # GHz/mW
    objectives: List[OptimizationObjective] = None
    preferred_wn_range: Tuple[float, float] = (0.5, 10.0)  # µm
    preferred_wp_range: Tuple[float, float] = (0.5, 10.0)  # µm
    preferred_vdd_range: Tuple[float, float] = (1.0, 5.0)  # V
```

### 3. ExecutionEngine

Orchestrates the optimization pipeline.

**Methods:**
- `execute(request: str) -> Dict`: Main entry point
- `_extract_optimization_params(constraints) -> Dict`: Convert constraints to optimizer parameters
- `_call_optimizer(params) -> Dict`: Invoke NSGA-II
- `_filter_by_constraints(pareto_front, constraints) -> List`: Filter results
- `_format_result(...) -> Dict`: Format output

### 4. OptimizationObjective (Enum)

Available objectives:
- `MINIMIZE_POWER`: Reduce power consumption
- `MAXIMIZE_FREQUENCY`: Increase operating frequency
- `MAXIMIZE_EFFICIENCY`: Optimize power/frequency ratio
- `BALANCE`: Multi-objective balance

## Usage Examples

### Example 1: Low Power Optimization

**Request:**
```
"optimize for low power under 1GHz"
```

**Parsing:**
- Objective: `MINIMIZE_POWER`
- Constraint: `max_frequency = 1.0 GHz`

**Result:**
```json
{
  "status": "success",
  "objectives": ["minimize_power"],
  "constraints": {
    "max_power": null,
    "min_frequency": null,
    "max_frequency": 1.0,
    "min_efficiency": null
  },
  "solutions": {
    "best_power": {
      "wn": 2.15, "wp": 4.30, "vdd": 2.50,
      "power": 8.42, "frequency": 0.92, "efficiency": 0.109
    }
  }
}
```

### Example 2: Performance-Critical Design

**Request:**
```
"maximize frequency, keep power under 20mW"
```

**Parsing:**
- Objective: `MAXIMIZE_FREQUENCY`
- Constraints:
  - `max_power = 20.0 mW`

**Result:**
```json
{
  "status": "success",
  "objectives": ["maximize_frequency"],
  "constraints": {
    "max_power": 20.0,
    "min_frequency": null,
    "max_frequency": null,
    "min_efficiency": null
  },
  "solutions": {
    "best_frequency": {
      "wn": 6.50, "wp": 8.00, "vdd": 4.50,
      "power": 19.87, "frequency": 2.34, "efficiency": 0.118
    }
  }
}
```

### Example 3: Balanced Design with Voltage Constraint

**Request:**
```
"balance power and efficiency, keep voltage low"
```

**Parsing:**
- Objectives: `MAXIMIZE_EFFICIENCY`, `MINIMIZE_POWER`
- Constraint: `preferred_vdd_range = (1.0, 2.5) V`

**Result:**
```json
{
  "status": "success",
  "objectives": ["maximize_efficiency", "minimize_power"],
  "solutions": {
    "best_efficiency": {
      "wn": 4.25, "wp": 6.50, "vdd": 2.00,
      "power": 12.50, "frequency": 1.44, "efficiency": 0.115
    }
  }
}
```

## CLI Usage

### Basic Command

```bash
python execution_cli.py "optimize for low power under 1GHz"
```

### Output Format

```
======================================================================
EXECUTION-BASED AI SYSTEM
======================================================================

Request: optimize for low power under 1GHz

Status: ✓ SUCCESS

OBJECTIVES:
  • minimize_power

CONSTRAINTS EXTRACTED:
  • Max Frequency: 1.0 GHz

OPTIMIZATION EXECUTION:
  • Population Size: 50
  • Generations: 30
  • Total Solutions: 50
  • Valid Solutions (meeting constraints): 47

OPTIMAL SOLUTIONS:

  MINIMUM POWER:
    Design Parameters:
      WN (NMOS width):  2.150 µm
      WP (PMOS width):  4.300 µm
      VDD (Supply):     2.500 V
    Performance:
      Frequency:        0.9200 GHz
      Power:            8.42 mW
      Efficiency:       0.1091 GHz/mW

  MAXIMUM FREQUENCY:
    Design Parameters:
      WN (NMOS width):  6.500 µm
      WP (PMOS width):  8.000 µm
      VDD (Supply):     4.500 V
    Performance:
      Frequency:        2.3400 GHz
      Power:            19.87 mW
      Efficiency:       0.1180 GHz/mW

  BEST EFFICIENCY:
    Design Parameters:
      WN (NMOS width):  4.250 µm
      WP (PMOS width):  6.500 µm
      VDD (Supply):     2.800 V
    Performance:
      Frequency:        1.4400 GHz
      Power:            12.50 mW
      Efficiency:       0.1152 GHz/mW

======================================================================
Execution completed successfully
======================================================================
```

## API Integration

### REST Endpoint

**POST** `/api/v1/execution/execute`

**Request:**
```json
{
  "request": "optimize for low power under 1GHz"
}
```

**Response:**
```json
{
  "status": "success",
  "request": "optimize for low power under 1GHz",
  "objectives": ["minimize_power"],
  "constraints": {
    "max_power": null,
    "min_frequency": null,
    "max_frequency": 1.0,
    "min_efficiency": null
  },
  "optimization": {
    "population_size": 50,
    "generations": 30,
    "total_solutions": 50,
    "valid_solutions": 47
  },
  "solutions": {
    "best_power": {...},
    "best_frequency": {...},
    "best_efficiency": {...}
  },
  "timestamp": "2026-04-13T10:30:45.123456"
}
```

### Supported Keywords Endpoint

**GET** `/api/v1/execution/supported-keywords`

Returns list of all supported natural language keywords and example requests.

### Health Check Endpoint

**GET** `/api/v1/execution/health`

```json
{
  "status": "healthy",
  "engine": "execution-based-ai",
  "capabilities": [
    "natural_language_parsing",
    "constraint_extraction",
    "nsga2_optimization",
    "pareto_front_derivation"
  ],
  "timestamp": "2026-04-13T10:30:45.123456"
}
```

## Design Parameters

### Circuit Parameters

- **WN (NMOS Width)**: 0.5 - 10.0 µm
  - Controls NMOS transistor sizing
  - Larger WN → higher frequency, higher power
  
- **WP (PMOS Width)**: 0.5 - 10.0 µm
  - Controls PMOS transistor sizing
  - Larger WP → higher frequency, higher power
  
- **VDD (Supply Voltage)**: 1.0 - 5.0 V
  - Controls supply voltage
  - Higher VDD → higher frequency, higher power

### Performance Metrics

- **Frequency (GHz)**: Operating frequency
  - Predicted using physics equations or ML
  - Target: Maximize for performance
  
- **Power (mW)**: Power consumption
  - Predicted using physics equations or ML
  - Target: Minimize for efficiency
  
- **Efficiency (GHz/mW)**: Performance per watt
  - Ratio of frequency to power
  - Target: Maximize for balanced designs
  
- **Delay (ns)**: Propagation delay
  - Inverse relationship with frequency
  - Used for internal calculations

## Constraint Filtering

Solutions are filtered to meet all specified constraints:

1. **Power Constraint**: `solution.power ≤ max_power`
2. **Frequency Constraints**:
   - Minimum: `solution.frequency ≥ min_frequency`
   - Maximum: `solution.frequency ≤ max_frequency`
3. **Efficiency Constraint**: `solution.efficiency ≥ min_efficiency`

Only solutions meeting ALL constraints are returned.

## Parameter Adaptation

The engine adapts optimizer parameters based on constraint severity:

### Tight Power Constraint (< 10 mW)
- Population Size: 100 (vs default 50)
- Generations: 50 (vs default 30)
- Rationale: More exploration needed for tight constraint

### Tight Frequency Constraint (< 0.5 GHz)
- Population Size: 80 (vs default 50)
- Generations: 40 (vs default 30)
- Rationale: Larger population for frequency space

## Testing

### Unit Tests

```bash
python test_execution_engine.py
```

Runs 10 comprehensive tests:
1. Power constraint parsing
2. Frequency constraint parsing
3. Voltage constraint parsing
4. Primary request execution
5. Complex multi-constraint execution
6. Efficiency optimization
7. Parameter adaptation
8. Solution filtering
9. Output format validation
10. Multiple domain keywords

### Integration Tests

Test execution system with NSGA-II optimizer:

```python
from execution_engine import ExecutionEngine

engine = ExecutionEngine()
result = engine.execute("optimize for low power under 1GHz")
assert result['status'] == 'success'
assert result['optimization']['valid_solutions'] > 0
```

## Error Handling

### Missing DEAP Library

If DEAP is not installed, system falls back to mock optimization:
- Returns realistic mock Pareto front
- Demonstrates system functionality without ML dependencies

### Invalid Constraints

Invalid constraint values are silently ignored:
- Non-numeric frequency: Skipped
- Negative power: Normalized
- Out-of-range parameters: Clamped to valid range

### Empty Requests

Empty or whitespace-only requests rejected with 422 status code.

## Performance Characteristics

### Parsing
- Parse time: ~5-10 ms for typical requests
- Regex-based pattern matching

### Optimization
- Optimization time: ~5-30 seconds (depending on population/generations)
- NSGA-II with binary tournament selection
- Pareto front extraction: O(n²) worst case

### Filtering
- Linear scan of Pareto front: O(n)
- Constraint evaluation: O(1) per solution

## Future Enhancements

1. **Multi-Chip Optimization**: Extend to multiple circuit blocks
2. **Hierarchical Constraints**: Support resource budgets
3. **Real-time Feedback**: Interactive constraint refinement
4. **Hardware-Specific Targets**: Technology node adaptation
5. **ML-Based Parsing**: Deep learning for better NLP
6. **Advanced Metrics**: Power breakdown (static/dynamic)
7. **Multi-Objective Visualization**: Pareto front 3D plots

## Files

- `execution_engine.py`: Core engine with parser and executor
- `execution_cli.py`: Command-line interface
- `test_execution_engine.py`: Comprehensive test suite
- `services/api/app/api/execution_routes.py`: FastAPI integration
- `services/api/app/main.py`: Router registration

## See Also

- [NSGA-II Documentation](NSGA2_API_DOCUMENTATION.md)
- [API Reference](API-REFERENCE.md)
- [Integration Guide](ML_INTEGRATION_GUIDE.md)
