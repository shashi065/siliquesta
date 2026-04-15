"""
CMOS Simulation Engine - Real-World Usage Examples

Copy-paste ready examples for common use cases.
"""

import numpy as np
from cmos_simulation_engine import CMOSEngine


# ============================================================================
# EXAMPLE 1: Basic Device Simulation
# ============================================================================

def example_basic():
    """Simulate a single CMOS logic gate."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Logic Gate Simulation")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    # NAND gate parameters
    C_load = 5e-12      # 5 pF load capacitance
    Id = 2e-3          # 2 mA drain current
    
    results = engine.simulate(C_load, Id)
    
    print(f"\nNAND Gate Performance:")
    print(f"  Load Capacitance: {C_load*1e12:.1f} pF")
    print(f"  Drain Current: {Id*1e3:.1f} mA")
    print(f"  Supply Voltage: 3.3 V")
    print(f"\n  Results:")
    print(f"    Propagation Delay: {results.delay.item():.4f} ns")
    print(f"    Max Frequency: {results.frequency.item():.4f} GHz")
    print(f"    Power @ 100MHz: {(results.power * 0.1).item():.4f} mW")


# ============================================================================
# EXAMPLE 2: Logic Cell Library Characterization
# ============================================================================

def example_cell_library():
    """Characterize timing for different logic cells."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Standard Cell Library Characterization")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    # Different cell types
    cells = {
        'INV': {'C': 2e-12, 'Id': 1e-3},       # Inverter
        'NAND2': {'C': 5e-12, 'Id': 2e-3},     # 2-input NAND
        'NOR2': {'C': 5e-12, 'Id': 1.5e-3},    # 2-input NOR
        'MUX2': {'C': 8e-12, 'Id': 3e-3},      # 2:1 Mux
        'DFF': {'C': 15e-12, 'Id': 5e-3},      # D Flip-Flop
    }
    
    print(f"\n{'Cell':>8} {'Cap (pF)':>12} {'Id (mA)':>12} {'Delay (ns)':>14} {'Freq (GHz)':>14}")
    print("-" * 64)
    
    for cell_name, params in cells.items():
        C, Id = params['C'], params['Id']
        results = engine.simulate(C, Id)
        delay = results.delay.item()
        freq = results.frequency.item()
        print(f"{cell_name:>8} {C*1e12:>12.1f} {Id*1e3:>12.1f} {delay:>14.4f} {freq:>14.4f}")


# ============================================================================
# EXAMPLE 3: Power Consumption Analysis
# ============================================================================

def example_power_analysis():
    """Analyze power at different operating frequencies."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Power Consumption vs Frequency")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    C = 5e-12  # Fixed 5pF load
    
    # Different operating points (varying Id changes frequency)
    operating_points = {
        'Standby (50MHz)': 0.33e-3,
        'Normal (500MHz)': 3.3e-3,
        'Boost (1GHz)': 6.6e-3,
        'Max (2GHz)': 13.2e-3,
    }
    
    print(f"\nPower Analysis (5 pF load):\n")
    print(f"{'Mode':>20} {'Id (mA)':>12} {'Freq (GHz)':>14} {'Power (mW)':>14}")
    print("-" * 62)
    
    for mode, Id in operating_points.items():
        results = engine.simulate(C, Id)
        freq = results.frequency.item()
        power = results.power.item()
        print(f"{mode:>20} {Id*1e3:>12.2f} {freq:>14.4f} {power:>14.4f}")


# ============================================================================
# EXAMPLE 4: Temperature-Dependent Performance
# ============================================================================

def example_temperature_scaling():
    """Model frequency/power changes with temperature."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Temperature Scaling")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    C = 5e-12
    Id_nominal = 2e-3
    
    # Temperature range (0°C to 125°C)
    # Current increases ~0.5% per °C (CMOS behavior)
    temperatures = np.linspace(0, 125, 6)
    Id_array = Id_nominal * (1 + 0.005 * (temperatures - 25))
    
    results = engine.simulate(C, Id_array)
    
    print(f"\nTemperature Effects (5pF load, 2mA nominal @25°C):\n")
    print(f"{'Temp (°C)':>12} {'Id (mA)':>12} {'Freq (GHz)':>14} {'Delay (ns)':>14} {'Power (mW)':>14}")
    print("-" * 70)
    
    for i, T in enumerate(temperatures):
        print(f"{T:>12.0f} {Id_array[i]*1e3:>12.3f} {results.frequency[i]:>14.4f} "
              f"{results.delay[i]:>14.4f} {results.power[i]:>14.4f}")


