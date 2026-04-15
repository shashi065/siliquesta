# SILIQUESTA Agentic Orchestrator - Complete Guide

## Overview

The **Agentic Orchestrator** is an execution-based autonomous design agent that coordinates three AI/ML components:

1. **NSGA-II Optimizer** - Multi-objective evolutionary optimization
2. **Digital Twin** - GPU-accelerated surrogate model predictions
3. **Reliability Engine** - Physics-based device degradation analysis

**Key Principle:** No chatbot responses. Only execution-based reasoning and design decisions backed by actual computations.

---

## Architecture

```
Natural Language Design Intent
         |
         v
    [Parse Intent]  → Extract targets, constraints, parameters
         |
         v
   [Plan Execution]  → Decide component execution order & intensity
         |
    +----+----+
    |    |    |
    v    v    v
  [NSGA-II] [DT] [Reliability]
    |      |      |
    +------+------+
         |
         v
  [Combine Results]  → Merge outputs, compute scores
         |
         v
   [Rank Designs]   → Pareto front, best design selection
         |
         v
 [Generate Reasoning]  → Why this design, confidence scores
         |
         v
  [Return Results]   → Best design + Pareto front + Explanation
```

---

## API Usage Examples

### 1. Basic Design Optimization

**Request:** Minimize power consumption with frequency constraint

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/orchestrator/optimize",
    json={
        "design_specification": "minimize power under 100mW with minimum 500MHz frequency",
        "optimization_layer": "full",
        "include_reliability_analysis": True
    }
)

result = response.json()

# Results structure:
# - best_design: {wn, wp, vdd, power_mw, frequency_mhz, reliability_score, ...}
# - best_design_reasoning: Why this design was selected
# - pareto_front: List of alternative designs (tradeoff options)
# - overall_confidence: 0.0-1.0 confidence score
# - component_confidence: Individual component confidence scores
```

### 2. High-Performance Design

```python
response = requests.post(
    "http://localhost:8000/api/v1/orchestrator/optimize",
    json={
        "design_specification": "maximize frequency for high performance, 28nm tech node, aggressive optimization",
        "optimization_layer": "full",
        "enable_distributed_optimization": True  # Use Ray for intensive search
    }
)

best = response.json()["best_design"]
print(f"Best design frequency: {best['frequency_mhz']:.0f} MHz")
print(f"Power consumption: {best['power_mw']:.2f} mW")
```

### 3. Reliability-Focused Design

```python
response = requests.post(
    "http://localhost:8000/api/v1/orchestrator/optimize",
    json={
        "design_specification": "prioritize device reliability, 10 year lifetime, temperature 125C",
        "include_reliability_analysis": True
    }
)

best = response.json()["best_design"]
print(f"Device lifetime: {best['device_lifetime_years']:.1f} years")
print(f"Reliability score: {best['reliability_score']:.2%}")
```

### 4. Parse Intent (Validate Specification)

Before running optimization, validate how the agent will interpret your specification:

```python
response = requests.post(
    "http://localhost:8000/api/v1/orchestrator/parse-intent",
    params={
        "specification": "minimize power under 100mW with >500MHz, 28nm tech"
    }
)

intent = response.json()["parsed_intent"]
print(f"Target: {intent['primary_target']}")
print(f"Constraints: {intent['max_power_mw']}mW, {intent['min_frequency_mhz']}MHz")
print(f"Tech: {intent['tech_node_nm']}nm")
```

### 5. Batch Optimization

```python
specifications = [
    "minimize power under 100mW",
    "maximize frequency with 500mW budget",
    "balanced design for 50mW and 300MHz",
]

response = requests.post(
    "http://localhost:8000/api/v1/orchestrator/batch-optimize",
    json={"specifications": specifications}
)

job_id = response.json()["job_id"]
# Background optimization running, poll for results
```

### 6. Get Capabilities

```python
response = requests.get(
    "http://localhost:8000/api/v1/orchestrator/capabilities"
)

capabilities = response.json()

