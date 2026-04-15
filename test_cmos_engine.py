"""
CMOS Simulation Engine - Advanced Usage Guide & Test Suite

Includes:
- Batch processing with different operational modes
- Performance benchmarking
- Real-world device simulations
- Integration with optimization frameworks
"""

import numpy as np
import time
from cmos_simulation_engine import CMOSEngine, CMOSResults


# ============================================================================
# ADVANCED EXAMPLES
# ============================================================================

def example_batch_processing():
    """Process multiple device batches efficiently."""
    print("\n" + "="*70)
    print("BATCH PROCESSING - Multiple Device Families")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=1.8)
    
    # Simulate different process nodes
    process_nodes = {
        '7nm': {'C_range': (0.1e-12, 1e-12), 'Id_range': (10e-3, 50e-3)},
        '5nm': {'C_range': (0.05e-12, 0.5e-12), 'Id_range': (20e-3, 100e-3)},
        '3nm': {'C_range': (0.02e-12, 0.2e-12), 'Id_range': (50e-3, 200e-3)},
    }
    
    for node, params in process_nodes.items():
        C_min, C_max = params['C_range']
        Id_min, Id_max = params['Id_range']
        
        C = np.linspace(C_min, C_max, 10)
        Id = np.linspace(Id_min, Id_max, 10)
        
        results = engine.simulate(C, Id)
        
        print(f"\n{node} Process Node:")
        print(f"  Frequency: {results.frequency.mean():.3f} GHz (±{results.frequency.std():.3f})")
        print(f"  Power: {results.power.mean():.3f} mW (±{results.power.std():.3f})")
        print(f"  Delay: {results.delay.mean():.3f} ns (±{results.delay.std():.3f})")


def example_performance_benchmark():
    """Benchmark vectorization performance."""
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARK - Vectorization vs Scalar")
    print("="*70)
    
    engine = CMOSEngine()
    n_samples = 1_000_000
    
    C = np.random.uniform(1e-12, 10e-12, n_samples)
    Id = np.random.uniform(1e-3, 10e-3, n_samples)
    
    # Vectorized (NumPy)
    start = time.perf_counter()
    results = engine.simulate(C, Id)
    vectorized_time = time.perf_counter() - start
    
    # Scalar (Python loop) - only small sample for demo
    n_sample = 10000
    start = time.perf_counter()
    delay_list = []
    freq_list = []
    power_list = []
    for i in range(n_sample):
        VDD = 3.3
        t_pd = (C[i] * VDD) / Id[i]
        f = 1 / t_pd
        p = C[i] * (VDD ** 2) * f
        delay_list.append(t_pd)
        freq_list.append(f)
        power_list.append(p)
    scalar_time = time.perf_counter() - start
    scalar_extrapolated = scalar_time * (n_samples / n_sample)
    
    print(f"Processing {n_samples:,} samples:")
    print(f"  Vectorized (NumPy): {vectorized_time*1000:.2f} ms")
    print(f"  Scalar (Python):    {scalar_extrapolated*1000:.2f} ms (extrapolated)")
    print(f"  Speedup: {scalar_extrapolated/vectorized_time:.1f}x faster")


def example_optimization_workflow():
    """Optimize device dimensions for target frequency and power."""
    print("\n" + "="*70)
    print("OPTIMIZATION - Find optimal C and Id for target specs")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    target_freq = 1.0  # GHz
    target_power = 10.0  # mW
    
    # Grid search
    C_values = np.linspace(1e-12, 20e-12, 50)
    Id_values = np.linspace(0.5e-3, 20e-3, 50)
    
    C_grid, Id_grid = np.meshgrid(C_values, Id_values, indexing='ij')
    results = engine.simulate(C_grid, Id_grid)
    
    # Find closest to target
    freq_error = np.abs(results.frequency - target_freq)
    power_error = np.abs(results.power - target_power)
    total_error = freq_error + power_error
    
    min_idx = np.argmin(total_error)
    best_c, best_id = C_grid.flat[min_idx], Id_grid.flat[min_idx]
    best_results = engine.simulate(best_c, best_id)
    
    print(f"Target specs: {target_freq:.2f} GHz @ {target_power:.2f} mW")
    print(f"\nOptimal found:")
    print(f"  C = {best_c*1e12:.3f} pF")
    print(f"  Id = {best_id*1e3:.3f} mA")
    print(f"  Achieved: {best_results.frequency.item():.3f} GHz @ {best_results.power.item():.3f} mW")


def example_temperature_analysis():
    """Analyze impact of temperature-dependent current variation."""
    print("\n" + "="*70)
    print("TEMPERATURE ANALYSIS - Impact on drain current")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    C = 5e-12
    Id_nominal = 2e-3
    
    # Temperature coefficients (simplified)
    temperatures = np.array([0, 25, 50, 75, 100, 125])
    # Typical: current increases ~0.5% per °C
    Id_temp = Id_nominal * (1 + 0.005 * (temperatures - 25))
    
    results = engine.simulate(C, Id_temp)
    
    print(f"Load: {C*1e12:.1f} pF, Temperature range: {temperatures[0]}-{temperatures[-1]}°C")
    print(f"\n{'Temp(°C)':>8} {'Id(mA)':>10} {'Freq(GHz)':>12} {'Delay(ns)':>12} {'Power(mW)':>12}")
    print("-" * 56)
    for i, T in enumerate(temperatures):
        print(f"{T:>8} {Id_temp[i]*1e3:>10.3f} {results.frequency[i]:>12.4f} {results.delay[i]:>12.4f} {results.power[i]:>12.4f}")


