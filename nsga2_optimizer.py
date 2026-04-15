"""
NSGA-II Multi-Objective Optimization for CMOS Design

Objectives:
  - Minimize Power Consumption (P = C * VDD^2 * f)
  - Maximize Frequency (f = 1 / t_pd)

Variables (Inputs):
  - WN: NMOS transistor width (affects drain current)
  - WP: PMOS transistor width (affects drain current)
  - VDD: Supply voltage

Implements NSGA-II using DEAP framework for Pareto-optimal front generation.
"""

import numpy as np
import random
from typing import Tuple, List, Dict
from dataclasses import dataclass
from pathlib import Path
import json

# DEAP imports
from deap import base, creator, tools, algorithms
from deap.benchmarks import binary_tournament


# ============================================================================
# CMOS Physics Equations
# ============================================================================

class CMOSModel:
    """CMOS device model with physics-based equations."""
    
    # Physical constants and typical values
    COX = 1.2e-3  # Gate oxide capacitance per unit area (F/m²)
    L = 28e-9     # Channel length (28nm technology node)
    CL = 5e-12    # Load capacitance (5 pF - typical)
    UN = 0.045    # NMOS carrier mobility (m²/V·s)
    UP = 0.015    # PMOS carrier mobility (m²/V·s)
    VTN = 0.4     # NMOS threshold voltage (V)
    VTP = -0.4    # PMOS threshold voltage (V)
    
    @staticmethod
    def calculate_drain_current(W: float, mobility: float, VDD: float) -> float:
        """
        Calculate drain current (saturation region).
        
        I_d = 0.5 * μ * (W/L) * C_ox * (VDD - V_T)^2
        
        Args:
            W: Transistor width (m)
            mobility: Carrier mobility (m²/V·s)
            VDD: Supply voltage (V)
        
        Returns:
            Drain current in amperes
        """
        if VDD <= 0.4:  # Below threshold voltage
            return 1e-9  # Minimal current
        
        vgate = VDD
        Id = (0.5 * mobility * (W / CMOSModel.L) * CMOSModel.COX * 
              (vgate - 0.4) ** 2)
        return max(Id, 1e-9)  # Ensure minimum current
    
    @staticmethod
    def combined_drain_current(WN: float, WP: float, VDD: float) -> float:
        """
        Effective drain current combining NMOS and PMOS.
        
        Uses ratio-based combination: I_d_eff ∝ (WN + WP) * VDD
        """
        Id_n = CMOSModel.calculate_drain_current(WN, CMOSModel.UN, VDD)
        Id_p = CMOSModel.calculate_drain_current(WP, CMOSModel.UP, VDD)
        # Effective current (roughly proportional to switching speed)
        Id_eff = (Id_n + Id_p) / 2.0
        return max(Id_eff, 1e-9)
    
    @staticmethod
    def propagation_delay(WN: float, WP: float, VDD: float) -> float:
        """
        Propagation delay: t_pd = (C_L * VDD) / I_d
        
        Args:
            WN: NMOS width
            WP: PMOS width
            VDD: Supply voltage
        
        Returns:
            Delay in seconds
        """
        Id = CMOSModel.combined_drain_current(WN, WP, VDD)
        t_pd = (CMOSModel.CL * VDD) / Id
        return max(t_pd, 1e-12)  # Minimum 1 ps
    
    @staticmethod
    def frequency(WN: float, WP: float, VDD: float) -> float:
        """
        Operating frequency: f = 1 / (2 * t_pd)
        
        Factor of 2 accounts for full cycle (rise + fall).
        """
        t_pd = CMOSModel.propagation_delay(WN, WP, VDD)
        f = 1.0 / (2.0 * t_pd)
        return f
    
    @staticmethod
    def power_consumption(WN: float, WP: float, VDD: float, 
                         clock_freq: float = 1e9) -> float:
        """
        Dynamic power consumption: P = C_L * VDD^2 * f * α
        
        where α is activity factor (assumed 0.3 for typical circuits)
        
        Args:
            WN: NMOS width
            WP: PMOS width
            VDD: Supply voltage
            clock_freq: Operating frequency (default 1 GHz)
        
        Returns:
            Power in watts
        """
        ACTIVITY_FACTOR = 0.3
        P = CMOSModel.CL * (VDD ** 2) * clock_freq * ACTIVITY_FACTOR
        return P


# ============================================================================
# NSGA-II Setup with DEAP
# ============================================================================

# Define fitness class for multi-objective optimization
creator.create("FitnessMulti", base.Fitness, 
               weights=(-1.0, 1.0))  # Minimize power, maximize frequency

# Define individual class
creator.create("Individual", list, fitness=creator.FitnessMulti)

