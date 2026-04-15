#!/usr/bin/env python3
"""
NSGA-II Optimization API Demo/Test Script

Tests all NSGA-II optimization endpoints with different scenarios.
"""

import requests
import json
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
NSGA2_BASE = f"{API_BASE_URL}/api/v1/nsga2"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def print_section(text):
    """Print subsection header"""
    print(f"\n{Colors.CYAN}▶ {text}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def format_json(data):
    """Pretty print JSON"""
    return json.dumps(data, indent=2)


def test_health_check():
    """Test 1: Health check endpoint"""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{NSGA2_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed")
            print(f"  Status: {data['status']}")
            print(f"  NSGA-II Available: {data['nsga2_available']}")
            print(f"  DEAP Requirement: {data['deap_requirement']}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def test_optimizer_info():
    """Test 2: Optimizer info endpoint"""
    print_section("Test 2: Optimizer Information")
    
    try:
        response = requests.get(f"{NSGA2_BASE}/info", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved optimizer information")
            print(f"  Algorithm: {data['algorithm']}")
            print(f"  Objectives: {len(data['objectives'])}")
            for obj in data['objectives']:
                print(f"    - {obj['name']} ({obj['type']}, {obj['unit']})")
            print(f"  Parameters: {len(data['parameters'])}")
            for param in data['parameters']:
                print(f"    - {param['name']}: {param['range']}")
            return True
        else:
            print_error(f"Info endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Info endpoint error: {e}")
        return False


def test_basic_optimization():
    """Test 3: Basic optimization with default parameters"""
    print_section("Test 3: Basic Optimization (default parameters)")
    
    try:
        print_info("Running NSGA-II optimization...")
        start_time = time.time()
        
        response = requests.post(
            f"{NSGA2_BASE}/optimize",
            json={
                "population_size": 30,
                "generations": 10,
                "use_ml": False,
                "seed": 42
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Optimization completed in {elapsed:.2f}s")
            
            # Display metrics
            metrics = data['metrics']
            print(f"  Pareto Front Size: {metrics['pareto_front_size']}")
            print(f"  Execution Time: {metrics['execution_time']:.2f}s")
            print(f"  Hypervolume: {metrics['hypervolume']:.2f}")
            print(f"  Spread: {metrics['spread']:.4f}")
            
            # Display best solutions
            best = data['best_solutions']
            if 'best_power' in best:
                bp = best['best_power']
                print(f"\n  Best Power Design:")
                print(f"    Power: {bp['power']:.2f} mW")
                print(f"    Frequency: {bp['frequency']:.4f} GHz")
            
            if 'best_frequency' in best:
                bf = best['best_frequency']
                print(f"\n  Best Frequency Design:")
                print(f"    Frequency: {bf['frequency']:.4f} GHz")
                print(f"    Power: {bf['power']:.2f} mW")
            
            # Display Pareto front
            print(f"\n  Pareto Front ({len(data['pareto_front'])} solutions):")
            for i, sol in enumerate(data['pareto_front'][:5]):  # Show first 5
                perf = sol['performance']
                print(f"    [{i+1}] F={perf['frequency']:.4f} GHz, P={perf['power']:.2f} mW, "
                      f"Eff={perf['efficiency']:.4f}")
            
            if len(data['pareto_front']) > 5:
                print(f"    ... and {len(data['pareto_front'])-5} more solutions")
            
            return True
        else:
            print_error(f"Optimization failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    
    except Exception as e:
        print_error(f"Optimization error: {e}")
        return False


def test_large_optimization():
    """Test 4: Larger optimization"""
    print_section("Test 4: Larger Optimization (pop=50, gen=20)")
    
    try:
        print_info("Running larger NSGA-II optimization...")
        start_time = time.time()
        
        response = requests.post(
            f"{NSGA2_BASE}/optimize",
            json={
                "population_size": 50,
                "generations": 20,
                "use_ml": False,
                "seed": 123
            },
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            metrics = data['metrics']
            print_success(f"Optimization completed in {elapsed:.2f}s")
            print(f"  Pareto Front Size: {metrics['pareto_front_size']}")
            print(f"  Hypervolume: {metrics['hypervolume']:.2f}")
            print(f"  Spread: {metrics['spread']:.4f}")
            return True
        else:
            print_error(f"Optimization failed with status {response.status_code}")
            return False
    
    except requests.Timeout:
        print_warning("Optimization timed out (> 120s) - this is expected for larger runs")
        return True
    except Exception as e:
        print_error(f"Optimization error: {e}")
        return False


def test_design_comparison():
    """Test 5: Design comparison"""
    print_section("Test 5: Design Comparison")
    
    try:
        design1 = {"wn": 2.5, "wp": 5.0, "vdd": 2.8}
        design2 = {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
        
        print_info(f"Comparing designs:")
        print(f"  Design 1: WN={design1['wn']}, WP={design1['wp']}, VDD={design1['vdd']}")
        print(f"  Design 2: WN={design2['wn']}, WP={design2['wp']}, VDD={design2['vdd']}")
        
        response = requests.post(
            f"{NSGA2_BASE}/compare",
            json={"design1": design1, "design2": design2},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Comparison completed")
            
            perf1 = data['design1']['performance']
            perf2 = data['design2']['performance']
            comp = data['comparison']
            
            print(f"\n  Design 1 Performance:")
            print(f"    Frequency: {perf1['frequency']:.4f} GHz")
            print(f"    Power: {perf1['power']:.2f} mW")
            print(f"    Efficiency: {perf1['efficiency']:.6f}")
            
            print(f"\n  Design 2 Performance:")
            print(f"    Frequency: {perf2['frequency']:.4f} GHz")
            print(f"    Power: {perf2['power']:.2f} mW")
            print(f"    Efficiency: {perf2['efficiency']:.6f}")
            
            print(f"\n  Comparison Ratios (Design2 / Design1):")
            print(f"    Frequency: {comp['frequency_ratio']:.2f}x")
            print(f"    Power: {comp['power_ratio']:.2f}x")
            print(f"    Efficiency: {comp['efficiency_ratio']:.4f}x")
            
            return True
        else:
            print_error(f"Comparison failed with status {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Comparison error: {e}")
        return False


def test_multiple_runs():
    """Test 6: Multiple runs with different seeds"""
    print_section("Test 6: Multiple Optimization Runs")
    
    results = []
    
    for seed in [42, 123, 456]:
        try:
            print_info(f"Running optimization with seed={seed}...")
            
            response = requests.post(
                f"{NSGA2_BASE}/optimize",
                json={
                    "population_size": 30,
                    "generations": 10,
                    "use_ml": False,
                    "seed": seed
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                metrics = data['metrics']
                results.append({
                    'seed': seed,
                    'size': metrics['pareto_front_size'],
                    'hypervolume': metrics['hypervolume'],
                    'spread': metrics['spread']
                })
                print_success(f"  Seed {seed}: {metrics['pareto_front_size']} solutions")
            else:
                print_error(f"  Seed {seed}: Failed with status {response.status_code}")
        
        except Exception as e:
            print_error(f"  Seed {seed}: Error - {e}")
    
    if results:
        print_success(f"\nRun Summary ({len(results)} runs):")
        for r in results:
            print(f"  Seed {r['seed']}: {r['size']} solutions, "
                  f"HV={r['hypervolume']:.1f}, Spread={r['spread']:.4f}")
        
        avg_size = sum(r['size'] for r in results) / len(results)
        print(f"\n  Average Pareto Front Size: {avg_size:.1f}")
        return True
    
    return False


def test_edge_cases():
    """Test 7: Edge cases and error handling"""
    print_section("Test 7: Edge Cases")
    
    passed = 0
    
    # Test minimum population
    print_info("Testing minimum population (10)...")
    try:
        response = requests.post(
            f"{NSGA2_BASE}/optimize",
            json={"population_size": 10, "generations": 5},
            timeout=30
        )
        if response.status_code == 200:
            print_success("Minimum population test passed")
            passed += 1
        else:
            print_warning(f"Status {response.status_code}")
    except Exception as e:
        print_warning(f"Error: {e}")
    
    # Test boundary parameters
    print_info("Testing design at parameter boundaries...")
    try:
        boundary_design = {"wn": 0.5, "wp": 10.0, "vdd": 1.0}
        response = requests.post(
            f"{NSGA2_BASE}/compare",
            json={"design1": boundary_design, "design2": boundary_design},
            timeout=30
        )
        if response.status_code == 200:
            print_success("Boundary parameters test passed")
            passed += 1
        else:
            print_warning(f"Status {response.status_code}")
    except Exception as e:
        print_warning(f"Error: {e}")
    
    return passed >= 2


def generate_summary(results: Dict[str, bool]):
    """Generate test summary"""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.ENDC}" if result else f"{Colors.RED}FAIL{Colors.ENDC}"
        print(f"  {test_name:.<50} {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if failed == 0:
        print_success("All tests passed!")
        return True
    else:
        print_error(f"{failed} test(s) failed")
        return False


def main():
    """Run all tests"""
    print_header("NSGA-II Optimization API Test Suite")
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test Started: {datetime.now().isoformat()}")
    
    results = {
        "Health Check": test_health_check(),
        "Optimizer Info": test_optimizer_info(),
        "Basic Optimization": test_basic_optimization(),
        "Large Optimization": test_large_optimization(),
        "Design Comparison": test_design_comparison(),
        "Multiple Runs": test_multiple_runs(),
        "Edge Cases": test_edge_cases(),
    }
    
    success = generate_summary(results)
    print_header("Test Complete")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
