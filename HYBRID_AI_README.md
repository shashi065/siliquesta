# SILIQUESTA Hybrid AI System

**Intelligent edge/cloud switching for AI predictions with automatic failover**

## 🎯 Overview

The SILIQUESTA Hybrid AI system provides a seamless solution for AI predictions that automatically switches between:

- **☁️ Cloud Backend**: Maximum accuracy, full GPU-accelerated models, advanced features
- **⚡ Edge Processing**: Fast local ONNX models, offline capability, no network required

The system detects network connectivity and automatically selects the optimal execution environment, ensuring your application always works—whether online or offline.

## 🌟 Key Features

✅ **Automatic Edge/Cloud Switching**
- Monitors connectivity in real-time
- Routes requests to available models
- Transparent to calling code (just call `/predict`)

✅ **Offline Capability**  
- Lightweight ONNX models (50-200MB)
- Near-instant inference (10-50ms)
- Only 2% accuracy loss vs cloud

✅ **Intelligent Fallback**
- Graceful degradation on cloud unavailability
- Failover tracking and metrics
- Quick recovery when cloud returns

✅ **Performance Monitoring**
- Real-time execution metrics
- Per-model performance statistics  
- Edge vs cloud usage tracking
- Latency and confidence measurements

✅ **Easy Integration**
- RESTful API endpoints
- Python client library
- FastAPI middleware
- Batch prediction support

## 📊 Architecture

```
User Request
    ↓
REST API (/hybrid/predict)
    ↓
Hybrid Orchestrator
    ├─ Check connectivity
    ├─ Check user preference
    ├─ Route to model
    └─ Execute & return
       ↙          ↖
   ONNX Edge    Cloud API
   Models       Backend
   (offline)    (online)
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install fastapi uvicorn onnxruntime pydantic

# Clone/download SILIQUESTA
git clone https://github.com/siliquesta/ai-system.git
cd siliquesta
```

### 2. Configuration

```bash
# Set environment variables (optional)
export CLOUD_API_URL="https://your-api.com"
export CLOUD_API_KEY="your-key"
export ENABLE_ONNX=true
export ENABLE_CLOUD=true
```

### 3. Start Server

```bash
# Run FastAPI server
python -m app.fastapi_app

# Server starts at http://localhost:8000
```

### 4. Make a Prediction

```bash
curl -X POST http://localhost:8000/hybrid/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "digital_twin",
    "inputs": {
      "wn": 2.5,
      "wp": 5.2,
      "vdd": 0.9,
      "temp": 25
    }
  }'
```

**Response (Online):**
```json
{
  "model_source": "cloud",
  "result": {"power": 5.2, "frequency": 2.5},
  "execution_time_ms": 150.5,
  "confidence": 0.98,
  "edge_degradation_percent": 0.0
}
```

**Response (Offline/Fallback):**
```json
{
  "model_source": "edge",
  "result": {"power": 5.18, "frequency": 2.48},
  "execution_time_ms": 25.3,
  "confidence": 0.96,
  "edge_degradation_percent": 2.0,
  "fallback_used": true
}
```

## 📚 API Endpoints

### Predictions
- **POST /hybrid/predict** - Make single prediction
- **POST /hybrid/predict/batch** - Batch predictions (optimized)

### Status & Monitoring
- **GET /hybrid/status** - Complete system status
- **GET /hybrid/connectivity** - Network connectivity info
- **GET /hybrid/models/available** - List edge models
- **GET /hybrid/performance** - Performance metrics

### Control
- **GET /hybrid/force-edge** - Force edge models (testing)
- **GET /hybrid/force-cloud** - Force cloud models (testing)
- **GET /hybrid/auto-switch** - Return to automatic mode

### Health
- **GET /health** - Quick health check
- **GET /info** - System information

## 💻 Python Client

