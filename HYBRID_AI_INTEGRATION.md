# SILIQUESTA Hybrid AI - Complete Integration Guide

## Overview

The SILIQUESTA Hybrid AI system provides **automatic edge/cloud switching** for predictions:

- **Online**: Uses cloud-based AI backend for maximum accuracy
- **Offline**: Falls back to lightweight ONNX models with 2% accuracy loss
- **Smart Switching**: Monitors connectivity and switches automatically
- **Fallback Mechanisms**: Graceful degradation when services unavailable

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Application                        │
│  (app.fastapi_app.create_app)                       │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌────────────┐ ┌──────────────┐
│ Routing │  │ Hybrid     │ │ Connectivity │
│ Layer   │  │ Orchestor  │ │ Detector     │
│         │  │            │ │              │
└─────────┘  └────────────┘ └──────────────┘
    │            │            │
    ├─────┬──────┴───────┬────┤
    │     │              │    │
    ▼     ▼              ▼    ▼
  ┌─────────────────────────────────┐
  │  ONNX Model Manager (Edge)      │
  │  - digital_twin.onnx (Quantized)│
  │  - optimizer.onnx               │
  │  - reliability.onnx             │
  │  - Fast offline inference       │
  └─────────────────────────────────┘
  
  ┌──────────────────────────────────┐
  │  Cloud AI Backend (Online)        │
  │  - Full neural networks           │
  │  - Maximum accuracy               │
  │  - GPU acceleration               │
  └──────────────────────────────────┘
```

## Components

### 1. Connectivity Detector
**File**: `app/connectivity_detector.py`

Monitors cloud connectivity and manages fallback:

```python
from app.connectivity_detector import get_connectivity_detector

detector = get_connectivity_detector()
is_online = detector.is_online()
source = detector.get_recommended_model_source()
```

**Features**:
- Periodic connectivity checks (configurable interval)
- Latency measurement
- Automatic fallback on repeated failures
- Recovery tracking

### 2. ONNX Model Manager
**File**: `app/onnx_model_manager.py`

Manages edge-based ONNX models:

```python
from app.onnx_model_manager import get_onnx_manager

manager = get_onnx_manager()
models = manager.list_models()
result = manager.inference("digital_twin", inputs)
```

**Models**:
- `digital_twin_edge.onnx`: Power/frequency prediction (Int8 quantized)
- `optimizer_edge.onnx`: Parameter optimization
- `reliability_edge.onnx`: Reliability estimation

### 3. Hybrid Orchestrator
**File**: `app/hybrid_orchestrator.py`

Routes requests to optimal model source:

```python
from app.hybrid_orchestrator import get_hybrid_orchestrator

orchestrator = get_hybrid_orchestrator()
request = HybridAIRequest(...)
response = await orchestrator.process(request)
```

**Routing Logic**:
```
Input Request
    │
    ├─ Check User Preference
    │  ├─ "edge" → Use ONNX
    │  ├─ "cloud" → Use Cloud API
    │  └─ "auto" → Check Connectivity
    │
    ├─ (if auto)
    │  ├─ Is Online?
    │  │  ├─ Yes → Use Cloud
    │  │  └─ No → Use ONNX
    │
    ├─ Execute on Selected Model
    │
    └─ Return Result with Metadata
```

### 4. REST API Routes
**File**: `app/api/hybrid_routes.py`

Exposed FastAPI endpoints:

#### Prediction Endpoints

**POST /hybrid/predict** - Single prediction
```bash
curl -X POST http://localhost:8000/hybrid/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "digital_twin",
    "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25},
    "user_preference": "auto"
  }'
```

**POST /hybrid/predict/batch** - Batch predictions
```bash
curl -X POST http://localhost:8000/hybrid/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"model_name": "digital_twin", "inputs": {...}},
    {"model_name": "optimizer", "inputs": {...}}
  ]'
