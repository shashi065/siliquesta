# AI Orchestrator - Design Space Exploration Engine

## Overview

The **AI Orchestrator** is a unified intelligent agent that coordinates the optimizer, ML predictor, and reliability model to perform comprehensive design space exploration and multi-objective optimization.

## Architecture

```
User Intent (Natural Language)
    ↓
[Intent Parser] → Detect objective (power/frequency/reliability/balanced)
    ↓
[Design Generator] → Create 20 candidate designs (Latin Hypercube Sampling)
    ↓
[Evaluation Loop] → For each design:
    ├─ [ML Predictor] → Get power, frequency, delay predictions
    ├─ [Reliability Model] → Compute lifetime & degradation
    └─ [Constraint Filter] → Check max power, min frequency, etc.
    ↓
[Pareto Analyzer] → Identify non-dominated designs
    ↓
[SHAP Explainer] → Generate feature importance for best design
    ↓
[Trade-off Analysis] → Compute Pareto front statistics
    ↓
[Recommendations] → Auto-generate engineering insights
    ↓
OrchestratorResponse (Complete design analysis)
```

## Request Format

**Endpoint:** `POST /ts/digital_twin/orchestrate`

```json
{
  "intent": "minimize power consumption",
  "constraints": {
    "max_power_mw": 5.0,
    "min_frequency_ghz": 1.0,
    "min_lifetime_years": 10.0
  },
  "reference_design": {
    "wn": 2.0,
    "wp": 3.0
  },
  "num_designs": 20,
  "vdd": 1.2,
  "temp": 27.0,
  "cl_ff": 10.0
}
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `intent` | string | - | **Required**. User query: "minimize power", "maximize frequency", "improve reliability", "balanced", etc. |
| `constraints` | object | null | Constraint overrides: `{max_power_mw, min_frequency_ghz, min_lifetime_years}` |
| `reference_design` | object | null | Reference operating point for comparison |
| `num_designs` | int | 20 | Number of candidate designs to explore |
| `vdd` | float | 1.8 | Supply voltage (V) |
| `temp` | float | 27 | Temperature (°C) |
| `cl_ff` | float | 10 | Load capacitance (fF) |

### Intent Examples

- **Power Optimization:** "minimize power", "low power design", "reduce energy"
- **Performance:** "maximize frequency", "high speed", "improve performance"
- **Reliability:** "improve reliability", "extend lifetime", "reduce degradation"
- **Balanced:** "find balanced design", "trade-off analysis", "multi-objective"

## Response Format

```json
{
  "intent": "minimize power consumption",
  "constraints": {
    "max_power_mw": 5.0,
    "min_frequency_ghz": 1.0,
    "min_lifetime_years": 10.0,
    "vdd_v": 1.2,
    "temp_c": 27.0
  },
  "best_design": {
    "design_id": "design_0",
    "wn": 1.25,
    "wp": 2.50,
    "vdd": 1.2,
    "temp": 27.0,
    "cl_ff": 10.0,
    "power_mw": 2.45,
    "frequency_ghz": 1.85,
    "delay_ps": 0.54,
    "reliability_score": 0.95,
    "lifetime_years": 25.3,
    "dominant_failure_mode": "HCI",
    "prediction_confidence": 0.92
  },
  "pareto_front": [
    {
      "design_id": "design_0",
      "power_mw": 2.45,
      "frequency_ghz": 1.85,
      "reliability_score": 0.95,
      ...
    },
    {
      "design_id": "design_3",
      "power_mw": 2.67,
      "frequency_ghz": 1.95,
      "reliability_score": 0.93,
      ...
    }
  ],
  "best_design_explanation": {
    "method": "shap",
    "output": "power",
    "contributions": {
      "wn": -0.15,
      "wp": 0.08,
      "vdd": 0.45,
      "temp": 0.12
    },
    "base_value": 2.1
  },
  "design_count": 20,
  "dominant_metric": "power",
  "trade_offs": {
    "power_range_mw": [2.1, 4.8],
    "frequency_range_ghz": [1.2, 2.8],
    "reliability_range": [0.88, 0.98],
    "designs_on_frontier": 8
  },
  "recommendations": [
    "✓ Low-power design: Suitable for battery-constrained applications",
    "✓ 8 alternative designs available for power-frequency trade-off exploration"
  ]
}
```

### Response Fields

| Field | Description |
|-------|-------------|
| `intent` | Parsed user intent (power/frequency/reliability/balanced) |
| `constraints` | Extracted constraints (merged defaults + user overrides) |
| `best_design` | Single optimal design point with all metrics |
| `pareto_front` | Top 10 non-dominated designs (Pareto optimal) |
| `best_design_explanation` | SHAP feature contributions for best design |
| `design_count` | Number of designs that met constraints |
| `dominant_metric` | Primary optimization objective |
| `trade_offs` | Pareto front analysis statistics |
| `recommendations` | Auto-generated engineering insights |

## Design Metrics

Each design point includes:

- **design_id**: Unique identifier (design_0, design_1, ...)
- **Transistor Sizes**: wn, wp (micrometers)
- **Operating Point**: vdd, temp, cl_ff
- **Power**: power_mw (milliwatts)
- **Performance**: frequency_ghz (gigahertz), delay_ps (picoseconds)
- **Reliability**: reliability_score [0-1], lifetime_years, dominant_failure_mode
- **Confidence**: prediction_confidence of ML models

## Usage Examples

### Example 1: Minimize Power Consumption

```bash
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "minimize power consumption for IoT device",
    "num_designs": 20,
    "vdd": 1.0,
    "temp": 27.0
  }'