```python
from app.api.hybrid_api_guide import HybridAIClient

# Create client
client = HybridAIClient("http://localhost:8000")

# Make prediction
result = client.predict(
    model_name="digital_twin",
    inputs={"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
)

print(f"Model used: {result['model_source']}")  # "edge" or "cloud"
print(f"Result: {result['result']}")
print(f"Time: {result['execution_time_ms']:.1f}ms")

# Batch predictions
predictions = [
    {"model_name": "digital_twin", "inputs": {...}},
    {"model_name": "optimizer", "inputs": {...}}
]
results = client.batch_predict(predictions)

# Check status
status = client.get_status()
print(f"Requests processed: {status['total_requests_processed']}")
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ONNX` | `true` | Enable edge ONNX models |
| `ENABLE_CLOUD` | `true` | Enable cloud backend |
| `CLOUD_API_URL` | - | Cloud API endpoint URL |
| `CLOUD_API_KEY` | - | Cloud API authentication key |
| `CONNECTIVITY_CHECK_INTERVAL` | `30` | Seconds between connectivity checks |
| `ONNX_MODEL_DIR` | `models/edge/onnx` | Path to ONNX models |
| `CLOUD_API_TIMEOUT` | `30` | Cloud request timeout (seconds) |

### Programmatic Configuration

```python
from app.fastapi_app import create_app

config = {
    "enable_onnx": True,
    "enable_cloud": True,
    "cloud_api_url": "https://api.example.com",
    "cloud_api_key": "your-key",
    "connectivity_check_interval": 30,
    "onnx_model_dir": "models/edge/onnx"
}

app = create_app(config)
```

## 📈 Performance

### Edge (ONNX) Models
- **Latency**: 10-50ms (local, offline)
- **Memory**: 50-200MB (quantized)
- **Accuracy Loss**: ~2% vs cloud
- **Use Case**: Offline, real-time, resource-constrained

### Cloud Models  
- **Latency**: 100-500ms (network dependent)
- **Memory**: Unlimited (server-side)
- **Accuracy**: 100% (baseline)
- **Use Case**: Online, batch, advanced features

### Comparison Table

| Metric | Edge | Cloud |
|--------|------|-------|
| Connection Required | No | Yes |
| Latency | 10-50ms | 100-500ms |
| Memory | <200MB | Unlimited |
| Accuracy | 98% | 100% |
| Cost | $0 | Variable |
| Deployment | Device | Server |

## 🧪 Testing

### Test Edge Models

```bash
# Force edge mode
curl http://localhost:8000/hybrid/force-edge

# Make prediction (uses ONNX)
curl -X POST http://localhost:8000/hybrid/predict \
  -d '{"model_name": "digital_twin", "inputs": {...}}'
```

### Test Cloud Models

```bash
# Force cloud mode
curl http://localhost:8000/hybrid/force-cloud

# Make prediction (uses cloud)
curl -X POST http://localhost:8000/hybrid/predict \
  -d '{"model_name": "digital_twin", "inputs": {...}}'
```

### Test Fallback

```bash
# Disconnect network
# Make prediction (should use edge)
# Response should show model_source = "edge"

# Restore network
# Make prediction (should use cloud)
# Response should show model_source = "cloud"
```

## 📊 Monitoring

### Real-Time Metrics

```bash
# Get system status
curl http://localhost:8000/hybrid/status | json_pp

# Get performance stats
curl http://localhost:8000/hybrid/performance | json_pp

# Monitor connectivity
curl http://localhost:8000/hybrid/connectivity | json_pp
```

### Dashboard Display

```python
import time
from app.api.hybrid_api_guide import HybridAIClient

client = HybridAIClient()

while True:
    status = client.get_status()
    conn = client.get_connectivity()
    
    print(f"AI Mode: {status['model_source']} | Online: {conn['is_online']}")
    print(f"Requests: {status['total_requests_processed']}")
    time.sleep(5)
```

## 🌍 Real-World Examples

### IoT Sensor Processing
```python
from app.api.hybrid_real_world_examples import IoTSensorProcessor

processor = IoTSensorProcessor()

# Process sensor reading (automatic edge/cloud)
result = await processor.process_reading(sensor_reading)
print(f"Model source: {result['model_source']}")
```

### Mobile App Integration
```python
from app.api.hybrid_real_world_examples import MobileAppAPI

api = MobileAppAPI()

# Quick prediction for mobile
result = await api.quick_predict(inputs)
print(f"Fast response: {result['time_ms']}ms")
```

### Edge Device (Raspberry Pi, Jetson)
```python
from app.api.hybrid_real_world_examples import EdgeDeviceProcessor

processor = EdgeDeviceProcessor()

# Reliable local processing with optional cloud sync
result = await processor.process_with_priority_reliability(inputs)
```

## 📁 Project Structure

