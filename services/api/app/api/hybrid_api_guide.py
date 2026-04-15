"""
Hybrid AI REST API - Complete Usage Guide
==========================================

This guide shows how to use the SILIQUESTA Hybrid AI API for edge/cloud
prediction with automatic switching and failover.

Author: SILIQUESTA Team
Version: 1.0
"""

import requests
import asyncio
from typing import Dict, Any
import json

# ============================================================================
# Configuration
# ============================================================================

API_URL = "http://localhost:8000"
HYBRID_API = f"{API_URL}/hybrid"


# ============================================================================
# 1. Basic Prediction (Auto Edge/Cloud)
# ============================================================================

def example_basic_prediction():
    """
    Make a prediction with automatic edge/cloud routing.
    
    The system will:
    - Check if internet is available
    - Use cloud (online) for best accuracy
    - Use ONNX (offline) with 2% loss if needed
    """
    
    print("\n" + "="*60)
    print("1. BASIC PREDICTION (Auto Edge/Cloud)")
    print("="*60)
    
    request = {
        "model_name": "digital_twin",
        "inputs": {
            "wn": 2.5,      # Normalized frequency (GHz)
            "wp": 5.2,      # Normalized power (W)
            "vdd": 0.9,     # Voltage (V)
            "temp": 25      # Temperature (°C)
        },
        "user_preference": "auto",
        "priority": "normal"
    }
    
    print("\n📤 Sending prediction request...")
    print(json.dumps(request, indent=2))
    
    response = requests.post(f"{HYBRID_API}/predict", json=request)
    result = response.json()
    
    print("\n📥 Response:")
    print(f"  Model Source: {result['model_source']}")  # "edge" or "cloud"
    print(f"  Result: {result['result']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Execution Time: {result['execution_time_ms']:.1f}ms")
    if result['model_source'] == 'edge':
        print(f"  Accuracy Degradation: {result['edge_degradation_percent']:.1f}%")


# ============================================================================
# 2. Force Edge Model (Offline Testing)
# ============================================================================

def example_force_edge():
    """
    Force use of edge (ONNX) models for testing offline scenarios.
    
    Use this to:
    - Simulate offline environment
    - Benchmark edge model performance
    - Test fallback mechanisms
    """
    
    print("\n" + "="*60)
    print("2. FORCE EDGE MODEL (Offline Testing)")
    print("="*60)
    
    print("\n1️⃣ Switch to edge model...")
    response = requests.get(f"{HYBRID_API}/force-edge")
    print(f"   {response.json()}")
    
    print("\n2️⃣ Make prediction with edge model...")
    request = {
        "model_name": "digital_twin",
        "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25},
        "user_preference": "auto"
    }
    
    response = requests.post(f"{HYBRID_API}/predict", json=request)
    result = response.json()
    
    print(f"   Model Source: {result['model_source']}")
    print(f"   Fast Execution: {result['execution_time_ms']:.1f}ms")
    print(f"   Lightweight: Yes (runs offline)")
    
    print("\n3️⃣ Return to auto mode...")
    response = requests.get(f"{HYBRID_API}/auto-switch")
    print(f"   {response.json()}")


# ============================================================================
# 3. Batch Predictions
# ============================================================================

def example_batch_predictions():
    """
    Process multiple predictions efficiently.
    
    Benefits:
    - Single connectivity check for all requests
    - Batches edge models when possible
    - Parallel cloud requests
    """
    
    print("\n" + "="*60)
    print("3. BATCH PREDICTIONS")
    print("="*60)
    
    predictions = [
        {
            "model_name": "digital_twin",
            "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25},
            "user_preference": "auto"
        },
        {
            "model_name": "optimizer",
            "inputs": {"wn": 2.8, "wp": 5.5, "vdd": 0.95, "temp": 30},
            "user_preference": "auto"
        },
        {
            "model_name": "reliability",
            "inputs": {"wn": 2.2, "wp": 4.8, "vdd": 0.85, "temp": 20},
            "user_preference": "auto"
        }
    ]
    
    print(f"\n📤 Processing {len(predictions)} predictions...")
    
    response = requests.post(f"{HYBRID_API}/predict/batch", json=predictions)
    results = response.json()
    
    print(f"\n📥 Results:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result['model_name']}")
        print(f"     Source: {result['model_source']}")
        print(f"     Time: {result['execution_time_ms']:.1f}ms")
        print(f"     Confidence: {result['confidence']:.2%}")


