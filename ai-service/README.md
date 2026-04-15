# SILIQUESTA AI Optimization Microservice

Production-ready FastAPI microservice for AI-powered circuit parameter optimization.

## 🚀 Tech Stack

- **FastAPI** - Modern async web framework
- **SciPy** - Scientific optimization algorithms
- **NumPy** - Numerical computations
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **scikit-learn** - ML utilities

## 📁 Project Structure

```
ai-service/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── models.py              # Pydantic models
├── optimizer.py           # Optimization logic
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
└── QUICKSTART.md          # Quick setup guide
```

## 🔧 Installation

### Prerequisites

- Python 3.9+
- pip or poetry

### Setup

1. **Create virtual environment:**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work for development)

4. **Start development server:**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Service running at `http://localhost:8000`

## 📚 API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-04-11T15:30:00Z"
}
```

### Service Info
```
GET /info
```

### Optimize Circuit Parameters
```
POST /optimize
```

**Request Body:**
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
    "power_budget": 1e-3,
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

**Response (200 OK):**
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
      "power_consumption": 1.2e-3,
      "propagation_delay": 1.5e-9,
      "gain": 15.2,
      "area": 2.5e-9,
      "slew_rate": 1.2e9,
      "noise_margin": 0.54
    },
    "optimized": {
      "power_consumption": 8.5e-4,
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

## 🔌 Integration with Node.js Backend

### Node.js Example

```javascript
// In your backend (Node.js)
import axios from 'axios';

const AI_SERVICE_URL = 'http://localhost:8000';

async function optimizeCircuit(parameters, objectives) {
  try {
    const response = await axios.post(`${AI_SERVICE_URL}/optimize`, {
      parameters,
      objectives,
      method: 'scipy',
      max_iterations: 500,
      tolerance: 1e-6,
    });

    return response.data;
  } catch (error) {
    console.error('Optimization failed:', error);
    throw error;
  }
}

// Usage in your simulation service
const optimizationResult = await optimizeCircuit({
  W_L_ratio: 10,
  supply_voltage: 1.8,
  operating_frequency: 1e9,
  load_capacitance: 1e-12,
}, {
  minimize_power: true,
  maximize_speed: true,
});
```

### Express Middleware

```javascript
// backend/src/middleware/aiIntegration.js
import axios from 'axios';

const AI_SERVICE = process.env.AI_SERVICE_URL || 'http://localhost:8000';

export const callAIOptimization = async (req, res, next) => {
  try {
    const { parameters, objectives } = req.body;
    
    const response = await axios.post(`${AI_SERVICE}/optimize`, {
      parameters,
      objectives,
    });

    req.optimizationResult = response.data;
    next();
  } catch (error) {
    res.status(502).json({
      error: 'AI Service unavailable',
      message: error.message,
    });
  }
};
```

### Backend .env

Add to backend `.env`:
```env
AI_SERVICE_URL=http://localhost:8000
```

## 🧪 Testing

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Optimize parameters
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
  }' | python -m json.tool
```

### Using Python

```python
import requests

url = "http://localhost:8000/optimize"
payload = {
    "parameters": {
        "W_L_ratio": 10,
        "supply_voltage": 1.8,
        "operating_frequency": 1e9,
        "load_capacitance": 1e-12
    },
    "objectives": {
        "minimize_power": True,
        "maximize_speed": True
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

## 📊 Advanced Configuration

### Environment Variables

```env
# Environment
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=info

# Server
HOST=0.0.0.0
PORT=8000

# CORS - Allow your backend URL
CORS_ORIGINS=http://localhost:5000,https://api.example.com

# Optimization
OPTIMIZATION_MAX_ITERATIONS=1000
OPTIMIZATION_TIMEOUT=60000
OPTIMIZATION_METHOD=scipy

# API
API_TIMEOUT=120
MAX_WORKERS=8
```

## 🚀 Production Deployment

### Using Gunicorn

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Using Systemd

Create `/etc/systemd/system/siliquesta-ai.service`:
```ini
[Unit]
Description=SILIQUESTA AI Optimization Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/siliquesta-ai
Environment="PATH=/opt/siliquesta-ai/venv/bin"
ExecStart=/opt/siliquesta-ai/venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable siliquesta-ai
sudo systemctl start siliquesta-ai
```

### Docker

```bash
docker build -t siliquesta-ai .
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e AI_SERVICE_PORT=8000 \
  siliquesta-ai
```

## 📈 Performance Optimization

### Optimization Algorithms

**SciPy (Default)**: Uses global optimization
- Faster convergence
- Good for circuit optimization
- Lower computational cost

**ML-based**: Requires trained model
- Faster for similar problems
- Requires training data
- Better for batch operations

### Tuning

```env
# For faster optimization
OPTIMIZATION_MAX_ITERATIONS=200
OPTIMIZATION_TIMEOUT=15000

# For better results
OPTIMIZATION_MAX_ITERATIONS=1000
OPTIMIZATION_TIMEOUT=60000

# For parallel processing
MAX_WORKERS=8
```

## 🔍 Monitoring & Logging

### Log Levels

```env
LOG_LEVEL=debug    # Verbose (development)
LOG_LEVEL=info     # Standard (production)
LOG_LEVEL=warning  # Only warnings and errors
```

### Example Logs

```
2024-04-11 15:30:45 - main - INFO - 🚀 Starting SILIQUESTA AI Optimization Service v1.0.0
2024-04-11 15:30:45 - main - INFO - Environment: development
2024-04-11 15:30:50 - main - INFO - Starting optimization request
2024-04-11 15:30:52 - main - INFO - Optimization completed - Improvement: 20.67%
```

## 📝 Common Issues

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
```

### CORS Issues
Update `CORS_ORIGINS` in `.env` to include your backend URL:
```env
CORS_ORIGINS=http://localhost:5000,http://localhost:3000
```

### Timeout Errors
Increase `OPTIMIZATION_TIMEOUT` in `.env`:
```env
OPTIMIZATION_TIMEOUT=60000  # 60 seconds
```

### Memory Issues
Reduce `OPTIMIZATION_MAX_ITERATIONS`:
```env
OPTIMIZATION_MAX_ITERATIONS=200
```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Schema**: http://localhost:8000/openapi.json

## 🔗 Related Services

- **Backend API**: http://localhost:5000
- **Frontend**: http://localhost:3000

## 📄 License

MIT License - See LICENSE file for details

## 💡 Next Steps

1. Train ML model for faster optimization
2. Add more optimization algorithms
3. Implement caching for similar requests
4. Add monitoring/alerting integration
5. Deploy to production cluster

Happy optimizing! 🎯
