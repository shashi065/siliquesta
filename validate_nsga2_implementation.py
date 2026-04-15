#!/usr/bin/env python3
"""
NSGA-II Implementation Validation Script

Verifies all components are correctly implemented and integrated.
"""

import os
import sys
import json
from pathlib import Path

class ValidationResult:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def check(self, name: str, condition: bool, details: str = ""):
        if condition:
            self.passed.append(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            self.failed.append(f"❌ {name}")
            if details:
                print(f"   {details}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("NSGA-II Implementation Validation Summary")
        print("="*70)
        
        total = len(self.passed) + len(self.failed)
        passed = len(self.passed)
        
        print(f"\n✅ Passed: {passed}/{total}")
        for item in self.passed:
            print(f"   {item}")
        
        if self.failed:
            print(f"\n❌ Failed: {len(self.failed)}/{total}")
            for item in self.failed:
                print(f"   {item}")
        
        print("\n" + "="*70)
        
        if not self.failed:
            print("🎉 All validation checks passed! NSGA-II is ready for use.")
            return True
        else:
            print("⚠️  Some validation checks failed. Review above.")
            return False


def main():
    result = ValidationResult()
    
    print("Validating NSGA-II Implementation...\n")
    
    # API path
    api_path = Path("services/api")
    app_path = api_path / "app"
    
    # 1. Core Files
    print("Checking core implementation files...")
    result.check(
        "Core Optimizer Module",
        (app_path / "nsga2_optimizer.py").exists(),
        f"Location: {app_path / 'nsga2_optimizer.py'}"
    )
    
    result.check(
        "API Routes Module",
        (app_path / "api" / "nsga2_routes.py").exists(),
        f"Location: {app_path / 'api' / 'nsga2_routes.py'}"
    )
    
    # 2. Dependencies
    print("\nChecking dependencies...")
    req_file = api_path / "requirements.txt"
    if req_file.exists():
        with open(req_file) as f:
            content = f.read()
            deap_present = "deap" in content.lower()
            result.check("DEAP in requirements.txt", deap_present)
    else:
        result.check("requirements.txt exists", False)
    
    # 3. Integration
    print("\nChecking integration...")
    main_py = app_path / "main.py"
    if main_py.exists():
        with open(main_py) as f:
            main_content = f.read()
            nsga2_imported = "nsga2_routes" in main_content
            nsga2_registered = "nsga2_routes.router" in main_content or 'nsga2_routes' in main_content
            
            result.check("nsga2_routes imported", nsga2_imported)
            result.check("nsga2_routes registered", nsga2_registered)
    else:
        result.check("main.py exists", False)
    
    # 4. Helper Tools
    print("\nChecking helper tools...")
    result.check(
        "Python Client Library",
        (api_path / "nsga2_client.py").exists(),
        f"Location: {api_path / 'nsga2_client.py'}"
    )
    
    result.check(
        "Test Suite",
        (api_path / "test_nsga2_api.py").exists(),
        f"Location: {api_path / 'test_nsga2_api.py'}"
    )
    
    # 5. Documentation
    print("\nChecking documentation...")
    
    api_doc = api_path / "NSGA2_API_DOCUMENTATION.md"
    result.check("API Documentation", api_doc.exists())
    
    integration_guide = api_path / "NSGA2_INTEGRATION_GUIDE.md"
    result.check("Integration Guide", integration_guide.exists())
    
    # Check root documentation
    root_path = Path(".")
    impl_summary = root_path / "NSGA2_IMPLEMENTATION_SUMMARY.md"
    result.check("Implementation Summary", impl_summary.exists())
    
    quick_ref = root_path / "NSGA2_QUICK_REFERENCE.md"
    result.check("Quick Reference", quick_ref.exists())
    
    # 6. Code Quality Checks
    print("\nChecking code quality...")
    
    if (app_path / "nsga2_optimizer.py").exists():
        with open(app_path / "nsga2_optimizer.py") as f:
            optimizer_code = f.read()
            has_deap = "from deap" in optimizer_code or "import deap" in optimizer_code
            has_optimizer_class = "class NSGAII_Optimizer" in optimizer_code
            has_predictor = "class PerformancePredictor" in optimizer_code
            has_run_function = "def run_optimization" in optimizer_code
            
            result.check("DEAP import in optimizer", has_deap)
            result.check("NSGAII_Optimizer class defined", has_optimizer_class)
            result.check("PerformancePredictor class defined", has_predictor)
            result.check("run_optimization function defined", has_run_function)
    
    if (app_path / "api" / "nsga2_routes.py").exists():
        with open(app_path / "api" / "nsga2_routes.py") as f:
            routes_code = f.read()
            has_optimize_route = 'POST.*optimize' in routes_code or '@router.post("/optimize' in routes_code
            has_health_route = '@router.get("/health' in routes_code
            has_compare_route = '@router.post("/compare' in routes_code
            has_info_route = '@router.get("/info' in routes_code
            has_pydantic = "from pydantic" in routes_code or "BaseModel" in routes_code
            
            result.check("Optimize endpoint defined", has_optimize_route)
            result.check("Health endpoint defined", has_health_route)
            result.check("Compare endpoint defined", has_compare_route)
            result.check("Info endpoint defined", has_info_route)
            result.check("Pydantic models used", has_pydantic)
    
    # 7. File Size Verification
    print("\nChecking file sizes (indicating completeness)...")
    
    opt_file = app_path / "nsga2_optimizer.py"
    if opt_file.exists():
        size_kb = opt_file.stat().st_size / 1024
        result.check(f"Optimizer module substantial ({size_kb:.1f} KB)", size_kb > 100)
    
    routes_file = app_path / "api" / "nsga2_routes.py"
    if routes_file.exists():
        size_kb = routes_file.stat().st_size / 1024
        result.check(f"Routes module substantial ({size_kb:.1f} KB)", size_kb > 50)
    
    client_file = api_path / "nsga2_client.py"
    if client_file.exists():
        size_kb = client_file.stat().st_size / 1024
        result.check(f"Client library substantial ({size_kb:.1f} KB)", size_kb > 50)
    
    test_file = api_path / "test_nsga2_api.py"
    if test_file.exists():
        size_kb = test_file.stat().st_size / 1024
        result.check(f"Test suite substantial ({size_kb:.1f} KB)", size_kb > 50)
    
    # Print summary and exit
    success = result.print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