# ============================================================================
# EXAMPLE 5: Design Space Exploration
# ============================================================================

def example_design_space():
    """Find optimal device sizes for specific targets."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Design Space Exploration")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    target_freq = 1.0  # GHz
    target_power = 10.0  # mW
    
    print(f"\nTarget Specifications:")
    print(f"  Frequency: {target_freq} GHz")
    print(f"  Power: {target_power} mW")
    
    # Grid search
    C_values = np.linspace(1e-12, 20e-12, 50)
    Id_values = np.linspace(0.5e-3, 20e-3, 50)
    C_grid, Id_grid = np.meshgrid(C_values, Id_values, indexing='ij')
    
    results = engine.simulate(C_grid, Id_grid)
    
    # Find multiple design points
    freq_error = np.abs(results.frequency - target_freq)
    power_error = np.abs(results.power - target_power)
    combined_error = freq_error + power_error
    
    # Get best 5 solutions
    best_indices = np.argsort(combined_error.flat)[:5]
    
    print(f"\nTop 5 Design Solutions:")
    print(f"{'#':>3} {'C (pF)':>10} {'Id (mA)':>10} {'Freq (GHz)':>12} {'Power (mW)':>12} {'Error':>10}")
    print("-" * 60)
    
    for rank, idx in enumerate(best_indices, 1):
        c, idd = C_grid.flat[idx], Id_grid.flat[idx]
        freq = results.frequency.flat[idx]
        power = results.power.flat[idx]
        error = combined_error.flat[idx]
        print(f"{rank:>3} {c*1e12:>10.2f} {idd*1e3:>10.2f} {freq:>12.4f} {power:>12.4f} {error:>10.4f}")


# ============================================================================
# EXAMPLE 6: Monte Carlo Yield Analysis
# ============================================================================

def example_monte_carlo_yield():
    """Estimate yield with manufacturing variations."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Yield Analysis with Monte Carlo")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    # Device specifications
    C_nominal = 5e-12
    C_variation = 0.15  # ±15%
    Id_nominal = 2e-3
    Id_variation = 0.20  # ±20%
    
    # Constraint: frequency must be >= 0.8 GHz
    freq_min = 0.8  # GHz
    
    print(f"\nProcess Variations:")
    print(f"  Capacitance: {C_nominal*1e12:.1f} pF ±{C_variation*100:.0f}%")
    print(f"  Drain Current: {Id_nominal*1e3:.1f} mA ±{Id_variation*100:.0f}%")
    print(f"  Spec: Frequency >= {freq_min} GHz")
    
    # Run Monte Carlo
    results = engine.monte_carlo_analysis(
        C_nominal=C_nominal,
        C_sigma=C_variation,
        Id_nominal=Id_nominal,
        Id_sigma=Id_variation,
        samples=100000,
        seed=42
    )
    
    # Calculate yield
    yield_percent = (np.sum(results.frequency >= freq_min) / len(results.frequency)) * 100
    
    print(f"\nMonte Carlo Results (100k samples):")
    print(f"  Mean Frequency: {results.frequency.mean():.4f} GHz")
    print(f"  Std Dev: {results.frequency.std():.4f} GHz")
    print(f"  Min: {results.frequency.min():.4f} GHz")
    print(f"  Max: {results.frequency.max():.4f} GHz")
    print(f"  Yield: {yield_percent:.2f}% (freq >= {freq_min} GHz)")


