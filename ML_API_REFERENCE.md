# ML Optimization API Reference

**Complete endpoint documentation for POST `/api/v1/projects/{project_id}/optimize-ml`**

---

## Endpoint Overview

**Method:** `POST`  
**Path:** `/api/v1/projects/{project_id}/optimize-ml`  
**Version:** v1  
**Authentication:** Bearer token required  
**Rate Limit:** 100 requests/minute per user  

---

## Request

### URL Parameters

| Parameter | Type | Required | Example |
|-----------|------|----------|---------|
| `project_id` | integer | Yes | 42 |

### Headers

```
Authorization: Bearer <your_token>
Content-Type: application/json
```

### Request Body

**Type:** `MLOptimizationRequest`

```typescript
{
  "baseline_params": {
    "wn": number,           // nMOS width (100-10000 nm)
    "wp": number,           // pMOS width (100-10000 nm)
    "vdd": number,          // Supply voltage (0.5-3.0 V)
    "cl": number,           // Load capacitance (1e-15 to 1e-9 F)
    "temp": number,         // Temperature (-40 to 125 °C)
    "tech_node": number,    // Technology node (3-28 nm) [OPTIONAL]
    "corner": string,       // Process corner: "TT"|"SS"|"FF"|"SF"|"FS" [OPTIONAL]
    "corner_factor": number // Corner multiplier (0.78-1.25) [OPTIONAL]
  },
  
  "objectives": {
    // Multi-objective weights (sum should ≈ 1.0)
    // Positive = maximize, negative = minimize
    
    "frequency": number,        // GHz (0 to 1) [OPTIONAL]
    "power": number,            // mW (-1 to 0) [OPTIONAL]
    "delay": number,            // ps (-1 to 0) [OPTIONAL]
    "gain": number,             // V/V (0 to 1) [OPTIONAL]
    "health_score": number      // 0-1 (0 to 1) [OPTIONAL]
  },
  
  "model_version": string,      // Model checkpoint: "default"|"physics" [OPTIONAL, default: "default"]
  "num_candidates": integer     // Candidates to evaluate (10-10000, default: 100) [OPTIONAL]
}
```

### Request Examples

#### Example 1: Basic Request (High Frequency, Low Power)

```json
{
  "baseline_params": {
    "wn": 500,
    "wp": 1000,
    "vdd": 1.2,
    "cl": 1e-12,
    "temp": 27,
    "tech_node": 7.0,
    "corner": "TT"
  },
  "objectives": {
    "frequency": 0.5,
    "power": -0.3,
    "health_score": 0.2
  },
  "model_version": "default",
  "num_candidates": 100
}
```

#### Example 2: Advanced Request (Custom Model, More Candidates)

```json
{
  "baseline_params": {
    "wn": 250,
    "wp": 500,
    "vdd": 0.9,
    "cl": 5e-13,
    "temp": 85,
    "tech_node": 5.0,
    "corner": "SS",
    "corner_factor": 0.9
  },
  "objectives": {
    "frequency": 0.3,
    "power": -0.4,
    "delay": -0.2,
    "gain": 0.05,
    "health_score": 0.05
  },
  "model_version": "physics",
  "num_candidates": 500
}
```

#### Example 3: Minimal Request (Use Defaults)

```json
{
  "baseline_params": {
    "wn": 500,
    "wp": 1000,
    "vdd": 1.2,
    "cl": 1e-12,
    "temp": 27
  },
  "objectives": {
    "frequency": 0.4,
    "power": -0.3,
    "health_score": 0.3
  }
}
```

---

## Response

### Success Response (HTTP 200)

**Type:** `MLOptimizationResponse`