print("Supported targets:", capabilities["supported_targets"])
print("Available components:", capabilities["components"].keys())
print("Execution modes:", capabilities["execution_modes"])
```

---

## Response Structure

### Full Optimization Response

```json
{
  "request_id": "req_1712000000000",
  "timestamp": "2024-04-14T10:30:00",
  
  "design_intent": {
    "primary_target": "power_minimal",
    "max_power": 100.0,
    "min_frequency": 500.0,
    "tech_node": 28,
    "corner": "TT"
  },
  
  "best_design": {
    "wn": 2.5,
    "wp": 5.2,
    "vdd": 0.9,
    "power_mw": 87.3,
    "frequency_mhz": 542.1,
    "delay_ns": 1.84,
    "reliability_score": 0.81,
    "device_lifetime_years": 8.1,
    "nbti_lifetime_years": 10.2,
    "hci_lifetime_years": 8.1,
    "em_lifetime_years": 12.5,
    "multi_objective_score": 0.823,
    "pareto_rank": 1
  },
  
  "best_design_reasoning": "Selection Reasoning: ...",
  
  "pareto_front": [
    { "same structure as best_design, pareto_rank": 1 },
    { "pareto_rank": 2 },
    { "pareto_rank": 3 },
    { "pareto_rank": 4 },
    { "pareto_rank": 5 }
  ],
  
  "execution_reasoning": "Execution Plan: ...",
  
  "constraint_satisfaction": {
    "max_power_met": true,
    "min_frequency_met": true,
    "min_lifetime_met": true,
    "process_corner_valid": true,
    "temperature_within_range": true
  },
  
  "overall_confidence": 0.847,
  
  "component_confidence": {
    "prediction_confidence": 0.82,
    "constraint_satisfaction": 1.0,
    "pareto_ranking": 1.0,
    "component_agreement": 0.89,
    "design_space_coverage": 0.92
  },
  
  "components_evaluated": ["optimizer", "digital_twin", "reliability"],
  
  "execution_time_ms": 3847.2
}
```

---

## Natural Language Intent Parsing

The orchestrator automatically extracts:

### Optimization Targets
| Phrase | Target | Behavior |
|--------|--------|----------|
| "minimize power", "low power" | `power_minimal` | Minimize power consumption |
| "maximize frequency", "high performance" | `frequency_maximal` | Maximize operating frequency |
| "efficiency", "ppa" | `ppa_optimal` | Optimize Power-Performance-Area |
| "reliability", "lifetime" | `reliability_focused` | Maximize device lifetime |
| (default) | `balanced` | Equal weight to all objectives |

### Constraint Extraction
| Pattern | Extracts |
|---------|----------|
| "under 100mW", "power budget 50mW" | `max_power` |
| ">500MHz", "minimum 1GHz", "1000MHz" | `min_frequency` |
| "10 year lifetime" | `min_lifetime` |
| "area < 1000um^2" | `max_area` |

### Process Parameters
| Pattern | Extracts |
|---------|----------|
| "28nm", "7nm", "5nm" | `tech_node` |
| "TT", "FF", "SS", "SF", "FS" | Process `corner` |
| "25C", "125C", "-40C" | Operating conditions |

### Optimization Intensity
| Phrase | Intensity | Population | Generations |
|--------|-----------|------------|-------------|
| "aggressive" | intensive | 300 | 100 |
| "normal", "standard" | standard | 100 | 50 |
| "quick", "fast" | light | 50 | 20 |

---

## Component Contributions

### 1. NSGA-II Optimizer
- **Role:** Generate Pareto-optimal design space
- **Output:** Population of non-dominated designs
- **Contribution to Confidence:** Pareto ranking (rank 1 = highest confidence)
- **Execution Time:** 100-300ms per generation

### 2. Digital Twin (GPU-Accelerated)
- **Role:** Fast surrogate model predictions
- **Models:** XGBoost + PyTorch neural networks
- **Output:** Power, frequency, delay predictions with confidence
- **Contribution to Confidence:** Prediction confidence (0.7-0.95)
- **Execution Time:** <1ms per prediction with GPU

### 3. Reliability Engine
- **Role:** Physics-based degradation analysis
- **Mechanisms:** NBTI, HCI, Electromigration
- **Output:** Device lifetime and reliability score
- **Contribution to Confidence:** Reliability confidence (0.7-0.85)
- **Execution Time:** <10ms per analysis

---

## Confidence Scoring

The orchestrator computes confidence from multiple factors:

```python
confidence_components = {
    "prediction_confidence": avg(power, freq, reliability confidence),  # 0.5-0.95
    "constraint_satisfaction": 1.0 if met else 0.7,                    # 0.7-1.0
    "pareto_ranking": 1.0 - (rank - 1) * 0.1,                          # 0.1-1.0
    "component_agreement": active_components / 3,                       # 0.33-1.0
    "design_space_coverage": min(1.0, n_designs / 10)                  # 0.0-1.0
}