# ============================================================================
# 4. System Status
# ============================================================================

def example_system_status():
    """
    Check complete hybrid system status.
    
    Includes:
    - Online/offline connectivity
    - Current model source
    - Loaded edge models
    - Performance statistics
    """
    
    print("\n" + "="*60)
    print("4. SYSTEM STATUS")
    print("="*60)
    
    print("\n1️⃣ Full system status:")
    response = requests.get(f"{HYBRID_API}/status")
    status = response.json()
    
    print(f"   Model Source: {status['model_source']}")
    print(f"   Requests Processed: {status['total_requests_processed']}")
    print(f"   Edge Models Available: {', '.join(status['edge_models_available'])}")
    
    print("\n2️⃣ Connectivity details:")
    response = requests.get(f"{HYBRID_API}/connectivity")
    conn = response.json()
    
    print(f"   Online: {'✓ Yes' if conn['is_online'] else '✗ No'}")
    print(f"   Fallback Active: {conn['fallback_active']}")
    if conn.get('latency_ms'):
        print(f"   Cloud Latency: {conn['latency_ms']:.0f}ms")
    print(f"   Consecutive Successes: {conn['consecutive_successes']}")


# ============================================================================
# 5. Available Models
# ============================================================================

def example_available_models():
    """
    List available ONNX edge models.
    
    Shows:
    - Model names
    - Model sizes
    - Quantization info
    - Input/output shapes
    """
    
    print("\n" + "="*60)
    print("5. AVAILABLE EDGE MODELS")
    print("="*60)
    
    response = requests.get(f"{HYBRID_API}/models/available")
    data = response.json()
    
    print(f"\nONNX Available: {data['onnx_available']}")
    print(f"Models Loaded: {data['models_loaded']}")
    
    print("\nAvailable Models:")
    for model in data['models']:
        print(f"\n  📦 {model['name']}")
        print(f"     Size: {model.get('size_mb', 'N/A')} MB")
        print(f"     Quantized: {model.get('quantized', False)}")


# ============================================================================
# 6. Performance Monitoring
# ============================================================================

def example_performance_monitoring():
    """
    Monitor system performance and statistics.
    
    Metrics:
    - Total requests processed
    - Edge vs cloud request counts
    - Average execution time
    - Average confidence
    - Recent execution history
    """
    
    print("\n" + "="*60)
    print("6. PERFORMANCE MONITORING")
    print("="*60)
    
    print("\n1️⃣ Overall performance:")
    response = requests.get(f"{HYBRID_API}/performance")
    perf = response.json()
    
    stats = perf['performance_stats']
    print(f"   Total Requests: {stats.get('total_requests', 0)}")
    print(f"   Edge Requests: {stats.get('edge_requests', 0)}")
    print(f"   Cloud Requests: {stats.get('cloud_requests', 0)}")
    print(f"   Avg Execution: {stats.get('avg_execution_time_ms', 0):.1f}ms")
    
    print(f"\n2️⃣ Recent executions ({len(perf['recent_executions'])} records):")
    for exec in perf['recent_executions'][:3]:
        print(f"   - {exec['model']} via {exec['source']} ({exec['time_ms']:.1f}ms)")
    
    print("\n3️⃣ Per-model performance:")
    response = requests.get(f"{HYBRID_API}/performance?model_name=digital_twin")
    model_perf = response.json()['performance_stats']
    
    print(f"   digital_twin Avg Conf: {model_perf.get('avg_confidence', 0):.2%}")


# ============================================================================
# 7. Fallback Testing
# ============================================================================

