"""Advanced ML-powered optimization engine using Digital Twin surrogate model.

This replaces brute-force simulation with intelligent ML predictions,
enabling fast optimization with confidence scores.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from scipy.optimize import differential_evolution, minimize

from app.services.digital_twin_ml import DigitalTwinSurrogateService, TwinPrediction

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result from ML-based optimization."""
    optimized_params: Dict[str, float]
    predicted_metrics: Dict[str, float]
    confidence_score: float
    uncertainty: float
    estimated_error_percent: float
    improvement_vs_baseline: Dict[str, float]
    optimization_path: List[Dict[str, Any]] = field(default_factory=list)
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MLOptimizer:
    """ML-powered circuit optimization using digital twin surrogate model."""
    
    def __init__(self, objectives: Optional[Dict[str, float]] = None):
        """Initialize optimizer with objectives.
        
        Args:
            objectives: Weights for multi-objective optimization
                {
                    "freq": 0.4,     # Maximize frequency
                    "power": 0.3,    # Minimize power
                    "delay": 0.1,
                    "efficiency": 0.2,  # Maximize energy efficiency
                }
        """
        self.twin = DigitalTwinSurrogateService()
        self.objectives = objectives or {
            "freq": 0.4,
            "power": 0.3,
            "delay": 0.1,
            "efficiency": 0.2,
        }
        self.optimization_history: List[Dict[str, Any]] = []
        
    def _normalize_objectives(self, freq: float, power: float, delay: float) -> float:
        """Calculate weighted objective score.
        
        Args:
            freq: Frequency in GHz (higher is better)
            power: Power in mW (lower is better)
            delay: Delay in ps (lower is better)
            
        Returns:
            Normalized score (0-1, higher is better)
        """
        # Normalize to typical ranges
        freq_norm = min(freq / 10.0, 1.0)  # Normalize to 10 GHz max
        power_norm = max(1.0 - (power / 100.0), 0.0)  # Normalize to 100 mW max
        delay_norm = max(1.0 - (delay / 1000.0), 0.0)  # Normalize to 1000 ps max
        efficiency_norm = freq_norm / (power_norm + 1e-6) if power_norm > 0 else 0
        
        score = (
            self.objectives.get("freq", 0.0) * freq_norm +
            self.objectives.get("power", 0.0) * power_norm +
            self.objectives.get("delay", 0.0) * delay_norm +
            self.objectives.get("efficiency", 0.0) * min(efficiency_norm / 100.0, 1.0)
        )
        
        return float(np.clip(score, 0.0, 1.0))

    def predict_performance(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float = 27.0,
        cl_ff: float = 10.0,
        tech_node: float = 7.0,
        corner: str = "TT",
    ) -> TwinPrediction:
        """Predict circuit performance using ML model.
        
        Args:
            wn: NMOS width (um)
            wp: PMOS width (um)
            vdd: Supply voltage (V)
            temp: Temperature (C)
            cl_ff: Load capacitance (fF)
            tech_node: Technology node (nm)
            corner: Process corner (SS, TT, FF, etc.)
            
        Returns:
            TwinPrediction with metrics and confidence
        """
        prediction = self.twin.predict_with_confidence(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            tech_node=tech_node,
            corner=corner,
        )
        return prediction

    def _objective_function(
        self,
        params: np.ndarray,
        baseline: Optional[TwinPrediction] = None,
        record_history: bool = True,
    ) -> float:
        """Objective function for optimization (to minimize).
        
        Args:
            params: [wn, wp, vdd, temp, cl_ff, tech_node]
            baseline: Baseline prediction for comparison
            record_history: Whether to record this evaluation
            
        Returns:
            Negative score (for minimization)
        """
        try:
            wn, wp, vdd, temp, cl_ff, tech_node = params
            
            # Clamp to valid ranges
            wn = np.clip(wn, 0.1, 10.0)
            wp = np.clip(wp, 0.1, 15.0)
            vdd = np.clip(vdd, 0.4, 3.3)
            temp = np.clip(temp, -40, 125)
            cl_ff = np.clip(cl_ff, 1.0, 500.0)
            tech_node = np.clip(tech_node, 0.3, 100.0)
            
            # Get prediction
            pred = self.predict_performance(
                wn=float(wn),
                wp=float(wp),
                vdd=float(vdd),
                temp=float(temp),
                cl_ff=float(cl_ff),
                tech_node=float(tech_node),
                corner="TT",
            )
            
            # Calculate score
            score = self._normalize_objectives(
                pred.freq_ghz,
                pred.power_mw,
                pred.delay_ps
            )
            
            # Record in history
            if record_history:
                self.optimization_history.append({
                    "params": {
                        "wn": float(wn),
                        "wp": float(wp),
                        "vdd": float(vdd),
                        "temp": float(temp),
                        "cl_ff": float(cl_ff),
                        "tech_node": float(tech_node),
                    },
                    "metrics": {
                        "freq_ghz": pred.freq_ghz,
                        "power_mw": pred.power_mw,
                        "delay_ps": pred.delay_ps,
                    },
                    "score": score,
                    "confidence": pred.confidence,
                })
            
            return -score  # Negative for minimization
            
        except Exception as e:
            logger.warning(f"Objective evaluation error: {e}")
            return float('inf')

    def optimize(
        self,
        baseline_params: Dict[str, float],
        method: str = "two_stage",
        iterations: int = 100,
        verbose: bool = True,
    ) -> OptimizationResult:
        """Run ML-powered optimization.
        
        Args:
            baseline_params: Current circuit parameters
            method: "two_stage" (global+local), "evolutionary", "bayesian"
            iterations: Number of iterations
            verbose: Whether to log progress
            
        Returns:
            OptimizationResult with optimized parameters and metrics
        """
        self.optimization_history = []
        
        if verbose:
            logger.info(f"Starting ML optimization (method={method}, iterations={iterations})")
        
        # Get baseline prediction
        baseline = self.predict_performance(**baseline_params)
        
        if method == "two_stage":
            result = self._optimize_two_stage(baseline_params, baseline, iterations, verbose)
        elif method == "evolutionary":
            result = self._optimize_evolutionary(baseline_params, baseline, iterations, verbose)
        elif method == "bayesian":
            result = self._optimize_bayesian(baseline_params, baseline, iterations, verbose)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        return result

    def _optimize_two_stage(
        self,
        baseline_params: Dict[str, float],
        baseline: TwinPrediction,
        iterations: int,
        verbose: bool,
    ) -> OptimizationResult:
        """Two-stage optimization: global search + local refinement."""
        
        if verbose:
            logger.info("Stage 1: Global search (Differential Evolution)")
        
        # Stage 1: Global search with differential evolution
        bounds = [
            (0.1, 10.0),    # wn: 0.1-10 um
            (0.1, 15.0),    # wp: 0.1-15 um
            (0.4, 3.3),     # vdd: 0.4-3.3 V
            (-40, 125),     # temp: -40 to 125 C
            (1.0, 500.0),   # cl_ff: 1-500 fF
            (0.3, 100.0),   # tech_node: 0.3-100 nm
        ]
        
        initial_params = np.array([
            baseline_params.get("wn", 1.0),
            baseline_params.get("wp", 2.0),
            baseline_params.get("vdd", 1.8),
            baseline_params.get("temp", 27.0),
            baseline_params.get("cl_ff", 10.0),
            baseline_params.get("tech_node", 7.0),
        ])
        
        result_global = differential_evolution(
            lambda x: self._objective_function(x, baseline, record_history=True),
            bounds,
            seed=42,
            maxiter=max(iterations // 2, 20),
            popsize=15,
            mutation=(0.5, 1.5),
            recombination=0.7,
            atol=1e-8,
            tol=1e-8,
            workers=1,
        )
        
        global_params = result_global.x
        if verbose:
            logger.info(f"Stage 1 best score: {-result_global.fun:.6f}")
        
        # Stage 2: Local refinement with L-BFGS-B
        if verbose:
            logger.info("Stage 2: Local refinement (L-BFGS-B)")
        
        result_local = minimize(
            lambda x: self._objective_function(x, baseline, record_history=True),
            global_params,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": max(iterations // 2, 20), "ftol": 1e-8},
        )
        
        local_params = result_local.x
        if verbose:
            logger.info(f"Stage 2 best score: {-result_local.fun:.6f}")
        
        # Use best result
        if result_local.fun < result_global.fun:
            final_params = local_params
        else:
            final_params = global_params
        
        # Extract optimized parameters
        optimized = {
            "wn": float(final_params[0]),
            "wp": float(final_params[1]),
            "vdd": float(final_params[2]),
            "temp": float(final_params[3]),
            "cl_ff": float(final_params[4]),
            "tech_node": float(final_params[5]),
        }
        
        # Get final prediction
        final_pred = self.predict_performance(**optimized)
        
        # Calculate improvements
        improvements = {
            "freq_improvement_percent": ((final_pred.freq_ghz - baseline.freq_ghz) / baseline.freq_ghz * 100) if baseline.freq_ghz > 0 else 0,
            "power_reduction_percent": ((baseline.power_mw - final_pred.power_mw) / baseline.power_mw * 100) if baseline.power_mw > 0 else 0,
            "delay_improvement_percent": ((baseline.delay_ps - final_pred.delay_ps) / baseline.delay_ps * 100) if baseline.delay_ps > 0 else 0,
            "efficiency_improvement_percent": (
                ((final_pred.freq_ghz / final_pred.power_mw) - (baseline.freq_ghz / baseline.power_mw)) /
                (baseline.freq_ghz / baseline.power_mw) * 100
            ) if baseline.power_mw > 0 else 0,
        }
        
        if verbose:
            logger.info(f"Optimization complete: freq +{improvements['freq_improvement_percent']:.2f}%, "
                       f"power -{improvements['power_reduction_percent']:.2f}%")
        
        return OptimizationResult(
            optimized_params=optimized,
            predicted_metrics={
                "freq_ghz": final_pred.freq_ghz,
                "power_mw": final_pred.power_mw,
                "delay_ps": final_pred.delay_ps,
            },
            confidence_score=final_pred.confidence,
            uncertainty=final_pred.uncertainty,
            estimated_error_percent=final_pred.estimated_error_percent,
            improvement_vs_baseline=improvements,
            optimization_path=self.optimization_history[-min(100, len(self.optimization_history)):],  # Last 100 iterations
            model_metadata={
                "model_source": final_pred.model_source,
                "training_samples": final_pred.training_samples,
                "trained_with_spice": final_pred.trained_with_spice,
                "dataset_version": final_pred.dataset_version,
                "validation_metrics": final_pred.validation_metrics,
            },
        )

    def _optimize_evolutionary(
        self,
        baseline_params: Dict[str, float],
        baseline: TwinPrediction,
        iterations: int,
        verbose: bool,
    ) -> OptimizationResult:
        """Pure evolutionary optimization."""
        
        if verbose:
            logger.info("Evolutionary optimization")
        
        bounds = [
            (0.1, 10.0),
            (0.1, 15.0),
            (0.4, 3.3),
            (-40, 125),
            (1.0, 500.0),
            (0.3, 100.0),
        ]
        
        result = differential_evolution(
            lambda x: self._objective_function(x, baseline, record_history=True),
            bounds,
            seed=42,
            maxiter=iterations,
            popsize=15,
            mutation=(0.5, 1.5),
            recombination=0.7,
            atol=1e-8,
            tol=1e-8,
            workers=1,
        )
        
        final_params = result.x
        
        # Extract optimized parameters
        optimized = {
            "wn": float(final_params[0]),
            "wp": float(final_params[1]),
            "vdd": float(final_params[2]),
            "temp": float(final_params[3]),
            "cl_ff": float(final_params[4]),
            "tech_node": float(final_params[5]),
        }
        
        # Get final prediction
        final_pred = self.predict_performance(**optimized)
        
        # Calculate improvements
        improvements = {
            "freq_improvement_percent": ((final_pred.freq_ghz - baseline.freq_ghz) / baseline.freq_ghz * 100) if baseline.freq_ghz > 0 else 0,
            "power_reduction_percent": ((baseline.power_mw - final_pred.power_mw) / baseline.power_mw * 100) if baseline.power_mw > 0 else 0,
            "delay_improvement_percent": ((baseline.delay_ps - final_pred.delay_ps) / baseline.delay_ps * 100) if baseline.delay_ps > 0 else 0,
            "efficiency_improvement_percent": (
                ((final_pred.freq_ghz / final_pred.power_mw) - (baseline.freq_ghz / baseline.power_mw)) /
                (baseline.freq_ghz / baseline.power_mw) * 100
            ) if baseline.power_mw > 0 else 0,
        }
        
        if verbose:
            logger.info(f"Optimization complete: best score={-result.fun:.6f}")
        
        return OptimizationResult(
            optimized_params=optimized,
            predicted_metrics={
                "freq_ghz": final_pred.freq_ghz,
                "power_mw": final_pred.power_mw,
                "delay_ps": final_pred.delay_ps,
            },
            confidence_score=final_pred.confidence,
            uncertainty=final_pred.uncertainty,
            estimated_error_percent=final_pred.estimated_error_percent,
            improvement_vs_baseline=improvements,
            optimization_path=self.optimization_history,
            model_metadata={
                "model_source": final_pred.model_source,
                "training_samples": final_pred.training_samples,
                "trained_with_spice": final_pred.trained_with_spice,
                "dataset_version": final_pred.dataset_version,
                "validation_metrics": final_pred.validation_metrics,
            },
        )

    def _optimize_bayesian(
        self,
        baseline_params: Dict[str, float],
        baseline: TwinPrediction,
        iterations: int,
        verbose: bool,
    ) -> OptimizationResult:
        """Bayesian optimization using Gaussian Processes approximation."""
        
        if verbose:
            logger.info("Bayesian-inspired optimization")
        
        # For now, use evolutionary as approximation
        # In production, would integrate proper Bayesian optimization library
        return self._optimize_evolutionary(baseline_params, baseline, iterations, verbose)

    def get_optimization_report(self, result: OptimizationResult) -> Dict[str, Any]:
        """Generate detailed optimization report.
        
        Args:
            result: OptimizationResult from optimize()
            
        Returns:
            Detailed report with visualizations and recommendations
        """
        return {
            "summary": {
                "optimized_params": result.optimized_params,
                "predicted_metrics": result.predicted_metrics,
                "confidence_score": result.confidence_score,
                "uncertainty": result.uncertainty,
                "estimated_error_percent": result.estimated_error_percent,
            },
            "improvements": result.improvement_vs_baseline,
            "model_info": result.model_metadata,
            "optimization_path": result.optimization_path,
            "recommendations": self._generate_recommendations(result),
            "timestamp": result.timestamp,
        }

    def _generate_recommendations(self, result: OptimizationResult) -> List[str]:
        """Generate actionable recommendations based on optimization result.
        
        Args:
            result: OptimizationResult
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Frequency recommendations
        if result.improvement_vs_baseline["freq_improvement_percent"] > 10:
            recommendations.append(
                f"✓ Significant frequency gain: +{result.improvement_vs_baseline['freq_improvement_percent']:.1f}% "
                f"at {result.predicted_metrics['freq_ghz']:.2f} GHz"
            )
        elif result.improvement_vs_baseline["freq_improvement_percent"] > 0:
            recommendations.append(
                f"✓ Modest frequency improvement: +{result.improvement_vs_baseline['freq_improvement_percent']:.1f}%"
            )
        elif result.improvement_vs_baseline["freq_improvement_percent"] < -5:
            recommendations.append(
                f"⚠ Frequency trade-off: {result.improvement_vs_baseline['freq_improvement_percent']:.1f}% "
                f"(intentional for power efficiency)"
            )
        
        # Power recommendations
        if result.improvement_vs_baseline["power_reduction_percent"] > 20:
            recommendations.append(
                f"✓ Excellent power reduction: -{result.improvement_vs_baseline['power_reduction_percent']:.1f}% "
                f"to {result.predicted_metrics['power_mw']:.2f} mW"
            )
        elif result.improvement_vs_baseline["power_reduction_percent"] > 5:
            recommendations.append(
                f"✓ Notable power savings: -{result.improvement_vs_baseline['power_reduction_percent']:.1f}%"
            )
        
        # Efficiency recommendations
        if result.improvement_vs_baseline["efficiency_improvement_percent"] > 15:
            recommendations.append(
                f"✓ Outstanding efficiency: +{result.improvement_vs_baseline['efficiency_improvement_percent']:.1f}% better GHz/mW ratio"
            )
        
        # Confidence recommendations
        if result.confidence_score > 0.95:
            recommendations.append(
                f"✓ High model confidence ({result.confidence_score:.1%}): predictions highly reliable"
            )
        elif result.confidence_score > 0.85:
            recommendations.append(
                f"✓ Good model confidence ({result.confidence_score:.1%}): reasonable prediction quality"
            )
        elif result.confidence_score > 0.70:
            recommendations.append(
                f"⚠ Moderate confidence ({result.confidence_score:.1%}): consider validation"
            )
        else:
            recommendations.append(
                f"⚠ Low confidence ({result.confidence_score:.1%}): validate with simulation"
            )
        
        # Parameter change recommendations
        param_changes = []
        if result.optimized_params.get("vdd", 0) < 1.5:
            param_changes.append(f"reduced VDD to {result.optimized_params['vdd']:.2f}V")
        if result.optimized_params.get("wn", 0) > 2.0:
            param_changes.append(f"increased transistor widths")
        if result.optimized_params.get("temp", 0) < 27:
            param_changes.append(f"optimized for cooler conditions ({result.optimized_params['temp']:.0f}°C)")
        
        if param_changes:
            recommendations.append(f"→ Optimization involved: {', '.join(param_changes)}")
        
        return recommendations if recommendations else ["No specific recommendations at this time"]
