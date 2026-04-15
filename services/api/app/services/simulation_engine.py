"""Realistic MOSFET-based circuit simulator."""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import numpy as np
from datetime import datetime


@dataclass
class MOSFETParams:
    """MOSFET device parameters."""
    wn: float  # nMOS width (nm)
    wp: float  # pMOS width (nm)
    vdd: float  # Supply voltage (V)
    vth_n: float = 0.35  # nMOS threshold voltage (V)
    vth_p: float = -0.35  # pMOS threshold voltage (V)
    cl: float = 1e-12  # Load capacitance (F)
    temp: float = 27  # Temperature (C)
    tox: float = 1.2e-9  # Gate oxide thickness (m)
    cox: float = 2.5e-3  # Gate oxide capacitance (F/m^2)
    u0: float = 350e-4  # Mobility at 27C (m^2/V·s)
    lambda_param: float = 0.05  # Channel length modulation


class CircuitSimulator:
    """MOSFET-based circuit simulator with realistic physics."""
    
    def __init__(self, params: MOSFETParams):
        """Initialize simulator with device parameters."""
        self.params = params
        self._calculate_derived_params()
    
    def _calculate_derived_params(self):
        """Calculate derived parameters from base params."""
        # Transconductance parameter
        self.kn = self.params.cox * self.params.u0 * (self.params.wn / 1e-9)
        self.kp = self.params.cox * self.params.u0 * (self.params.wp / 1e-9)
        
        # Temperature effects on threshold voltage
        temp_coeff = 2e-4  # V/K
        self.vth_n = self.params.vth_n + temp_coeff * (self.params.temp - 27)
        self.vth_p = self.params.vth_p - temp_coeff * (self.params.temp - 27)
        
        # Mobility degradation with temperature
        self.u_temp = self.params.u0 * ((self.params.temp + 273) / 300) ** (-1.5)
    
    def drain_current(self, vgs: float, vds: float, is_pmos: bool = False) -> float:
        """
        Calculate drain current using MOSFET model.
        Id = (k/2) * (W/L) * (Vgs - Vth)^2 * (1 + lambda * Vds)
        """
        if is_pmos:
            vth = self.vth_p
            k = self.kp
        else:
            vth = self.vth_n
            k = self.kn
        
        # Saturation check
        vgs_eff = abs(vgs - vth)
        if vgs_eff <= 0:
            return 0.0  # Device off
        
        # Linear vs saturation region
        vds_sat = vgs_eff * 0.8  # Approximate saturation voltage
        
        if abs(vds) < vds_sat:
            # Linear region
            id_lat = (k / 2) * (vgs_eff ** 2) + k * vgs_eff * abs(vds) - (k / 2) * (abs(vds) ** 2)
        else:
            # Saturation region
            id_lat = (k / 2) * (vgs_eff ** 2) * (1 + self.params.lambda_param * abs(vds))
        
        return max(0.0, id_lat)
    
    def transconductance(self, vgs: float, is_pmos: bool = False) -> float:
        """Calculate transconductance gm = dId/dVgs."""
        if is_pmos:
            vth = self.vth_p
            k = self.kp
        else:
            vth = self.vth_n
            k = self.kn
        
        vgs_eff = abs(vgs - vth)
        if vgs_eff <= 0:
            return 0.0
        
        gm = k * vgs_eff
        return gm
    
    def output_impedance(self, vds: float, is_pmos: bool = False) -> float:
        """Calculate output impedance ro = 1/(lambda * Id)."""
        # Get current at this Vds
        if is_pmos:
            vgs = self.params.vdd + self.vth_p
        else:
            vgs = self.vth_n + (self.params.vdd / 2)
        
        id_q = self.drain_current(vgs, vds, is_pmos)
        if id_q < 1e-9:
            return 1e9  # Very high impedance
        
        ro = 1.0 / (self.params.lambda_param * id_q)
        return ro
    
    def simulate_inverter(self) -> Dict[str, float]:
        """Simulate CMOS inverter DC characteristics."""
        # Operating point: input at VDD/2
        vin = self.params.vdd / 2
        
        # nMOS: Vgs = Vin, Vds = Vout
        # pMOS: Vgs = Vin - VDD, Vds = Vout - VDD
        
        # Iteratively solve for output voltage
        vout = self.params.vdd / 2
        for _ in range(10):  # Convergence iterations
            in_nmos = vin
            vds_nmos = vout
            id_n = self.drain_current(in_nmos, vds_nmos, is_pmos=False)
            
            vgs_pmos = vin - self.params.vdd
            vds_pmos = vout - self.params.vdd
            id_p = self.drain_current(vgs_pmos, vds_pmos, is_pmos=True)
            
            # Current balance: Id_n = Id_p at equilibrium
            if abs(id_n - id_p) < 1e-12:
                break
            
            # Adjust Vout
            if id_n > id_p:
                vout -= 0.01
            else:
                vout += 0.01
            vout = max(0, min(self.params.vdd, vout))
        
        # Calculate gain at operating point
        gm_n = self.transconductance(vin, is_pmos=False)
        gm_p = self.transconductance(vin - self.params.vdd, is_pmos=True)
        ro_n = self.output_impedance(vout, is_pmos=False)
        ro_p = self.output_impedance(vout - self.params.vdd, is_pmos=True)
        
        # Gain: Av = -gm * (ro_n || ro_p)
        ro_eq = (ro_n * ro_p) / (ro_n + ro_p) if (ro_n + ro_p) > 0 else 0
        gain = -gm_n * ro_eq if gm_n > 0 else 0
        
        return {
            "vout": vout,
            "id_n": id_n,
            "id_p": id_p,
            "gm": gm_n,
            "gain": abs(gain),
            "ro": ro_eq,
        }
    
    def calculate_delay(self) -> float:
        """Calculate propagation delay using RC model."""
        # RC delay: tau = R * C
        # Estimate resistance from transconductance
        inv_sim = self.simulate_inverter()
        gm = inv_sim.get("gm", 1e-5)
        
        if gm > 0:
            r_est = 1.0 / (gm * 10)  # Approximate resistance
        else:
            r_est = 1e6
        
        tau = r_est * self.params.cl
        # Delay = ln(2) * tau ≈ 0.69 * tau
        delay = 0.69 * tau
        return delay
    
    def calculate_power(self) -> Dict[str, float]:
        """Calculate power dissipation."""
        inv_sim = self.simulate_inverter()
        id_static = inv_sim.get("id_n", 0)  # Quiescent current
        
        # Static power: P_static = Vdd * I_leak
        p_static = self.params.vdd * id_static
        
        # Dynamic power: P_dynamic = C_l * Vdd^2 * f
        # Assume 1 MHz for calculation
        frequency = 1e6
        p_dynamic = self.params.cl * (self.params.vdd ** 2) * frequency
        
        # Short-circuit power (approximate)
        p_short = 0.1 * p_dynamic
        
        return {
            "static": p_static,
            "dynamic": p_dynamic,
            "short_circuit": p_short,
            "total": p_static + p_dynamic + p_short,
        }
    
    def calculate_ring_oscillator_freq(self, num_stages: int = 5) -> float:
        """
        Estimate frequency of ring oscillator.
        f = 1 / (2 * N * tpd)
        """
        delay = self.calculate_delay()
        # Ring oscillator frequency
        freq = 1.0 / (2.0 * num_stages * delay) if delay > 0 else 0
        return freq
    
    def simulate_aging(self, years: int = 1, hours_per_day: float = 24.0, days_per_year: float = 365.0) -> Dict[str, Any]:
        """
        Simulate aging effects (NBTI, HCI) over extended operation.
        
        Returns:
        - Baseline metrics
        - Degraded metrics after aging
        - Health score (0-100)
        """
        # Get baseline metrics
        baseline_delay = self.calculate_delay()
        baseline_power = self.calculate_power()
        baseline_inv = self.simulate_inverter()
        baseline_gain = baseline_inv.get("gain", 0)
        baseline_freq = self.calculate_ring_oscillator_freq()
        
        # Vth margin calculation
        vgs_eff = (self.params.vdd / 2) - self.vth_n
        vth_margin_initial = vgs_eff  # In volts
        
        # NBTI degradation (Vth increases)
        # ΔVth = K * t^n, where n ≈ 0.16 for long-term aging
        total_hours = years * hours_per_day * days_per_year
        nbti_constant = 5e-4  # Empirical constant (V/hour^0.16)
        n_nbti = 0.16
        delta_vth_nbti = nbti_constant * (total_hours ** n_nbti)
        
        # HCI degradation (Vth shifts, negative)
        hci_constant = 1e-4  # Empirical constant
        n_hci = 0.5
        delta_vth_hci = -hci_constant * (total_hours ** n_hci)
        
        # Total Vth shift
        total_vth_shift = delta_vth_nbti + delta_vth_hci
        
        # Update Vth and recalculate
        degraded_params = MOSFETParams(
            wn=self.params.wn,
            wp=self.params.wp,
            vdd=self.params.vdd,
            vth_n=self.vth_n + total_vth_shift,  # Increased threshold
            vth_p=self.vth_p - total_vth_shift,
            cl=self.params.cl,
            temp=self.params.temp,
        )
        
        degraded_sim = CircuitSimulator(degraded_params)
        degraded_delay = degraded_sim.calculate_delay()
        degraded_power = degraded_sim.calculate_power()
        degraded_inv = degraded_sim.simulate_inverter()
        degraded_gain = degraded_inv.get("gain", 0)
        degraded_freq = degraded_sim.calculate_ring_oscillator_freq()
        
        # Updated Vth margin
        vgs_eff_degraded = (self.params.vdd / 2) - degraded_sim.vth_n
        vth_margin_degraded = vgs_eff_degraded
        
        # Health score based on performance retention
        freq_retention = (degraded_freq / baseline_freq) * 100 if baseline_freq > 0 else 0
        power_increase = ((degraded_power["total"] - baseline_power["total"]) / baseline_power["total"]) * 100 if baseline_power["total"] > 0 else 0
        vth_margin_retention = (vth_margin_degraded / vth_margin_initial) * 100 if vth_margin_initial > 0 else 0
        
        # Health score: lower is worse
        health_score = (freq_retention * 0.4 + (100 - power_increase) * 0.3 + vth_margin_retention * 0.3)
        health_score = max(0, min(100, health_score))
        
        return {
            "years": years,
            "total_hours": total_hours,
            "baseline": {
                "frequency": baseline_freq,
                "delay": baseline_delay,
                "power": baseline_power["total"],
                "gain": baseline_gain,
                "vth_margin": vth_margin_initial,
            },
            "degraded": {
                "frequency": degraded_freq,
                "delay": degraded_delay,
                "power": degraded_power["total"],
                "gain": degraded_gain,
                "vth_margin": vth_margin_degraded,
            },
            "degradation": {
                "nbti": delta_vth_nbti,
                "hci": delta_vth_hci,
                "total_vth_shift": total_vth_shift,
                "freq_degradation_pct": ((baseline_freq - degraded_freq) / baseline_freq) * 100 if baseline_freq > 0 else 0,
                "power_increase_pct": power_increase,
            },
            "health_score": health_score,
        }
    
    def simulate(self, include_aging_years: Optional[int] = None) -> Dict[str, Any]:
        """Run complete simulation."""
        inv_sim = self.simulate_inverter()
        delay = self.calculate_delay()
        power = self.calculate_power()
        freq = self.calculate_ring_oscillator_freq()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "wn": self.params.wn,
                "wp": self.params.wp,
                "vdd": self.params.vdd,
                "cl": self.params.cl,
                "temp": self.params.temp,
            },
            "metrics": {
                "frequency": freq,
                "delay": delay,
                "power": power["total"],
                "gain": inv_sim.get("gain", 0),
            },
            "details": {
                "inverter": inv_sim,
                "power_breakdown": power,
            },
        }
        
        if include_aging_years:
            aging_data = self.simulate_aging(years=include_aging_years)
            results["aging"] = aging_data
            results["health_score"] = aging_data["health_score"]
        
        return results


def create_simulator(params_dict: Dict[str, Any]) -> CircuitSimulator:
    """Factory function to create simulator from dict."""
    params = MOSFETParams(
        wn=params_dict.get("wn", 500),
        wp=params_dict.get("wp", 1000),
        vdd=params_dict.get("vdd", 1.2),
        cl=params_dict.get("cl", 1e-12),
        temp=params_dict.get("temp", 27),
    )
    return CircuitSimulator(params)