def example_supply_voltage_sweep():
    """Analysis across supply voltage variations."""
    print("\n" + "="*70)
    print("SUPPLY VOLTAGE SWEEP - VDD variation analysis")
    print("="*70)
    
    engine = CMOSEngine()
    
    C = 5e-12
    Id = 2e-3
    voltages = np.array([1.5, 1.8, 2.5, 3.3, 5.0])
    
    results = engine.simulate(C, np.full_like(voltages, Id), voltages)
    
    print(f"Fixed: C={C*1e12:.1f}pF, Id={Id*1e3:.1f}mA")
    print(f"\n{'VDD(V)':>8} {'Freq(GHz)':>12} {'Delay(ns)':>12} {'Power(mW)':>12} {'Power/Freq':>15}")
    print("-" * 60)
    for i, v in enumerate(voltages):
        power_per_freq = results.power[i] / results.frequency[i] if results.frequency[i] > 0 else float('inf')
        print(f"{v:>8.1f} {results.frequency[i]:>12.4f} {results.delay[i]:>12.4f} {results.power[i]:>12.4f} {power_per_freq:>15.6f}")


def example_statistical_margins():
    """Compute design margins with manufacturing variations."""
    print("\n" + "="*70)
    print("STATISTICAL MARGINS - Design robustness analysis")
    print("="*70)
    
    engine = CMOSEngine()
    
    # Monte Carlo at nominal
    nominal_results = engine.monte_carlo_analysis(
        C_nominal=5e-12, C_sigma=0.15,
        Id_nominal=2e-3, Id_sigma=0.20,
        samples=100000, seed=42
    )
    
    mean_freq = nominal_results.frequency.mean()
    std_freq = nominal_results.frequency.std()
    
    # Compute margins (3-sigma = 99.7% coverage)
    margin_percent = (std_freq / mean_freq) * 300  # 3*sigma/mean * 100
    worst_case_freq = mean_freq - 3*std_freq
    
    print(f"Nominal: C=5pF (±15%), Id=2mA (±20%)")
    print(f"\nStatistical Results (100k MC samples):")
    print(f"  Mean frequency: {mean_freq:.4f} GHz")
    print(f"  Std deviation: {std_freq:.4f} GHz")
    print(f"  3-Sigma margin: ±{margin_percent:.2f}%")
    print(f"  Worst case (3σ): {worst_case_freq:.4f} GHz")
    print(f"  Yield confidence: 99.7%")


# ============================================================================
# TEST SUITE
# ============================================================================

def run_tests():
    """Comprehensive test suite."""
    print("\n" + "="*70)
    print("TEST SUITE - Validation of CMOS Engine")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    passed = 0
    failed = 0
    
    # Test 1: Scalar simulation
    print("\nTest 1: Scalar simulation...")
    try:
        C, Id = 5e-12, 2e-3
        results = engine.simulate(C, Id)
        # Results can be 0-d arrays or numpy scalars; both are valid
        assert hasattr(results.delay, 'shape')
        assert hasattr(results.frequency, 'shape')
        assert hasattr(results.power, 'shape')
        print("  ✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1
    
    # Test 2: Array simulation
    print("Test 2: Array simulation (broadcasting)...")
    try:
        C = np.array([1e-12, 5e-12, 10e-12])
        Id = np.array([1e-3, 2e-3, 5e-3])
        results = engine.simulate(C, Id)
        assert results.delay.shape == (3,)
        assert np.all(results.frequency > 0)
        print("  ✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 3: Equations correctness
    print("Test 3: Equation verification...")
    try:
        C, Id, VDD = 5e-12, 2e-3, 3.3
        results = engine.simulate(C, Id, VDD)
        
        # Verify equations manually
        expected_delay = (C * VDD) / Id * 1e9  # Convert to ns
        expected_freq = 1 / (expected_delay / 1e9) / 1e9  # Convert to GHz
        expected_power = C * (VDD ** 2) * (1 / (expected_delay / 1e9)) * 1e3  # Convert to mW
        
        assert np.isclose(results.delay.item(), expected_delay, rtol=1e-6)
        assert np.isclose(results.frequency.item(), expected_freq, rtol=1e-6)
        assert np.isclose(results.power.item(), expected_power, rtol=1e-6)
        print("  [PASS] Equations verified correct")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 4: Invalid inputs
    print("Test 4: Error handling (negative values)...")
    try:
        engine.simulate(-5e-12, 2e-3)
        print("  [FAIL] Should reject negative capacitance")
        failed += 1
    except ValueError:
        print("  [PASS] Correctly rejects invalid inputs")
        passed += 1
    
    # Test 5: Broadcasting rules
    print("Test 5: Broadcasting shape compatibility...")
    try:
        C = np.ones((5, 3))
        Id = np.ones((5, 1))
        results = engine.simulate(C, Id)
        assert results.delay.shape == (5, 3)
        print("  [PASS] Broadcasting shape compatibility verified")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 6: Parametric sweep
    print("Test 6: Parametric sweep...")
    try:
        grid, results = engine.parametric_sweep(
            (1e-12, 10e-12, 5),
            (1e-3, 10e-3, 5)
        )
        assert grid.shape == (5, 5, 2)
        assert results.delay.shape == (5, 5)
        print("  [PASS] Parametric sweep working correctly")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Summary
    print("\n" + "-"*70)
    print(f"Tests: {passed} passed, {failed} failed (Total: {passed + failed})")
    print("-"*70)
    
    return failed == 0


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run test suite
    success = run_tests()
    
    # Run advanced examples
    if success:
        example_batch_processing()
        example_performance_benchmark()
        example_optimization_workflow()
        example_temperature_analysis()
        example_supply_voltage_sweep()
        example_statistical_margins()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70)