```typescript
{
  // Job metadata
  "job_id": number,                    // Unique job ID
  "status": string,                    // "completed" | "failed"
  "project_id": number,                // Project being optimized
  
  // Optimized parameters
  "optimized_params": {
    "wn": number,                      // Optimized nMOS width (nm)
    "wp": number,                      // Optimized pMOS width (nm)
    "vdd": number,                     // Optimized supply voltage (V)
    "cl": number,                      // Optimized load capacitance (F)
    // ... other parameters if provided
  },
  
  // Predicted performance at optimized params
  "predicted_metrics": {
    "frequency": number,               // GHz
    "delay": number,                   // ps
    "power": number,                   // mW
    "gain": number,                    // V/V
    "health_score": number             // 0-1
  },
  
  // CONFIDENCE: Key metric for decision-making
  "confidence_score": number,          // 0-1 (from MC Dropout)
  
  // Per-metric uncertainty (standard deviation)
  "uncertainty_estimates": {
    "frequency": number,               // Std dev in GHz
    "delay": number,                   // Std dev in ps
    "power": number,                   // Std dev in mW
    "gain": number,                    // Std dev in V/V
    "health_score": number             // Std dev
  },
  
  // ML-specific metadata
  "model_version": string,             // "default" | "physics" | custom
  "is_prediction": true,               // Always true (not simulation)
  "execution_time_ms": number,         // Computation time
  
  // Timestamps
  "created_at": string,                // ISO 8601: "2024-04-12T10:30:45"
  "completed_at": string               // ISO 8601
}
```

### Success Response Example

```json
{
  "job_id": 42,
  "status": "completed",
  "project_id": 1,
  
  "optimized_params": {
    "wn": 548.3,
    "wp": 1156.4,
    "vdd": 1.18,
    "cl": 1.05e-12,
    "temp": 27,
    "tech_node": 7.0,
    "corner": "TT"
  },
  
  "predicted_metrics": {
    "frequency": 2.451,
    "delay": 145.3,
    "power": 0.784,
    "gain": 1.023,
    "health_score": 0.921
  },
  
  "confidence_score": 0.8347,
  
  "uncertainty_estimates": {
    "frequency": 0.124,
    "delay": 8.7,
    "power": 0.045,
    "gain": 0.052,
    "health_score": 0.082
  },
  
  "model_version": "default",
  "is_prediction": true,
  "execution_time_ms": 45.2,
  
  "created_at": "2024-04-12T10:30:45Z",
  "completed_at": "2024-04-12T10:30:45.045Z"
}
```

### Error Response (HTTP 4xx/5xx)

#### 400 - Bad Request

**Problem:** Invalid parameters

```json
{
  "status": "error",
  "code": "INVALID_REQUEST",
  "message": "Invalid parameters in baseline_params",
  "details": {
    "wn": "Must be between 100 and 10000"
  }
}
```

#### 404 - Not Found

**Problem:** Project doesn't exist

```json
{
  "status": "error",
  "code": "PROJECT_NOT_FOUND",
  "message": "Project 999 not found"
}
```

#### 500 - Internal Server Error

**Problem:** ML model unavailable, falls back to simulation

```json
{
  "status": "error",
  "code": "ML_MODEL_UNAVAILABLE",
  "message": "Model 'default' not found. Falling back to simulation...",
  "fallback_method": "simulation",
  "fallback_status": "in_progress"
}
```

---

## Parameter Guide

### baseline_params

**Required fields** (must provide):

| Field | Min | Max | Default | Unit | Notes |
|-------|-----|-----|---------|------|-------|
| `wn` | 100 | 10000 | - | nm | nMOS transistor width |
| `wp` | 100 | 10000 | - | nm | pMOS transistor width |
| `vdd` | 0.5 | 3.0 | - | V | Supply voltage |
| `cl` | 1e-15 | 1e-9 | - | F | Load capacitance |
| `temp` | -40 | 125 | - | °C | Temperature |

**Optional fields** (use defaults if omitted):

| Field | Min | Max | Default | Unit |
|-------|-----|-----|---------|------|
| `tech_node` | 3 | 28 | 7.0 | nm |
| `corner` | - | - | "TT" | Process corner |
| `corner_factor` | 0.78 | 1.25 | 1.0 | Multiplier |

