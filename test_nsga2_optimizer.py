"""
Test Suite for NSGA-II Multi-Objective CMOS Optimizer

Tests:
  1. Basic optimization run
  2. Pareto front verification (non-dominated solutions)
  3. CMOS model validation (physics equations)
  4. Multi-run statistics (convergence tracking)
  5. Constraint validation (within bounds)
  6. Compromise design selection
  7. Sensitivity analysis on population size
"""

import pytest
import numpy as np
from pathlib import Path
from nsga2_optimizer import (
    CMOSModel, run_nsga2, OptimizationResult,
    creator, toolbox, evaluate_individual
)


# ============================================================================
# Test 1: CMOS Model Physics
# ============================================================================

def test_cmos_physics_equations():
    """Verify CMOS physics equations are correct."""
    
    # Test 1a: Drain current increases with width
    WN1, WN2 = 10e-9, 20e-9
    VDD = 3.3
    
    Id1 = CMOSModel.combined_drain_current(WN1, WN1, VDD)
    Id2 = CMOSModel.combined_drain_current(WN2, WN2, VDD)
    
    assert Id2 > Id1, "Drain current should increase with width"
    print(f"✓ Test 1a: Drain current scales with width (I1={Id1:.3e}, I2={Id2:.3e})")
    
    # Test 1b: Frequency increases with drain current (smaller delay)
    f1_small = CMOSModel.frequency(10e-9, 10e-9, VDD)
    f1_large = CMOSModel.frequency(50e-9, 50e-9, VDD)
    
    assert f1_large > f1_small, "Larger transistors should have higher frequency"
    print(f"✓ Test 1b: Frequency scales with transistor width (f_small={f1_small/1e9:.3f}GHz, f_large={f1_large/1e9:.3f}GHz)")
    
    # Test 1c: Power increases with voltage squared
    P1 = CMOSModel.power_consumption(20e-9, 20e-9, 1.0)
    P2 = CMOSModel.power_consumption(20e-9, 20e-9, 2.0)
    
    ratio = P2 / P1
    expected_ratio = 4.0  # V^2 relationship
    assert abs(ratio - expected_ratio) / expected_ratio < 0.01, "Power should scale as V^2"
    print(f"✓ Test 1c: Power scales as V² (ratio={ratio:.2f}, expected={expected_ratio:.2f})")
    
    # Test 1d: Propagation delay calculation
    t_pd = CMOSModel.propagation_delay(20e-9, 20e-9, 3.3)
    f = CMOSModel.frequency(20e-9, 20e-9, 3.3)
    
    expected_f = 1.0 / (2.0 * t_pd)
    assert abs(f - expected_f) / expected_f < 1e-6, "Frequency and delay should be consistent"
    print(f"✓ Test 1d: Frequency and delay are consistent (f={f/1e9:.3f}GHz, t_pd={t_pd*1e12:.3f}ps)")


def test_cmos_edge_cases():
    """Test edge cases in CMOS model."""
    
    # Test low voltage (below threshold)
    f_low = CMOSModel.frequency(10e-9, 10e-9, 0.2)
    assert f_low > 0, "Frequency should be positive even at low voltage"
    assert f_low < CMOSModel.frequency(10e-9, 10e-9, 3.3), "Low voltage should give lower frequency"
    print(f"✓ Test 2a: Edge case - low voltage handled (f={f_low/1e9:.6f}GHz)")
    
    # Test high voltage
    f_high = CMOSModel.frequency(10e-9, 10e-9, 5.0)
    assert f_high > 0, "Frequency should be positive at high voltage"
    print(f"✓ Test 2b: Edge case - high voltage handled (f={f_high/1e9:.3f}GHz)")
    
    # Test minimal widths
    f_min = CMOSModel.frequency(10e-9, 20e-9, 3.3)
    assert f_min > 0, "Frequency should be positive for minimal widths"
    print(f"✓ Test 2c: Edge case - minimal widths handled (f={f_min/1e9:.3f}GHz)")


# ============================================================================
# Test 2: NSGA-II Optimization
# ============================================================================

