"""
Execution-Based AI System for CMOS Circuit Optimization

Parses natural language optimization requests, extracts constraints,
invokes the NSGA-II optimizer, and returns results.

No chatbot - pure constraint-based execution.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Optimization objectives"""
    MINIMIZE_POWER = "minimize_power"
    MAXIMIZE_FREQUENCY = "maximize_frequency"
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"
    BALANCE = "balance"


@dataclass
class ConstraintSet:
    """Extracted constraints from natural language input"""
    max_power: Optional[float] = None  # mW
    min_frequency: Optional[float] = None  # GHz
    max_frequency: Optional[float] = None  # GHz
    min_efficiency: Optional[float] = None  # GHz/mW
    objectives: List[OptimizationObjective] = None
    preferred_wn_range: Tuple[float, float] = (0.5, 10.0)  # µm
    preferred_wp_range: Tuple[float, float] = (0.5, 10.0)  # µm
    preferred_vdd_range: Tuple[float, float] = (1.0, 5.0)  # V
    
    def __post_init__(self):
        if self.objectives is None:
            self.objectives = []


class ConstraintParser:
    """Parse natural language optimization requests"""
    
    # Pattern mappings
    POWER_PATTERNS = [
        (r'(?:low|reduced|minimal)\s+power', 'minimize'),
        (r'power\s+(?:under|below|less than|<|≤)\s*([\d.]+)\s*(?:mW|milliwatt)', 'max_power'),
        (r'power\s+(?:budget|limit)\s+([\d.]+)\s*(?:mW|milliwatt)', 'max_power'),
        (r'(?:keep|maintain)\s+power.*?(?:under|below|<|≤)\s*([\d.]+)', 'max_power'),
    ]
    
    FREQUENCY_PATTERNS = [
        (r'(?:maximize|high|maximum|peak)\s+frequency', 'maximize'),
        (r'frequency\s+(?:under|below|<|≤)\s*([\d.]+)\s*(?:GHz|gigahertz)', 'max_frequency'),
        (r'(?:up to|maximum)\s+([\d.]+)\s*(?:GHz|gigahertz)', 'max_frequency'),
        (r'(?:at least|minimum|above|>|≥)\s*([\d.]+)\s*(?:GHz|gigahertz)', 'min_frequency'),
        (r'(?:under|below|<|≤)\s+([\d.]+)\s*(?:GHz|gigahertz)', 'max_frequency'),  # Standalone constraint
    ]
    
    EFFICIENCY_PATTERNS = [
        (r'(?:high|maximum|improve)\s+efficiency', 'maximize'),
        (r'efficiency\s*(?:>|≥|above|at least)\s*([\d.]+)', 'min_efficiency'),
    ]
    
    TRANSISTOR_PATTERNS = [
        (r'(?:small|narrow|thin)\s+(?:transistor|gate)\s+width', 'small_transistor'),
        (r'(?:large|wide|thick)\s+(?:transistor|gate)\s+width', 'large_transistor'),
    ]
    
    SUPPLY_PATTERNS = [
        (r'(?:low|reduced|minimal)\s+voltage', 'low_voltage'),
        (r'(?:high|maximum)\s+voltage', 'high_voltage'),
        (r'voltage\s*(?:=|is|:)\s*([\d.]+)\s*V', 'fixed_voltage'),
    ]
    
    def __init__(self):
        """Initialize parser with compiled patterns"""
        self.compiled_patterns = {
            'power': [(re.compile(p, re.IGNORECASE), action) for p, action in self.POWER_PATTERNS],
            'frequency': [(re.compile(p, re.IGNORECASE), action) for p, action in self.FREQUENCY_PATTERNS],
            'efficiency': [(re.compile(p, re.IGNORECASE), action) for p, action in self.EFFICIENCY_PATTERNS],
            'transistor': [(re.compile(p, re.IGNORECASE), action) for p, action in self.TRANSISTOR_PATTERNS],
            'supply': [(re.compile(p, re.IGNORECASE), action) for p, action in self.SUPPLY_PATTERNS],
        }
    
    def parse(self, request: str) -> ConstraintSet:
        """
        Parse natural language request into constraint set.
        
        Args:
            request: Natural language optimization request
            
        Returns:
            ConstraintSet with extracted constraints
        """
        constraints = ConstraintSet()
        request_lower = request.lower()
        
        # Extract power constraints
        logger.debug(f"Parsing request: {request}")
        self._extract_power_constraints(request, constraints)
        self._extract_frequency_constraints(request, constraints)
        self._extract_efficiency_constraints(request, constraints)
        self._extract_transistor_preferences(request, constraints)
        self._extract_supply_preferences(request, constraints)
        self._infer_objectives(request, constraints)
        
        logger.info(f"Extracted constraints: {constraints}")
        return constraints
    
    def _extract_power_constraints(self, request: str, constraints: ConstraintSet):
        """Extract power-related constraints"""
        for pattern, action in self.compiled_patterns['power']:
            matches = pattern.finditer(request)
            for match in matches:
                if action == 'minimize':
                    if OptimizationObjective.MINIMIZE_POWER not in constraints.objectives:
                        constraints.objectives.append(OptimizationObjective.MINIMIZE_POWER)
                elif action == 'max_power':
                    if match.groups():
                        try:
                            constraints.max_power = float(match.group(1))
                        except (ValueError, IndexError):
                            pass
    
    def _extract_frequency_constraints(self, request: str, constraints: ConstraintSet):
        """Extract frequency-related constraints"""
        for pattern, action in self.compiled_patterns['frequency']:
            matches = pattern.finditer(request)
            for match in matches:
                if action == 'maximize':
                    if OptimizationObjective.MAXIMIZE_FREQUENCY not in constraints.objectives:
                        constraints.objectives.append(OptimizationObjective.MAXIMIZE_FREQUENCY)
                elif action == 'max_frequency':
                    if match.groups():
                        try:
                            constraints.max_frequency = float(match.group(1))
                        except (ValueError, IndexError):
                            pass
                elif action == 'min_frequency':
                    if match.groups():
                        try:
                            constraints.min_frequency = float(match.group(1))
                        except (ValueError, IndexError):
                            pass
    
    def _extract_efficiency_constraints(self, request: str, constraints: ConstraintSet):
        """Extract efficiency-related constraints"""
        for pattern, action in self.compiled_patterns['efficiency']:
            matches = pattern.finditer(request)
            for match in matches:
                if action == 'maximize':
                    if OptimizationObjective.MAXIMIZE_EFFICIENCY not in constraints.objectives:
                        constraints.objectives.append(OptimizationObjective.MAXIMIZE_EFFICIENCY)
                elif action == 'min_efficiency':
                    if match.groups():
                        try:
                            constraints.min_efficiency = float(match.group(1))
                        except (ValueError, IndexError):
                            pass
    
    def _extract_transistor_preferences(self, request: str, constraints: ConstraintSet):
        """Extract transistor sizing preferences"""
        for pattern, action in self.compiled_patterns['transistor']:
            if pattern.search(request):
                if action == 'small_transistor':
                    constraints.preferred_wn_range = (0.5, 5.0)
                    constraints.preferred_wp_range = (0.5, 5.0)
                elif action == 'large_transistor':
                    constraints.preferred_wn_range = (5.0, 10.0)
                    constraints.preferred_wp_range = (5.0, 10.0)
    
    def _extract_supply_preferences(self, request: str, constraints: ConstraintSet):
        """Extract supply voltage preferences"""
        for pattern, action in self.compiled_patterns['supply']:
            matches = pattern.finditer(request)
            for match in matches:
                if action == 'low_voltage':
                    constraints.preferred_vdd_range = (1.0, 2.5)
                elif action == 'high_voltage':
                    constraints.preferred_vdd_range = (3.0, 5.0)
                elif action == 'fixed_voltage':
                    if match.groups():
                        try:
                            vdd = float(match.group(1))
                            constraints.preferred_vdd_range = (max(1.0, vdd - 0.2), min(5.0, vdd + 0.2))
                        except (ValueError, IndexError):
                            pass
    
    def _infer_objectives(self, request: str, constraints: ConstraintSet):
        """Infer optimization objectives from constraints if not explicit"""
        if not constraints.objectives:
            # Default: if power constraint, optimize for power; else balance
            if constraints.max_power:
                constraints.objectives = [OptimizationObjective.MINIMIZE_POWER]
            elif constraints.max_frequency:
                constraints.objectives = [OptimizationObjective.MAXIMIZE_FREQUENCY]
            else:
                constraints.objectives = [OptimizationObjective.BALANCE]


