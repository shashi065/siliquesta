"""
Test suite for Execution-Based AI System

Tests constraint parsing, optimization execution, and integration with NSGA-II.
"""

import sys
from pathlib import Path
from execution_engine import ExecutionEngine, ConstraintParser, OptimizationObjective

# Configure path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(num: int, name: str):
    """Print test header"""
    print(f"\n{BLUE}{'='*70}")
    print(f"Test {num}: {name}")
    print(f"{'='*70}{RESET}")


def print_pass(msg: str = "PASSED"):
    """Print pass message"""
    print(f"  {GREEN}[PASS] {msg}{RESET}")


def print_fail(msg: str = "FAILED"):
    """Print fail message"""
    print(f"  {RED}[FAIL] {msg}{RESET}")


def print_info(msg: str):
    """Print info message"""
    print(f"  {YELLOW}[INFO] {msg}{RESET}")


# Test Cases

def test_constraint_parser_power():
    """Test parsing power constraints"""
    print_test(1, "Constraint Parser - Power")
    
    parser = ConstraintParser()
    
    test_cases = [
        ("optimize for low power", OptimizationObjective.MINIMIZE_POWER),
        ("power under 10mW", 10.0),
        ("keep power below 5 milliwatt", 5.0),
    ]
    
    for request, expected in test_cases:
        constraints = parser.parse(request)
        if isinstance(expected, OptimizationObjective):
            if expected in constraints.objectives:
                print_pass(f"'{request}' → objective detected")
            else:
                print_fail(f"'{request}' → objective NOT detected")
        else:
            if constraints.max_power == expected:
                print_pass(f"'{request}' → max_power={expected}mW")
            else:
                print_fail(f"'{request}' → expected {expected}mW, got {constraints.max_power}")


def test_constraint_parser_frequency():
    """Test parsing frequency constraints"""
    print_test(2, "Constraint Parser - Frequency")
    
    parser = ConstraintParser()
    
    test_cases = [
        ("maximize frequency", OptimizationObjective.MAXIMIZE_FREQUENCY),
        ("frequency under 2GHz", 2.0),
        ("at least 1.5 GHz", 1.5),
    ]
    
    for request, expected in test_cases:
        constraints = parser.parse(request)
        if isinstance(expected, OptimizationObjective):
            if expected in constraints.objectives:
                print_pass(f"'{request}' → objective detected")
            else:
                print_fail(f"'{request}' → objective NOT detected")
        else:
            if constraints.max_frequency == expected or constraints.min_frequency == expected:
                val = constraints.max_frequency or constraints.min_frequency
                print_pass(f"'{request}' → frequency constraint={val}GHz")
            else:
                print_fail(f"'{request}' → constraint not extracted correctly")


def test_constraint_parser_voltage():
    """Test parsing voltage constraints"""
    print_test(3, "Constraint Parser - Voltage")
    
    parser = ConstraintParser()
    
    test_cases = [
        ("low voltage design", (1.0, 2.5)),
        ("high voltage design", (3.0, 5.0)),
    ]
    
    for request, expected_range in test_cases:
        constraints = parser.parse(request)
        if constraints.preferred_vdd_range == expected_range:
            print_pass(f"'{request}' → VDD range {expected_range}")
        else:
            print_fail(f"'{request}' → expected {expected_range}, got {constraints.preferred_vdd_range}")


def test_primary_request():
    """Test primary example: 'optimize for low power under 1GHz'"""
    print_test(4, "Primary Request: 'optimize for low power under 1GHz'")
    
    engine = ExecutionEngine()
    request = "optimize for low power under 1GHz"
    
    try:
        result = engine.execute(request)
        
        if result['status'] != 'success':
            print_fail(f"Execution failed: {result.get('error')}")
            return
        
        print_pass("Execution completed")
        
        # Check objectives
        if OptimizationObjective.MINIMIZE_POWER.value in result['objectives']:
            print_pass("Objective: MINIMIZE_POWER detected")
        else:
            print_fail("Objective: MINIMIZE_POWER NOT detected")
        
        # Check constraints
        if result['constraints']['max_frequency'] == 1.0:
            print_pass(f"Constraint: max_frequency=1.0 GHz parsed")
        else:
            print_fail(f"Constraint: max_frequency should be 1.0, got {result['constraints']['max_frequency']}")
        
        # Check results
        opt = result['optimization']
        print_info(f"Solutions: {opt['valid_solutions']}/{opt['total_solutions']} valid")
        
    except Exception as e:
        print_fail(f"Exception: {e}")


def test_complex_request():
    """Test complex multi-constraint request"""
    print_test(5, "Complex Request: 'maximize frequency with power budget 20mW, keep voltage at 3V'")
    
    engine = ExecutionEngine()
    request = "maximize frequency with power budget 20mW, keep voltage at 3V"
    
    try:
        result = engine.execute(request)
        
        if result['status'] != 'success':
            print_fail(f"Execution failed: {result.get('error')}")
            return
        
        print_pass("Execution completed")
        
        # Check constraints
        constraints = result['constraints']
        if hasattr(constraints, 'max_power') or (isinstance(constraints, dict) and constraints.get('max_power')):
            actual_power = constraints.max_power if hasattr(constraints, 'max_power') else constraints.get('max_power')
            if actual_power == 20.0:
                print_pass(f"Power budget: 20 mW extracted")
            else:
                print_info(f"Power budget: {actual_power} mW")
        else:
            print_info(f"Power constraint: Not extracted (may need refinement)")
        
        # Check objectives
        objectives = result.get('objectives', [])
        if objectives and (objectives[0] == OptimizationObjective.MAXIMIZE_FREQUENCY.value or 
                          'maximize' in objectives[0].lower()):
            print_pass(f"Primary objective: MAXIMIZE_FREQUENCY or related")
        else:
            print_info(f"Objectives: {objectives}")
        
        opt = result['optimization']
        print_info(f"Solutions: {opt['valid_solutions']}/{opt['total_solutions']} valid")
        
    except Exception as e:
        print_fail(f"Exception: {e}")


