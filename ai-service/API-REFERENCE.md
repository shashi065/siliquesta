# AI Service API Documentation

Complete API reference for SILIQUESTA AI optimization microservice.

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required (service-to-service communication).

---

## Health & Status Endpoints

### Health Check
Get service health status.

**Endpoint:**
```
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-04-11T15:30:00Z"
}
```

**Use Case:** Monitor service availability

---

### Service Info
Get detailed service information with endpoints.

**Endpoint:**
```
GET /info
```

**Response (200 OK):**
```json
{
  "name": "SILIQUESTA AI Optimization Service",
  "version": "1.0.0",
  "description": "AI-powered circuit parameter optimization microservice",
  "environment": "development",
  "endpoints": {
    "health": "/health",
    "optimize": "/optimize",
    "docs": "/docs",
    "redoc": "/redoc"
  },
  "timestamp": "2024-04-11T15:30:00Z"
}
```

---

## Optimization Endpoint

### Optimize Circuit Parameters
Main optimization endpoint for circuit parameter tuning.

**Endpoint:**
```
POST /optimize
```

**Request Headers:**
```
Content-Type: application/json
```

### Request Body

**Full Example with All Parameters:**
```json
{
  "parameters": {
    "W_L_ratio": 10,
    "finger_ratio": 1,
    "supply_voltage": 1.8,
    "operating_frequency": 1e9,
    "load_capacitance": 1e-12,
    "technology_node": 28e-9,
    "temperature": 27,
    "bias_current": 1e-6,
    "device_mismatch": 0.01,
    "power_budget": 0.001,
    "area_budget": 1e-9
  },
  "objectives": {
    "minimize_power": true,
    "minimize_area": false,
    "maximize_speed": true,
    "maximize_gain": false
  },
  "method": "scipy",
  "max_iterations": 500,
  "tolerance": 1e-6
}
```

**Minimal Example (for quick tests):**
```json
{
  "parameters": {
    "W_L_ratio": 10,
    "supply_voltage": 1.8,
    "operating_frequency": 1e9,
    "load_capacitance": 1e-12
  }
}
```

---

### Request Parameters

#### Circuit Parameters (Required)

| Field | Type | Required | Range | Default | Description |
|-------|------|----------|-------|---------|-------------|
| `W_L_ratio` | float | Yes | > 0 | - | Transistor width/length ratio |
| `finger_ratio` | float | No | > 0 | 1 | Number of finger multipliers |
| `supply_voltage` | float | Yes | > 0 | - | Supply voltage in volts |
| `operating_frequency` | float | No | > 0 | 1e9 | Operating frequency in Hz |
| `load_capacitance` | float | No | > 0 | 1e-12 | Load capacitance in Farads |
| `technology_node` | float | No | > 0 | 28e-9 | Technology node in meters |
| `temperature` | float | No | - | 27 | Operating temperature in °C |
| `bias_current` | float | No | > 0 | 1e-6 | Bias current in Amperes |
| `device_mismatch` | float | No | >= 0 | 0.01 | Device mismatch percentage |
| `power_budget` | float | No | > 0 | null | Power budget constraint in Watts |
| `area_budget` | float | No | > 0 | null | Area budget constraint in m² |

#### Optimization Objectives (Optional)

