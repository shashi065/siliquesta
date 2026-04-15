# AI Orchestrator - Quick Start Guide

## What It Does

The **AI Orchestrator** takes a natural language design request and intelligently explores the design space to find optimal circuit designs considering power, frequency, and reliability simultaneously.

## Quick Example

### Request
```bash
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "minimize power consumption for IoT device",
    "num_designs": 20,
    "vdd": 1.2,
    "temp": 27.0
  }'
```

### Response Preview
```json
{
  "intent": "minimize power consumption",
  "dominant_metric": "power",
  "design_count": 20,
  
  "best_design": {
    "design_id": "design_0",
    "wn": 1.25,
    "wp": 2.50,
    "power_mw": 2.45,
    "frequency_ghz": 1.85,
    "reliability_score": 0.95,
    "lifetime_years": 25.3,
    "dominant_failure_mode": "HCI"
  },
  
  "pareto_front": [
    { "power_mw": 2.45, "frequency_ghz": 1.85, ... },
    { "power_mw": 2.67, "frequency_ghz": 1.95, ... },
    ...
  ],
  
  "best_design_explanation": {
    "method": "shap",
    "contributions": {
      "vdd": 0.45,
      "wn": -0.15,
      "temp": 0.12,
      "wp": 0.08
    }
  },
  
  "recommendations": [
    "✓ Low-power design: Good for battery-constrained applications",
    "✓ 8 alternative designs available for power-frequency trade-off exploration"
  ]
}
```

## Intent Keywords

Orchestrator detects intent from natural language:

| Keywords | Detected Objective |
|----------|-------------------|
| "minimize power", "low power", "reduce energy" | **Power Optimization** |
| "maximize frequency", "high speed", "improve performance" | **Performance** |
| "reliability", "lifetime", "degradation" | **Reliability** |
| "balanced", "trade-off" | **Multi-objective** |

## Use Cases

### 1. Low-Power IoT Device
```json
{
  "intent": "minimize power for battery-powered IoT sensor",
  "constraints": {
    "max_power_mw": 5.0,
    "min_lifetime_years": 5.0
  },
  "num_designs": 20,
  "vdd": 1.0
}
```

**Output:** Ultra-low power design suitable for years of battery operation

### 2. High-Performance Server
```json
{
  "intent": "maximize frequency for data center performance",
  "constraints": {
    "max_power_mw": 20.0,
    "min_lifetime_years": 3.0
  },
  "num_designs": 20,
  "vdd": 1.8,
  "temp": 85.0
}
```

**Output:** High-frequency design optimized for performance

### 3. Automotive Electronics
```json
{
  "intent": "balanced design for automotive with high reliability",
  "constraints": {
    "min_lifetime_years": 15.0
  },
  "num_designs": 25,
  "temp": 90.0
}
```

**Output:** Balanced design with extended lifetime for 15+ years

### 4. Consumer Electronics
```json
{
  "intent": "balanced power and performance for smartphone",
  "num_designs": 30,
  "vdd": 1.5,
  "temp": 50.0
}
```

**Output:** Balanced design with multiple trade-off options

## Response Structure

```
OrchestratorResponse
├── intent (str)                          - Parsed intent
├── constraints (dict)                    - Active constraints
├── best_design (OrchestratorDesign)      - Optimal design
├── pareto_front (list)                   - 10 best alternatives
├── best_design_explanation (dict)        - SHAP analysis
├── design_count (int)                    - Designs evaluated
├── dominant_metric (str)                 - Primary objective
├── trade_offs (dict)                     - Pareto statistics
└── recommendations (list)                - Engineering insights
```

## Best Design Fields

```
{
  "design_id": "design_N",
  "wn": 1.25,                    # NMOS transistor width (μm)
  "wp": 2.50,                    # PMOS transistor width (μm)
  "vdd": 1.2,                    # Supply voltage (V)
  "temp": 27.0,                  # Operating temperature (°C)
  "cl_ff": 10.0,                 # Load capacitance (fF)
  
  "power_mw": 2.45,              # Power consumption (mW)
  "frequency_ghz": 1.85,         # Operating frequency (GHz)
  "delay_ps": 0.54,              # Gate delay (ps)
  
  "reliability_score": 0.95,     # [0-1] health (1=fresh, 0=failed)
  "lifetime_years": 25.3,        # Device lifetime estimate (years)
  "dominant_failure_mode": "HCI", # Main degradation: NBTI|HCI|EM
  
  "prediction_confidence": 0.92  # ML model confidence [0-1]
}
```