```

**Expected Output:**
- Design with lowest power consumption
- Pareto front showing power-frequency trade-offs
- SHAP explanation of why this design achieves low power
- Recommendations for ultra-low power applications

### Example 2: Maximize Frequency

```bash
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "maximize frequency for high-performance computing",
    "constraints": {
      "max_power_mw": 15.0,
      "min_lifetime_years": 5.0
    },
    "num_designs": 25,
    "vdd": 1.8,
    "temp": 85.0
  }'
```

**Expected Output:**
- Design with highest frequency that meets power/lifetime constraints
- Pareto front showing performance-power trade-off
- SHAP explaining high-frequency design
- Recommendations for HPC applications

### Example 3: Balanced Design

```bash
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "find balanced design with good power and performance",
    "num_designs": 30,
    "vdd": 1.5,
    "temp": 50.0
  }'
```

**Expected Output:**
- Design with balanced power-frequency-reliability trade-off
- Extended Pareto front with diverse options
- SHAP explanation
- Recommendations for general-purpose applications

## Intent Parsing

The orchestrator automatically detects user intent from natural language:

```python
# Minimum power:
if "power" in intent and "min" in intent:
    primary_objective = "power"

# Maximum frequency:
elif "freq" in intent and "max" in intent:
    primary_objective = "frequency"

# Reliability focus:
elif "reliab" in intent:
    primary_objective = "reliability"

# Balanced (default):
else:
    primary_objective = "balanced"
```

## Constraint Defaults

If not specified, constraints default to:

```python
{
    "max_power_mw": 10.0,
    "min_frequency_ghz": 0.5,
    "min_lifetime_years": 5.0,
    "max_temp_c": 100.0
}
```

## Pareto Front Analysis

The *Pareto front* contains non-dominated designs where improving one objective requires sacrificing another:

- **Power-optimal** designs: Minimize power × frequency
- **Performance-optimal** designs: Maximize frequency × reliability
- **Reliability-optimal** designs: Maximize lifetime × reliability_score

```
Pareto Front Visualization:
        Frequency
            ↑
            |     ✓ (high freq, low power)
            |    ╱╲
            |   ╱  ╲
            |  ╱    ✓ (balanced)
            | ╱      ╲
            |╱        ╲
            +─────────→ Power