```json
{
  "minimize_power": true,        // Reduce power consumption
  "minimize_area": false,        // Reduce chip area
  "maximize_speed": true,        // Increase speed/reduce delay
  "maximize_gain": false         // Increase circuit gain
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `minimize_power` | boolean | true | Minimize power consumption |
| `minimize_area` | boolean | false | Minimize chip area |
| `maximize_speed` | boolean | false | Maximize operating speed |
| `maximize_gain` | boolean | false | Maximize circuit gain |

#### Algorithm Options (Optional)

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `method` | string | "scipy" | scipy, ml, hybrid | Optimization algorithm |
| `max_iterations` | int | 500 | 1-10000 | Maximum iterations |
| `tolerance` | float | 1e-6 | > 0 | Convergence tolerance |

---

### Response

**Success Response (200 OK):**

```json
{
  "success": true,
  "optimized_parameters": {
    "W_L_ratio": 12.5,
    "finger_ratio": 1.2,
    "supply_voltage": 1.5,
    "operating_frequency": 1e9,
    "bias_current": 1.2e-6,
    "other_params": {}
  },
  "metrics_comparison": {
    "original": {
      "power_consumption": 0.0012,
      "propagation_delay": 1.5e-9,
      "gain": 15.2,
      "area": 2.5e-9,
      "slew_rate": 1.2e9,
      "noise_margin": 0.54
    },
    "optimized": {
      "power_consumption": 0.00085,
      "propagation_delay": 1.2e-9,
      "gain": 18.5,
      "area": 2.2e-9,
      "slew_rate": 1.5e9,
      "noise_margin": 0.58
    },
    "improvements": {
      "power_consumption": 29.17,
      "propagation_delay": 20.0,
      "gain": 21.71,
      "area": 12.0
    }
  },
  "overall_improvement": 20.67,
  "iterations_used": 127,
  "convergence": true,
  "execution_time": 2.34,
  "method_used": "scipy",
  "notes": "Optimization completed in 2.34s with convergence"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether optimization succeeded |
| `optimized_parameters` | object | Optimized circuit parameters |
| `metrics_comparison` | object | Original vs optimized metrics |
| `overall_improvement` | float | Overall improvement percentage |
| `iterations_used` | int | Number of iterations used |
| `convergence` | boolean | Whether algorithm converged |
| `execution_time` | float | Execution time in seconds |
| `method_used` | string | Which optimization method was used |
| `notes` | string | Additional notes about optimization |

#### Metrics Fields

| Metric | Unit | Description |
|--------|------|-------------|
| `power_consumption` | Watts (W) | Total power consumption |
| `propagation_delay` | Seconds (s) | Gate delay time |
| `gain` | Decibels (dB) | Circuit voltage gain |
| `area` | Square Meters (m²) | Circuit area |
| `slew_rate` | Volts/Second (V/s) | Output swing rate |
| `noise_margin` | Volts (V) | Noise immunity margin |

---

### Error Responses

#### Validation Error (400)
```json
{
  "error": "Validation Error",
  "message": "Invalid input",
  "details": {
    "W_L_ratio": "value must be greater than 0",
    "supply_voltage": "value must be greater than 0"
  },
  "timestamp": "2024-04-11T15:30:00Z"
}
```

#### Service Timeout (504)
```json
{
  "error": "Service Unavailable",
  "message": "Optimization timeout exceeded",
  "timestamp": "2024-04-11T15:30:00Z"
}
```

#### Server Error (500)
```json
{
  "error": "Internal Server Error",
  "message": "Internal optimization error",
  "timestamp": "2024-04-11T15:30:00Z"
}
```

#### Not Found (404)
```json
{
  "error": "Not Found",
  "message": "Endpoint '/invalid' not found",
  "timestamp": "2024-04-11T15:30:00Z"
}
```

---

## Request Examples

### Example 1: Simple Optimization
Minimize power with basic parameters.

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8
    }
  }'
```

### Example 2: Power-Optimized Design
Focus on power and area with budget constraints.

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8,
      "operating_frequency": 1e9,
      "load_capacitance": 1e-12,
      "power_budget": 0.001,
      "area_budget": 1e-9
    },
    "objectives": {
      "minimize_power": true,
      "minimize_area": true,
      "maximize_speed": false
    },
    "max_iterations": 1000
  }'
```

### Example 3: High-Speed Design
Maximize speed for high-performance applications.

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 20,
      "supply_voltage": 3.3,
      "operating_frequency": 5e9,
      "load_capacitance": 5e-12
    },
    "objectives": {
      "minimize_power": false,
      "maximize_speed": true,
      "maximize_gain": true
    }
  }'