# Create toolbox
toolbox = base.Toolbox()

# Attribute generators (bounds for each variable)
BOUNDS = {
    'WN': (10e-9, 100e-9),      # 10-100 nm
    'WP': (20e-9, 200e-9),      # 20-200 nm
    'VDD': (1.0, 5.0),          # 1-5 V
}

toolbox.register("WN", random.uniform, BOUNDS['WN'][0], BOUNDS['WN'][1])
toolbox.register("WP", random.uniform, BOUNDS['WP'][0], BOUNDS['WP'][1])
toolbox.register("VDD", random.uniform, BOUNDS['VDD'][0], BOUNDS['VDD'][1])

toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.WN, toolbox.WP, toolbox.VDD), n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evaluate_individual(individual: creator.Individual) -> Tuple[float, float]:
    """
    Evaluate an individual (design point).
    
    Returns:
        (power, frequency) for multi-objective evaluation
    """
    WN, WP, VDD = individual
    
    # Calculate objectives
    power = CMOSModel.power_consumption(WN, WP, VDD)
    freq = CMOSModel.frequency(WN, WP, VDD)
    
    return power, freq


def mutate_gaussian(individual: creator.Individual, 
                   sigma: float = 0.1, 
                   indpb: float = 0.2) -> Tuple[creator.Individual]:
    """
    Gaussian mutation for continuous variables.
    
    Args:
        individual: Individual to mutate
        sigma: Standard deviation of Gaussian
        indpb: Probability per attribute
    
    Returns:
        Mutated individual
    """
    for i, (lower, upper) in enumerate([BOUNDS['WN'], BOUNDS['WP'], BOUNDS['VDD']]):
        if random.random() < indpb:
            mutation = random.gauss(0, sigma * (upper - lower))
            individual[i] = np.clip(individual[i] + mutation, lower, upper)
    
    return individual,


def crossover_blend(ind1: creator.Individual, 
                   ind2: creator.Individual,
                   alpha: float = 0.5) -> Tuple[creator.Individual, creator.Individual]:
    """
    Blend crossover (BLX-alpha) for continuous variables.
    
    Args:
        ind1: First parent
        ind2: Second parent
        alpha: Blend parameter
    
    Returns:
        Two offspring
    """
    for i, (lower, upper) in enumerate([BOUNDS['WN'], BOUNDS['WP'], BOUNDS['VDD']]):
        if random.random() < 0.5:
            x1, x2 = ind1[i], ind2[i]
            d = abs(x2 - x1)
            range_min = min(x1, x2) - alpha * d
            range_max = max(x1, x2) + alpha * d
            
            range_min = max(range_min, lower)
            range_max = min(range_max, upper)
            
            ind1[i] = random.uniform(range_min, range_max)
            ind2[i] = random.uniform(range_min, range_max)
    
    return ind1, ind2


# Register genetic operators
toolbox.register("evaluate", evaluate_individual)
toolbox.register("mate", crossover_blend)
toolbox.register("mutate", mutate_gaussian)
toolbox.register("select", tools.selNSGA2)


# ============================================================================
# NSGA-II Algorithm Implementation
# ============================================================================

@dataclass
class OptimizationResult:
    """Container for optimization results."""
    pareto_front: List[creator.Individual]
    pareto_objectives: List[Tuple[float, float]]
    generation_history: Dict
    statistics: Dict
    best_power: float
    best_frequency: float
    compromise_design: Tuple[float, float, float]