**Corner Values:**
- `"TT"` - Typical-Typical (default)
- `"SS"` - Slow-Slow (slower, lower power)
- `"FF"` - Fast-Fast (faster, higher power)
- `"SF"` - Slow nMOS, Fast pMOS
- `"FS"` - Fast nMOS, Slow pMOS

### objectives

**Weight Distribution:**

All weights should sum to approximately 1.0 (e.g., 0.4 + 0.3 + 0.3 = 1.0).

| Objective | Range | Sign | Meaning |
|-----------|-------|------|---------|
| `frequency` | 0 to 1 | Positive | Maximize frequency (GHz) |
| `power` | -1 to 0 | Negative | Minimize power (mW) |
| `delay` | -1 to 0 | Negative | Minimize delay (ps) |
| `gain` | 0 to 1 | Positive | Maximize gain (V/V) |
| `health_score` | 0 to 1 | Positive | Maximize reliability (0-1) |

**Example weight combinations:**

```json
{
  "high_frequency": {
    "frequency": 0.60,
    "power": -0.25,
    "health_score": 0.15
  },
  "balanced": {
    "frequency": 0.35,
    "power": -0.35,
    "gain": 0.20,
    "health_score": 0.10
  },
  "low_power": {
    "frequency": 0.20,
    "power": -0.60,
    "health_score": 0.20
  }
}
```

### model_version

**Available models:**

| Version | Description | Training Data | Speed | Accuracy |
|---------|-------------|----------------|-------|----------|
| `"default"` | Synthetic physics-based | Generated equations | Fast | 92-96% |
| `"physics"` | SPICE simulated | Real simulator | Slower | 95-98% |

**Selection guide:**
- Use `"default"` for interactive design (fastest)
- Use `"physics"` when accuracy critical (slower but better)

### num_candidates

**Behavior:**

| Value | Time | Quality | Use Case |
|-------|------|---------|----------|
| 10-50 | 20-50ms | Basic | Quick exploration |
| 50-200 | 50-150ms | Good | Normal design |
| 200-1000 | 150-500ms | Better | Detailed optimization |
| 1000-10000 | 500ms-2s | Best | Final verification |

**Note:** Larger values give better results but take longer (still <2s vs. 10-20s for simulation).

---

## Confidence Score Guide

### What is confidence_score?

The `confidence_score` (0-1) indicates how confident the model is in its prediction, calculated from MC Dropout uncertainty:

```
confidence = 1 / (1 + average_relative_uncertainty)
```

Higher = more confident (less uncertain). **Use this to decide whether to trust the prediction.**

### Decision Table

| Score | Interpretation | Action |
|-------|----------------|--------|
| **0.90-1.00** | ⭐⭐⭐⭐⭐ Very High | Use directly in production |
| **0.80-0.90** | ⭐⭐⭐⭐ High | Safe to use with monitoring |
| **0.70-0.80** | ⭐⭐⭐ Medium | May need verification |
| **0.60-0.70** | ⭐⭐ Low | Recommend simulation |
| **<0.60** | ⭐ Very Low | Always verify with simulation |

### Step 1: Check Confidence

```python
response = requests.post(endpoint, json=request).json()
confidence = response["confidence_score"]

if confidence > 0.85:
    # ✓ Use ML result directly
    params = response["optimized_params"]
else:
    # ✗ Confidence too low - what to do?
    pass
```

### Step 2: Use Uncertainty Estimates

If uncertain, check ranges:

```python
frequency = response["predicted_metrics"]["frequency"]
uncertainty = response["uncertainty_estimates"]["frequency"]

print(f"Frequency: {frequency} GHz")
print(f"Range: {frequency - uncertainty} to {frequency + uncertainty} GHz")
print(f"This means: 68% probability within this range")
```

### Step 3: Fallback Strategy

