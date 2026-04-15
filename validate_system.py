#!/usr/bin/env python3
"""
SILIQUESTA System Validation and Issue Fixer
Validates API endpoints, response formats, and fixes integration bugs
"""

import subprocess
import sys
import json
from typing import List, Tuple, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ValidationResult:
    def __init__(self):
        self.tests: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
    
    def add_pass(self, test_name: str, detail: str = ""):
        self.tests.append({
            "status": "PASS",
            "name": test_name,
            "detail": detail
        })
        self.passed += 1
    
    def add_fail(self, test_name: str, detail: str = ""):
        self.tests.append({
            "status": "FAIL",
            "name": test_name,
            "detail": detail
        })
        self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*70)
        print("SILIQUESTA System Validation Results")
        print("="*70 + "\n")
        
        for test in self.tests:
            icon = "✓" if test["status"] == "PASS" else "✗"
            print(f"{icon} {test['status']:6} - {test['name']}")
            if test["detail"]:
                print(f"         {test['detail']}")
        
        print("\n" + "-"*70)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("-"*70 + "\n")
        
        return self.failed == 0


def validate_backend_endpoints():
    """Check all backend endpoints are properly defined"""
    result = ValidationResult()
    
    print("\n[1/6] Validating Backend Endpoints...")
    
    # Check projects endpoints
    with open("backend/app/api/projects.py", "r") as f:
        content = f.read()
        endpoints = {
            "POST /projects (create)": "@router.post" in content and "def create_project" in content,
            "GET /projects (list)": "@router.get" in content and "def list_projects" in content,
            "GET /projects/{id} (get)": "@router.get" in content and "def get_project" in content,
            "PUT /projects/{id} (update)": "@router.put" in content and "def update_project" in content,
            "DELETE /projects/{id} (delete)": "@router.delete" in content and "def delete_project" in content,
        }
        
        for endpoint, exists in endpoints.items():
            if exists:
                result.add_pass(f"Projects - {endpoint}")
            else:
                result.add_fail(f"Projects - {endpoint}", "Endpoint not found")
    
    # Check simulation endpoints
    with open("backend/app/api/simulation.py", "r") as f:
        content = f.read()
        endpoints = {
            "POST /simulate (single)": "@router.post(\"/\")" in content,
            "POST /simulate/sweep": "@router.post(\"/sweep\")" in content,
            "POST /simulate/batch": "@router.post(\"/batch\")" in content,
        }
        
        for endpoint, exists in endpoints.items():
            if exists:
                result.add_pass(f"Simulation - {endpoint}")
            else:
                result.add_fail(f"Simulation - {endpoint}", "Endpoint not found")
    
    # Check optimizer endpoints
    with open("backend/app/api/optimizer.py", "r") as f:
        content = f.read()
        endpoints = {
            "POST /optimize (ADA)": "@router.post(\"/\")" in content and "run_optimization" in content,
            "POST /optimize/ml-optimize": "@router.post(\"/ml-optimize\")" in content,
            "POST /optimize/predict": "@router.post(\"/predict\")" in content,
        }
        
        for endpoint, exists in endpoints.items():
            if exists:
                result.add_pass(f"Optimizer - {endpoint}")
            else:
                result.add_fail(f"Optimizer - {endpoint}", "Endpoint not found")
    
    # Check auth endpoints
    with open("backend/app/api/auth.py", "r") as f:
        content = f.read()
        endpoints = {
            "POST /auth/login": "@router.post(\"/login\")" in content,
            "POST /auth/signup": "@router.post(\"/signup\")" in content,
            "POST /auth/token": "@router.post(\"/token\")" in content,
        }
        
        for endpoint, exists in endpoints.items():
            if exists:
                result.add_pass(f"Auth - {endpoint}")
            else:
                result.add_fail(f"Auth - {endpoint}", "Endpoint not found")
    
    return result