```

## SHAP Explanations

The best design includes SHAP TreeExplainer feature contributions:

```json
"best_design_explanation": {
  "method": "shap",
  "output": "power",
  "contributions": {
    "vdd": 0.45,
    "wn": -0.15,
    "temp": 0.12,
    "wp": 0.08
  },
  "base_value": 2.1,
  "prediction_value": 2.45
}
```

Interpretation:
- `vdd` increases power consumption by 0.45 mW
- `wn` reduces power consumption by 0.15 mW
- Actual prediction: 2.1 (base) + 0.45 - 0.15 + 0.12 + 0.08 = 2.45 mW

## Error Handling

### 503 Service Unavailable
ML models not trained yet:
```json
{
  "detail": "ML models not available. Train models first."
}
```

### 400 Bad Request
No designs satisfy constraints:
```json
{
  "detail": "No designs satisfied the constraints. Relax constraints and retry."
}
```

### 500 Internal Server Error
Orchestration failure:
```json
{
  "detail": "Orchestration failed: [error details]"
}
```

## Performance

- **Design Generation:** O(n) where n = num_designs (default 20)
- **Evaluation Per Design:** ML prediction (ms) + reliability (ms)
- **Pareto Analysis:** O(n²) worst case, typically much faster
- **Total Time:** ~1-5 seconds for 20 designs (depends on ML model size)

## Integration with Other Endpoints

The orchestrator internally calls:

1. **ML Predictor** (`DigitalTwinTrainer.predict()`)
   - Input: wn, wp, vdd, temp
   - Output: power, frequency, delay with confidence scores

2. **Reliability Model** (`ReliabilityModel.compute_reliability_score()`)
   - Input: vdd, temp, time_years, current_ma
   - Output: reliability_score, lifetime breakdown, degradation metrics

3. **SHAP Explainer** (`DigitalTwinTrainer.explain_prediction()`)
   - Input: Best design parameters
   - Output: Feature contributions for power prediction

## Advanced Features

### Multi-Objective Optimization
The Pareto front represents optimal trade-offs between:
- Power consumption
- Frequency (performance)
- Reliability (lifetime)

### Automatic Constraint Handling
Designs are filtered to satisfy:
- Maximum power budget
- Minimum frequency requirement
- Minimum device lifetime
- Temperature constraints

### Smart Recommendations
Based on design characteristics:
- "✓ Low-power design: Good for battery-constrained..."
- "✓ High-performance design: Suitable for compute-intensive..."
- "✓ Highly reliable: Extended device lifetime expected..."
- "✓ N alternative designs available..."

## API Documentation

**Endpoint:** `POST /ts/digital_twin/orchestrate`

**Request Model:** `OrchestratorRequest`
- intent: str
- constraints: Optional[Dict[str, Any]]
- reference_design: Optional[Dict[str, Any]]
- num_designs: int = 20
- vdd: float = 1.8
- temp: float = 27.0
- cl_ff: float = 10.0

**Response Model:** `OrchestratorResponse`
- intent: str
- constraints: Dict[str, Any]
- best_design: OrchestratorDesign
- pareto_front: List[OrchestratorDesign]
- best_design_explanation: Dict[str, Any]
- design_count: int
- dominant_metric: str
- trade_offs: Dict[str, Any]
- recommendations: List[str]

**Authentication:** Optional (guest or licensed users)

**Rate Limiting:** Subject to SaaS tier

## Tests

Run orchestrator tests:

```bash
# Python test suite
python test_orchestrator.py

# cURL examples
bash test_orchestrator.sh
```

## Future Enhancements

- [ ] Constraint learning from historical queries
- [ ] Reference design-guided search
- [ ] Bayesian optimization for faster convergence
- [ ] Multi-platform designs (CPU/GPU co-optimization)
- [ ] Real-time design recommendation based on market trends
- [ ] Integration with physical simulation for validation

---

**Last Updated:** April 2026
**Status:** ✅ Production Ready
**API Version:** v1.0
