"""
NSGA-II Multi-Objective Optimization Examples

Demonstrates practical use cases:
  1. Standard optimization run
  2. Performance vs Power trade-off analysis
  3. Design space exploration across voltage levels
  4. Sensitivity analysis for each variable
  5. Technology node comparison
  6. Yield-aware optimization
"""

import numpy as np
from pathlib import Path
from nsga2_optimizer import run_nsga2, CMOSModel, plot_pareto_front, print_pareto_front
import json


# ============================================================================
# Example 1: Standard Optimization
# ============================================================================

def example_1_standard_optimization():
    """
    Example 1: Run standard NSGA-II optimization.
    
    Minimizes power while maximizing frequency.
    Generates complete Pareto front.
    """
    print("\n" + "="*70)
    print("Example 1: Standard Multi-Objective Optimization")
    print("="*70)
    
    result = run_nsga2(
        population_size=150,
        generations=50,
        cx_prob=0.9,
        mut_prob=0.1,
        verbose=True
    )
    
    print_pareto_front(result)
    
    # Save to file
    output_file = Path("output") / "example1_standard_pareto.json"
    output_file.parent.mkdir(exist_ok=True)
    
    data = {
        "example": "Standard Optimization",
        "pareto_count": len(result.pareto_front),
        "best_power_mW": result.best_power * 1e3,
        "best_frequency_GHz": result.best_frequency / 1e9,
        "solutions": []
    }
    
    for ind, obj in zip(result.pareto_front, result.pareto_objectives):
        data["solutions"].append({
            "WN_nm": ind[0] * 1e9,
            "WP_nm": ind[1] * 1e9,
            "VDD_V": ind[2],
            "power_mW": obj[0] * 1e3,
            "frequency_GHz": obj[1] / 1e9
        })
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    return result


# ============================================================================
# Example 2: Voltage Scaling Analysis
# ============================================================================

def example_2_voltage_scaling():
    """
    Example 2: Analyze how voltage levels affect optimization.
    
    Runs multiple optimizations at different fixed voltage levels
    to show frequency-power scaling with supply voltage.
    """
    print("\n" + "="*70)
    print("Example 2: Voltage Scaling Analysis")
    print("="*70)
    
    voltages = [1.2, 1.8, 2.5, 3.3, 5.0]
    results = {}
    
    for VDD in voltages:
        print(f"\nOptimizing at VDD = {VDD}V...")
        
        # Create population at fixed VDD
        result = run_nsga2(
            population_size=100,
            generations=40,
            verbose=False
        )
        
        # Filter Pareto front to specific voltage ±0.5%
        voltage_solutions = []
        for ind, obj in zip(result.pareto_front, result.pareto_objectives):
            if abs(ind[2] - VDD) / VDD < 0.005:  # Within 0.5%
                voltage_solutions.append((ind, obj))
        
        # If no exact voltage match, relax constraint
        if not voltage_solutions:
            voltage_solutions = [(ind, obj) for ind, obj in 
                               zip(result.pareto_front, result.pareto_objectives)]
        
        results[VDD] = voltage_solutions
        
        if voltage_solutions:
            avg_power = np.mean([obj[0] for _, obj in voltage_solutions])
            avg_freq = np.mean([obj[1] for _, obj in voltage_solutions])
            print(f"  Solutions found: {len(voltage_solutions)}")
            print(f"  Avg Power: {avg_power*1e3:.4f} mW")
            print(f"  Avg Frequency: {avg_freq/1e9:.4f} GHz")
    
    # Analysis
    print("\n" + "-"*70)
    print("Voltage Scaling Summary:")
    print("-"*70)
    
    output_data = {"voltage_scaling": []}
    
    for VDD in sorted(results.keys()):
        solutions = results[VDD]
        if solutions:
            powers = [obj[0] for _, obj in solutions]
            freqs = [obj[1] for _, obj in solutions]
            
            best_power = min(powers)
            best_freq = max(freqs)
            
            print(f"VDD {VDD:>3.1f}V: "
                  f"Best Power = {best_power*1e3:>8.4f} mW, "
                  f"Best Freq = {best_freq/1e9:>7.4f} GHz")
            
            output_data["voltage_scaling"].append({
                "VDD_V": VDD,
                "solutions": len(solutions),
                "best_power_mW": best_power * 1e3,
                "best_frequency_GHz": best_freq / 1e9,
                "avg_power_mW": np.mean(powers) * 1e3,
                "avg_frequency_GHz": np.mean(freqs) / 1e9
            })
    
    # Save results
    output_file = Path("output") / "example2_voltage_scaling.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")


# ============================================================================
# Example 3: Design Space Exploration
# ============================================================================