overall_confidence = mean(all components)
```

**Interpretation:**
- **0.9-1.0** - High confidence, trusted recommendation
- **0.7-0.9** - Good confidence, reliable design
- **0.5-0.7** - Moderate confidence, consider alternatives
- **<0.5** - Low confidence, verify results

---

## Design Intent Structure

```python
@dataclass
class DesignIntent:
    primary_target: OptimizationTarget           # What to optimize
    wn_range: Tuple[float, float] = (0.1, 10.0)  # NMOS width range
    wp_range: Tuple[float, float] = (0.1, 10.0)  # PMOS width range
    vdd_range: Tuple[float, float] = (0.8, 1.8)  # Supply voltage
    temp_range: Tuple[float, float] = (0, 125)   # Temperature
    
    # Hard constraints (must be met)
    max_power: Optional[float] = None             # mW
    min_frequency: Optional[float] = None         # MHz
    min_lifetime: Optional[float] = None          # Years
    max_area: Optional[float] = None              # um^2
    
    # Soft preferences
    corner: str = "TT"                            # Process corner
    tech_node: int = 28                           # nm
    optimization_priority: str = "balanced"       # "aggressive"/"balanced"/"conservative"
```

---

## Execution Plan Reasoning

Based on design intent, the orchestrator adapts its execution:

### For Power-Minimal Designs
```
1. Initialize standard NSGA-II (100 pop, 50 gen)
2. Run optimization focusing on minimizing power
3. Enhance winners with Digital Twin predictions
4. Verify reliability meets lifetime targets
5. Select designs with lowest power from Pareto front
6. Confidence boost: constraint satisfaction
```

### For Aggressive Performance
```
1. Initialize intensive NSGA-II (300 pop, 100 gen)
2. Use GPU acceleration for fitness evaluation
3. Distribute to Ray workers if enabled
4. Enhance all designs with Digital Twin
5. Filter by frequency and reliability
6. Select fastest designs from Pareto front
7. Confidence boost: deep design space exploration
```

### For Reliability-Focused
```
1. Initialize standard NSGA-II
2. Run with reliability constraints enforced
3. Enhance with Digital Twin + Reliability Engine
4. Deep reliability analysis (NBTI, HCI, EM)
5. Select designs with highest device lifetime
6. Confidence boost: comprehensive degradation analysis
```

---

## Python Client Example

```python
from siliquesta_client import OrchestratorClient

# Initialize client
client = OrchestratorClient(api_url="http://localhost:8000")

# Simple optimization
result = client.optimize(
    design_specification="minimize power under 100mW with >500MHz"
)

# Access results
best_design = result.best_design
print(f"Best Design: {best_design.wn}um x {best_design.wp}um @ {best_design.vdd}V")
print(f"Performance: {best_design.frequency_mhz:.0f} MHz, {best_design.power_mw:.1f} mW")
print(f"Lifetime: {best_design.device_lifetime_years:.1f} years")
print(f"Confidence: {result.overall_confidence:.1%}")

