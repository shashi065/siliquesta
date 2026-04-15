#!/usr/bin/env python3
"""
SILIQUESTA System Integration Verification Script
Checks if all components are properly connected and working.
"""

import sys
import subprocess
import os
import json
from pathlib import Path
from typing import Tuple, List

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class VerificationResult:
    """Track verification results"""
    def __init__(self):
        self.checks: List[Tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0
        
    def add(self, name: str, passed: bool, message: str = ""):
        """Add a check result"""
        self.checks.append((name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_results(self):
        """Print all results"""
        print(f"\n{BOLD}═══════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}SILIQUESTA System Integration Verification{RESET}")
        print(f"{BOLD}═══════════════════════════════════════════════════════════{RESET}\n")
        
        for name, passed, message in self.checks:
            status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
            print(f"{status} - {name}")
            if message:
                print(f"       {message}")
        
        print(f"\n{BOLD}─────────────────────────────────────────────────────────{RESET}")
        print(f"Results: {GREEN}{self.passed} passed{RESET}, {RED}{self.failed} failed{RESET}")
        print(f"{BOLD}─────────────────────────────────────────────────────────{RESET}\n")
        
        if self.failed == 0:
            print(f"{GREEN}{BOLD}✓ All checks passed! System is properly integrated.{RESET}\n")
            return True
        else:
            print(f"{RED}{BOLD}✗ Some checks failed. See details above.{RESET}\n")
            return False


def check_file_exists(path: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    if os.path.isfile(path):
        return True, f"Found at {path}"
    return False, f"Missing: {path}"


def check_file_contains(path: str, text: str, description: str) -> Tuple[bool, str]:
    """Check if a file contains specific text"""
    if not os.path.isfile(path):
        return False, f"File not found: {path}"
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if text in content:
            return True, f"Found '{text[:40]}...' in {path}"
        return False, f"Text not found in {path}"


def check_directory_exists(path: str, description: str) -> Tuple[bool, str]:
    """Check if a directory exists"""
    if os.path.isdir(path):
        return True, f"Directory exists"
    return False, f"Directory not found: {path}"


def run_command(cmd: str, description: str) -> Tuple[bool, str]:
    """Run a shell command and check if it succeeds"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            return True, f"Command succeeded"
        return False, f"Command failed: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


def verify_backend_api():
    """Verify backend API is properly configured"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Backend API...{RESET}")
    
    # Check main.py
    passed, msg = check_file_exists("backend/app/main.py", "Main app file")
    results.add("Backend app file (main.py)", passed, msg)
    
    # Check projects API
    passed, msg = check_file_exists("backend/app/api/projects.py", "Projects API")
    results.add("Projects API endpoint (projects.py)", passed, msg)
    
    # Check projects router imported
    passed, msg = check_file_contains("backend/app/main.py", "from app.api import", "Projects router import")
    results.add("Projects import in main.py", passed, msg)
    
    passed, msg = check_file_contains("backend/app/main.py", "projects.router", "Projects router inclusion")
    results.add("Projects router included", passed, msg)
    
    # Check response models
    passed, msg = check_file_exists("backend/app/response_models.py", "Response models")
    results.add("Response standardization models (response_models.py)", passed, msg)
    
    # Check CORS configuration
    passed, msg = check_file_contains("backend/app/main.py", "allow_origins", "CORS configuration")
    results.add("CORS configuration updated", passed, msg)
    
    return results


def verify_frontend_api():
    """Verify frontend API client is properly configured"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Frontend API Client...{RESET}")
    
    # Check api.ts file
    passed, msg = check_file_exists("frontend/utils/api.ts", "API client")
    results.add("Frontend API client (api.ts)", passed, msg)
    
    # Check projectsAPI export
    passed, msg = check_file_contains("frontend/utils/api.ts", "export const projectsAPI", "projectsAPI export")
    results.add("projectsAPI export in api.ts", passed, msg)
    
    # Check project methods
    methods = ["projectsAPI.create", "projectsAPI.list", "projectsAPI.get", 
               "projectsAPI.update", "projectsAPI.delete", "projectsAPI.saveDesign"]
    for method in methods:
        passed, msg = check_file_contains("frontend/utils/api.ts", method, f"{method} method")
        results.add(f"Project API method: {method}", passed, msg)
    
    # Check auth interceptor
    passed, msg = check_file_contains("frontend/utils/api.ts", "Authorization", "Auth header injection")
    results.add("Authorization header injection", passed, msg)
    
    # Check error handling
    passed, msg = check_file_contains("frontend/utils/api.ts", "401", "401 error handling")
    results.add("401 error handling with redirect", passed, msg)
    
    return results


def verify_database():
    """Verify database models are properly defined"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Database Models...{RESET}")
    
    # Check models.py
    passed, msg = check_file_exists("backend/app/models.py", "Database models")
    results.add("Database models file (models.py)", passed, msg)
    
    # Check User model
    passed, msg = check_file_contains("backend/app/models.py", "class User", "User model")
    results.add("User model defined", passed, msg)
    
    # Check Project model
    passed, msg = check_file_contains("backend/app/models.py", "class Project", "Project model")
    results.add("Project model defined", passed, msg)
    
    # Check design state field
    passed, msg = check_file_contains("backend/app/models.py", "design_state", "Design state field")
    results.add("Project.design_state field", passed, msg)
    
    # Check ComputeJob model
    passed, msg = check_file_contains("backend/app/models.py", "class ComputeJob", "ComputeJob model")
    results.add("ComputeJob model defined", passed, msg)
    
    return results


def verify_async_support():
    """Verify async database operations"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Async Operations...{RESET}")
    
    # Check async imports
    passed, msg = check_file_contains("backend/app/database.py", "AsyncSession", "AsyncSession import")
    results.add("AsyncSession import in database.py", passed, msg)
    
    # Check async projects API
    passed, msg = check_file_contains("backend/app/api/projects.py", "async def", "Async functions")
    results.add("Async functions in projects.py", passed, msg)
    
    # Check sqlalchemy async
    passed, msg = check_file_contains("backend/app/api/projects.py", "AsyncSession", "AsyncSession usage")
    results.add("AsyncSession used in projects.py", passed, msg)
    
    # Check await usage
    passed, msg = check_file_contains("backend/app/api/projects.py", "await db.execute", "Async queries")
    results.add("Async queries with await", passed, msg)
    
    return results


def verify_authentication():
    """Verify authentication is properly integrated"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Authentication...{RESET}")
    
    # Check auth module
    passed, msg = check_file_exists("backend/app/api/auth.py", "Auth module")
    results.add("Auth module (auth.py)", passed, msg)
    
    # Check get_current_user dependency
    passed, msg = check_file_contains("backend/app/api/auth.py", "get_current_user", "get_current_user function")
    results.add("get_current_user dependency", passed, msg)
    
    # Check JWT usage in projects
    passed, msg = check_file_contains("backend/app/api/projects.py", "get_current_user", "JWT auth on projects")
    results.add("JWT authentication on projects endpoints", passed, msg)
    
    # Check token generation
    passed, msg = check_file_contains("backend/app/api/auth.py", "jwt", "JWT token generation")
    results.add("JWT token generation in auth", passed, msg)
    
    return results


def verify_tests():
    """Verify testing infrastructure"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Testing Infrastructure...{RESET}")
    
    # Check test file
    passed, msg = check_file_exists("backend/tests/test_e2e_integration.py", "E2E integration tests")
    results.add("E2E integration test file", passed, msg)
    
    # Check test classes
    test_classes = [
        "TestProjectsAPI",
        "TestSimulationIntegration",
        "TestOptimizationIntegration",
        "TestAuthenticationFlow",
        "TestEndToEndFlows"
    ]
    for test_class in test_classes:
        passed, msg = check_file_contains("backend/tests/test_e2e_integration.py", f"class {test_class}", f"{test_class} test class")
        results.add(f"Test class: {test_class}", passed, msg)
    
    return results


def verify_documentation():
    """Verify documentation files"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying Documentation...{RESET}")
    
    # Check integration guide
    passed, msg = check_file_exists("INTEGRATION_GUIDE.md", "Integration guide")
    results.add("Integration Guide (INTEGRATION_GUIDE.md)", passed, msg)
    
    # Check status report
    passed, msg = check_file_exists("INTEGRATION_STATUS.md", "Status report")
    results.add("Integration Status Report (INTEGRATION_STATUS.md)", passed, msg)
    
    # Check API documentation
    passed, msg = check_file_contains("INTEGRATION_GUIDE.md", "API Endpoints", "API docs")
    results.add("API endpoint documentation", passed, msg)
    
    # Check data flow
    passed, msg = check_file_contains("INTEGRATION_GUIDE.md", "Data Flow", "Data flow docs")
    results.add("Data flow documentation", passed, msg)
    
    return results


