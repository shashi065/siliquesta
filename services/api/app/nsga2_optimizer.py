"""
NSGA-II Multi-Objective Optimizer for CMOS Circuit Optimization

Full NSGA-II Implementation with Constraint Support

Optimizes CMOS circuit parameters to:
- Minimize: Power consumption
- Maximize: Operating frequency

Constraints:
- Minimum acceptable frequency: freq >= freq_min
- Maximum power budget: power <= power_max

Uses DEAP's implementation of NSGA-II (Non-dominated Sorting Genetic Algorithm II)

Inputs:
- WN: NMOS transistor width (µm)
- WP: PMOS transistor width (µm)
- VDD: Supply voltage (V)

Outputs:
- Pareto front with optimal trade-offs
- Format: [{"wn": float, "wp": float, "vdd": float, "power": float, "frequency": float, "delay": float}, ...]
- Reproducible results with fixed random seed
"""

from typing import Dict, List, Tuple, Optional, NamedTuple
import numpy as np
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)

# Try DEAP import
try:
    from deap import base, creator, tools, algorithms
    DEAP_AVAILABLE = True
except ImportError:
    DEAP_AVAILABLE = False
    logger.warning("DEAP not installed. Install with: pip install deap")


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class CircuitParameters:
    """CMOS circuit design parameters."""
    wn: float  # NMOS width (µm)
    wp: float  # PMOS width (µm)
    vdd: float  # Supply voltage (V)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.wn, self.wp, self.vdd])
    
    @classmethod
    def from_array(cls, arr: np.ndarray) -> "CircuitParameters":
        """Create from numpy array."""
        return cls(float(arr[0]), float(arr[1]), float(arr[2]))


@dataclass
class CircuitPerformance:
    """CMOS circuit performance metrics."""
    frequency: float  # GHz
    power: float  # mW
    delay: float  # ns
    efficiency: float  # GHz/mW
    
    def __repr__(self):
        return (f"Performance(f={self.frequency:.2f}GHz, "
                f"P={self.power:.2f}mW, D={self.delay:.2f}ns, "
                f"η={self.efficiency:.2f}GHz/mW)")


class ParetoSolution(NamedTuple):
    """A solution on the Pareto front."""
    parameters: CircuitParameters
    performance: CircuitPerformance
    fitness: Tuple[float, float]  # (power, -frequency) for NSGA-II
    rank: int = 1


@dataclass
class OptimizationMetrics:
    """Metrics from optimization run."""
    generations: int
    population_size: int
    execution_time: float
    pareto_front_size: int
    hypervolume: float
    spread: float
    convergence: List[float]
    timestamp: str


# ============================================================================
# Performance Predictor (using ML model or equations)
# ============================================================================