```
services/api/app/
├── fastapi_app.py                 # FastAPI application factory
├── connectivity_detector.py        # Network connectivity monitoring
├── hybrid_orchestrator.py          # Request routing logic
├── onnx_model_manager.py          # Edge model management
├── models.py                      # Data models
└── api/
    ├── hybrid_routes.py           # REST API endpoints
    ├── hybrid_api_guide.py        # Usage examples
    └── hybrid_real_world_examples.py  # Integration examples

models/edge/onnx/
├── digital_twin_edge.onnx         # Power/frequency prediction
├── optimizer_edge.onnx            # Parameter optimization
└── reliability_edge.onnx          # Reliability estimation

docs/
├── HYBRID_AI_INTEGRATION.md       # Complete integration guide
└── HYBRID_AI_QUICK_REFERENCE.md   # Quick reference
```

## 🤖 Supported Models

### Edge Models (ONNX - Quantized)
1. **digital_twin** - Power/frequency prediction
2. **optimizer** - Parameter optimization
3. **reliability** - Reliability estimation

### Cloud Models
- Full neural network variants
- Advanced preprocessing
- GPU acceleration
- Ensemble models

## 🔒 Security

### API Key Management
```bash
# Set API key securely
export CLOUD_API_KEY=$(cat /run/secrets/cloud_api_key)

# Or use environment-specific configurations
source .env.production
```

### Network Security
- TLS/HTTPS for cloud API calls
- Local ONNX models never leave device
- Fallback works without cloud access

## 📞 Support & Troubleshooting

### Common Issues

**Problem: Always using edge models**
```bash
# Check connectivity
curl http://localhost:8000/hybrid/connectivity

# Verify cloud API reachable
curl -I $CLOUD_API_URL
```

**Problem: High latency**
```bash
# Check network latency
curl http://localhost:8000/hybrid/connectivity | jq .latency_ms

# Consider forcing edge mode
curl http://localhost:8000/hybrid/force-edge
```

**Problem: ONNX models not loading**
```bash
# Verify models exist
ls models/edge/onnx/

# Check model availability
curl http://localhost:8000/hybrid/models/available
```

## 📖 Documentation

- **[Complete Integration Guide](HYBRID_AI_INTEGRATION.md)** - Full setup and deployment
- **[Quick Reference](HYBRID_AI_QUICK_REFERENCE.md)** - Quick start and common tasks  
- **[API Guide](services/api/app/api/hybrid_api_guide.py)** - API usage examples
- **[Real-World Examples](services/api/app/api/hybrid_real_world_examples.py)** - Practical implementations

## 🚀 Deployment

### Docker

```bash
# Build
docker build -t siliquesta-hybrid-ai .

# Run
docker run -p 8000:8000 \
  -e CLOUD_API_URL="https://api.example.com" \
  -e CLOUD_API_KEY="your-key" \
  siliquesta-hybrid-ai
```

### Kubernetes

```bash
# Deploy
kubectl apply -f k8s/hybrid-ai-deployment.yaml

# Expose service
kubectl expose deployment hybrid-ai --port=8000 --type=LoadBalancer
```

## 📊 Performance Tips

1. **Batch Predictions**: Use `/hybrid/predict/batch` for multiple predictions
2. **Monitor Connectivity**: Check `/hybrid/connectivity` regularly
3. **Cache Results**: Implement result caching for identical inputs
4. **Force Mode Testing**: Use `/hybrid/force-edge` and `/hybrid/force-cloud` for benchmarking
5. **Model Selection**: Choose appropriate model for your use case

## 🎓 Learning Resources

- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [Python Examples](services/api/app/api/hybrid_api_guide.py) - Code samples
- [Real-World Scenarios](services/api/app/api/hybrid_real_world_examples.py) - Practical use cases

## 📝 Roadmap

- [ ] WebSocket support for streaming predictions
- [ ] Health check probes with custom thresholds
- [ ] Advanced caching layer
- [ ] Model versioning support
- [ ] A/B testing framework
- [ ] Custom metrics export

## 📄 License

SILIQUESTA Hybrid AI System - Advanced AI Infrastructure

## 🤝 Contributing

Contributions welcome! Please refer to the project guidelines.

## 📧 Contact

For questions or support:
- Email: support@siliquesta.com
- Documentation: ./docs/
- Issues: [GitHub Issues](https://github.com/siliquesta/ai-system/issues)

---

**Built with ❤️ by the SILIQUESTA Team**

*Making AI accessible, reliable, and intelligent—online and offline.*