```python
if response["confidence_score"] < 0.75:
    # Monte Carlo interpretation:
    # At 50 MC samples, 1-std-dev captures ~68% of predictions
    uncertainty = response["uncertainty_estimates"]
    
    # Option A: Use with caution
    proceed_with_caution()
    
    # Option B: Request more evaluation
    response2 = request_with_more_candidates(num_candidates=500)
    
    # Option C: Fall back to simulation
    sim_result = run_simulation(response["optimized_params"])
```

---

## Workflows & Examples

### Workflow 1: Standard ML Optimization

```python
import requests
import json

# Step 1: Prepare request
request_body = {
    "baseline_params": {
        "wn": 500, "wp": 1000, "vdd": 1.2, "cl": 1e-12, 
        "temp": 27, "tech_node": 7.0, "corner": "TT"
    },
    "objectives": {
        "frequency": 0.4,
        "power": -0.3,
        "health_score": 0.3
    },
    "model_version": "default",
    "num_candidates": 100
}

# Step 2: Send request
response = requests.post(
    "http://api.siliquesta.io/api/v1/projects/1/optimize-ml",
    json=request_body,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

result = response.json()

# Step 3: Check result
if result["confidence_score"] > 0.80:
    print(f"✓ Optimized: {result['optimized_params']}")
    print(f"✓ Performance: {result['predicted_metrics']}")
    print(f"✓ Confidence: {result['confidence_score']:.2f} ⭐")
else:
    print(f"⚠ Low confidence ({result['confidence_score']:.2f})")
    print(f"Uncertainty: {result['uncertainty_estimates']}")
```

### Workflow 2: High-Accuracy Mode (More Candidates)

```python
# When you need better results
response = requests.post(
    endpoint,
    json={
        ...request_body...,
        "num_candidates": 1000,  # More search
        "model_version": "physics"  # More accurate model
    }
)

# Results are more reliable but take slightly longer
# (still <500ms vs. 2-5s for simulation)
```

### Workflow 3: Batch Optimization

```python
import concurrent.futures

parameters_to_optimize = [
    {"wn": 300, "wp": 600, ...},
    {"wn": 400, "wp": 800, ...},
    {"wn": 500, "wp": 1000, ...},
]

def optimize_one(params):
    return requests.post(
        endpoint,
        json={"baseline_params": params, "objectives": {...}}
    ).json()

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(optimize_one, parameters_to_optimize)
    
for result in results:
    print(f"Confidence: {result['confidence_score']}")
    print(f"Optimized: {result['optimized_params']}")
```

### Workflow 4: Comparison (ML vs Simulation)

```python
# Get ML result first (fast)
ml_response = requests.post(endpoint, json={...}).json()
ml_time = ml_response["execution_time_ms"]

# If confidence low, also run simulation
if ml_response["confidence_score"] < 0.75:
    sim_result = requests.post(
        f"/api/v1/projects/{project_id}/optimize",  # Simulation endpoint
        json={...}
    ).json()
    sim_time = sim_result.get("execution_time_ms", 3000)
    
    # Compare
    print(f"ML ({ml_time}ms): {ml_response['predicted_metrics']['frequency']:.3f} GHz")
    print(f"Sim ({sim_time}ms): {sim_result['predicted_metrics']['frequency']:.3f} GHz")
    
    # Use better result
    if ml_response["confidence_score"] > 0.80:
        use_ml = True
    else:
        use_ml = False
else:
    use_ml = True

result = ml_response if use_ml else sim_result
```

---

## Limits & Constraints

### Rate Limiting

```
100 requests/minute per API key
1000 requests/minute per IP (burst)
```

**Response header when rate limited:**

```
HTTP 429 Too Many Requests

X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2024-04-12T10:31:45Z
```

### Request Timeout

```
Timeout: 30 seconds
Typical response: 30-150ms
```

### Parameter Ranges

**Enforced validation:**