```

### Example 4: Balanced Optimization
Multi-objective optimization.

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8,
      "operating_frequency": 1e9,
      "load_capacitance": 1e-12,
      "temperature": 100,
      "bias_current": 5e-7
    },
    "objectives": {
      "minimize_power": true,
      "minimize_area": true,
      "maximize_speed": true,
      "maximize_gain": true
    },
    "method": "scipy",
    "max_iterations": 500,
    "tolerance": 1e-6
  }'
```

---

## Response Examples

### Successful Optimization
```json
{
  "success": true,
  "optimized_parameters": {
    "W_L_ratio": 12.5,
    "finger_ratio": 1.2,
    "supply_voltage": 1.5,
    "operating_frequency": 1e9,
    "bias_current": 1.2e-6,
    "other_params": {}
  },
  "metrics_comparison": {
    "original": {
      "power_consumption": 0.0012,
      "propagation_delay": 1.5e-9,
      "gain": 15.2,
      "area": 2.5e-9,
      "slew_rate": 1.2e9,
      "noise_margin": 0.54
    },
    "optimized": {
      "power_consumption": 0.00085,
      "propagation_delay": 1.2e-9,
      "gain": 18.5,
      "area": 2.2e-9,
      "slew_rate": 1.5e9,
      "noise_margin": 0.58
    },
    "improvements": {
      "power_consumption": 29.17,
      "propagation_delay": 20.0,
      "gain": 21.71,
      "area": 12.0
    }
  },
  "overall_improvement": 20.67,
  "iterations_used": 127,
  "convergence": true,
  "execution_time": 2.34,
  "method_used": "scipy",
  "notes": "Optimization completed in 2.34s with convergence"
}
```

### Partial Convergence
```json
{
  "success": true,
  "optimized_parameters": { ... },
  "overall_improvement": 15.2,
  "iterations_used": 500,
  "convergence": false,
  "execution_time": 4.12,
  "notes": "Optimization reached max iterations without full convergence"
}
```

---

## Performance Considerations

### Execution Time

- **Small problems**: 0.5 - 2 seconds
- **Medium problems**: 2 - 5 seconds
- **Large problems**: 5 - 30 seconds (with higher iterations)

### Optimization Methods

| Method | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| scipy | Medium | High | General purpose, accurate results |
| ml | Fast | Medium | Similar problems, batch processing |
| hybrid | Variable | High | Complex multi-objective |

### Timeout Handling

```bash
# Default timeout is 30 seconds
# Adjust in .env:
OPTIMIZATION_TIMEOUT=60000  # 60 seconds for complex problems
```

---

## HTTP Status Codes

| Code | Meaning | Used When |
|------|---------|-----------|
| 200 | OK | Optimization successful |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Endpoint not found |
| 504 | Gateway Timeout | Optimization timeout |
| 500 | Server Error | Internal error |

---

## Testing

### Using Python

```python
import requests

url = "http://localhost:8000/optimize"
data = {
    "parameters": {
        "W_L_ratio": 10,
        "supply_voltage": 1.8,
        "operating_frequency": 1e9
    },
    "objectives": {
        "minimize_power": True,
        "maximize_speed": True
    }
}

response = requests.post(url, json=data)
print(response.json())
```

### Using Node.js

```javascript
const axios = require('axios');

const data = {
  parameters: {
    W_L_ratio: 10,
    supply_voltage: 1.8,
    operating_frequency: 1e9
  },
  objectives: {
    minimize_power: true,
    maximize_speed: true
  }
};

axios.post('http://localhost:8000/optimize', data)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

---

## Rate Limiting

No built-in rate limiting (suitable for backend-to-backend calls). If exposing publicly, add rate limiting in backend.

---

## CORS

Configured to accept requests from:
- localhost:5000 (Node backend)
- localhost:3000 (Frontend)
- localhost:8000 (This service)

Update `CORS_ORIGINS` in `.env` for different domains.

---

## Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Support

For issues or questions:
1. Check logs: `docker logs <container_id>`
2. Verify service: `curl http://localhost:8000/health`
3. Check integration: See [INTEGRATION.md](./INTEGRATION.md)

Happy optimizing! 🚀
