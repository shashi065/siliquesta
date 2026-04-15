# Hybrid AI - Quick Reference & Deployment Guide

## Quick Start (5 minutes)

### 1. Install & Run

```bash
# Install dependencies
pip install fastapi uvicorn onnxruntime pydantic

# Set environment (optional, uses defaults if not set)
export CLOUD_API_URL="https://your-api.com"
export CLOUD_API_KEY="your-key"

# Start API server
python -m app.fastapi_app
```

Server running at: `http://localhost:8000`

### 2. Make a Prediction

```bash
curl -X POST http://localhost:8000/hybrid/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "digital_twin",
    "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
  }'
```

### 3. Check Status

```bash
curl http://localhost:8000/hybrid/status
```

## Common API Calls

### Check if Online/Offline

```bash
curl http://localhost:8000/hybrid/connectivity | jq .is_online
```

### Force Test Mode

```bash
# Test with edge models only (offline mode)
curl http://localhost:8000/hybrid/force-edge

# Make prediction (uses edge)
curl -X POST http://localhost:8000/hybrid/predict -d '...'

# Switch back to auto mode
curl http://localhost:8000/hybrid/auto-switch
```

### Batch Predictions

```bash
curl -X POST http://localhost:8000/hybrid/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"model_name": "digital_twin", "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}},
    {"model_name": "optimizer", "inputs": {"wn": 2.8, "wp": 5.5, "vdd": 0.95, "temp": 30}}
  ]'
```

### Performance Metrics

```bash
# Overall stats
curl http://localhost:8000/hybrid/performance

# Per-model stats
curl "http://localhost:8000/hybrid/performance?model_name=digital_twin"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ONNX` | `true` | Enable edge ONNX models |
| `ENABLE_CLOUD` | `true` | Enable cloud backend |
| `CLOUD_API_URL` | - | Cloud API endpoint |
| `CLOUD_API_KEY` | - | Cloud API authentication key |
| `CONNECTIVITY_CHECK_INTERVAL` | `30` | Seconds between connectivity checks |
| `CONNECTIVITY_TIMEOUT` | `5` | Timeout for connectivity check (seconds) |
| `CLOUD_API_TIMEOUT` | `30` | Cloud request timeout (seconds) |
| `ONNX_MODEL_DIR` | `models/edge/onnx` | Path to ONNX models |
| `API_HOST` | `0.0.0.0` | API binding address |
| `API_PORT` | `8000` | API port |

## Deployment Checklist

### Pre-Deployment

- [ ] ONNX models properly quantized and tested
- [ ] Cloud API URL validated and accessible
- [ ] API key/credentials secured in environment/vault
- [ ] Network connectivity requirements documented
- [ ] Fallback mechanism tested
- [ ] Performance baselines established
- [ ] Logging configured
- [ ] Monitoring setup ready

### Deployment

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Environment variables configured
- [ ] API tests passed: `curl http://localhost:8000/health`
- [ ] Edge models loaded: `curl http://localhost:8000/hybrid/models/available`
- [ ] Connectivity check working: `curl http://localhost:8000/hybrid/connectivity`
- [ ] Prediction test passed: Make a test prediction
- [ ] Fallback tested: Force edge mode and verify
- [ ] Documentation accessible at `/docs`

### Post-Deployment

- [ ] Monitor real-time status every 5 minutes
- [ ] Check error logs for first hour
- [ ] Verify both edge and cloud models working
- [ ] Monitor performance metrics
- [ ] Document any issues encountered
- [ ] Set up alerting for connectivity issues

## Response Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | All good |
| 400 | Bad request | Check request format |
| 404 | Not found | Check model name or endpoint |
| 500 | Server error | Check logs |
| 503 | Unavailable | Check service status |

## File Structure

```
app/
├── fastapi_app.py                 # FastAPI app factory
├── connectivity_detector.py        # Connectivity monitoring
├── hybrid_orchestrator.py          # Request routing logic
├── onnx_model_manager.py          # Edge model management
├── models.py                      # Pydantic models
├── api/
│   ├── hybrid_routes.py           # REST endpoints
│   └── hybrid_api_guide.py        # Usage examples
└── config.py                      # Configuration

models/edge/onnx/
├── digital_twin_edge.onnx         # Power/frequency prediction
├── optimizer_edge.onnx            # Parameter optimization
└── reliability_edge.onnx          # Reliability estimation
```

## System Architecture

```
┌─────────────────────────────────────────┐
│         REST API Endpoints              │
├─────────────────────────────────────────┤
│  /predict, /status, /connectivity, ... │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────────┐  ┌─────────────────┐
│   Hybrid     │  │  Connectivity   │
│ Orchestrator │  │   Detector      │
└──────────────┘  └─────────────────┘
    │                 │
    ├─────────┬───────┤
    │         │       │
    ▼         ▼       ▼
 ┌─────────────────────────┐
 │  Model Selection Logic  │
 └─────────────────────────┘
    │                 │
    ▼                 ▼
┌──────────────┐  ┌─────────────────┐
│ ONNX Edge    │  │ Cloud Backend   │
│ Models       │  │ (REST API)      │
│ ~50MB        │  │ Full models     │
│ 2% accuracy  │  │ Max accuracy    │
│ loss         │  │                 │
└──────────────┘  └─────────────────┘
```

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Edge Latency | <50ms | Local inference, no network |
| Cloud Latency | 100-500ms | Depends on network/server |
| Edge Memory | <200MB | Quantized models |
| Accuracy Loss (Edge) | 1-3% | vs. cloud models |
| Fallback Time | <100ms | Quick switch to edge |
| Connectivity Check | Every 30s | Configurable |