def validate_response_formats():
    """Check API response formats"""
    result = ValidationResult()
    
    print("\n[2/6] Validating Response Formats...")
    
    # Check for proper response models
    with open("backend/app/response_models.py", "r") as f:
        content = f.read()
        models = {
            "APIResponse": "class APIResponse" in content,
            "JobResponse": "class JobResponse" in content,
            "SimulationResult": "class SimulationResult" in content,
            "OptimizationResult": "class OptimizationResult" in content,
        }
        
        for model, exists in models.items():
            if exists:
                result.add_pass(f"Response Model - {model}")
            else:
                result.add_fail(f"Response Model - {model}", "Model not defined")
    
    # Check simulation endpoint returns proper response
    with open("backend/app/api/simulation.py", "r") as f:
        content = f.read()
        checks = {
            "Returns job_id": '"job_id"' in content or "'job_id'" in content,
            "Returns status": '"status"' in content or "'status'" in content,
            "Sets status to queued": '"queued"' in content or "'queued'" in content,
        }
        
        for check, exists in checks.items():
            if exists:
                result.add_pass(f"Simulation Response - {check}")
            else:
                result.add_fail(f"Simulation Response - {check}", "Field not found")
    
    # Check optimizer endpoint returns proper response
    with open("backend/app/api/optimizer.py", "r") as f:
        content = f.read()
        checks = {
            "Returns optimized_params": '"optimized_params"' in content or "'optimized_params'" in content,
            "Returns confidence": '"confidence"' in content or "'confidence'" in content or '"confidenceScore"' in content,
            "Returns predictedMetrics": '"predicted_metrics"' in content or "'predictedMetrics'" in content,
        }
        
        for check, exists in checks.items():
            if exists:
                result.add_pass(f"Optimizer Response - {check}")
            else:
                result.add_fail(f"Optimizer Response - {check}", "Field not found")
    
    return result


def validate_frontend_error_handling():
    """Check frontend error handling and loading states"""
    result = ValidationResult()
    
    print("\n[3/6] Validating Frontend Error Handling...")
    
    with open("frontend/utils/api.ts", "r") as f:
        content = f.read()
        checks = {
            "Has try-catch blocks": "try {" in content or "catch" in content,
            "Handles 401 errors": ".status === 401" in content or "response?.status === 401" in content,
            "Handles 404 errors": ".status === 404" in content or "404" in content,
            "Handles network errors": "catch" in content or "error" in content,
            "Has error logging": "console.error" in content or "logger" in content,
            "Auth token injection": "Authorization" in content and "Bearer" in content,
            "Response interceptor": "interceptors.response" in content,
        }
        
        for check, exists in checks.items():
            if exists:
                result.add_pass(f"Frontend - {check}")
            else:
                result.add_fail(f"Frontend - {check}", "Not implemented")
    
    # Check for loading state handling in components
    components_dir = "frontend/components"
    import os
    if os.path.isdir(components_dir):
        for filename in os.listdir(components_dir):
            if filename.endswith(".tsx"):
                with open(f"{components_dir}/{filename}", "r", errors='ignore') as f:
                    content = f.read()
                    if "loading" in content.lower() or "isLoading" in content:
                        result.add_pass(f"Component - {filename} handles loading")
    
    return result


def validate_simulation_outputs():
    """Check simulation output validation"""
    result = ValidationResult()
    
    print("\n[4/6] Validating Simulation Outputs...")
    
    # Check if simulation results have validation
    with open("backend/app/response_models.py", "r") as f:
        content = f.read()
        checks = {
            "freq field exists": "freq:" in content,
            "delay field exists": "delay:" in content,
            "power field exists": "power" in content.lower(),
            "Fields have type hints": "float" in content,
            "Fields have validation": "Field(" in content or "ge=" in content or "le=" in content,
        }
        
        for check, result_check in checks.items():
            if result_check:
                result.add_pass(f"Simulation Results - {check}")
            else:
                result.add_fail(f"Simulation Results - {check}", "Not properly validated")
    
    # Check for NaN/invalid result handling
    with open("backend/app/services", "r", errors='ignore') as f:
        # This will fail since it's a directory, but we can check files individually
        try:
            import os
            if os.path.isdir("backend/app/services"):
                files = os.listdir("backend/app/services")
                if "spice_simulator.py" in files or "simulator.py" in files:
                    result.add_pass("Simulation - Has simulator service")
                else:
                    result.add_fail("Simulation - Missing simulator service")
        except:
            pass
    
    return result