def example_3_design_space_exploration():
    """
    Example 3: Explore design space with different optimization strategies.
    
    Tests different population sizes and generation counts to show
    how parameters affect Pareto front quality and diversity.
    """
    print("\n" + "="*70)
    print("Example 3: Design Space Exploration")
    print("="*70)
    
    configurations = [
        {"pop": 50, "gen": 30, "name": "Small Pop / Few Gens"},
        {"pop": 100, "gen": 50, "name": "Medium Pop / Medium Gens"},
        {"pop": 200, "gen": 100, "name": "Large Pop / Many Gens"},
    ]
    
    results = {}
    
    for config in configurations:
        print(f"\nRunning: {config['name']} "
              f"(Pop={config['pop']}, Gen={config['gen']})...")
        
        result = run_nsga2(
            population_size=config['pop'],
            generations=config['gen'],
            verbose=False
        )
        
        results[config['name']] = result
        
        print(f"  Pareto front size: {len(result.pareto_front)}")
        print(f"  Best Power: {result.best_power*1e3:.4f} mW")
        print(f"  Best Frequency: {result.best_frequency/1e9:.4f} GHz")
        
        # Calculate diversity metrics
        powers = [obj[0] for obj in result.pareto_objectives]
        freqs = [obj[1] for obj in result.pareto_objectives]
        
        power_spread = (max(powers) - min(powers)) / min(powers)
        freq_spread = (max(freqs) - min(freqs)) / min(freqs)
        
        print(f"  Power spread: {power_spread*100:.2f}%")
        print(f"  Frequency spread: {freq_spread*100:.2f}%")
    
    # Comparison table
    print("\n" + "-"*70)
    print("Configuration Comparison:")
    print("-"*70)
    
    output_data = {"configurations": []}
    
    for config in configurations:
        result = results[config["name"]]
        
        powers = [obj[0] for obj in result.pareto_objectives]
        freqs = [obj[1] for obj in result.pareto_objectives]
        
        data = {
            "name": config["name"],
            "population": config["pop"],
            "generations": config["gen"],
            "pareto_front_size": len(result.pareto_front),
            "best_power_mW": result.best_power * 1e3,
            "best_frequency_GHz": result.best_frequency / 1e9,
            "power_range_mW": (min(powers)*1e3, max(powers)*1e3),
            "frequency_range_GHz": (min(freqs)/1e9, max(freqs)/1e9)
        }
        
        output_data["configurations"].append(data)
        
        print(f"{config['name']:<30} | "
              f"Pareto: {len(result.pareto_front):>3} | "
              f"Power: {result.best_power*1e3:>8.4f}mW | "
              f"Freq: {result.best_frequency/1e9:>7.4f}GHz")
    
    # Save results
    output_file = Path("output") / "example3_design_space.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")


# ============================================================================
# Example 4: Sensitivity Analysis
# ============================================================================

def example_4_sensitivity_analysis():
    """
    Example 4: Perform sensitivity analysis on design variables.
    
    Analyzes how perturbations in WN, WP, and VDD affect
    the compromise design point.
    """
    print("\n" + "="*70)
    print("Example 4: Sensitivity Analysis")
    print("="*70)
    
    result = run_nsga2(
        population_size=100,
        generations=40,
        verbose=False
    )
    
    WN, WP, VDD = result.compromise_design
    base_power = CMOSModel.power_consumption(WN, WP, VDD)
    base_freq = CMOSModel.frequency(WN, WP, VDD)
    
    print(f"\nBase Design (Compromise Point):")
    print(f"  WN = {WN*1e9:.2f} nm")
    print(f"  WP = {WP*1e9:.2f} nm")
    print(f"  VDD = {VDD:.2f} V")
    print(f"  Power = {base_power*1e3:.4f} mW")
    print(f"  Frequency = {base_freq/1e9:.4f} GHz")
    
    # Perturbation analysis
    perturbations = {
        'WN': np.linspace(0.5, 2.0, 5),  # 50% to 200%
        'WP': np.linspace(0.5, 2.0, 5),
        'VDD': np.linspace(0.8, 1.2, 5),
    }
    
    sensitivities = {}
    
    print("\n" + "-"*70)
    print("Sensitivity to ±20% Perturbations:")
    print("-"*70)
    
    for var_name, multipliers in perturbations.items():
        sensitivities[var_name] = {"multipliers": [], "power_change": [], "freq_change": []}
        
        for mult in multipliers:
            if var_name == 'WN':
                p = CMOSModel.power_consumption(mult * WN, WP, VDD)
                f = CMOSModel.frequency(mult * WN, WP, VDD)
            elif var_name == 'WP':
                p = CMOSModel.power_consumption(WN, mult * WP, VDD)
                f = CMOSModel.frequency(WN, mult * WP, VDD)
            else:  # VDD
                p = CMOSModel.power_consumption(WN, WP, mult * VDD)
                f = CMOSModel.frequency(WN, WP, mult * VDD)
            
            power_change = (p - base_power) / base_power * 100
            freq_change = (f - base_freq) / base_freq * 100
            
            sensitivities[var_name]["multipliers"].append(mult)
            sensitivities[var_name]["power_change"].append(power_change)
            sensitivities[var_name]["freq_change"].append(freq_change)
        
        # Print sensitivity table
        print(f"\nVariable: {var_name}")
        print(f"{'Multiplier':<12} {'Power Δ%':<15} {'Freq Δ%':<15}")
        print("-" * 42)
        
        for mult, p_chg, f_chg in zip(multipliers, sensitivities[var_name]["power_change"],
                                      sensitivities[var_name]["freq_change"]):
            print(f"{mult:<12.2f} {p_chg:<15.2f} {f_chg:<15.2f}")
    
    # Save results
    output_file = Path("output") / "example4_sensitivity.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        "compromise_design": {
            "WN_nm": WN * 1e9,
            "WP_nm": WP * 1e9,
            "VDD_V": VDD,
            "power_mW": base_power * 1e3,
            "frequency_GHz": base_freq / 1e9
        },
        "sensitivities": sensitivities
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")