def run_nsga2(population_size: int = 100,
              generations: int = 50,
              cx_prob: float = 0.9,
              mut_prob: float = 0.1,
              verbose: bool = True) -> OptimizationResult:
    """
    Run NSGA-II multi-objective optimization.
    
    Args:
        population_size: Size of population
        generations: Number of generations to evolve
        cx_prob: Crossover probability
        mut_prob: Mutation probability
        verbose: Print progress
    
    Returns:
        OptimizationResult with Pareto front and statistics
    """
    
    # Initialize population
    pop = toolbox.population(n=population_size)
    
    # Evaluate initial population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"NSGA-II Multi-Objective Optimization")
        print(f"{'='*70}")
        print(f"Population: {population_size}")
        print(f"Generations: {generations}")
        print(f"Crossover prob: {cx_prob}, Mutation prob: {mut_prob}")
        print(f"{'='*70}\n")
    
    # Statistics
    stats = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats.register("avg_power", lambda x: np.mean([v[0] for v in x]))
    stats.register("avg_freq", lambda x: np.mean([v[1] for v in x]))
    stats.register("min_power", lambda x: np.min([v[0] for v in x]))
    stats.register("max_freq", lambda x: np.max([v[1] for v in x]))
    
    history = {'gen': [], 'evals': [], 'avg_power': [], 'avg_freq': [],
               'min_power': [], 'max_freq': [], 'pareto_size': []}
    
    # Main evolutionary loop
    for gen in range(generations):
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]
        
        # Apply crossover and mutation
        for i in range(1, len(offspring), 2):
            if random.random() < cx_prob:
                offspring[i-1], offspring[i] = toolbox.mate(offspring[i-1], offspring[i])
                del offspring[i-1].fitness.values
                del offspring[i].fitness.values
        
        for i in range(len(offspring)):
            if random.random() < mut_prob:
                offspring[i], = toolbox.mutate(offspring[i])
                del offspring[i].fitness.values
        
        # Evaluate individuals with invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Select the best individuals from parents and offspring
        pop = toolbox.select(pop + offspring, population_size)
        
        # Record statistics
        fits = [ind.fitness.values for ind in pop]
        record = stats.compile(pop)
        history['gen'].append(gen)
        history['evals'].append(len(invalid_ind))
        history['avg_power'].append(record['avg_power'])
        history['avg_freq'].append(record['avg_freq'])
        history['min_power'].append(record['min_power'])
        history['max_freq'].append(record['max_freq'])
        history['pareto_size'].append(len(pop))
        
        if verbose and (gen % 10 == 0 or gen == generations - 1):
            print(f"Gen {gen:>3d} | Pop: {len(pop):>3d} | "
                  f"Avg Power: {record['avg_power']:.3e}W | "
                  f"Max Freq: {record['max_freq']/1e9:.3f}GHz")
    
    # Extract Pareto front
    pareto_front = tools.sortNondominated(pop, len(pop), first_front_only=True)[0]
    
    # Sort by power for better presentation
    pareto_front.sort(key=lambda x: x.fitness.values[0])
    
    pareto_objectives = [ind.fitness.values for ind in pareto_front]
    
    # Find compromise design (closest to utopian point)
    if pareto_objectives:
        powers = [obj[0] for obj in pareto_objectives]
        freqs = [obj[1] for obj in pareto_objectives]
        
        # Normalize to [0, 1]
        min_power, max_power = min(powers), max(powers)
        min_freq, max_freq = min(freqs), max(freqs)
        
        if max_power > min_power and max_freq > min_freq:
            norm_powers = [(p - min_power) / (max_power - min_power) for p in powers]
            norm_freqs = [(f - min_freq) / (max_freq - min_freq) for f in freqs]
            
            # Find closest to (0, 1) - min power, max freq
            distances = [np.sqrt((1-nf)**2 + np.power(np.power(np.multiply(np.subtract(1.0, norm_powers[i]), 1.0), 2.0), 0.5)) 
                        for i, nf in enumerate(norm_freqs)]
            compromise_idx = np.argmin(distances)
            compromise_design = (pareto_front[compromise_idx][0],
                               pareto_front[compromise_idx][1],
                               pareto_front[compromise_idx][2])
        else:
            compromise_design = pareto_front[0]
    else:
        compromise_design = (0, 0, 0)
    
    # Final statistics
    result_stats = {
        'population_size': population_size,
        'generations': generations,
        'pareto_front_size': len(pareto_front),
        'best_power': min(powers) if powers else 0,
        'best_frequency': max(freqs) if freqs else 0,
        'power_range': (min(powers), max(powers)) if powers else (0, 0),
        'frequency_range': (min(freqs), max(freqs)) if freqs else (0, 0),
    }
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"NSGA-II Optimization Complete")
        print(f"{'='*70}")
        print(f"Pareto Front Size: {len(pareto_front)}")
        print(f"Best Power: {result_stats['best_power']:.3e} W")
        print(f"Best Frequency: {result_stats['best_frequency']/1e9:.3f} GHz")
        print(f"Compromise Design (WN, WP, VDD): "
              f"({compromise_design[0]*1e9:.2f}nm, "
              f"{compromise_design[1]*1e9:.2f}nm, "
              f"{compromise_design[2]:.2f}V)")
        print(f"{'='*70}\n")
    
    return OptimizationResult(
        pareto_front=pareto_front,
        pareto_objectives=pareto_objectives,
        generation_history=history,
        statistics=result_stats,
        best_power=result_stats['best_power'],
        best_frequency=result_stats['best_frequency'],
        compromise_design=compromise_design
    )