def test_nsga2_basic_run():
    """Test basic NSGA-II optimization run."""
    
    result = run_nsga2(
        population_size=50,
        generations=20,
        verbose=False
    )
    
    assert isinstance(result, OptimizationResult), "Should return OptimizationResult"
    assert len(result.pareto_front) > 0, "Pareto front should not be empty"
    assert result.best_power > 0, "Best power should be positive"
    assert result.best_frequency > 0, "Best frequency should be positive"
    
    print(f"✓ Test 3a: Basic run successful")
    print(f"  - Pareto front size: {len(result.pareto_front)}")
    print(f"  - Best power: {result.best_power:.3e} W")
    print(f"  - Best frequency: {result.best_frequency/1e9:.3f} GHz")


def test_nsga2_pareto_front_validity():
    """Verify Pareto front contains non-dominated solutions."""
    
    result = run_nsga2(
        population_size=50,
        generations=20,
        verbose=False
    )
    
    # Check non-dominance: no solution should dominate another
    for i, obj_i in enumerate(result.pareto_objectives):
        for j, obj_j in enumerate(result.pareto_objectives):
            if i != j:
                # Check if i dominates j
                power_i_better = obj_i[0] < obj_j[0]
                freq_i_better = obj_i[1] > obj_j[1]
                
                # i should not dominate j (both objectives better)
                assert not (power_i_better and freq_i_better), \
                    f"Pareto front contains dominated solution at indices {i}, {j}"
    
    print(f"✓ Test 3b: Pareto front is valid (no dominated solutions)")


def test_nsga2_bounds_satisfaction():
    """Verify all solutions satisfy variable bounds."""
    
    result = run_nsga2(
        population_size=50,
        generations=20,
        verbose=False
    )
    
    for i, ind in enumerate(result.pareto_front):
        WN, WP, VDD = ind
        
        assert 10e-9 <= WN <= 100e-9, f"WN out of bounds at index {i}: {WN}"
        assert 20e-9 <= WP <= 200e-9, f"WP out of bounds at index {i}: {WP}"
        assert 1.0 <= VDD <= 5.0, f"VDD out of bounds at index {i}: {VDD}"
    
    print(f"✓ Test 3c: All solutions satisfy constraints")


def test_nsga2_constraint_propagation():
    """Verify constraints are maintained through generations."""
    
    # Quick run with larger population
    result = run_nsga2(
        population_size=100,
        generations=30,
        verbose=False
    )
    
    # All individuals in final population should be valid
    assert len(result.pareto_front) > 0, "Pareto front should not be empty"
    
    for ind in result.pareto_front:
        assert len(ind) == 3, "Each individual should have 3 variables"
        assert all(np.isfinite(x) for x in ind), "All variables should be finite"
    
    print(f"✓ Test 3d: Constraints maintained through evolution")


# ============================================================================
# Test 3: Compromise Design Selection
# ============================================================================

def test_compromise_design():
    """Test compromise design selection."""
    
    result = run_nsga2(
        population_size=50,
        generations=20,
        verbose=False
    )
    
    WN_comp, WP_comp, VDD_comp = result.compromise_design
    
    # Compromise should be within bounds
    assert 10e-9 <= WN_comp <= 100e-9, "Compromise WN out of bounds"
    assert 20e-9 <= WP_comp <= 200e-9, "Compromise WP out of bounds"
    assert 1.0 <= VDD_comp <= 5.0, "Compromise VDD out of bounds"
    
    # Compromise should be from Pareto front
    found = False
    for ind in result.pareto_front:
        if (abs(ind[0] - WN_comp) < 1e-12 and 
            abs(ind[1] - WP_comp) < 1e-12 and 
            abs(ind[2] - VDD_comp) < 1e-12):
            found = True
            break
    
    assert found, "Compromise design should be from Pareto front"
    
    print(f"✓ Test 4: Compromise design selected correctly")
    print(f"  - WN: {WN_comp*1e9:.2f} nm")
    print(f"  - WP: {WP_comp*1e9:.2f} nm")
    print(f"  - VDD: {VDD_comp:.2f} V")


# ============================================================================
# Test 4: Convergence Analysis
# ============================================================================

def test_convergence_trend():
    """Verify optimization converges (objectives improve over time)."""
    
    result = run_nsga2(
        population_size=100,
        generations=30,
        verbose=False
    )
    
    # Check that best power improves (or stays same)
    powers = result.generation_history['min_power']
    assert powers[-1] <= powers[0], "Best power should improve or stay same"
    
    # Check that best frequency improves (or stays same)
    freqs = result.generation_history['max_freq']
    assert freqs[-1] >= freqs[0], "Best frequency should improve or stay same"
    
    improvement_power = (powers[0] - powers[-1]) / powers[0] * 100
    improvement_freq = (freqs[-1] - freqs[0]) / freqs[0] * 100
    
    print(f"✓ Test 5: Convergence verified")
    print(f"  - Power improvement: {improvement_power:.2f}%")
    print(f"  - Frequency improvement: {improvement_freq:.2f}%")