```

#### Status Endpoints

**GET /hybrid/status** - Complete system status
```bash
curl http://localhost:8000/hybrid/status
```

**GET /hybrid/connectivity** - Connectivity details
```bash
curl http://localhost:8000/hybrid/connectivity
```

**GET /hybrid/models/available** - List edge models
```bash
curl http://localhost:8000/hybrid/models/available
```

**GET /hybrid/performance** - Performance metrics
```bash
curl http://localhost:8000/hybrid/performance
curl "http://localhost:8000/hybrid/performance?model_name=digital_twin"
```

#### Control Endpoints

**GET /hybrid/force-edge** - Force edge model
```bash
curl http://localhost:8000/hybrid/force-edge
```

**GET /hybrid/force-cloud** - Force cloud model
```bash
curl http://localhost:8000/hybrid/force-cloud
```

**GET /hybrid/auto-switch** - Return to auto mode
```bash
curl http://localhost:8000/hybrid/auto-switch
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Core dependencies
pip install fastapi uvicorn pydantic

# ONNX for edge inference
pip install onnx onnxruntime

# For cloud API integration (if using cloud models)
pip install requests aiohttp

# Optional: For advanced monitoring
pip install prometheus-client
```

### 2. Configure the System

**With environment variables:**
```bash
export ENABLE_ONNX=true
export ENABLE_CLOUD=true
export CLOUD_API_URL="https://your-api.com"
export CLOUD_API_KEY="your-key"
export CONNECTIVITY_CHECK_INTERVAL=30
export ONNX_MODEL_DIR="models/edge/onnx"

python -m app.fastapi_app
```

**Programmatically:**
```python
from app.fastapi_app import create_app

config = {
    "enable_onnx": True,
    "enable_cloud": True,
    "cloud_api_url": "https://your-api.com",
    "cloud_api_key": "your-key",
    "connectivity_check_interval": 30,
    "onnx_model_dir": "models/edge/onnx"
}

app = create_app(config)
```

### 3. Verify Setup

```bash
# Check API is running
curl http://localhost:8000/health

# Check hybrid system status
curl http://localhost:8000/hybrid/status

# View API documentation
# Open: http://localhost:8000/docs
```

## Usage Examples

### Python Client

```python
from app.api.hybrid_api_guide import HybridAIClient

client = HybridAIClient("http://localhost:8000")

