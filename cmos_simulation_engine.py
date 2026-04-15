"""
CMOS Simulation Engine - Fast vectorized CMOS device modeling.

Implements key CMOS equations with NumPy vectorization:
- Propagation delay: t_pd = (C * VDD) / Id
- Frequency: f = 1 / t_pd
- Power consumption: P = C * VDD^2 * f

Usage:
    engine = CMOSEngine()
    results = engine.simulate(capacitance, voltage, current)
"""

import numpy as np
from dataclasses import dataclass
from typing import Union, Tuple, Optional


@dataclass
class CMOSResults:
    """Container for CMOS simulation results."""
    delay: np.ndarray          # Propagation delay (nanoseconds)
    frequency: np.ndarray      # Operating frequency (GHz)
    power: np.ndarray          # Power consumption (milliwatts)
    
    def __repr__(self) -> str:
        return (
            f"CMOSResults(\n"
            f"  delay_min={self.delay.min():.4f}ns, "
            f"delay_max={self.delay.max():.4f}ns\n"
            f"  freq_min={self.frequency.min():.4f}GHz, "
            f"freq_max={self.frequency.max():.4f}GHz\n"
            f"  power_min={self.power.min():.4f}mW, "
            f"power_max={self.power.max():.4f}mW\n"
            f")"
        )