def save_results(result: OptimizationResult, output_dir: Path = Path("output")):
    """
    Save optimization results to files.
    
    Args:
        result: OptimizationResult object
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Save Pareto front as CSV
    pareto_file = output_dir / "pareto_front.csv"
    with open(pareto_file, 'w') as f:
        f.write("WN(nm),WP(nm),VDD(V),Power(W),Frequency(GHz)\n")
        for ind, obj in zip(result.pareto_front, result.pareto_objectives):
            f.write(f"{ind[0]*1e9:.6f},{ind[1]*1e9:.6f},{ind[2]:.6f},"
                   f"{obj[0]:.6e},{obj[1]/1e9:.6f}\n")
    
    # Save statistics as JSON
    stats_file = output_dir / "optimization_stats.json"
    stats_dict = {
        'population_size': result.statistics['population_size'],
        'generations': result.statistics['generations'],
        'pareto_front_size': result.statistics['pareto_front_size'],
        'best_power_W': result.statistics['best_power'],
        'best_frequency_GHz': result.statistics['best_frequency'] / 1e9,
        'power_range_W': tuple(result.statistics['power_range']),
        'frequency_range_GHz': (result.statistics['frequency_range'][0]/1e9,
                               result.statistics['frequency_range'][1]/1e9),
        'compromise_design': {
            'WN_nm': result.compromise_design[0] * 1e9,
            'WP_nm': result.compromise_design[1] * 1e9,
            'VDD_V': result.compromise_design[2]
        }
    }
    with open(stats_file, 'w') as f:
        json.dump(stats_dict, f, indent=2)
    
    print(f"Results saved:")
    print(f"  - {pareto_file}")
    print(f"  - {stats_file}")


# ============================================================================
# Visualization & Analysis
# ============================================================================

def plot_pareto_front(result: OptimizationResult, save_path: Path = None):
    """
    Plot Pareto front (Power vs Frequency).
    
    Args:
        result: OptimizationResult object
        save_path: Path to save figure
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  matplotlib not installed. Skipping plot.")
        return
    
    powers = [obj[0] * 1e3 for obj in result.pareto_objectives]  # Convert to mW
    freqs = [obj[1] / 1e9 for obj in result.pareto_objectives]   # Convert to GHz
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Plot Pareto front
    ax.plot(powers, freqs, 'b-o', linewidth=2, markersize=8, label='Pareto Front')
    
    # Highlight compromise design
    comp_power = CMOSModel.power_consumption(result.compromise_design[0],
                                             result.compromise_design[1],
                                             result.compromise_design[2]) * 1e3
    comp_freq = CMOSModel.frequency(result.compromise_design[0],
                                    result.compromise_design[1],
                                    result.compromise_design[2]) / 1e9
    ax.plot(comp_power, comp_freq, 'r*', markersize=20, label='Compromise Design')
    
    # Labels and formatting
    ax.set_xlabel('Power Consumption (mW)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (GHz)', fontsize=12, fontweight='bold')
    ax.set_title('NSGA-II Pareto Front: Power vs Frequency Trade-off', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    # Add annotations for extreme points
    if len(powers) > 0:
        min_power_idx = np.argmin(powers)
        max_freq_idx = np.argmax(freqs)
        
        ax.annotate('Min Power', xy=(powers[min_power_idx], freqs[min_power_idx]),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        ax.annotate('Max Frequency', xy=(powers[max_freq_idx], freqs[max_freq_idx]),
                   xytext=(10, -20), textcoords='offset points',
                   fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Pareto front plot saved: {save_path}")
    
    plt.show()


def print_pareto_front(result: OptimizationResult):
    """
    Print Pareto front in human-readable format.
    
    Args:
        result: OptimizationResult object
    """
    print(f"\n{'='*90}")
    print(f"PARETO FRONT - Top Designs")
    print(f"{'='*90}")
    print(f"{'#':<3} {'WN(nm)':<10} {'WP(nm)':<10} {'VDD(V)':<10} "
          f"{'Power(mW)':<15} {'Freq(GHz)':<12}")
    print(f"{'-'*90}")
    
    for i, (ind, obj) in enumerate(zip(result.pareto_front, result.pareto_objectives)):
        print(f"{i+1:<3} {ind[0]*1e9:<10.2f} {ind[1]*1e9:<10.2f} {ind[2]:<10.2f} "
              f"{obj[0]*1e3:<15.6e} {obj[1]/1e9:<12.4f}")
    
    print(f"{'='*90}\n")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NSGA-II Multi-Objective CMOS Optimization")
    print("="*70)
    
    # Run optimization
    result = run_nsga2(
        population_size=100,
        generations=50,
        cx_prob=0.9,
        mut_prob=0.1,
        verbose=True
    )
    
    # Print results
    print_pareto_front(result)
    
    # Save results
    save_results(result)
    
    # Plot Pareto front
    try:
        plot_pareto_front(result, save_path=Path("output/pareto_front.png"))
    except Exception as e:
        print(f"Could not generate plot: {e}")
    
    print("="*70)
    print("Optimization Complete!")
    print("="*70)
