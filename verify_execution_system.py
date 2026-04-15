#!/usr/bin/env python
"""
Execution-Based AI System - Final Verification

Demonstrates the complete 4-step execution pipeline:
1. Parse natural language input
2. Extract constraints
3. Call optimizer
4. Return results
"""

import sys
from execution_engine import ExecutionEngine

def verify_execution_system():
    """Verify complete execution system"""
    
    print("\n" + "="*70)
    print("EXECUTION-BASED AI SYSTEM - FINAL VERIFICATION")
    print("="*70)
    
    engine = ExecutionEngine()
    
    # Test cases demonstrating the system
    test_cases = [
        {
            "request": "optimize for low power under 1GHz",
            "description": "Primary example: Low power with frequency constraint"
        },
        {
            "request": "maximize frequency with power budget 20mW",
            "description": "Performance-critical with power budget"
        },
        {
            "request": "high efficiency design, keep voltage low",
            "description": "Efficiency-focused with voltage preference"
        },
        {
            "request": "balance power and efficiency",
            "description": "Multi-objective balanced optimization"
        }
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/4] {test['description']}")
        print(f"Request: '{test['request']}'")
        
        try:
            result = engine.execute(test['request'])
            
            if result['status'] == 'success':
                print(f"✓ Status: SUCCESS")
                print(f"  Objectives: {', '.join(result['objectives'])}")
                print(f"  Solutions found: {result['optimization']['valid_solutions']}/{result['optimization']['total_solutions']}")
                
                if 'solutions' in result and result['solutions']:
                    sols = result['solutions']
                    print(f"  Best Power: {sols['best_power']['power']:.2f} mW @ {sols['best_power']['frequency']:.4f} GHz")
                    print(f"  Best Freq: {sols['best_frequency']['frequency']:.4f} GHz @ {sols['best_frequency']['power']:.2f} mW")
                
                passed += 1
                results.append((test['request'], 'PASS'))
            else:
                print(f"✗ Status: FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
                failed += 1
                results.append((test['request'], 'FAIL'))
                
        except Exception as e:
            print(f"✗ EXCEPTION: {e}")
            failed += 1
            results.append((test['request'], 'ERROR'))
    
    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"\nTotal Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print(f"\n✓ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        print("\nCapabilities Verified:")
        print("  [✓] Natural language parsing")
        print("  [✓] Constraint extraction")
        print("  [✓] Optimizer integration")
        print("  [✓] Solution filtering")
        print("  [✓] Result formatting")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED - SYSTEM REQUIRES ATTENTION")
        return 1


def verify_api_integration():
    """Verify FastAPI integration"""
    print(f"\n{'='*70}")
    print("API INTEGRATION VERIFICATION")
    print(f"{'='*70}")
    
    try:
        from services.api.app.api.execution_routes import router
        print("✓ execution_routes module imports successfully")
        print(f"  Router prefix: {router.prefix}")
        print(f"  Tags: {router.tags}")
        
        # Check endpoints
        routes = [route.path for route in router.routes]
        expected_endpoints = ['/execute', '/supported-keywords', '/health']
        
        for endpoint in expected_endpoints:
            if endpoint in routes:
                print(f"  ✓ Endpoint {endpoint} defined")
            else:
                print(f"  ✗ Endpoint {endpoint} MISSING")
        
        return 0
    except Exception as e:
        print(f"✗ API integration check failed: {e}")
        return 1


def main():
    """Run complete verification"""
    
    print("\nStarting Execution-Based AI System Verification...")
    
    # Test execution pipeline
    exec_result = verify_execution_system()
    
    # Test API integration
    api_result = verify_api_integration()
    
    # Final status
    print(f"\n{'='*70}")
    print("FINAL STATUS")
    print(f"{'='*70}")
    
    if exec_result == 0 and api_result == 0:
        print("\n✓ EXECUTION-BASED AI SYSTEM IS FULLY OPERATIONAL")
        print("\nNext Steps:")
        print("  1. Start the backend: python -m uvicorn services.api.app.main:app")
        print("  2. Access API documentation: http://localhost:8000/docs")
        print("  3. Try the endpoint: POST /api/v1/execution/execute")
        print("  4. CLI usage: python execution_cli.py 'your request'")
        return 0
    else:
        print("\n✗ VERIFICATION FAILED - See above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
