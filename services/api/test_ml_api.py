"""
Quick integration test for the ML Prediction API.

Run this after starting the backend to verify the API is working.

Usage:
    # First start the backend
    uvicorn app.main:app --reload
    
    # In another terminal
    python test_ml_api.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
API_V1_BASE = f"{API_BASE_URL}/api/v1"
PREDICT_BASE = f"{API_V1_BASE}/predict"

# ANSI colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def test_backend_health():
    """Test backend health endpoint."""
    print_header("1. Testing Backend Health")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print_success("Backend is running")
            data = response.json()
            print(f"  Status: {data['status']}")
            return True
        else:
            print_error(f"Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on port 8000?")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_predict_health():
    """Test ML prediction health endpoint."""
    print_header("2. Testing ML Prediction Health")
    
    try:
        response = requests.get(f"{PREDICT_BASE}/health")
        data = response.json()
        
        if data['status'] == 'healthy':
            print_success("ML prediction service is healthy")
            print(f"  Model Trained: {data['model_trained']}")
            if data['model_trained']:
                print(f"  Training Date: {data['training_date']}")
                print(f"  Training Samples: {data['training_samples']}")
            return True
        else:
            print_error(f"ML service unhealthy: {data.get('error', 'Unknown error')}")
            if not data['model_trained']:
                print_info("Tip: Train a model using /predict/train endpoint first")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_model_info():
    """Get model information."""
    print_header("3. Getting Model Information")
    
    try:
        response = requests.get(f"{PREDICT_BASE}/models")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Model information retrieved")
            print(f"  Trained: {data['trained']}")
            print(f"  Features: {', '.join(data['feature_names'])}")
            
            if data['performance_metrics']:
                print("\n  Performance Metrics:")
                for target, metrics in data['performance_metrics'].items():
                    print(f"    {target}:")
                    print(f"      R²: {metrics.get('r2', 'N/A'):.4f}")
                    print(f"      RMSE: {metrics.get('rmse', 'N/A'):.6e}")
            return True
        else:
            print_error(f"Failed to get model info: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_single_prediction():
    """Test single prediction endpoint."""
    print_header("4. Testing Single Prediction")
    
    # Test inputs
    test_cases = [
        {"name": "Nominal", "C": 5e-12, "Id": 2e-3, "VDD": 3.3},
        {"name": "High Performance", "C": 1e-12, "Id": 5e-3, "VDD": 5.0},
        {"name": "Low Power", "C": 10e-12, "Id": 1e-3, "VDD": 1.8},
    ]
    
    for case in test_cases:
        try:
            print(f"\nTesting: {case['name']}")
            print(f"  Input: C={case['C']*1e12:.1f}pF, Id={case['Id']*1e3:.1f}mA, VDD={case['VDD']:.1f}V")
            
            response = requests.post(
                PREDICT_BASE,
                json={"C": case['C'], "Id": case['Id'], "VDD": case['VDD']}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Prediction received")
                
                for target in ['frequency', 'power', 'delay']:
                    pred = data[target]
                    print(f"    {target.upper()}:")
                    print(f"      Value: {pred['predicted_value']:.6f}")
                    print(f"      Confidence: {pred['confidence']:.1%}")
                    print(f"      95% CI: [{pred['lower_bound']:.6f}, {pred['upper_bound']:.6f}]")
            else:
                print_error(f"Prediction failed: {response.status_code}")
                if response.status_code == 503:
                    print_info("Model not trained. Use /predict/train to train first.")
                
        except Exception as e:
            print_error(f"Error: {e}")


def test_batch_prediction():
    """Test batch prediction endpoint."""
    print_header("5. Testing Batch Prediction")
    
    batch_data = [
        {"C": 5e-12, "Id": 2e-3, "VDD": 3.3},
        {"C": 1e-12, "Id": 5e-3, "VDD": 5.0},
    ]
    
    try:
        response = requests.post(
            f"{PREDICT_BASE}/batch",
            json=batch_data
        )
        
        if response.status_code == 200:
            predictions = response.json()
            print_success(f"Batch prediction received ({len(predictions)} items)")
            for i, pred in enumerate(predictions):
                print(f"  Item {i+1}: Frequency={pred['frequency']['predicted_value']:.3f} GHz")
        else:
            print_error(f"Batch prediction failed: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error: {e}")


def test_train_model():
    """Test model training endpoint."""
    print_header("6. Testing Model Training (Optional)")
    
    print_info("Training model with 1000 samples...")
    print_info("This will take 1-2 minutes, continuing with other tests...\n")
    
    try:
        # Start training asynchronously
        response = requests.post(
            f"{PREDICT_BASE}/train",
            json={"n_samples": 1000, "model_name": "test_model"},
            timeout=600  # 10 minute timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Model trained: {data['model_name']}")
            print(f"  Status: {data['status']}")
            print(f"  Samples: {data['training_samples']}")
            if 'performance_metrics' in data:
                print("  Performance:")
                for target, metrics in data['performance_metrics'].items():
                    print(f"    {target}: R²={metrics.get('r2', 'N/A'):.4f}")
        else:
            print_error(f"Training failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print_error("Training request timed out (> 10 minutes)")
    except Exception as e:
        print_error(f"Error: {e}")


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "ML Prediction API Integration Test" + " "*18 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.RESET}")
    
    # Run tests
    results = []
    
    results.append(("Backend Health", test_backend_health()))
    if not results[-1][1]:
        print_error("Cannot continue without backend. Exiting.")
        return
    
    results.append(("ML Health Check", test_predict_health()))
    
    if results[-1][1]:  # If model is ready
        results.append(("Model Info", test_model_info()))
        results.append(("Single Prediction", test_single_prediction()))
        results.append(("Batch Prediction", test_batch_prediction()))
    else:
        print_info("Skipping prediction tests - model not trained")
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {Colors.BOLD}{passed}/{total} passed{Colors.RESET}")
    
    # Next steps
    if passed == total and results[1][1]:  # All pass and model is trained
        print_success("All tests passed! ML API is ready to use.")
    else:
        print(f"\n{Colors.YELLOW}Next steps:{Colors.RESET}")
        if not results[1][1]:
            print("  1. Train a model:")
            print("     POST /api/v1/predict/train")
            print("  2. Re-run this test")
        
        print(f"\n  Visit API documentation:")
        print(f"    Swagger UI: http://localhost:8000/docs")
        print(f"    ReDoc: http://localhost:8000/redoc")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