class PerformancePredictor:
    """Predict circuit performance from parameters."""
    
    def __init__(self, use_ml: bool = False):
        """
        Initialize predictor.
        
        Args:
            use_ml: Use ML model if available, otherwise use equations
        """
        self.use_ml = use_ml
        self.ml_model = None
        
        if use_ml:
            try:
                from app.ml_prediction_model import XGBoostCMOSPredictor
                self.ml_model = XGBoostCMOSPredictor()
                try:
                    self.ml_model.load("cmos_predictor_v1")
                    logger.info("Loaded ML model for performance prediction")
                except FileNotFoundError:
                    logger.warning("ML model not found, using equations")
                    self.ml_model = None
            except ImportError:
                logger.warning("ML model not available, using equations")
    
    def predict(self, params: CircuitParameters) -> CircuitPerformance:
        """
        Predict circuit performance.
        
        Args:
            params: Circuit parameters
            
        Returns:
            Predicted performance
        """
        if self.ml_model is not None:
            # Use ML model - map WN, WP, VDD to C, Id, VDD for ML model
            # This is a simplified mapping; actual mapping would depend on circuit
            c_fF = (params.wn + params.wp) * 0.5  # Approximate capacitance in fF
            id_mA = params.vdd * 2.0  # Approximate drain current
            
            predictions = self.ml_model.predict(
                C=c_fF * 1e-15,  # Convert fF to F
                Id=id_mA * 1e-3,  # Convert mA to A
                VDD=params.vdd
            )
            
            frequency = predictions["frequency"].predicted_value
            power = predictions["power"].predicted_value
            delay = predictions["delay"].predicted_value
        else:
            # Use simplified CMOS equations
            frequency, power, delay = self._predict_with_equations(params)
        
        efficiency = frequency / power if power > 0 else 0
        
        return CircuitPerformance(
            frequency=float(frequency),
            power=float(power),
            delay=float(delay),
            efficiency=float(efficiency)
        )
    
    @staticmethod
    def _predict_with_equations(params: CircuitParameters) -> Tuple[float, float, float]:
        """
        Predict performance using simplified CMOS equations.
        
        Deterministic predictions based on:
        - Delay: t_d = (C·VDD) / (2·I_d)
        - Frequency: f = 1 / (2·t_d)  [assuming 2-phase logic]
        - Power: P = C·VDD²·f + I_leak·VDD
        
        Parameters:
            - Minimum transistor width: 0.5 µm
            - Load capacitance proportional to (WN + WP)
            - Drain current proportional to W/L ratio and (VDD - VT)
            - Leakage proportional to W and VDD
        
        Args:
            params: Circuit parameters (wn, wp, vdd)
            
        Returns:
            Tuple of (frequency_GHz, power_mW, delay_ns) - DETERMINISTIC
        """
        # Gate length (minimum feature size in µm, 7nm ≈ 0.007µm, but for this level assume ~0.1µm)
        L = 0.1
        
        # Threshold voltage (typical for modern CMOS)
        VT = 0.4
        
        # Load capacitance (proportional to transistor width) - in pF
        # Typical: 1 pF per µm of width at 7nm node
        c_load = (params.wn + params.wp) * 0.05  # pF (scaled for simulation)
        
        # Effective capacitance including interconnect
        c_total = c_load + 0.1  # Add 0.1 pF for interconnect parasities
        
        # transconductance parameter (µn·Cox) - typical ~100 µA/V² for modern CMOS
        kn = 100.0  # µA/V²
        
        # Drain current magnitude (related to (WN/L) × (VDD - VT)²)
        # I_d ∝ (W/L) × (VDD - VT)²
        eff_width = params.wn + params.wp  # Effective width
        overdrive = max(params.vdd - VT, 0.1)  # VDD - VT, minimum 0.1V
        
        # Steady-state drain current (mA) - using simplified saturation equation
        i_drain = kn * (eff_width / L) * (overdrive ** 2) / 1000.0  # Convert to mA
        i_drain = max(i_drain, 0.1)  # Minimum current to avoid division by zero
        
        # Propagation delay (ns)
        # Using simplified inverter delay model
        delay_ns = (c_total * params.vdd) / (2.0 * i_drain)
        
        # Operating frequency (GHz) - based on maximum clock frequency
        # Assuming 2 stages for worst-case delay contribution
        max_frequency_ghz = 1.0 / (2.0 * delay_ns * 1e-9)
        max_frequency_ghz = min(max_frequency_ghz, 15.0)  # Cap at 15 GHz for physical realism
        max_frequency_ghz = max(max_frequency_ghz, 0.1)
        
        # Dynamic power (mW): P_d = α·C·VDD²·f
        # α = switching activity factor (assume 0.3 for typical workload)
        alpha = 0.3
        p_dynamic = alpha * c_total * (params.vdd ** 2) * max_frequency_ghz
        
        # Leakage power (mW): P_leak = I_leak·VDD
        # Leakage current scales with (WN + WP) and exponentially with VDD
        # I_leak ≈ 0.001 µA per µm at nominal VDD
        i_leak_ua = (params.wn + params.wp) * 0.001 * np.exp((params.vdd - 1.2) / 0.1)
        p_leak = i_leak_ua * params.vdd / 1000.0  # Convert µA to mA
        
        total_power = p_dynamic + p_leak
        total_power = max(total_power, 0.01)  # Minimum 0.01 mW
        
        # Return clean, deterministic values (NO noise added)
        return float(max_frequency_ghz), float(total_power), float(delay_ns)


# ============================================================================
# NSGA-II Optimizer
# ============================================================================