def example_fallback_testing():
    """
    Demonstrate automatic fallback to edge when cloud is unavailable.
    
    Scenario:
    - Try cloud prediction
    - If cloud unavailable or slow
    - Automatically fall back to edge ONNX
    """
    
    print("\n" + "="*60)
    print("7. FALLBACK TESTING")
    print("="*60)
    
    print("\n1️⃣ Make prediction in auto mode...")
    request = {
        "model_name": "digital_twin",
        "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25},
        "user_preference": "auto",
        "priority": "normal"
    }
    
    response = requests.post(f"{HYBRID_API}/predict", json=request)
    result = response.json()
    
    print(f"   Model Source: {result['model_source']}")
    print(f"   Fallback Used: {result['fallback_used']}")
    
    if result['fallback_used']:
        print(f"   ⚠️  Cloud was unavailable, switched to edge")
        print(f"   ✓ Accuracy Degradation: {result['edge_degradation_percent']:.1f}%")
    else:
        print(f"   ✓ Cloud available, using best accuracy")


# ============================================================================
# 8. Python Client Library Example
# ============================================================================

class HybridAIClient:
    """
    Python client for SILIQUESTA Hybrid AI API.
    
    Example:
    ```python
    client = HybridAIClient("http://localhost:8000")
    
    result = client.predict(
        model_name="digital_twin",
        inputs={"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
    )
    print(f"Model used: {result['model_source']}")
    print(f"Result: {result['result']}")
    ```
    """
    
    def __init__(self, api_url: str = API_URL):
        """Initialize client"""
        self.api_url = api_url
        self.hybrid_api = f"{api_url}/hybrid"
    
    def predict(self, model_name: str, inputs: Dict[str, Any],
                user_preference: str = "auto") -> Dict[str, Any]:
        """
        Make a hybrid prediction.
        
        Args:
            model_name: Model to use (digital_twin, optimizer, reliability)
            inputs: Input parameters for the model
            user_preference: "auto", "edge", or "cloud"
        
        Returns:
            Prediction result with model source and metadata
        """
        request = {
            "model_name": model_name,
            "inputs": inputs,
            "user_preference": user_preference,
            "priority": "normal"
        }
        
        response = requests.post(f"{self.hybrid_api}/predict", json=request)
        return response.json()
    
    def batch_predict(self, predictions: list) -> list:
        """
        Make multiple predictions efficiently.
        
        Args:
            predictions: List of prediction requests
        
        Returns:
            List of results
        """
        response = requests.post(f"{self.hybrid_api}/predict/batch", json=predictions)
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        response = requests.get(f"{self.hybrid_api}/status")
        return response.json()
    
    def get_connectivity(self) -> Dict[str, Any]:
        """Get connectivity information"""
        response = requests.get(f"{self.hybrid_api}/connectivity")
        return response.json()
    
    def get_performance(self, model_name: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        url = f"{self.hybrid_api}/performance"
        if model_name:
            url += f"?model_name={model_name}"
        
        response = requests.get(url)
        return response.json()
    
    def force_edge(self) -> Dict[str, str]:
        """Force use of edge models"""
        response = requests.get(f"{self.hybrid_api}/force-edge")
        return response.json()
    
    def force_cloud(self) -> Dict[str, str]:
        """Force use of cloud models"""
        response = requests.get(f"{self.hybrid_api}/force-cloud")
        return response.json()


def example_client_usage():
    """Example of using the Python client"""
    
    print("\n" + "="*60)
    print("8. PYTHON CLIENT EXAMPLE")
    print("="*60)
    
    # Create client
    client = HybridAIClient()
    
    print("\n1️⃣ Get system status:")
    status = client.get_status()
    print(f"   Model Source: {status['model_source']}")
    print(f"   Requests Processed: {status['total_requests_processed']}")
    
    print("\n2️⃣ Make prediction:")
    result = client.predict(
        model_name="digital_twin",
        inputs={"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}
    )
    print(f"   Result: {result['result']}")
    print(f"   Source: {result['model_source']}")
    print(f"   Time: {result['execution_time_ms']:.1f}ms")
    
    print("\n3️⃣ Batch predictions:")
    predictions = [
        {"model_name": "digital_twin", "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25}},
        {"model_name": "optimizer", "inputs": {"wn": 2.8, "wp": 5.5, "vdd": 0.95, "temp": 30}},
    ]
    results = client.batch_predict(predictions)
    print(f"   Processed {len(results)} predictions")
    
    print("\n4️⃣ Performance metrics:")
    perf = client.get_performance()
    stats = perf['performance_stats']
    print(f"   Total Requests: {stats.get('total_requests', 0)}")
    print(f"   Avg Time: {stats.get('avg_execution_time_ms', 0):.1f}ms")


# ============================================================================
# 9. Integration with FastAPI App
# ============================================================================

def example_fastapi_integration():
    """
    Show how to integrate the hybrid API with your FastAPI app.
    
    In your main FastAPI file (main.py):
    
    ```python
    from fastapi import FastAPI
    from app.fastapi_app import create_app
    
    # Create app with hybrid AI support
    app = create_app({
        "enable_onnx": True,
        "enable_cloud": True,
        "connectivity_check_interval": 30,
        "cloud_api_timeout": 30
    })
    
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
    
    Or with environment variables:
    
    ```python
    import os
    
    config = {
        "enable_onnx": os.getenv("ENABLE_ONNX", "true").lower() == "true",
        "enable_cloud": os.getenv("ENABLE_CLOUD", "true").lower() == "true",
        "cloud_api_url": os.getenv("CLOUD_API_URL", "https://api.example.com"),
        "cloud_api_key": os.getenv("CLOUD_API_KEY", "")
    }
    
    app = create_app(config)
    ```
    """
    
    print("\n" + "="*60)
    print("9. FASTAPI INTEGRATION")
    print("="*60)
    
    code = '''
from fastapi import FastAPI
from app.fastapi_app import create_app

# Create app with hybrid AI
app = create_app({
    "enable_onnx": True,
    "enable_cloud": True,
    "connectivity_check_interval": 30
})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    print("\nIntegration code:")
    print(code)


# ============================================================================
# 10. Advanced: Monitoring & Dashboards
# ============================================================================

def example_monitoring():
    """
    Monitor hybrid system in real-time.
    
    ```python
    import time
    
    client = HybridAIClient()
    
    while True:
        status = client.get_status()
        conn = client.get_connectivity()
        
        print(f"Model: {status['model_source']} | Online: {conn['is_online']}")
        print(f"Requests: {status['total_requests_processed']}")
        
        time.sleep(5)
    ```
    """
    
    print("\n" + "="*60)
    print("10. REAL-TIME MONITORING")
    print("="*60)
    
    print("""
Use this code to monitor the system in real-time:

```python
import time
from datetime import datetime

client = HybridAIClient()

while True:
    status = client.get_status()
    conn = client.get_connectivity()
    perf = client.get_performance()
    
    # Display status
    timestamp = datetime.now().strftime("%H:%M:%S")
    online = "🟢 Online" if conn['is_online'] else "🔴 Offline"
    source = status['model_source'].upper()
    
    print(f"{timestamp} | {online} | Using {source}")
    print(f"  Total Requests: {status['total_requests_processed']}")
    print(f"  Avg Time: {perf['performance_stats'].get('avg_execution_time_ms', 0):.1f}ms")
    print()
    
    time.sleep(5)
```
""")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all examples"""
    
    print("\n" + "="*70)
    print("SILIQUESTA HYBRID AI REST API - COMPLETE USAGE GUIDE")
    print("="*70)
    
    examples = [
        ("Basic Prediction", example_basic_prediction),
        ("Force Edge Model", example_force_edge),
        ("Batch Predictions", example_batch_predictions),
        ("System Status", example_system_status),
        ("Available Models", example_available_models),
        ("Performance Monitoring", example_performance_monitoring),
        ("Fallback Testing", example_fallback_testing),
        ("Python Client", example_client_usage),
        ("FastAPI Integration", example_fastapi_integration),
        ("Real-Time Monitoring", example_monitoring),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*70)
    print("QUICK START")
    print("="*70)
    
    print("""
1. Start the API server:
   python -m app.fastapi_app
   
   Or with environment config:
   CLOUD_API_URL="https://your-api.com" python -m app.fastapi_app

2. In another terminal, make a prediction:
   
   python -c "
   import requests
   r = requests.post('http://localhost:8000/hybrid/predict', json={
       'model_name': 'digital_twin',
       'inputs': {'wn': 2.5, 'wp': 5.2, 'vdd': 0.9, 'temp': 25}
   })
   print(r.json())
   "

3. Check API documentation:
   http://localhost:8000/docs
   
4. Monitor system status:
   curl http://localhost:8000/hybrid/status | json_pp
""")


if __name__ == "__main__":
    main()