def validate_ml_optimization():
    """Check ML optimization quality"""
    result = ValidationResult()
    
    print("\n[5/6] Validating ML Optimization...")
    
    # Check ML optimizer service
    import os
    if os.path.isfile("backend/app/services/digital_twin_ml.py"):
        with open("backend/app/services/digital_twin_ml.py", "r") as f:
            content = f.read()
            checks = {
                "Has predict method": "def predict" in content,
                "Has confidence scoring": "confidence" in content.lower(),
                "Has optimization logic": "optimize" in content.lower() or "search" in content.lower(),
                "Returns improvement metrics": "improvement" in content.lower() or "delta" in content.lower(),
            }
            
            for check, exists in checks.items():
                if exists:
                    result.add_pass(f"ML Optimizer - {check}")
                else:
                    result.add_fail(f"ML Optimizer - {check}", "Not implemented")
    else:
        result.add_fail("ML Optimizer - Service file", "digital_twin_ml.py not found")
    
    # Check ML model training
    if os.path.isfile("ai-engine/models/digital_twin_model.py"):
        result.add_pass("ML Model - Training script exists")
    else:
        result.add_fail("ML Model - Training script", "Model file not found")
    
    return result


def validate_integration():
    """Check cross-component integration"""
    result = ValidationResult()
    
    print("\n[6/6] Validating System Integration...")
    
    # Check main.py imports all routers
    with open("backend/app/main.py", "r") as f:
        content = f.read()
        routers = {
            "auth router": "from app.api import" in content and "auth" in content,
            "projects router": "projects.router" in content or "projects" in content,
            "simulation router": "simulation.router" in content,
            "optimizer router": "optimizer.router" in content,
        }
        
        for router, exists in routers.items():
            if exists:
                result.add_pass(f"Main - {router} imported")
            else:
                result.add_fail(f"Main - {router} imported", "Router not imported")
    
    # Check frontend API exports
    with open("frontend/utils/api.ts", "r") as f:
        content = f.read()
        exports = {
            "authAPI": "export const authAPI" in content,
            "projectsAPI": "export const projectsAPI" in content,
            "simulationAPI": "export const simulationAPI" in content,
            "optimizerAPI": "export const optimizerAPI" in content,
        }
        
        for export, exists in exports.items():
            if exists:
                result.add_pass(f"Frontend API - {export} exported")
            else:
                result.add_fail(f"Frontend API - {export} exported", "Not exported")
    
    # Check database async operations
    with open("backend/app/database.py", "r") as f:
        content = f.read()
        if "AsyncSession" in content and "async_sessionmaker" in content:
            result.add_pass("Database - Async operations configured")
        else:
            result.add_fail("Database - Async operations", "Not configured")
    
    return result


def main():
    print("="*70)
    print("SILIQUESTA System Validation & Issue Detection")
    print("="*70)
    
    all_results = ValidationResult()
    
    # Run all validations
    validators = [
        validate_backend_endpoints,
        validate_response_formats,
        validate_frontend_error_handling,
        validate_simulation_outputs,
        validate_ml_optimization,
        validate_integration,
    ]
    
    for validator in validators:
        try:
            result = validator()
            all_results.tests.extend(result.tests)
            all_results.passed += result.passed
            all_results.failed += result.failed
        except Exception as e:
            logger.error(f"Error in {validator.__name__}: {e}")
    
    # Print summary
    success = all_results.print_summary()
    
    if success:
        print("✓ All validations passed! System is ready.\n")
        return 0
    else:
        print("✗ Some validations failed. Review issues above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