class CMOSEngine:
    """
    Vectorized CMOS simulation engine for fast device modeling.
    
    Supports scalar and array inputs with automatic broadcasting.
    All calculations use NumPy for optimal performance.
    """
    
    def __init__(self, default_vdd: float = 3.3):
        """
        Initialize CMOS engine.
        
        Args:
            default_vdd: Default supply voltage in volts (3.3V typical).
        """
        self.default_vdd = default_vdd
        self._validate_positive(default_vdd, "VDD")
    
    @staticmethod
    def _validate_positive(value: Union[float, np.ndarray], name: str) -> None:
        """Validate that value(s) are positive."""
        if isinstance(value, np.ndarray):
            if np.any(value <= 0):
                raise ValueError(f"{name} must be positive, got: {value}")
        else:
            if value <= 0:
                raise ValueError(f"{name} must be positive, got: {value}")
    
    def simulate(
        self,
        capacitance: Union[float, np.ndarray],
        drain_current: Union[float, np.ndarray],
        voltage: Optional[Union[float, np.ndarray]] = None,
    ) -> CMOSResults:
        """
        Simulate CMOS device parameters.
        
        Args:
            capacitance: Load capacitance in farads (scalar or array).
            drain_current: Drain current in amperes (scalar or array).
            voltage: Supply voltage in volts. If None, uses default_vdd.
        
        Returns:
            CMOSResults with delay, frequency, and power arrays.
        
        Raises:
            ValueError: If inputs are invalid or dimensions incompatible.
        
        Example:
            >>> engine = CMOSEngine(default_vdd=3.3)
            >>> C = np.array([1e-12, 2e-12, 5e-12])  # 1-5 pF
            >>> Id = np.array([1e-3, 2e-3, 5e-3])    # 1-5 mA
            >>> results = engine.simulate(C, Id)
            >>> print(results.frequency)
        """
        # Convert inputs to numpy arrays
        C = np.asarray(capacitance, dtype=np.float64)
        Id = np.asarray(drain_current, dtype=np.float64)
        VDD = np.asarray(voltage if voltage is not None else self.default_vdd, dtype=np.float64)
        
        # Validate inputs
        self._validate_positive(C, "Capacitance")
        self._validate_positive(Id, "Drain current")
        self._validate_positive(VDD, "Voltage (VDD)")
        
        # Broadcast shapes
        try:
            shape = np.broadcast_shapes(C.shape, Id.shape, VDD.shape)
        except ValueError as e:
            raise ValueError(f"Input shapes incompatible for broadcasting: {e}")
        
        C = np.broadcast_to(C, shape)
        Id = np.broadcast_to(Id, shape)
        VDD = np.broadcast_to(VDD, shape)
        
        # CMOS Equations (vectorized)
        # t_pd = (C * VDD) / Id
        delay = (C * VDD) / Id  # nanoseconds
        
        # f = 1 / t_pd
        # Guard against division by zero
        frequency = np.divide(
            1.0,
            delay,
            out=np.full_like(delay, np.inf),
            where=delay != 0
        )
        
        # P = C * VDD^2 * f
        power = C * (VDD ** 2) * frequency
        
        # Convert units
        delay_ns = delay * 1e9      # seconds to nanoseconds
        freq_ghz = frequency / 1e9  # Hz to GHz
        power_mw = power * 1e3      # watts to milliwatts
        
        return CMOSResults(
            delay=delay_ns,
            frequency=freq_ghz,
            power=power_mw
        )
    
    def parametric_sweep(
        self,
        capacitance_range: Tuple[float, float, int],
        current_range: Tuple[float, float, int],
        voltage: Optional[float] = None,
    ) -> Tuple[np.ndarray, CMOSResults]:
        """
        Perform parametric sweep over capacitance and current ranges.
        
        Args:
            capacitance_range: (min, max, steps) for capacitance sweep.
            current_range: (min, max, steps) for current sweep.
            voltage: Supply voltage (uses default if None).
        
        Returns:
            Tuple of (parameter_grid, results) where grid is 2D array of (C, Id) pairs.
        
        Example:
            >>> engine = CMOSEngine()
            >>> C_range = (1e-12, 10e-12, 5)    # 1-10 pF, 5 steps
            >>> Id_range = (1e-3, 10e-3, 5)    # 1-10 mA, 5 steps
            >>> grid, results = engine.parametric_sweep(C_range, Id_range)
        """
        C_min, C_max, C_steps = capacitance_range
        Id_min, Id_max, Id_steps = current_range
        
        C_sweep = np.linspace(C_min, C_max, C_steps)
        Id_sweep = np.linspace(Id_min, Id_max, Id_steps)
        
        C_grid, Id_grid = np.meshgrid(C_sweep, Id_sweep, indexing='ij')
        
        results = self.simulate(C_grid, Id_grid, voltage)
        
        return np.stack([C_grid, Id_grid], axis=-1), results
    
    def monte_carlo_analysis(
        self,
        C_nominal: float,
        C_sigma: float,
        Id_nominal: float,
        Id_sigma: float,
        voltage: Optional[float] = None,
        samples: int = 10000,
        seed: Optional[int] = None,
    ) -> CMOSResults:
        """
        Monte Carlo uncertainty analysis with Gaussian variations.
        
        Args:
            C_nominal: Nominal capacitance.
            C_sigma: Capacitance standard deviation (as fraction, e.g., 0.1 = 10%).
            Id_nominal: Nominal drain current.
            Id_sigma: Drain current standard deviation (as fraction).
            voltage: Supply voltage.
            samples: Number of Monte Carlo samples.
            seed: Random seed for reproducibility.
        
        Returns:
            CMOSResults with distributions from MC analysis.
        
        Example:
            >>> engine = CMOSEngine()
            >>> results = engine.monte_carlo_analysis(
            ...     C_nominal=5e-12, C_sigma=0.1,
            ...     Id_nominal=2e-3, Id_sigma=0.15,
            ...     samples=50000, seed=42
            ... )
            >>> print(f"Freq: {results.frequency.mean():.2f} ± {results.frequency.std():.2f} GHz")
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Generate Gaussian distributions
        C_samples = np.random.normal(C_nominal, C_nominal * C_sigma, samples)
        Id_samples = np.random.normal(Id_nominal, Id_nominal * Id_sigma, samples)
        
        # Ensure no negative values
        C_samples = np.abs(C_samples)
        Id_samples = np.abs(Id_samples)
        
        return self.simulate(C_samples, Id_samples, voltage)
    
    def sensitivity_analysis(
        self,
        C_nominal: float,
        Id_nominal: float,
        voltage: Optional[float] = None,
        delta_percent: float = 5.0,
    ) -> dict:
        """
        Compute local sensitivity of outputs to parameter variations.
        
        Args:
            C_nominal: Nominal capacitance.
            Id_nominal: Nominal drain current.
            voltage: Supply voltage.
            delta_percent: Percent variation for sensitivity calculation.
        
        Returns:
            Dictionary with sensitivities for each output.
        
        Example:
            >>> engine = CMOSEngine()
            >>> sens = engine.sensitivity_analysis(5e-12, 2e-3)
            >>> print(f"Delay sensitivity to C: {sens['delay']['C']:.3f}")
        """
        delta = delta_percent / 100.0
        
        # Nominal point
        nominal = self.simulate(C_nominal, Id_nominal, voltage)
        
        # Perturbed: capacitance +5%
        C_plus = self.simulate(C_nominal * (1 + delta), Id_nominal, voltage)
        # Perturbed: capacitance -5%
        C_minus = self.simulate(C_nominal * (1 - delta), Id_nominal, voltage)
        
        # Perturbed: current +5%
        Id_plus = self.simulate(C_nominal, Id_nominal * (1 + delta), voltage)
        # Perturbed: current -5%
        Id_minus = self.simulate(C_nominal, Id_nominal * (1 - delta), voltage)
        
        # Central difference sensitivities
        return {
            'delay': {
                'C': (C_plus.delay - C_minus.delay) / (2 * delta),
                'Id': (Id_plus.delay - Id_minus.delay) / (2 * delta),
            },
            'frequency': {
                'C': (C_plus.frequency - C_minus.frequency) / (2 * delta),
                'Id': (Id_plus.frequency - Id_minus.frequency) / (2 * delta),
            },
            'power': {
                'C': (C_plus.power - C_minus.power) / (2 * delta),
                'Id': (Id_plus.power - Id_minus.power) / (2 * delta),
            }
        }


# ============================================================================
# Utility Functions
# ============================================================================

def quick_simulate(
    capacitance: Union[float, np.ndarray],
    drain_current: Union[float, np.ndarray],
    voltage: float = 3.3,
) -> CMOSResults:
    """
    Quick access function for one-off simulations.
    
    Args:
        capacitance: Load capacitance in farads.
        drain_current: Drain current in amperes.
        voltage: Supply voltage in volts (default: 3.3V).
    
    Returns:
        CMOSResults object.
    """
    engine = CMOSEngine(default_vdd=voltage)
    return engine.simulate(capacitance, drain_current)


if __name__ == "__main__":
    # ========================================================================
    # Example Usage & Demonstrations
    # ========================================================================
    
    print("=" * 70)
    print("CMOS SIMULATION ENGINE - DEMONSTRATION")
    print("=" * 70)
    
    # Initialize engine
    engine = CMOSEngine(default_vdd=3.3)
    
    # Example 1: Single point simulation
    print("\n1. SINGLE POINT SIMULATION")
    print("-" * 70)
    C = 5e-12  # 5 pF
    Id = 2e-3  # 2 mA
    results = engine.simulate(C, Id)
    print(f"Input: C={C*1e12:.1f}pF, Id={Id*1e3:.1f}mA")
    print(f"Results:")
    print(f"  Delay: {results.delay.item():.4f} ns")
    print(f"  Frequency: {results.frequency.item():.4f} GHz")
    print(f"  Power: {results.power.item():.4f} mW")
    
    # Example 2: Array simulation (vectorized)
    print("\n2. VECTORIZED ARRAY SIMULATION")
    print("-" * 70)
    C_array = np.array([1e-12, 3e-12, 5e-12, 10e-12])  # 1-10 pF
    Id_array = np.array([1e-3, 2e-3, 3e-3, 5e-3])      # 1-5 mA
    results = engine.simulate(C_array, Id_array)
    print(f"Simulating {len(C_array)} devices:")
    for i in range(len(C_array)):
        print(f"  Device {i+1}: C={C_array[i]*1e12:.1f}pF, Id={Id_array[i]*1e3:.1f}mA")
        print(f"    → Delay: {results.delay[i]:.4f}ns, Freq: {results.frequency[i]:.4f}GHz, Power: {results.power[i]:.4f}mW")
    
    # Example 3: Parametric sweep
    print("\n3. PARAMETRIC SWEEP (5x5 grid)")
    print("-" * 70)
    C_range = (1e-12, 10e-12, 5)
    Id_range = (1e-3, 10e-3, 5)
    grid, results = engine.parametric_sweep(C_range, Id_range)
    print(f"Frequency range: {results.frequency.min():.4f} - {results.frequency.max():.4f} GHz")
    print(f"Power range: {results.power.min():.4f} - {results.power.max():.4f} mW")
    print(f"Delay range: {results.delay.min():.4f} - {results.delay.max():.4f} ns")
    
    # Example 4: Monte Carlo analysis
    print("\n4. MONTE CARLO ANALYSIS (50k samples)")
    print("-" * 70)
    mc_results = engine.monte_carlo_analysis(
        C_nominal=5e-12,
        C_sigma=0.1,        # 10% std dev
        Id_nominal=2e-3,
        Id_sigma=0.15,      # 15% std dev
        samples=50000,
        seed=42
    )
    print(f"Frequency: {mc_results.frequency.mean():.4f} ± {mc_results.frequency.std():.4f} GHz")
    print(f"Power: {mc_results.power.mean():.4f} ± {mc_results.power.std():.4f} mW")
    print(f"Delay: {mc_results.delay.mean():.4f} ± {mc_results.delay.std():.4f} ns")
    
    # Example 5: Sensitivity analysis
    print("\n5. SENSITIVITY ANALYSIS")
    print("-" * 70)
    sensitivity = engine.sensitivity_analysis(
        C_nominal=5e-12,
        Id_nominal=2e-3,
        delta_percent=5.0
    )
    print("Delay sensitivities (nominal point):")
    print(f"  ∂delay/∂C  = {sensitivity['delay']['C']:.6f}")
    print(f"  ∂delay/∂Id = {sensitivity['delay']['Id']:.6f}")
    print("Frequency sensitivities:")
    print(f"  ∂freq/∂C   = {sensitivity['frequency']['C']:.6f}")
    print(f"  ∂freq/∂Id  = {sensitivity['frequency']['Id']:.6f}")
    print("Power sensitivities:")
    print(f"  ∂power/∂C  = {sensitivity['power']['C']:.6f}")
    print(f"  ∂power/∂Id = {sensitivity['power']['Id']:.6f}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