## Example Integration in FastAPI

```python
# main.py
from fastapi import FastAPI
from app.fastapi_app import create_app

config = {
    "enable_onnx": True,
    "enable_cloud": True,
    "cloud_api_url": "https://api.example.com",
    "cloud_api_key": "your-key",
    "connectivity_check_interval": 30
}

app = create_app(config)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
```

## Testing the Hybrid System

### Test 1: Verify Both Models Work

```bash
# Force edge
curl http://localhost:8000/hybrid/force-edge
curl -X POST http://localhost:8000/hybrid/predict \
  -d '{"model_name": "digital_twin", "inputs": {...}}'
# Note: model_source = "edge"

# Force cloud
curl http://localhost:8000/hybrid/force-cloud
curl -X POST http://localhost:8000/hybrid/predict \
  -d '{"model_name": "digital_twin", "inputs": {...}}'
# Note: model_source = "cloud"

# Back to auto
curl http://localhost:8000/hybrid/auto-switch
```

### Test 2: Verify Fallback

```bash
# Simulate offline by stopping network
# Make prediction (should use edge)
# Curl should show model_source = "edge"

# Restore network
# Make prediction (should use cloud)
# Curl should show model_source = "cloud"
```

### Test 3: Performance Comparison

```python
import requests
import time

urls = [
    "http://localhost:8000/hybrid/force-edge",
    "http://localhost:8000/hybrid/force-cloud"
]

for url in urls:
    requests.get(url)
    
    times = []
    for _ in range(10):
        start = time.time()
        requests.post("http://localhost:8000/hybrid/predict", 
                     json={"model_name": "digital_twin", "inputs": {...}})
        times.append((time.time() - start) * 1000)
    
    print(f"Mode {url.split('-')[-1]}: {sum(times)/len(times):.1f}ms avg")
```

## Monitoring Commands

```bash
# Real-time status
watch -n 5 "curl -s http://localhost:8000/hybrid/status | jq ."

# Performance tracking
curl http://localhost:8000/hybrid/performance | jq '.performance_stats'

# Connectivity monitoring
curl http://localhost:8000/hybrid/connectivity | jq .

# Model availability
curl http://localhost:8000/hybrid/models/available | jq .
```

## Troubleshooting Decision Tree

```
Problem: Always using edge
├─ Check: curl .../hybrid/status
├─ If model_source = "edge"
│  ├─ Check connectivity: curl .../hybrid/connectivity
│  ├─ If is_online = false
│  │  ├─ Problem: Network unreachable
│  │  └─ Solution: Check network, cloud API URL
│  └─ If is_online = true
│     ├─ Problem: Cloud API issue
│     └─ Solution: Check cloud API key, URL, logs

Problem: Always using cloud
├─ Check: Likely working correctly
├─ If you want offline capability
│  └─ Check: ENABLE_ONNX=true, models loaded

Problem: High latency
├─ Check: curl .../hybrid/connectivity
├─ If latency_ms > 1000
│  ├─ Problem: Network congestion
│  └─ Solution: Consider forcing edge
├─ If latency_ms < 100
│  └─ Problem: Not network
│     └─ Solution: Check cloud server load

Problem: ONNX models not loading
├─ Check: curl .../hybrid/models/available
├─ If models_loaded = 0
│  ├─ Problem: Models not found or corrupted
│  └─ Solution: Verify model directory, re-download
└─ If models_loaded > 0
   └─ Problem: ONNX runtime issue
      └─ Solution: Reinstall onnxruntime
```

## Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "app.fastapi_app"]
```

```bash
# Build
docker build -t hybrid-ai .

# Run
docker run -p 8000:8000 \
  -e CLOUD_API_URL="https://api.example.com" \
  -e CLOUD_API_KEY="your-key" \
  hybrid-ai
```

## Environment Setup

```bash
# Development
export ENABLE_ONNX=true
export ENABLE_CLOUD=true
export DEBUG=true

# Production
export ENABLE_ONNX=true
export ENABLE_CLOUD=true
export CLOUD_API_KEY=$(cat /run/secrets/cloud_api_key)
export CLOUD_API_URL="https://prod-api.example.com"
```

## Health Indicators

✅ **System is healthy when:**
- `GET /health` returns 200
- `GET /hybrid/connectivity` shows is_online = true or detecting properly
- Both edge and cloud can return results
- Performance metrics show requests being processed

⚠️ **Warning signs:**
- Frequent switching between edge/cloud (every request)
- Connectivity check failures
- Model loading errors
- High error rates from cloud API

🔴 **Critical failures:**
- API doesn't respond
- Cannot load ANY models
- Continuous cloud API timeouts
- No fallback available

## Support Resources

- API Documentation: `http://localhost:8000/docs`
- Usage Guide: `app/api/hybrid_api_guide.py`
- Integration Guide: `HYBRID_AI_INTEGRATION.md`
- Architecture: `services/api/README.md`
