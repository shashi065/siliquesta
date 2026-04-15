"""
Orchestrator Service Integration Layer
=======================================

Wires the agentic orchestrator to real AI/ML services:
- Digital Twin ML service
- NSGA-II optimizer
- Reliability engine

Handles dependency injection and error recovery.
"""

import logging
from typing import Optional, List, Dict, Any
from app.agentic_orchestrator import CircuitDesign, DesignIntent

logger = logging.getLogger(__name__)


class OrchestratorServiceIntegration:
    """Integration layer connecting orchestrator to actual services"""
    
    def __init__(self):
        """Initialize integration layer"""
        self.digital_twin_service = None
        self.optimizer_service = None
        self.reliability_model = None
        self._initialized = False
        logger.info("✓ OrchestratorServiceIntegration initialized")
    
    async def initialize_services(self, 
                                  digital_twin_service=None,
                                  optimizer_service=None,
                                  reliability_model=None) -> bool:
        """
        Initialize service references.
        
        Args:
            digital_twin_service: Digital Twin ML prediction service
            optimizer_service: NSGA-II optimizer instance
            reliability_model: Reliability degradation model
        
        Returns:
            True if at least one service initialized
        """
        try:
            self.digital_twin_service = digital_twin_service
            self.optimizer_service = optimizer_service
            self.reliability_model = reliability_model
            
            available = sum([
                self.digital_twin_service is not None,
                self.optimizer_service is not None,
                self.reliability_model is not None
            ])
            
            logger.info(f"✓ Services initialized: {available}/3 available")
            self._initialized = available > 0
            return self._initialized
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    async def get_digital_twin_prediction(self, design: CircuitDesign, 
                                         design_intent: DesignIntent) -> Dict[str, Any]:
        """
        Get Digital Twin predictions for a design.
        
        Returns:
            Dictionary with power, frequency, delay, and confidence scores
        """
        try:
            if not self.digital_twin_service:
                logger.warning("Digital Twin service not available, using defaults")
                return self._get_default_prediction(design)
            
            # Call actual service
            prediction = await self.digital_twin_service.predict(
                wn=design.wn,
                wp=design.wp,
                vdd=design.vdd,
                temperature=design.temperature,
                corner=design_intent.corner,
                tech_node=design_intent.tech_node
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Digital Twin prediction failed: {e}, using defaults")
            return self._get_default_prediction(design)
    
    async def get_optimizer_pareto_front(self, 
                                        design_intent: DesignIntent,
                                        population_size: int = 100,
                                        generations: int = 50) -> List[Dict[str, Any]]:
        """
        Get Pareto-optimal designs from NSGA-II optimizer.
        
        Returns:
            List of design dictionaries with performance metrics
        """
        try:
            if not self.optimizer_service:
                logger.warning("Optimizer service not available, generating random designs")
                return self._get_random_pareto_designs(design_intent, population_size)
            
            # Call actual optimizer
            result = await self.optimizer_service.optimize(
                population_size=population_size,
                generations=generations,
                use_ml=True,
                constraints={
                    "max_power": design_intent.max_power,
                    "min_frequency": design_intent.min_frequency,
                }
            )
            
            return result.get("pareto_front", [])
            
        except Exception as e:
            logger.error(f"Optimizer failed: {e}, returning random designs")
            return self._get_random_pareto_designs(design_intent, population_size)
    
    async def get_reliability_analysis(self, design: CircuitDesign,
                                      design_intent: DesignIntent) -> Dict[str, Any]:
        """
        Get device reliability analysis for a design.
        
        Returns:
            Dictionary with reliability_score, device_lifetime, mechanism lifetimes
        """
        try:
            if not self.reliability_model:
                logger.warning("Reliability model not available, using defaults")
                return self._get_default_reliability(design)
            
            # Call actual reliability model
            reliability = self.reliability_model.compute_device_reliability(
                wn=design.wn,
                wp=design.wp,
                vdd=design.vdd,
                temperature=design.temperature
            )
            
            return reliability
            
        except Exception as e:
            logger.error(f"Reliability analysis failed: {e}, using defaults")
            return self._get_default_reliability(design)
    
    # ========================================================================
    # Default implementations for graceful degradation
    # ========================================================================
    
    def _get_default_prediction(self, design: CircuitDesign) -> Dict[str, Any]:
        """Generate default Digital Twin predictions using simple physics models"""
        # Simple CMOS model for fallback
        Wn, Wp = design.wn, design.wp
        Vdd, T = design.vdd, design.temperature
        
        # Saturation current model
        Un = 400  # cm^2/V*s (NMOS mobility)
        Up = 100  # cm^2/V*s (PMOS mobility)
        Cox = 2.0e-3  # F/m^2
        Leff = 28e-9  # m
        
        # Temperature dependency
        T_ref = 27.0
        alpha_u = -0.5  # %/K
        u_n = Un * (1 + (alpha_u / 100) * (T - T_ref))
        u_p = Up * (1 + (alpha_u / 100) * (T - T_ref))
        
        # Drive currents
        I_dn = 0.5 * u_n * Cox * (Wn / Leff) * (Vdd ** 2) * 1e-6  # mA
        I_dp = 0.5 * u_p * Cox * (Wp / Leff) * (Vdd ** 2) * 1e-6  # mA
        
        # Load capacitance
        C_load = 1e-14  # 10 fF
        
        # Propagation delays
        t_pd_fall = (C_load * Vdd) / (I_dn * 1e-3)  # ns
        t_pd_rise = (C_load * Vdd) / (I_dp * 1e-3)  # ns
        t_pd = (t_pd_fall + t_pd_rise) / 2
        
        # Frequency and power
        frequency = 1000 / (2 * t_pd) if t_pd > 0 else 1.0  # MHz
        power = frequency * C_load * Vdd * Vdd * 1e6 * 1e-3  # mW
        
        return {
            "power": max(0.1, power),
            "frequency": max(1.0, frequency),
            "delay": max(0.01, t_pd),
            "power_confidence": 0.7,
            "frequency_confidence": 0.7,
            "delay_confidence": 0.7,
            "model": "fallback_physics_model"
        }
    
    def _get_default_reliability(self, design: CircuitDesign) -> Dict[str, Any]:
        """Generate default reliability analysis"""
        T = design.temperature
        Vdd = design.vdd
        
        # NBTI (PMOS)
        Ea_nbti = 0.05  # eV
        A_nbti = 2.5e-3
        n_nbti = 0.25
        m_nbti = 2.0
        
        # HCI (NMOS)
        Ea_hci = 0.12  # eV
        A_hci = 1.2e-4
        n_hci = 0.3
        
        # EM (Electromigration)
        Ea_em = 0.75  # eV
        A_em = 1e6
        n_em = 2.1
        
        # Boltzmann constant
        k = 8.617e-5  # eV/K
        T_abs = T + 273.15
        
        # Time to failure (10 year reference)
        t_ref = 10  # years
        t_ref_s = t_ref * 365 * 24 * 3600
        
        try:
            # NBTI lifetime
            factor_nbti = (A_nbti * (t_ref_s / t_ref_s) ** n_nbti * 
                          np.exp(Ea_nbti / (k * T_abs)) * (Vdd ** m_nbti))
            nbti_lifetime = (1.0 / factor_nbti) * t_ref if factor_nbti > 0 else 10.0
            
            # HCI lifetime
            factor_hci = (A_hci * (t_ref_s / t_ref_s) ** n_hci * 
                         np.exp(Ea_hci / (k * T_abs)))
            hci_lifetime = (1.0 / factor_hci) * t_ref if factor_hci > 0 else 8.0
            
            # EM lifetime
            factor_em = (A_em * (t_ref_s / t_ref_s) ** n_em * 
                        np.exp(Ea_em / (k * T_abs)))
            em_lifetime = (1.0 / factor_em) * t_ref if factor_em > 0 else 12.0
            
        except:
            nbti_lifetime = 10.0
            hci_lifetime = 8.0
            em_lifetime = 12.0
        
        # Overall reliability = minimum of all mechanisms
        device_lifetime = min(nbti_lifetime, hci_lifetime, em_lifetime)
        
        # Reliability score (normalized to 10 year reference)
        reliability_score = max(0.0, min(1.0, device_lifetime / 10.0))
        
        return {
            "reliability_score": float(reliability_score),
            "device_lifetime": float(device_lifetime),
            "nbti_lifetime": float(nbti_lifetime),
            "hci_lifetime": float(hci_lifetime),
            "em_lifetime": float(em_lifetime),
            "confidence": 0.7,
            "model": "fallback_physics_model"
        }
    
    def _get_random_pareto_designs(self, design_intent: DesignIntent, 
                                   num_designs: int = 20) -> List[Dict[str, Any]]:
        """Generate random Pareto-like designs for testing"""
        import random
        
        designs = []
        for i in range(num_designs):
            wn = random.uniform(*design_intent.wn_range)
            wp = random.uniform(*design_intent.wp_range)
            vdd = random.uniform(*design_intent.vdd_range)
            
            # Simple physics model
            freq = (500 + random.gauss(0, 100)) * (vdd / 1.0)
            power = (50 + random.gauss(0, 20)) / (vdd / 1.0)
            delay = 1000 / freq if freq > 0 else 2.0
            
            designs.append({
                "wn": float(wn),
                "wp": float(wp),
                "vdd": float(vdd),
                "frequency": float(max(1.0, freq)),
                "power": float(max(0.1, power)),
                "delay": float(max(0.01, delay))
            })
        
        return designs


# Global integration instance
_integration: Optional[OrchestratorServiceIntegration] = None


def get_integration() -> OrchestratorServiceIntegration:
    """Get or create global integration instance"""
    global _integration
    if _integration is None:
        _integration = OrchestratorServiceIntegration()
    return _integration


# Import numpy for calculations
import numpy as np