class NSGAII_Optimizer:
    """
    NSGA-II Multi-Objective Optimizer for CMOS circuits.
    
    Objectives:
    - Minimize: Power consumption
    - Maximize: Operating frequency (equivalent to minimize -frequency)
    
    Constraints:
    - Frequency >= freq_min (GHz)
    - Power <= power_max (mW)
    
    Parameter Bounds:
    - WN: 0.5 - 10 µm
    - WP: 0.5 - 10 µm
    - VDD: 1.0 - 5.0 V
    """
    
    def __init__(
        self,
        use_ml: bool = False,
        random_seed: int = 42,
        freq_min: float = 0.0,
        power_max: float = 1000.0
    ):
        """
        Initialize optimizer with full NSGA-II support.
        
        Args:
            use_ml: Use ML model for performance prediction
            random_seed: Random seed for reproducibility (CRITICAL)
            freq_min: Minimum frequency constraint (GHz). Default: 0.0 (unconstrained)
            power_max: Maximum power constraint (mW). Default: 1000.0 (unconstrained)
        """
        if not DEAP_AVAILABLE:
            raise RuntimeError("DEAP not installed. Install with: pip install deap")
        
        # Set random seeds for full reproducibility - CRITICAL for reproducible results
        self.random_seed = random_seed
        import random
        random.seed(random_seed)  # Python's built-in random
        np.random.seed(random_seed)  # NumPy random
        
        # Constraint parameters
        self.freq_min = freq_min
        self.power_max = power_max
        
        self.predictor = PerformancePredictor(use_ml=use_ml)
        self.setup_deap()
        
        self.pareto_front: List[ParetoSolution] = []
        self.population = None
        self.metrics: Optional[OptimizationMetrics] = None
        
        logger.info(f"NSGA-II Optimizer initialized (seed={random_seed}, "
                   f"freq_min={freq_min}GHz, power_max={power_max}mW)")
    
    def setup_deap(self):
        """Setup DEAP framework."""
        # Create fitness class (minimize power, maximize frequency)
        if hasattr(creator, "FitnessMulti"):
            del creator.FitnessMulti
        if hasattr(creator, "Individual"):
            del creator.Individual
        
        creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))
        creator.create("Individual", list, fitness=creator.FitnessMulti)
        
        self.toolbox = base.Toolbox()
        
        # Attribute generators
        self.toolbox.register("wn", np.random.uniform, 0.5, 10.0)
        self.toolbox.register("wp", np.random.uniform, 0.5, 10.0)
        self.toolbox.register("vdd", np.random.uniform, 1.0, 5.0)
        
        # Structure initializers
        self.toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            (self.toolbox.wn, self.toolbox.wp, self.toolbox.vdd),
            n=1
        )
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Genetic operators
        self.toolbox.register("evaluate", self.evaluate)
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.3)
        self.toolbox.register("select", tools.selNSGA2)
        
        # Bounds enforcement
        self.toolbox.decorate("mate", self.check_bounds)
        self.toolbox.decorate("mutate", self.check_bounds)
    
    def check_bounds(self, func):
        """Decorator to enforce parameter bounds."""
        def wrapper(*args, **kwargs):
            offspring = func(*args, **kwargs)
            for child in offspring:
                child[0] = np.clip(child[0], 0.5, 10.0)  # WN
                child[1] = np.clip(child[1], 0.5, 10.0)  # WP
                child[2] = np.clip(child[2], 1.0, 5.0)   # VDD
            return offspring
        return wrapper
    
    def evaluate(self, individual: List) -> Tuple[float, float]:
        """
        Evaluate fitness with constraint handling.
        
        Uses constraint penalty method:
        - If constraints violated, return large penalty values
        - If constraints satisfied, return actual objectives
        
        Args:
            individual: [WN, WP, VDD]
            
        Returns:
            Tuple of (power_fitness, frequency_fitness)
            - power_fitness: minimize (lower is better)
            - frequency_fitness: maximize (but returned as negative for minimization)
        """
        params = CircuitParameters(wn=individual[0], wp=individual[1], vdd=individual[2])
        perf = self.predictor.predict(params)
        
        # Check constraints
        freq_violation = max(0.0, self.freq_min - perf.frequency)
        power_violation = max(0.0, perf.power - self.power_max)
        
        # Penalty coefficient (large value to enforce constraints)
        penalty_coeff = 1000.0
        
        # Power fitness (minimize)
        power_fitness = perf.power + penalty_coeff * power_violation
        
        # Frequency fitness (maximize, so negative for minimization)
        freq_fitness = -perf.frequency - penalty_coeff * freq_violation
        
        # Normalize to reasonable scale for DEAP
        power_fitness = power_fitness / 100.0
        freq_fitness = freq_fitness / 10.0
        
        return (power_fitness, freq_fitness)
    
    def optimize(
        self,
        population_size: int = 100,
        generations: int = 50,
        cxpb: float = 0.7,
        mutpb: float = 0.3,
        verbose: bool = True
    ) -> List[ParetoSolution]:
        """
        Run NSGA-II optimization.
        
        Args:
            population_size: Population size
            generations: Number of generations
            cxpb: Crossover probability
            mutpb: Mutation probability
            verbose: Print progress
            
        Returns:
            List of Pareto-optimal solutions
        """
        start_time = datetime.now()
        
        # Create initial population
        pop = self.toolbox.population(n=population_size)
        
        # Evaluate initial population
        fitnesses = map(self.toolbox.evaluate, pop)
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        if verbose:
            logger.info(f"Starting NSGA-II optimization: {generations} generations, {population_size} individuals")
        
        # Statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        
        # Run algorithm
        convergence = []
        for gen in range(generations):
            # Select the next generation individuals
            offspring = self.toolbox.select(pop, len(pop))
            offspring = [self.toolbox.clone(ind) for ind in offspring]
            
            # Apply crossover
            for i in range(1, len(offspring), 2):
                if np.random.random() < cxpb:
                    offspring[i-1], offspring[i] = self.toolbox.mate(offspring[i-1], offspring[i])
                    del offspring[i-1].fitness.values
                    del offspring[i].fitness.values
            
            # Apply mutation
            for i in range(len(offspring)):
                if np.random.random() < mutpb:
                    offspring[i], = self.toolbox.mutate(offspring[i])
                    del offspring[i].fitness.values
            
            # Evaluate individuals with invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # Select the best individuals
            pop = self.toolbox.select(pop + offspring, population_size)
            
            # Track convergence
            record = stats.compile(pop)
            convergence.append(record)
            
            if verbose and (gen + 1) % max(1, generations // 10) == 0:
                logger.info(f"Generation {gen+1}/{generations}: "
                          f"Pareto size: {len([p for p in pop if len(p.fitness.values) == 2])}")
        
        # Extract Pareto front
        self.population = pop
        self.pareto_front = self._extract_pareto_front(pop)
        
        # Compute metrics
        exec_time = (datetime.now() - start_time).total_seconds()
        self.metrics = OptimizationMetrics(
            generations=generations,
            population_size=population_size,
            execution_time=exec_time,
            pareto_front_size=len(self.pareto_front),
            hypervolume=self._compute_hypervolume(),
            spread=self._compute_spread(),
            convergence=convergence,
            timestamp=datetime.now().isoformat()
        )
        
        if verbose:
            logger.info(f"Optimization complete in {exec_time:.2f}s")
            logger.info(f"Pareto front size: {len(self.pareto_front)}")
        
        return self.pareto_front
    
    def _extract_pareto_front(self, population) -> List[ParetoSolution]:
        """Extract Pareto-optimal solutions from population."""
        solutions = []
        
        for idx, individual in enumerate(population):
            if len(individual.fitness.values) != 2:
                continue
            
            params = CircuitParameters(wn=individual[0], wp=individual[1], vdd=individual[2])
            perf = self.predictor.predict(params)
            
            # Check if Pareto-dominant (for visualization purposes)
            is_dominated = False
            for sol in solutions:
                if (sol.performance.power <= perf.power and 
                    sol.performance.frequency >= perf.frequency):
                    is_dominated = True
                    break
            
            if not is_dominated:
                solutions.append(ParetoSolution(
                    parameters=params,
                    performance=perf,
                    fitness=individual.fitness.values,
                    rank=1
                ))
        
        # Sort by frequency (ascending)
        solutions.sort(key=lambda s: s.performance.power)
        return solutions
    
    def _compute_hypervolume(self) -> float:
        """Compute hypervolume metric."""
        if not self.pareto_front:
            return 0.0
        
        # Reference point: worst case (max power, min frequency)
        ref_point = (max(s.performance.power for s in self.pareto_front) * 1.1,
                    -min(s.performance.frequency for s in self.pareto_front) * 0.9)
        
        # Compute hypervolume (simplified)
        hv = 0.0
        prev_power = 0
        for sol in sorted(self.pareto_front, key=lambda s: s.performance.power):
            hv += sol.performance.frequency * (sol.performance.power - prev_power)
            prev_power = sol.performance.power
        
        return float(hv)
    
    def _compute_spread(self) -> float:
        """Compute spread metric (convergence diversity)."""
        if len(self.pareto_front) < 2:
            return 0.0
        
        powers = [s.performance.power for s in self.pareto_front]
        freqs = [s.performance.frequency for s in self.pareto_front]
        
        spread = np.sqrt(
            (np.max(powers) - np.min(powers)) ** 2 +
            (np.max(freqs) - np.min(freqs)) ** 2
        )
        
        return float(spread)
    
    def get_pareto_front(self) -> List[ParetoSolution]:
        """Get current Pareto front."""
        return self.pareto_front
    
    def get_best_power(self) -> Optional[ParetoSolution]:
        """Get solution with minimum power."""
        return min(self.pareto_front, key=lambda s: s.performance.power) if self.pareto_front else None
    
    def get_best_frequency(self) -> Optional[ParetoSolution]:
        """Get solution with maximum frequency."""
        return max(self.pareto_front, key=lambda s: s.performance.frequency) if self.pareto_front else None
    
    def get_best_efficiency(self) -> Optional[ParetoSolution]:
        """Get solution with best efficiency (GHz/mW)."""
        return max(self.pareto_front, key=lambda s: s.performance.efficiency) if self.pareto_front else None
    
    def export_pareto_front(self, filename: str):
        """Export Pareto front to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "generations": self.metrics.generations if self.metrics else 0,
                "population_size": self.metrics.population_size if self.metrics else 0,
                "execution_time": self.metrics.execution_time if self.metrics else 0,
                "pareto_front_size": len(self.pareto_front),
                "hypervolume": self.metrics.hypervolume if self.metrics else 0,
                "spread": self.metrics.spread if self.metrics else 0,
            },
            "pareto_front": [
                {
                    "parameters": {
                        "wn": sol.parameters.wn,
                        "wp": sol.parameters.wp,
                        "vdd": sol.parameters.vdd,
                    },
                    "performance": {
                        "frequency": sol.performance.frequency,
                        "power": sol.performance.power,
                        "delay": sol.performance.delay,
                        "efficiency": sol.performance.efficiency,
                    }
                }
                for sol in self.pareto_front
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Pareto front exported to {filename}")
    
    def get_pareto_front_dict(self) -> List[Dict]:
        """
        Get Pareto front in requested output format.
        
        Returns:
            List of dictionaries with format:
            [{"wn": float, "wp": float, "vdd": float, "power": float, "frequency": float, "delay": float}, ...]
        """
        return [
            {
                "wn": sol.parameters.wn,
                "wp": sol.parameters.wp,
                "vdd": sol.parameters.vdd,
                "power": sol.performance.power,
                "frequency": sol.performance.frequency,
                "delay": sol.performance.delay
            }
            for sol in self.pareto_front
        ]


# ============================================================================
# Utility Functions
# ============================================================================


def run_optimization(
    population_size: int = 100,
    generations: int = 50,
    use_ml: bool = False,
    seed: int = 42,
    freq_min: float = 0.0,
    power_max: float = 1000.0,
    verbose: bool = True
) -> Tuple[List[ParetoSolution], OptimizationMetrics]:
    """
    Run NSGA-II optimization with constraints.
    
    Args:
        population_size: Population size (default 100)
        generations: Number of generations (default 50)
        use_ml: Use ML model for performance prediction (default False)
        seed: Random seed for reproducibility (default 42)
        freq_min: Minimum frequency constraint in GHz (default 0.0 = no constraint)
        power_max: Maximum power constraint in mW (default 1000.0 = no constraint)
        verbose: Print progress (default True)
        
    Returns:
        Tuple of (pareto_front, metrics)
        - pareto_front: List[ParetoSolution] - Pareto-optimal solutions
        - metrics: OptimizationMetrics - Statistics from optimization run
    """
    # Set global seeds for reproducibility
    import random
    random.seed(seed)
    np.random.seed(seed)
    
    optimizer = NSGAII_Optimizer(
        use_ml=use_ml,
        random_seed=seed,
        freq_min=freq_min,
        power_max=power_max
    )
    pareto_front = optimizer.optimize(
        population_size=population_size,
        generations=generations,
        verbose=verbose
    )
    return pareto_front, optimizer.metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("NSGA-II CMOS Multi-Objective Optimizer - FULL NSGA-II IMPLEMENTATION")
    print("=" * 80)
    
    # Example 1: Basic optimization (no constraints)
    print("\n[Example 1] Unconstrained Multi-Objective Optimization")
    print("-" * 80)
    
    pareto_front, metrics = run_optimization(
        population_size=100,
        generations=50,
        use_ml=False,
        seed=42,
        verbose=True
    )
    
    print(f"\n✓ Optimization Complete")
    print(f"  Pareto Front Size: {len(pareto_front)}")
    print(f"  Execution Time: {metrics.execution_time:.2f}s")
    print(f"  Hypervolume: {metrics.hypervolume:.2f}")
    print(f"  Spread: {metrics.spread:.2f}")
    
    print("\nTop 5 Solutions (sorted by power):")
    for i, sol in enumerate(sorted(pareto_front, key=lambda s: s.performance.power)[:5]):
        print(f"  {i+1}. WN={sol.parameters.wn:5.2f}µm, WP={sol.parameters.wp:5.2f}µm, "
              f"VDD={sol.parameters.vdd:4.2f}V | "
              f"f={sol.performance.frequency:6.2f}GHz, P={sol.performance.power:6.2f}mW")
    
    # Example 2: Constrained optimization
    print("\n" + "=" * 80)
    print("[Example 2] Constrained Optimization (f_min=2.0 GHz, P_max=50 mW)")
    print("=" * 80)
    
    pareto_front_constrained, metrics_constrained = run_optimization(
        population_size=100,
        generations=50,
        use_ml=False,
        seed=42,
        freq_min=2.0,  # Minimum 2.0 GHz
        power_max=50.0,  # Maximum 50 mW
        verbose=False
    )
    
    print(f"\n✓ Optimization Complete")
    print(f"  Pareto Front Size: {len(pareto_front_constrained)}")
    print(f"  Execution Time: {metrics_constrained.execution_time:.2f}s")
    
    if pareto_front_constrained:
        print("\nFeasible Solutions (satisfying constraints):")
        for i, sol in enumerate(pareto_front_constrained[:5]):
            status = "✓" if (sol.performance.frequency >= 2.0 and sol.performance.power <= 50.0) else "✗"
            print(f"  {status} {i+1}. WN={sol.parameters.wn:5.2f}µm, WP={sol.parameters.wp:5.2f}µm, "
                  f"VDD={sol.parameters.vdd:4.2f}V | "
                  f"f={sol.performance.frequency:6.2f}GHz, P={sol.performance.power:6.2f}mW")
    else:
        print("\nNo feasible solutions found satisfying the constraints.")
        print("Try relaxing constraints or increasing population/generations.")
    
    # Example 3: Output format verification
    print("\n" + "=" * 80)
    print("[Example 3] Requested Output Format Verification")
    print("=" * 80)
    
    # Assuming optimizer is still in scope
    optimizer = NSGAII_Optimizer(random_seed=42, freq_min=0)
    optimizer.optimize(population_size=50, generations=20, verbose=False)
    
    output_dicts = optimizer.get_pareto_front_dict()
    print(f"\n✓ Output Format: List of {len(output_dicts)} solutions")
    if output_dicts:
        print("\nFirst solution (JSON-serializable):")
        import json
        print(json.dumps(output_dicts[0], indent=2))
        
        print("\nAll solution keys (verify format):", list(output_dicts[0].keys()))
    
    print("\n" + "=" * 80)
    print("NSGA-II Implementation Complete")
    print("=" * 80)