| Parameter | Min | Max | Unit |
|-----------|-----|-----|------|
| wn, wp | 100 | 10000 | nm |
| vdd | 0.5 | 3.0 | V |
| cl | 1e-15 | 1e-9 | F |
| temp | -40 | 125 | °C |
| tech_node | 3 | 28 | nm |
| corner_factor | 0.78 | 1.25 | - |

**Out-of-range values:**

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Parameter validation failed",
  "details": {
    "wn": "Value 50000 exceeds maximum 10000"
  }
}
```

---

## SDK Usage (TypeScript/JavaScript)

### Installation

```bash
npm install @siliquesta/client
```

### Usage

```typescript
import { SiliquestaClient } from "@siliquesta/client";

const client = new SiliquestaClient({
  apiKey: "YOUR_API_KEY",
  baseUrl: "https://api.siliquesta.io"
});

// Optimize
const result = await client.projects.optimizeML(projectId, {
  baseline_params: {
    wn: 500,
    wp: 1000,
    vdd: 1.2,
    cl: 1e-12,
    temp: 27
  },
  objectives: {
    frequency: 0.4,
    power: -0.3,
    health_score: 0.3
  }
});

// Check confidence
if (result.confidence_score > 0.85) {
  console.log("✓ High confidence prediction");
  console.log(result.optimized_params);
} else {
  console.log("⚠ Low confidence, uncertainty:");
  console.log(result.uncertainty_estimates);
}
```

---

## Troubleshooting

### Problem: Low confidence_score

**Possible causes:**
1. Parameters outside training distribution
2. Unusual objective weights
3. Low model accuracy on this design point

**Solutions:**
```python
# Solution 1: Use more candidates
response = request_with_more_candidates(num_candidates=500)

# Solution 2: Use higher-accuracy model
response = request_api(model_version="physics")

# Solution 3: Verify with simulation
sim_result = simulate(response["optimized_params"])

# Solution 4: Check parameter ranges
if baseline["wn"] < 200 or baseline["wn"] > 5000:
    print("Parameters outside typical range")
```

### Problem: "Model not found" error

**Cause:** ML model checkpoint not trained yet

**Solution:**
```bash
# Train the model
python backend/scripts/setup_ml_model.py
```

### Problem: High uncertainty in predictions

**Interpretation:** Model is uncertain about this design point

**Response:**
```python
# High uncertainty = wider confidence interval
for metric, uncertainty in result["uncertainty_estimates"].items():
    value = result["predicted_metrics"][metric]
    low = value - uncertainty
    high = value + uncertainty
    print(f"{metric}: {value} ± {uncertainty} ({low} to {high})")

# Decision:
if result["confidence_score"] > 0.70:
    use_result_with_caveats()
else:
    verify_with_simulation()
```

### Problem: Timeout (>10 seconds)

**Cause:** System overloaded or num_candidates too high

**Solution:**
```python
# Reduce candidates
response = request_api(num_candidates=50)  # Was 10000

# Or use faster model
response = request_api(model_version="default")  # Was "physics"
```

---

## Summary Quick Reference

### Endpoint
```
POST /api/v1/projects/{project_id}/optimize-ml
```

### Key Features
- ✅ 50-100x faster than simulation
- ✅ Confidence scores (0-1) for decision making
- ✅ Uncertainty quantification per metric
- ✅ Multi-objective optimization
- ✅ Automatic fallback to simulation if needed

### Decision Flow
```
confidence > 0.85? → YES → Use ML result ✓
                  → NO  → Use simulation OR request higher accuracy
```

### Response Time
```
Typical: 30-150ms
Max: 500ms (with 1000+ candidates)
Respects: <2s always (vs. 2-5s for simulation)
```

### Confidence Interpretation
```
0.90+: ⭐⭐⭐⭐⭐ Use directly
0.80-0.90: ⭐⭐⭐⭐ Use with confidence
0.70-0.80: ⭐⭐⭐ May verify
0.60-0.70: ⭐⭐ Recommend simulation
<0.60: ⭐ Always simulate
```