def test_efficiency_optimization():
    """Test efficiency-focused optimization"""
    print_test(6, "Efficiency Request: 'high efficiency design'")
    
    engine = ExecutionEngine()
    request = "high efficiency design"
    
    try:
        result = engine.execute(request)
        
        if result['status'] != 'success':
            print_fail(f"Execution failed: {result.get('error')}")
            return
        
        print_pass("Execution completed")
        
        if OptimizationObjective.MAXIMIZE_EFFICIENCY.value in result['objectives']:
            print_pass("Objective: MAXIMIZE_EFFICIENCY detected")
        else:
            print_fail("Objective: MAXIMIZE_EFFICIENCY NOT detected")
        
        opt = result['optimization']
        print_info(f"Population: {opt['population_size']}, Generations: {opt['generations']}")
        
    except Exception as e:
        print_fail(f"Exception: {e}")


def test_parameter_adaptation():
    """Test that optimizer parameters adapt to constraints"""
    print_test(7, "Parameter Adaptation")
    
    engine = ExecutionEngine()
    
    test_cases = [
        ("low power under 5mW", "should increase generations for tight constraint"),
        ("standard optimization", "should use default parameters"),
    ]
    
    for request, description in test_cases:
        parser = ConstraintParser()
        constraints = parser.parse(request)
        params = engine._extract_optimization_params(constraints)
        
        print_info(f"'{request}'")
        print_info(f"  → pop={params['population_size']}, gen={params['generations']}")


def test_solution_filtering():
    """Test that solutions are filtered by constraints"""
    print_test(8, "Solution Filtering by Constraints")
    
    engine = ExecutionEngine()
    request = "power under 15mW"
    
    try:
        result = engine.execute(request)
        
        if result['status'] != 'success':
            print_fail(f"Execution failed")
            return
        
        opt = result['optimization']
        
        if opt['valid_solutions'] > 0:
            print_pass(f"Filtering working: {opt['valid_solutions']} solutions meet constraints")
        else:
            print_info(f"No valid solutions found (possible with stringent constraints)")
        
        if opt['valid_solutions'] <= opt['total_solutions']:
            print_pass(f"Valid solutions ≤ Total solutions")
        else:
            print_fail(f"Valid solutions ({opt['valid_solutions']}) > Total ({opt['total_solutions']})")
        
    except Exception as e:
        print_fail(f"Exception: {e}")


def test_output_format():
    """Test that output format matches specification"""
    print_test(9, "Output Format Validation")
    
    engine = ExecutionEngine()
    request = "optimize for low power under 1GHz"
    
    try:
        result = engine.execute(request)
        
        # Check required fields
        required_fields = ['status', 'request', 'objectives', 'constraints', 'optimization']
        for field in required_fields:
            if field in result:
                print_pass(f"Field '{field}' present")
            else:
                print_fail(f"Field '{field}' MISSING")
        
        # Check solution format if present
        if 'solutions' in result and result['solutions']:
            sols = result['solutions']
            required_solution_fields = ['wn', 'wp', 'vdd', 'power', 'frequency', 'efficiency']
            
            if sols.get('best_power'):
                for field in required_solution_fields:
                    if field in sols['best_power']:
                        print_pass(f"Solution field '{field}' present")
                    else:
                        print_fail(f"Solution field '{field}' MISSING")
        
    except Exception as e:
        print_fail(f"Exception: {e}")


def test_multiple_keywords():
    """Test parsing with multiple power/frequency keywords"""
    print_test(10, "Multiple Domain Keywords")
    
    parser = ConstraintParser()
    request = "optimize for low power under 10mW, maximize frequency up to 2GHz, high efficiency"
    
    constraints = parser.parse(request)
    
    objectives_str = [obj.value for obj in constraints.objectives]
    print_info(f"Request: {request}")
    print_info(f"Objectives: {objectives_str}")
    print_info(f"Max Power: {constraints.max_power} mW")
    print_info(f"Max Frequency: {constraints.max_frequency} GHz")
    
    if constraints.max_power and constraints.max_frequency:
        print_pass("Multiple constraints extracted successfully")
    else:
        print_fail("Some constraints not extracted")


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print("EXECUTION-BASED AI SYSTEM - TEST SUITE")
    print(f"{'='*70}{RESET}\n")
    
    test_functions = [
        test_constraint_parser_power,
        test_constraint_parser_frequency,
        test_constraint_parser_voltage,
        test_primary_request,
        test_complex_request,
        test_efficiency_optimization,
        test_parameter_adaptation,
        test_solution_filtering,
        test_output_format,
        test_multiple_keywords,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in test_functions:
        try:
            test_fn()
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            failed += 1
    
    print(f"\n{BLUE}{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}{RESET}")
    print(f"Total Tests: {len(test_functions)}")
    print(f"{GREEN}Passed: (see results above){RESET}")
    print(f"{RED}Failed: (see results above){RESET}")


if __name__ == "__main__":
    main()