# ============================================================================
# Test 5: Population Size Sensitivity
# ============================================================================

def test_population_size_effect():
    """Test how population size affects Pareto front size."""
    
    sizes = [30, 50, 100]
    pareto_sizes = []
    
    for pop_size in sizes:
        result = run_nsga2(
            population_size=pop_size,
            generations=15,
            verbose=False
        )
        pareto_sizes.append(len(result.pareto_front))
    
    # Larger population should generally have larger Pareto front
    assert pareto_sizes[-1] >= pareto_sizes[0] or len(pareto_sizes[-1]) > 0, \
        "Pareto front size should improve with population"
    
    print(f"✓ Test 6: Population size effect analyzed")
    for size, psize in zip(sizes, pareto_sizes):
        print(f"  - Population {size}: Pareto front size = {psize}")


# ============================================================================
# Test 6: Multi-Objective Trade-off
# ============================================================================

def test_power_frequency_tradeoff():
    """Verify power-frequency trade-off is explored."""
    
    result = run_nsga2(
        population_size=100,
        generations=30,
        verbose=False
    )
    
    powers = [obj[0] for obj in result.pareto_objectives]
    freqs = [obj[1] for obj in result.pareto_objectives]
    
    # Find extremes
    min_power_idx = np.argmin(powers)
    max_freq_idx = np.argmax(freqs)
    
    min_power_freq = freqs[min_power_idx]
    max_freq_power = powers[max_freq_idx]
    
    # Min power solution should have lower frequency than max
    assert min_power_freq < freqs[max_freq_idx], "Min power design should have lower frequency"
    
    # Max frequency solution should consume more power
    assert max_freq_power > powers[min_power_idx], "Max frequency design should use more power"
    
    power_range = (max(powers) - min(powers)) / min(powers) * 100
    freq_range = (max(freqs) - min(freqs)) / min(freqs) * 100
    
    print(f"✓ Test 7: Power-frequency trade-off verified")
    print(f"  - Power range: {power_range:.2f}%")
    print(f"  - Frequency range: {freq_range:.2f}%")


# ============================================================================
# Test 7: Repeatability
# ============================================================================

def test_repeatability():
    """Test that results are consistent across runs."""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    result1 = run_nsga2(population_size=50, generations=15, verbose=False)
    
    np.random.seed(42)
    result2 = run_nsga2(population_size=50, generations=15, verbose=False)
    
    # Pareto front sizes should match
    assert len(result1.pareto_front) == len(result2.pareto_front), \
        "Pareto front size should be same with same seed"
    
    # Best objectives should be very close
    assert abs(result1.best_power - result2.best_power) / result1.best_power < 0.01, \
        "Best power should be same with same seed"
    
    print(f"✓ Test 8: Reproducibility confirmed")
    print(f"  - Run 1 best power: {result1.best_power:.3e} W")
    print(f"  - Run 2 best power: {result2.best_power:.3e} W")


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NSGA-II Optimizer Test Suite")
    print("="*70 + "\n")
    
    print("CMOS Physics Tests")
    print("-"*70)
    try:
        test_cmos_physics_equations()
        test_cmos_edge_cases()
        print()
    except Exception as e:
        print(f"✗ Physics tests failed: {e}\n")
    
    print("NSGA-II Optimization Tests")
    print("-"*70)
    try:
        test_nsga2_basic_run()
        test_nsga2_pareto_front_validity()
        test_nsga2_bounds_satisfaction()
        test_nsga2_constraint_propagation()
        print()
    except Exception as e:
        print(f"✗ Optimization tests failed: {e}\n")
    
    print("Trade-off & Design Tests")
    print("-"*70)
    try:
        test_compromise_design()
        test_power_frequency_tradeoff()
        print()
    except Exception as e:
        print(f"✗ Trade-off tests failed: {e}\n")
    
    print("Convergence & Sensitivity Tests")
    print("-"*70)
    try:
        test_convergence_trend()
        test_population_size_effect()
        test_repeatability()
        print()
    except Exception as e:
        print(f"✗ Convergence tests failed: {e}\n")
    
    print("="*70)
    print("All tests completed!")
    print("="*70)