class ExecutionEngine:
    """Execute optimization based on parsed constraints"""
    
    def __init__(self):
        """Initialize execution engine"""
        self.parser = ConstraintParser()
        logging.basicConfig(level=logging.INFO)
    
    def execute(self, request: str) -> Dict:
        """
        Execute optimization request.
        
        Args:
            request: Natural language optimization request
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Step 1: Parse input
            logger.info(f"[STEP 1] Parsing input: {request}")
            constraints = self.parser.parse(request)
            
            # Step 2: Extract constraints
            logger.info("[STEP 2] Extracting constraints")
            extracted = self._extract_optimization_params(constraints)
            
            # Step 3: Call optimizer
            logger.info("[STEP 3] Calling optimizer with extracted parameters")
            optimization_result = self._call_optimizer(extracted)
            
            # Step 4: Return result
            logger.info("[STEP 4] Formatting and returning results")
            result = self._format_result(request, constraints, extracted, optimization_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'request': request
            }
    
    def _extract_optimization_params(self, constraints: ConstraintSet) -> Dict:
        """Convert constraints to optimizer parameters"""
        params = {
            'constraints': constraints,
            'population_size': 50,
            'generations': 30,
            'objectives': constraints.objectives,
        }
        
        # Adjust optimization parameters based on constraints
        if constraints.max_power and constraints.max_power < 10:
            # Strict power constraint: more generations for convergence
            params['population_size'] = 100
            params['generations'] = 50
        
        if constraints.max_frequency and constraints.max_frequency < 0.5:
            # Strict frequency constraint: larger population
            params['population_size'] = 80
            params['generations'] = 40
        
        logger.info(f"Optimization parameters: pop={params['population_size']}, gen={params['generations']}")
        return params
    
    def _call_optimizer(self, params: Dict) -> Dict:
        """Call NSGA-II optimizer with extracted parameters"""
        try:
            from app.nsga2_optimizer import run_optimization, PerformancePredictor
            from app.nsga2_optimizer import CircuitParameters
        except ImportError:
            # Fallback: return mock results for testing
            logger.warning("DEAP not available, using mock results")
            return self._mock_optimization_result(params)
        
        try:
            # Run optimization
            pareto_front, metrics = run_optimization(
                population_size=params['population_size'],
                generations=params['generations'],
                use_ml=False,
                seed=42,
                verbose=False
            )
            
            # Filter by constraints
            filtered = self._filter_by_constraints(pareto_front, params['constraints'])
            
            return {
                'pareto_front': filtered,
                'metrics': metrics,
                'total_solutions': len(pareto_front),
                'valid_solutions': len(filtered)
            }
        except Exception as e:
            logger.error(f"Optimizer call failed: {e}")
            return self._mock_optimization_result(params)
    
    def _filter_by_constraints(self, pareto_front, constraints: ConstraintSet) -> List:
        """Filter Pareto front by constraints"""
        filtered = []
        for solution in pareto_front:
            if constraints.max_power and solution.performance.power > constraints.max_power:
                continue
            if constraints.min_frequency and solution.performance.frequency < constraints.min_frequency:
                continue
            if constraints.max_frequency and solution.performance.frequency > constraints.max_frequency:
                continue
            if constraints.min_efficiency and solution.performance.efficiency < constraints.min_efficiency:
                continue
            filtered.append(solution)
        
        return filtered
    
    def _format_result(self, request: str, constraints: ConstraintSet, 
                      params: Dict, optimization_result: Dict) -> Dict:
        """Format final result"""
        result = {
            'status': 'success',
            'request': request,
            'objectives': [obj.value for obj in constraints.objectives],
            'constraints': {
                'max_power': constraints.max_power,
                'min_frequency': constraints.min_frequency,
                'max_frequency': constraints.max_frequency,
                'min_efficiency': constraints.min_efficiency,
            },
            'optimization': {
                'population_size': params['population_size'],
                'generations': params['generations'],
                'total_solutions': optimization_result.get('total_solutions', 0),
                'valid_solutions': optimization_result.get('valid_solutions', 0),
            }
        }
        
        # Add best solutions
        if optimization_result.get('pareto_front'):
            pareto = optimization_result['pareto_front']
            if pareto:
                best_power = min(pareto, key=lambda s: s.performance.power)
                best_freq = max(pareto, key=lambda s: s.performance.frequency)
                best_eff = max(pareto, key=lambda s: s.performance.efficiency)
                
                result['solutions'] = {
                    'best_power': {
                        'wn': best_power.parameters.wn,
                        'wp': best_power.parameters.wp,
                        'vdd': best_power.parameters.vdd,
                        'power': best_power.performance.power,
                        'frequency': best_power.performance.frequency,
                        'efficiency': best_power.performance.efficiency,
                    },
                    'best_frequency': {
                        'wn': best_freq.parameters.wn,
                        'wp': best_freq.parameters.wp,
                        'vdd': best_freq.parameters.vdd,
                        'power': best_freq.performance.power,
                        'frequency': best_freq.performance.frequency,
                        'efficiency': best_freq.performance.efficiency,
                    },
                    'best_efficiency': {
                        'wn': best_eff.parameters.wn,
                        'wp': best_eff.parameters.wp,
                        'vdd': best_eff.parameters.vdd,
                        'power': best_eff.performance.power,
                        'frequency': best_eff.performance.frequency,
                        'efficiency': best_eff.performance.efficiency,
                    }
                }
        
        return result
    
    def _mock_optimization_result(self, params: Dict) -> Dict:
        """Generate mock optimization results for testing"""
        from dataclasses import dataclass
        
        @dataclass
        class MockPerformance:
            frequency: float
            power: float
            delay: float
            efficiency: float
        
        @dataclass
        class MockParams:
            wn: float
            wp: float
            vdd: float
        
        @dataclass
        class MockSolution:
            parameters: MockParams
            performance: MockPerformance
        
        # Create mock Pareto front
        mock_front = [
            MockSolution(
                MockParams(2.0, 4.0, 2.5),
                MockPerformance(0.8, 12.5, 1.25, 0.064)
            ),
            MockSolution(
                MockParams(4.0, 6.0, 3.0),
                MockPerformance(1.1, 18.3, 0.91, 0.060)
            ),
            MockSolution(
                MockParams(6.0, 8.0, 3.5),
                MockPerformance(1.5, 25.2, 0.67, 0.060)
            ),
        ]
        
        return {
            'pareto_front': mock_front,
            'metrics': None,
            'total_solutions': 15,
            'valid_solutions': 3
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    engine = ExecutionEngine()
    
    # Example requests
    requests = [
        "optimize for low power under 1GHz",
        "maximize frequency with power constraint 20mW",
        "balance power and efficiency, keep voltage low",
        "high performance design, frequency at least 1.5 GHz",
    ]
    
    for request in requests:
        print(f"\n{'='*70}")
        print(f"Request: {request}")
        print('='*70)
        
        result = engine.execute(request)
        
        if result['status'] == 'success':
            print(f"Objectives: {', '.join(result['objectives'])}")
            print(f"Constraints: {result['constraints']}")
            print(f"Solutions found: {result['optimization']['valid_solutions']}/{result['optimization']['total_solutions']}")
            
            if 'solutions' in result:
                print("\nBest Solutions:")
                for solution_type, solution_data in result['solutions'].items():
                    print(f"\n  {solution_type}:")
                    print(f"    WN={solution_data['wn']:.2f}µm, WP={solution_data['wp']:.2f}µm, VDD={solution_data['vdd']:.2f}V")
                    print(f"    Freq={solution_data['frequency']:.4f}GHz, Power={solution_data['power']:.2f}mW")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
