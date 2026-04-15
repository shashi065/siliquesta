#!/usr/bin/env python3
"""
Async Task System - Test Suite

Demonstrates submitting async jobs and monitoring status.
"""

import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def submit_optimization_job(wn: float = 1.0, wp: float = 2.0) -> str:
    """Submit optimization job and return job_id."""
    payload = {
        "wn": wn,
        "wp": wp,
        "vdd": 1.8,
        "temp": 27.0,
        "cl_ff": 10.0,
        "max_power": 5.0,
        "population_size": 48,
        "generations": 10,
    }
    
    response = requests.post(f"{BASE_URL}/ts/optimizer/", json=payload)
    response.raise_for_status()
    data = response.json()
    return data["job_id"]


def submit_ml_optimization_job(objective: str = "balanced") -> str:
    """Submit ML optimization job and return job_id."""
    payload = {
        "wn": 1.0,
        "wp": 2.0,
        "vdd": 1.8,
        "temp": 27.0,
        "objective": objective,
        "iterations": 100,
        "method": "two_stage",
    }
    
    response = requests.post(f"{BASE_URL}/ts/optimizer/ml-optimize", json=payload)
    response.raise_for_status()
    data = response.json()
    return data["job_id"]


def submit_training_job(samples: int = 5000) -> str:
    """Submit training job and return job_id."""
    payload = {
        "sample_count": samples,
        "prefer_spice": False,
    }
    
    response = requests.post(f"{BASE_URL}/ts/digital_twin/train", json=payload)
    response.raise_for_status()
    data = response.json()
    return data["job_id"]


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get current status of a job."""
    response = requests.get(f"{BASE_URL}/status/task/{job_id}/status")
    response.raise_for_status()
    return response.json()


def get_job_result(job_id: str) -> Dict[str, Any]:
    """Get result of a completed job."""
    try:
        response = requests.get(f"{BASE_URL}/status/task/{job_id}/result")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 202:
            return {"status": "pending", "message": "Task not yet complete"}
        raise


def monitor_job(job_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
    """
    Monitor a job until completion.
    
    Args:
        job_id: Job ID to monitor
        timeout: Max seconds to wait
        poll_interval: Seconds between status checks
        
    Returns:
        Final job result or timeout notification
    """
    print(f"\n{'='*60}")
    print(f"Monitoring Job: {job_id}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > timeout:
            print(f"❌ TIMEOUT after {timeout} seconds")
            return {"status": "timeout"}
        
        # Get status
        try:
            status = get_job_status(job_id)
            job_status = status.get("status", "unknown").upper()
            
            print(f"[{elapsed:>6.1f}s] Status: {job_status:<10}", end="")
            
            # Check if complete
            if status.get("successful"):
                print(" ✅ COMPLETE")
                result = get_job_result(job_id)
                print(f"\nResult keys: {list(result.keys())}")
                return result
            
            elif job_status == "FAILURE":
                print(" ❌ FAILED")
                error = status.get("error", "Unknown error")
                print(f"Error: {error}")
                return status
            
            else:
                print(f" (waiting...)")
        
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return {"status": "error", "error": str(e)}
        
        # Wait before next poll
        time.sleep(poll_interval)


def test_optimization():
    """Test optimization job submission and monitoring."""
    print("\n" + "="*60)
    print("TEST 1: Optimization Job")
    print("="*60)
    
    print("\n1. Submitting optimization job...")
    job_id = submit_optimization_job(wn=1.0, wp=2.0)
    print(f"   Job ID: {job_id}")
    
    print("\n2. Monitoring job status...")
    result = monitor_job(job_id, timeout=120)
    
    if result.get("status") != "timeout":
        print(f"\n3. Success! Result summary:")
        if "pareto_front" in result:
            print(f"   - Pareto front size: {len(result['pareto_front'])}")
        if "best_design" in result:
            print(f"   - Best design: wn={result['best_design'].get('wn')}, wp={result['best_design'].get('wp')}")


def test_ml_optimization():
    """Test ML optimization job submission and monitoring."""
    print("\n" + "="*60)
    print("TEST 2: ML Optimization Job")
    print("="*60)
    
    print("\n1. Submitting ML optimization job...")
    job_id = submit_ml_optimization_job(objective="power")
    print(f"   Job ID: {job_id}")
    
    print("\n2. Monitoring job status...")
    result = monitor_job(job_id, timeout=120)
    
    if result.get("status") != "timeout":
        print(f"\n3. Success! Result summary:")
        if "optimized_params" in result:
            print(f"   - Optimized parameters: {result['optimized_params']}")


def test_training():
    """Test training job submission and monitoring."""
    print("\n" + "="*60)
    print("TEST 3: Model Training Job")
    print("="*60)
    
    print("\n1. Submitting training job (5000 samples)...")
    job_id = submit_training_job(samples=5000)
    print(f"   Job ID: {job_id}")
    
    print("\n2. Monitoring job status...")
    result = monitor_job(job_id, timeout=300)  # Training takes longer
    
    if result.get("status") != "timeout":
        print(f"\n3. Success! Result summary:")
        if "metadata" in result:
            print(f"   - Models trained: {result['metadata']}")


def test_batch_submission():
    """Test submitting multiple jobs simultaneously."""
    print("\n" + "="*60)
    print("TEST 4: Batch Job Submission")
    print("="*60)
    
    print("\n1. Submitting 3 optimization jobs...")
    job_ids = []
    for i in range(3):
        job_id = submit_optimization_job(wn=0.5+i*0.5, wp=2.0+i*0.5)
        job_ids.append(job_id)
        print(f"   Job {i+1}: {job_id}")
    
    print("\n2. Monitoring all jobs in parallel...")
    results = {}
    for job_id in job_ids:
        result = monitor_job(job_id, timeout=60, poll_interval=3)
        results[job_id] = result
    
    print(f"\n3. Batch complete! Processed {len(results)} jobs")


def test_quick_status_check():
    """Test quick status checks without waiting."""
    print("\n" + "="*60)
    print("TEST 5: Quick Status Check")
    print("="*60)
    
    print("\n1. Submitting quick optimization job...")
    job_id = submit_ml_optimization_job()
    print(f"   Job ID: {job_id}")
    
    print("\n2. Quick status check (immediate):")
    status = get_job_status(job_id)
    print(f"   Status: {status.get('status')}")
    print(f"   Successful: {status.get('successful')}")
    
    print("\n3. Attempting immediate result retrieval (should fail):")
    try:
        result = get_job_result(job_id)
        print(f"   {result}")
    except Exception as e:
        print(f"   Expected: Task not yet complete ({e.response.status_code})")
    
    print("\n4. This demonstrates non-blocking API behavior")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("ASYNC TASK SYSTEM - TEST SUITE")
        print("="*60)
        print("\nPrerequisites:")
        print("  • Redis running: redis-server")
        print("  • Celery workers running: celery -A app.celery_app worker")
        print("  • API running: python -m uvicorn app.main:app")
        print("\nMake sure API is at:", BASE_URL)
        
        # Run tests
        test_quick_status_check()
        test_ml_optimization()
        test_optimization()
        test_training()
        # test_batch_submission()  # Uncomment for stress test
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETE")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to API at {BASE_URL}")
        print("   Make sure:")
        print("   1. Redis is running: redis-server")
        print("   2. Celery worker is running: celery -A app.celery_app worker")
        print("   3. API is running: python -m uvicorn app.main:app")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