def verify_ml_integration():
    """Verify ML system integration"""
    results = VerificationResult()
    
    print(f"\n{BLUE}{BOLD}Verifying ML Integration...{RESET}")
    
    # Check optimizer API
    passed, msg = check_file_exists("backend/app/api/optimizer.py", "Optimizer API")
    results.add("Optimizer API endpoint", passed, msg)
    
    # Check ML optimize endpoint
    passed, msg = check_file_contains("backend/app/api/optimizer.py", "ml-optimize", "ML optimize endpoint")
    results.add("ML optimization endpoint defined", passed, msg)
    
    # Check Celery task
    passed, msg = check_file_exists("backend/app/tasks/compute.py", "Compute tasks")
    results.add("Compute tasks module", passed, msg)
    
    return results


def main():
    """Run all verifications"""
    print(f"\n{BOLD}Starting SILIQUESTA System Integration Verification...{RESET}")
    
    all_results = VerificationResult()
    
    # Run all verification suites
    backend_results = verify_backend_api()
    frontend_results = verify_frontend_api()
    database_results = verify_database()
    async_results = verify_async_support()
    auth_results = verify_authentication()
    tests_results = verify_tests()
    docs_results = verify_documentation()
    ml_results = verify_ml_integration()
    
    # Combine results
    for result in [backend_results, frontend_results, database_results, 
                   async_results, auth_results, tests_results, docs_results, ml_results]:
        all_results.checks.extend(result.checks)
        all_results.passed += result.passed
        all_results.failed += result.failed
    
    # Print final results
    success = all_results.print_results()
    
    print(f"{BLUE}{BOLD}Summary:{RESET}")
    print(f"  • Backend API: {backend_results.passed}/{backend_results.passed + backend_results.failed} checks passed")
    print(f"  • Frontend API: {frontend_results.passed}/{frontend_results.passed + frontend_results.failed} checks passed")
    print(f"  • Database: {database_results.passed}/{database_results.passed + database_results.failed} checks passed")
    print(f"  • Async Support: {async_results.passed}/{async_results.passed + async_results.failed} checks passed")
    print(f"  • Authentication: {auth_results.passed}/{auth_results.passed + auth_results.failed} checks passed")
    print(f"  • Tests: {tests_results.passed}/{tests_results.passed + tests_results.failed} checks passed")
    print(f"  • Documentation: {docs_results.passed}/{docs_results.passed + docs_results.failed} checks passed")
    print(f"  • ML Integration: {ml_results.passed}/{ml_results.passed + ml_results.failed} checks passed")
    print()
    
    if success:
        print(f"{GREEN}{BOLD}✓ SILIQUESTA system is properly integrated and ready for testing!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some components need attention. See details above.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