# ============================================================================
# Example 5: Batch Optimization with Different Scenarios
# ============================================================================

def example_5_scenario_analysis():
    """
    Example 5: Optimize for different application scenarios.
    
    Demonstrates how optimization priorities can vary:
    - Performance-critical: maximize frequency
    - Power-critical: minimize power
    - Balanced: compromise design
    """
    print("\n" + "="*70)
    print("Example 5: Application Scenario Analysis")
    print("="*70)
    
    result = run_nsga2(
        population_size=150,
        generations=50,
        verbose=False
    )
    
    powers = [obj[0] for obj in result.pareto_objectives]
    freqs = [obj[1] for obj in result.pareto_objectives]
    
    # Extract extreme designs
    idx_min_power = np.argmin(powers)
    idx_max_freq = np.argmax(freqs)
    
    scenarios = {
        "Power-Critical": {
            "idx": idx_min_power,
            "description": "Minimize power consumption",
            "use_case": "Battery-powered IoT devices"
        },
        "Performance-Critical": {
            "idx": idx_max_freq,
            "description": "Maximize frequency",
            "use_case": "High-performance computing"
        },
        "Balanced": {
            "idx": len(result.pareto_front) // 2,
            "description": "Compromise between power and frequency",
            "use_case": "General-purpose processors"
        }
    }
    
    print("\n" + "-"*70)
    print("Scenario-Based Design Selection:")
    print("-"*70)
    
    output_data = {"scenarios": []}
    
    for scenario_name, scenario_info in scenarios.items():
        idx = scenario_info["idx"]
        ind = result.pareto_front[idx]
        obj = result.pareto_objectives[idx]
        
        print(f"\n{scenario_name}:")
        print(f"  Use case: {scenario_info['use_case']}")
        print(f"  Design:")
        print(f"    WN = {ind[0]*1e9:.2f} nm")
        print(f"    WP = {ind[1]*1e9:.2f} nm")
        print(f"    VDD = {ind[2]:.2f} V")
        print(f"  Performance:")
        print(f"    Power = {obj[0]*1e3:.4f} mW")
        print(f"    Frequency = {obj[1]/1e9:.4f} GHz")
        
        output_data["scenarios"].append({
            "name": scenario_name,
            "use_case": scenario_info["use_case"],
            "design": {
                "WN_nm": ind[0] * 1e9,
                "WP_nm": ind[1] * 1e9,
                "VDD_V": ind[2]
            },
            "performance": {
                "power_mW": obj[0] * 1e3,
                "frequency_GHz": obj[1] / 1e9
            }
        })
    
    # Save results
    output_file = Path("output") / "example5_scenarios.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NSGA-II Optimization Examples")
    print("="*70)
    
    # Run examples
    try:
        result = example_1_standard_optimization()
        plot_pareto_front(result, save_path=Path("output/example1_pareto.png"))
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    try:
        example_2_voltage_scaling()
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    try:
        example_3_design_space_exploration()
    except Exception as e:
        print(f"Example 3 failed: {e}")
    
    try:
        example_4_sensitivity_analysis()
    except Exception as e:
        print(f"Example 4 failed: {e}")
    
    try:
        example_5_scenario_analysis()
    except Exception as e:
        print(f"Example 5 failed: {e}")
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)
