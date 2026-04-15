# Quick Start - SILIQUESTA AI Service

Get the AI optimization microservice running in 5 minutes!

## ⚡ Quick Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

✅ Leave defaults as-is for development

### 4. Start Service
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

🎉 Service running at `http://localhost:8000`

## 🧪 Test It

### Health Check
```bash
curl http://localhost:8000/health
```

### Optimize Parameters
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8,
      "operating_frequency": 1e9,
      "load_capacitance": 1e-12
    },
    "objectives": {
      "minimize_power": true,
      "maximize_speed": true
    }
  }'
```

Expected response (≈2-3 seconds):
```json
{
  "success": true,
  "optimized_parameters": {
    "W_L_ratio": 12.5,
    "supply_voltage": 1.5,
    "...": "..."
  },
  "overall_improvement": 20.67,
  "execution_time": 2.34
}
```

## 📖 Interactive API Docs

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try endpoints directly from the UI!

## 🔗 Call from Node.js Backend

```javascript
// backend/src/services/optimizationService.js
import axios from 'axios';

const AI_SERVICE = 'http://localhost:8000';

export async function optimizeCircuit(params, objectives) {
  const response = await axios.post(`${AI_SERVICE}/optimize`, {
    parameters: params,
    objectives: objectives,
  });
  return response.data;
}
```

Usage in your backend:
```javascript
// In a route or service
const result = await optimizeCircuit({
  W_L_ratio: 10,
  supply_voltage: 1.8,
  operating_frequency: 1e9,
  load_capacitance: 1e-12,
}, {
  minimize_power: true,
  maximize_speed: true,
});

console.log(`Improvement: ${result.overall_improvement}%`);
```

## 📊 Input Parameters Explained

### Circuit Parameters
| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `W_L_ratio` | float | 10 | Transistor width/length ratio |
| `supply_voltage` | float | 1.8 | Supply voltage in volts |
| `operating_frequency` | float | 1e9 | Clock frequency in Hz |
| `load_capacitance` | float | 1e-12 | Output load in Farads |
| `bias_current` | float | 1e-6 | Bias current in Amperes |

### Optimization Objectives
```json
{
  "minimize_power": true,      // Reduce power consumption
  "maximize_speed": true,      // Increase speed/reduce delay
  "minimize_area": false,      // Reduce chip area
  "maximize_gain": false       // Increase circuit gain
}
```

## 📈 Output Metrics

```json
"metrics_comparison": {
  "original": {
    "power_consumption": 0.0012,      // Watts
    "propagation_delay": 1.5e-9,      // Seconds
    "gain": 15.2,                     // dB
    "area": 2.5e-9,                   // Square meters
    "slew_rate": 1.2e9,               // V/s
    "noise_margin": 0.54              // Volts
  },
  "optimized": { ... },
  "improvements": {
    "power_consumption": 29.17,       // % improvement
    "propagation_delay": 20.0,
    "... ": "..."
  }
}
```

## 🎯 Integration Examples

### Example 1: Simple Optimization
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 5,
      "supply_voltage": 1.2
    }
  }'
```

### Example 2: Power-Optimized Design
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 10,
      "supply_voltage": 1.8,
      "power_budget": 0.001
    },
    "objectives": {
      "minimize_power": true,
      "minimize_area": true
    }
  }'
```

### Example 3: High-Speed Design
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "W_L_ratio": 20,
      "supply_voltage": 3.3,
      "operating_frequency": 5e9
    },
    "objectives": {
      "maximize_speed": true,
      "maximize_gain": true
    }
  }'
```

## 🛠️ Useful Commands

```bash
# Development with auto-reload
python -m uvicorn main:app --reload

# Production deployment
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# See all endpoints
curl http://localhost:8000/info

# Run tests
pytest tests/

# Format code
black .

# Lint
flake8 .
```

## ⚙️ Configuration

Edit `.env` for different setups:

**Fast optimization (development):**
```env
OPTIMIZATION_MAX_ITERATIONS=200
OPTIMIZATION_TIMEOUT=15000
DEBUG=True
```

**Better results (production):**
```env
OPTIMIZATION_MAX_ITERATIONS=1000
OPTIMIZATION_TIMEOUT=60000
DEBUG=False
```

**Multi-backend setup:**
```env
CORS_ORIGINS=http://localhost:5000,http://192.168.1.100:5000
```

## 🐛 Troubleshooting

### Service won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux
```

### Timeout errors
Increase `OPTIMIZATION_TIMEOUT` in `.env`:
```env
OPTIMIZATION_TIMEOUT=60000  # 60 seconds
```

### CORS errors from Node backend
Update `.env`:
```env
CORS_ORIGINS=http://localhost:5000
```

### Memory issues
Reduce iterations:
```env
OPTIMIZATION_MAX_ITERATIONS=200
```

## 📚 Next Steps

1. ✅ Service running locally
2. 📌 Integrate with Node backend (see examples above)
3. 🚀 Deploy to production
4. 📊 Monitor performance
5. 🔧 Tune optimization parameters

## 📖 Full Documentation

See [README.md](./README.md) for comprehensive guide.

Happy optimizing! 🚀