# Alternative designs (Pareto front)
for i, design in enumerate(result.pareto_front):
    print(f"Option {i+1}: {design.frequency_mhz:.0f} MHz, {design.power_mw:.1f} mW")

# Why this design?
print("\nReasoning:")
print(result.best_design_reasoning)
```

---

## Monitoring & Diagnostics

### Get Health Status
```python
response = requests.get("http://localhost:8000/api/v1/orchestrator/health")
health = response.json()
print(f"Status: {health['status']}")
print(f"Components: {health['components_available']}")
print(f"Avg execution: {health['average_execution_time_ms']:.0f}ms")
print(f"Total optimizations: {health['total_optimizations_run']}")
```

### Get Execution History
```python
response = requests.get("http://localhost:8000/api/v1/orchestrator/execution-history?limit=10")
history = response.json()
print(f"Success rate: {history['success_rate_percent']:.1f}%")
for exec_info in history['recent_executions']:
    print(f"  {exec_info['timestamp']}: {exec_info['design_intent'][:50]}...")
```

### Explain Decision
```python
response = requests.post(
    f"http://localhost:8000/api/v1/orchestrator/explain-decision/{request_id}"
)
explanation = response.json()
print(explanation)
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Intent Parsing | <1ms | Deterministic |
| NSGA-II (100 pop, 50 gen) | 2-5s | CPU or GPU |
| Digital Twin Prediction (100 designs) | 50-150ms | GPU accelerated |
| Reliability Analysis (100 designs) | 100-500ms | CPU based |
| Results Aggregation | <100ms | Local |
| **Total (standard)** | **2-6s** | Full optimization |
| **Total (intensive)** | **10-30s** | Deep exploration |

---

## Integration with Backend Services

The orchestrator automatically integrates with:

1. **Digital Twin Service** (`/api/v1/twin/predict/ml`)
   - XGBoost surrogate model
   - GPU-accelerated predictions
   - Confidence scoring

2. **NSGA-II Optimizer** (`/api/v1/nsga2/optimize`)
   - Multi-objective evolutionary algorithm
   - Pareto front generation
   - Ray distributed support

3. **ML Predictions API** (`/api/v1/predict`)
   - CMOS parameter predictions
   - Model management

4. **Reliability Engine** (physics-based module)
   - NBTI, HCI, EM degradation
   - Device lifetime computation

---

## Error Handling & Graceful Degradation

If a component fails:

1. **Optimizer unavailable?** → Use random design sampling
2. **Digital Twin unavailable?** → Use simple physics model predictions
3. **Reliability unavailable?** → Assume nominal lifetime
4. **GPU unavailable?** → Automatically fall back to CPU
5. **Ray unavailable?** → Use sequential execution

Result: **System continues functioning with reduced precision.**

---

## Best Practices

1. **Start with parsed intent** - Validate the agent's understanding of your spec
2. **Use appropriate intensity** - Aggressive for critical designs, standard for most cases
3. **Check confidence scores** - High confidence (>0.8) indicates reliable recommendation
4. **Review Pareto front** - See design tradeoffs, select based on your preferences
5. **Monitor execution time** - Adjust intensity if needed for timing constraints
6. **Enable GPU** - 8-10x speedup for intensive optimizations
7. **Batch similar specs** - Amortize orchestrator initialization cost

---

## Future Enhancements

- [ ] Multi-level parallelism (data + model parallelism)
- [ ] Hybrid quantum-classical optimization
- [ ] Federated design optimization across teams
- [ ] Real-time design feedback and refinement
- [ ] Circuit-specific domain knowledge integration
- [ ] Active learning from design outcomes
- [ ] Automated constraint inference from requirements
- [ ] Stakeholder multi-objective negotiation

---

## References

- **NSGA-II:** Deb et al., "A fast and elitist multiobjective genetic algorithm: NSGA-II"
- **Digital Twin:** ML-based CMOS surrogate with XGBoost and PyTorch
- **Reliability:** Physics-based degradation models (NBTI, HCI, EM)
- **Orchestration:** Agentic design pattern with execution-based reasoning