# ============================================================================
# EXAMPLE 7: Voltage Scaling for Power Efficiency
# ============================================================================

def example_voltage_scaling():
    """Optimize supply voltage for power-performance tradeoff."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Voltage Scaling - Power vs Performance")
    print("="*70)
    
    engine = CMOSEngine()
    
    C = 5e-12
    Id = 2e-3
    
    # Modern supply voltages
    voltages = np.array([1.2, 1.5, 1.8, 2.5, 3.3, 5.0])
    
    results = engine.simulate(C, np.full_like(voltages, Id), voltages)
    
    print(f"\nSupply Voltage Scaling (5pF, 2mA):\n")
    print(f"{'VDD (V)':>10} {'Freq (GHz)':>12} {'Power (mW)':>12} {'Energy/Op (pJ)':>16} {'PDP':>12}")
    print("-" * 68)
    
    for i, V in enumerate(voltages):
        freq = results.frequency[i]
        power = results.power[i]
        # Energy per operation: Power / Frequency
        energy_per_op = (power / (freq + 1e-10)) if freq > 0 else float('inf')
        # Power-Delay Product: Power * Delay time
        pdp = power * results.delay[i] if freq > 0 else float('inf')
        
        print(f"{V:>10.1f} {freq:>12.4f} {power:>12.4f} {energy_per_op:>16.2f} {pdp:>12.2e}")


# ============================================================================
# EXAMPLE 8: Sensitivity Analysis
# ============================================================================

def example_sensitivity():
    """Understand which parameters affect performance most."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Sensitivity Analysis")
    print("="*70)
    
    engine = CMOSEngine(default_vdd=3.3)
    
    C_nominal = 5e-12
    Id_nominal = 2e-3
    
    # Compute sensitivities
    sensitivities = engine.sensitivity_analysis(
        C_nominal=C_nominal,
        Id_nominal=Id_nominal,
        delta_percent=5.0
    )
    
    print(f"\nSensitivity Analysis (±5% perturbation):")
    print(f"  Nominal: C={C_nominal*1e12:.1f}pF, Id={Id_nominal*1e3:.1f}mA, VDD=3.3V\n")
    
    print("Delay Sensitivity:")
    print(f"  ∂delay/∂C:  {sensitivities['delay']['C']:.6f} (delay increases with C)")
    print(f"  ∂delay/∂Id: {sensitivities['delay']['Id']:.6f} (delay decreases with Id)")
    
    print("\nFrequency Sensitivity:")
    print(f"  ∂freq/∂C:   {sensitivities['frequency']['C']:.8f} (freq decreases with C)")
    print(f"  ∂freq/∂Id:  {sensitivities['frequency']['Id']:.8f} (freq increases with Id)")
    
    print("\nPower Sensitivity:")
    print(f"  ∂power/∂C:  {sensitivities['power']['C']:.6f} (power increases with C)")
    print(f"  ∂power/∂Id: {sensitivities['power']['Id']:.6f} (power increases with Id)")
    
    print("\nConclusions:")
    if abs(sensitivities['delay']['C']) > abs(sensitivities['delay']['Id']):
        print("  • Delay is MORE sensitive to capacitance variations")
    else:
        print("  • Delay is MORE sensitive to current variations")
    
    print("  • Frequency sensitivity mirrors delay sensitivity (inverse relationship)")
    print("  • Power scales with both capacitance and current")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CMOS SIMULATION ENGINE - PRACTICAL EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_basic()
    example_cell_library()
    example_power_analysis()
    example_temperature_scaling()
    example_design_space()
    example_monte_carlo_yield()
    example_voltage_scaling()
    example_sensitivity()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETE")
    print("="*70)
    print("\nFor more information, see CMOS_ENGINE_README.md")