# Make prediction
result = client.predict(
    model_name="digital_twin",
    inputs={"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
)

print(f"Using: {result['model_source']}")  # "edge" or "cloud"
print(f"Result: {result['result']}")
print(f"Time: {result['execution_time_ms']:.1f}ms")
```

### Batch Processing

```python
predictions = [
    {
        "model_name": "digital_twin",
        "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
    },
    {
        "model_name": "optimizer",
        "inputs": {"wn": 2.8, "wp": 5.5, "vdd": 0.95, "temp": 30}
    }
]

results = client.batch_predict(predictions)

for result in results:
    print(f"{result['model_name']}: {result['model_source']}")
```

### Force Testing

```python
# Test edge performance
client.force_edge()
result1 = client.predict(...)  # Uses ONNX

# Test cloud performance  
client.force_cloud()
result2 = client.predict(...)  # Uses cloud

# Compare
print(f"Edge: {result1['execution_time_ms']:.1f}ms")
print(f"Cloud: {result2['execution_time_ms']:.1f}ms")

# Return to auto
client.force_edge()  # Back to automatic switching
```

## Performance Characteristics

### Edge (ONNX) Models
- **Latency**: 10-50ms (offline)
- **Memory**: 50-200MB
- **Accuracy Loss**: ~2% vs cloud
- **Benefits**: No network required, instant response

### Cloud Models
- **Latency**: 100-500ms (varies with network)
- **Memory**: Unlimited (server-side)
- **Accuracy**: Maximum (100% baseline)
- **Benefits**: Best accuracy, advanced features

## Monitoring & Diagnostics

### Real-Time Status

```python
from app.api.hybrid_api_guide import HybridAIClient
import time

client = HybridAIClient()

while True:
    status = client.get_status()
    conn = client.get_connectivity()
    
    print(f"Mode: {status['model_source']}")
    print(f"Online: {conn['is_online']}")
    print(f"Requests: {status['total_requests_processed']}")
    
    time.sleep(5)
```

### Performance Analysis

```python
client = HybridAIClient()

# Get metrics
perf = client.get_performance()
stats = perf['performance_stats']

print(f"Total Requests: {stats['total_requests']}")
print(f"Edge Requests: {stats['edge_requests']}")
print(f"Cloud Requests: {stats['cloud_requests']}")
print(f"Avg Execution: {stats['avg_execution_time_ms']:.1f}ms")
print(f"Avg Confidence: {stats['avg_confidence']:.2%}")

# Per-model metrics
model_perf = client.get_performance("digital_twin")
```

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Run API server
CMD ["python", "-m", "app.fastapi_app"]
```

**Build and run:**
```bash
docker build -t siliquesta-hybrid-ai .
docker run -p 8000:8000 \
  -e CLOUD_API_URL="https://api.example.com" \
  -e CLOUD_API_KEY="your-key" \
  siliquesta-hybrid-ai
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hybrid-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hybrid-ai
  template:
    metadata:
      labels:
        app: hybrid-ai
    spec:
      containers:
      - name: hybrid-ai
        image: siliquesta-hybrid-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: CLOUD_API_URL
          valueFrom:
            secretKeyRef:
              name: hybrid-ai-secrets
              key: api-url
        - name: CLOUD_API_KEY
          valueFrom:
            secretKeyRef:
              name: hybrid-ai-secrets
              key: api-key
```

## Troubleshooting

### Issue: Always using edge models

**Check connectivity:**
```bash
curl http://localhost:8000/hybrid/connectivity
```

**Check if cloud API is reachable:**
```bash
# Test cloud connectivity directly
curl -I $CLOUD_API_URL
```

**Solution:** Verify `CLOUD_API_URL` and `CLOUD_API_KEY` environment variables.

### Issue: High latency with cloud

**Check network conditions:**
```python
client = HybridAIClient()
conn = client.get_connectivity()
print(f"Latency: {conn.get('latency_ms', 'N/A')}ms")
```

**Solution:** Consider forcing edge mode or increasing timeout.

### Issue: ONNX models not loading

**Check models directory:**
```bash
ls models/edge/onnx/
```

**Check API response:**
```bash
curl http://localhost:8000/hybrid/models/available
```

**Solution:** Verify ONNX model files exist and are properly formatted.

## API Response Examples

### Successful Prediction (Cloud)

```json
{
  "model_name": "digital_twin",
  "result": {
    "power": 5.2,
    "frequency": 2.5
  },
  "model_source": "cloud",
  "execution_time_ms": 150.5,
  "confidence": 0.98,
  "edge_degradation_percent": 0.0,
  "fallback_used": false,
  "latency_ms": 120,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### Fallback to Edge (Offline)

```json
{
  "model_name": "digital_twin",
  "result": {
    "power": 5.18,
    "frequency": 2.48
  },
  "model_source": "edge",
  "execution_time_ms": 25.3,
  "confidence": 0.96,
  "edge_degradation_percent": 2.0,
  "fallback_used": true,
  "latency_ms": null,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## Best Practices

1. **Use auto mode** by default - system handles switching automatically
2. **Monitor connectivity** - watch for frequent switches between edge/cloud
3. **Batch predictions** when possible - more efficient for multiple requests
4. **Set appropriate timeouts** - balance between latency and reliability
5. **Cache results** for identical inputs - reduces redundant API calls
6. **Use force-edge/force-cloud** for testing and benchmarking only

## Support & Troubleshooting

For issues:
1. Check system status: `GET /hybrid/status`
2. Review recent executions: `GET /hybrid/performance`
3. Verify connectivity: `GET /hybrid/connectivity`
4. Test with forced modes: `GET /hybrid/force-edge`
5. Check logs for error details

## Next Steps

- [Deployment Guide](DEPLOYMENT.md)
- [Performance Tuning](PERFORMANCE.md)
- [Security Configuration](SECURITY.md)
- [Monitoring Setup](MONITORING.md)