## Pareto Front Explained

The `pareto_front` contains designs where **no design is strictly better** across all metrics:

- **Design A:** Low power, medium frequency
- **Design B:** Medium power, high frequency
- **Design C:** High reliability, medium power

You cannot improve one without sacrificing another. That's why it's called the **Pareto frontier**.

## Trade-Offs Dictionary

```json
{
  "power_range_mw": [2.1, 4.8],          // Min-max power on frontier
  "frequency_range_ghz": [1.2, 2.8],     // Min-max frequency on frontier
  "reliability_range": [0.88, 0.98],     // Min-max reliability on frontier
  "designs_on_frontier": 8                // Number of Pareto-optimal designs
}
```

## SHAP Explanations

Shows which parameters impact the best design:

```json
{
  "method": "shap",
  "output": "power",
  "base_value": 2.1,              // Average base power (mW)
  "prediction_value": 2.45,       // Actual predicted power (mW)
  "contributions": {
    "vdd": 0.45,                  // VDD adds +0.45 mW
    "wn": -0.15,                  // NMOS width reduces -0.15 mW
    "temp": 0.12,                 // Temperature adds +0.12 mW
    "wp": 0.08                    // PMOS width adds +0.08 mW
  }
}
```

**Interpretation:** 
- Base power estimate: 2.1 mW
- VDD effect: +0.45 mW (increases power)
- Reducing wn: -0.15 mW (decreases power)
- Other effects: +0.20 mW
- **Total: 2.1 + 0.45 - 0.15 + 0.20 = 2.6 mW** (approximately actual 2.45)

## Constraints

### Default Constraints
```json
{
  "max_power_mw": 10.0,           // Maximum power budget
  "min_frequency_ghz": 0.5,       // Minimum performance requirement
  "min_lifetime_years": 5.0,      // Minimum device lifetime
  "max_temp_c": 100.0             // Maximum operating temperature
}
```

### Override Constraints
```json
{
  "constraints": {
    "max_power_mw": 5.0,          // Override max power
    "min_frequency_ghz": 1.5,     // Override min frequency
    "min_lifetime_years": 10.0    // Override min lifetime
  }
}
```

## Testing

### Python Test
```bash
python test_orchestrator.py
```

Runs 3 test scenarios:
1. Minimize power
2. Maximize frequency
3. Balanced design

### cURL Tests
```bash
bash test_orchestrator.sh
```

Provides 4 curl examples with expected response formats

## Common Patterns

### Pattern 1: Aggressive Power Minimization
```json
{
  "intent": "minimize power",
  "constraints": {"max_power_mw": 2.0},
  "vdd": 0.9
}
```

### Pattern 2: Maximum Performance
```json
{
  "intent": "maximize frequency",
  "constraints": {"max_power_mw": 20.0},
  "vdd": 1.8,
  "temp": 85.0
}
```

### Pattern 3: Reliability Focus
```json
{
  "intent": "improve reliability",
  "constraints": {"min_lifetime_years": 15.0},
  "vdd": 1.0,
  "temp": 27.0
}
```

### Pattern 4: Explore Extensively
```json
{
  "intent": "find best design",
  "num_designs": 40,
  "vdd": 1.5
}
```

## Performance Tips

- **Fewer designs (10):** Fast (~1 sec), less thorough
- **Default designs (20):** Balanced (2-3 sec)
- **More designs (30+):** Thorough (5+ sec)

## Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| 503 Service Unavailable | ML models not trained | Train models using /predict endpoint |
| 400 Bad Request | No designs satisfy constraints | Relax constraints (increase max_power, decrease min_freq) |
| 500 Internal Server Error | Processing error | Check logs, retry with different parameters |

## Integration

The orchestrator automatically calls:

1. **ML Predictor** - Fast performance estimation
2. **Reliability Model** - Lifetime assessment
3. **SHAP Explainer** - Feature importance

All happen transparently under the hood.

## Next Steps

1. **Try the examples:** Use cURL or Python test script
2. **Explore trade-offs:** Review pareto_front for alternatives
3. **Understand decisions:** Read best_design_explanation
4. **Read recommendations:** Get domain-specific insights
5. **Implement best design:** Use wn, wp values in hardware

---

**Ready to explore your design space!** 🚀

For detailed documentation, see: [ORCHESTRATOR_API.md](ORCHESTRATOR_API.md)
