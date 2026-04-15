"""Production-grade AI optimization engine.

Two-stage optimization:
1. Global search (Differential Evolution)
2. Local refinement (L-BFGS-B)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.optimize import differential_evolution, minimize
from dataclasses import dataclass, field
from datetime import datetime

from app.services.simulation_engine import create_simulator

logger = logging.getLogger(__name__)


@dataclass
class PerformanceTracker:
    """Track optimization performance metrics."""
    iterations: List[int] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    best_score: float = -np.inf
    best_iteration: int = 0
    
    def record(self, iteration: int, score: float):
        """Record iteration result."""
        self.iterations.append(iteration)
        self.scores.append(score)
        if score > self.best_score:
            self.best_score = score
            self.best_iteration = iteration
    
    def convergence_info(self) -> Dict[str, Any]:
        """Get convergence analysis."""
        if not self.scores:
            return {}
        
        return {
            "total_iterations": len(self.scores),
            "best_score": self.best_score,
            "best_at_iteration": self.best_iteration,
            "final_score": self.scores[-1],
            "improvement": self.scores[-1] - self.scores[0] if self.scores else 0,
            "convergence_efficiency": (self.best_iteration / len(self.scores)) if self.scores else 0,
            "improvement_trend": float(np.mean(np.diff(self.scores[-10:]))) if len(self.scores) > 10 else 0,
        }


class ProductionADAOptimizer:
    """Advanced optimization engine for circuit parameters."""
    
    def __init__(
        self,
        baseline_params: Dict[str, float],
        objectives: Dict[str, float],
        seed: Optional[int] = None,
    ):
        """
        Initialize optimizer.
        
        baseline_params: Initial circuit parameters
        objectives: Multi-objective weights (freq, power, health, cost)
        """
        self.baseline_params = baseline_params
        self.objectives = objectives
        self.seed = seed or 42
        self.rng = np.random.RandomState(self.seed)
        self.pareto_solutions: List[Dict[str, Any]] = []
    
    def _weighted_objective(
        self,
        params: np.ndarray,
        track_performance: Optional[PerformanceTracker] = None,
        iteration: Optional[int] = None,
    ) -> float:
        """
        Evaluate weighted multi-objective score.
        
        Returns: Score (higher is better)
        """
        try:
            # Convert params array to dict
            param_dict = {
                "wn": params[0],
                "wp": params[1],
                "vdd": params[2],
                "cl": self.baseline_params.get("cl", 1e-12),
                "temp": self.baseline_params.get("temp", 27),
            }
            
            # Simulate circuit
            sim = create_simulator(param_dict)
            results = sim.simulate()
            metrics = results["metrics"]
            
            # Normalize metrics
            baseline_sim = create_simulator(self.baseline_params)
            baseline_results = baseline_sim.simulate()
            baseline_metrics = baseline_results["metrics"]
            
            # Avoid division by zero
            freq_norm = metrics["frequency"] / (baseline_metrics["frequency"] + 1e-12)
            power_norm = metrics["power"] / (baseline_metrics["power"] + 1e-12)
            
            # Health score from aging analysis (if available)
            health_norm = results.get("health_score", 80) / 100.0
            
            # Cost estimation (relative to baseline)
            cost_norm = param_dict["wn"] * param_dict["wp"] / (
                self.baseline_params["wn"] * self.baseline_params["wp"]
            )
            
            # Weighted multi-objective score
            score = (
                self.objectives.get("freq", 0.0) * freq_norm +
                self.objectives.get("power", 0.0) / power_norm +  # Minimize power
                self.objectives.get("health", 0.0) * health_norm +
                self.objectives.get("cost", 0.0) / cost_norm  # Minimize cost
            )
            
            # Track if requested
            if track_performance and iteration is not None:
                track_performance.record(iteration, score)
            
            return score
        
        except Exception as e:
            logger.warning(f"Evaluation error at params {params}: {e}")
            return -np.inf
    
    def optimize_evolutionary(
        self,
        iterations: int = 50,
        track_performance: Optional[PerformanceTracker] = None,
    ) -> Tuple[np.ndarray, float]:
        """
        Global optimization using differential evolution.
        
        Returns: (best_params, best_score)
        """
        # Parameter bounds: [wn, wp, vdd]
        bounds = [
            (200, 5000),    # wn: 200-5000 nm
            (400, 10000),   # wp: 400-10000 nm
            (0.8, 3.0),     # vdd: 0.8-3.0 V
        ]
        
        # Set up callback to track convergence
        def callback(xk, convergence=None):
            if track_performance:
                iteration = len(track_performance.iterations)
                score = -self._weighted_objective(xk, track_performance, iteration)
                return False
            return False
        
        # Run differential evolution
        result = differential_evolution(
            lambda x: -self._weighted_objective(x, track_performance),  # Negative for minimization
            bounds,
            seed=self.seed,
            maxiter=iterations,
            popsize=15,
            mutation=(0.5, 1.5),
            recombination=0.7,
            atol=1e-6,
            tol=1e-6,
            callback=callback,
            workers=1,  # Single-threaded for reproducibility
        )
        
        return result.x, -result.fun
    
    def optimize_gradient_based(
        self,
        initial_params: np.ndarray,
        track_performance: Optional[PerformanceTracker] = None,
    ) -> Tuple[np.ndarray, float]:
        """
        Local refinement using L-BFGS-B.
        
        Returns: (optimized_params, best_score)
        """
        # Parameter bounds
        bounds = [
            (200, 5000),
            (400, 10000),
            (0.8, 3.0),
        ]
        
        # Optimize
        iteration_counter = {"count": 0}
        
        def callback(xk):
            if track_performance:
                iteration_counter["count"] += 1
                score = self._weighted_objective(xk, track_performance, iteration_counter["count"])
        
        result = minimize(
            lambda x: -self._weighted_objective(x, track_performance),
            initial_params,
            method="L-BFGS-B",
            bounds=bounds,
            callback=callback,
            options={"maxiter": 50, "ftol": 1e-6},
        )
        
        return result.x, -result.fun
    
    def optimize_two_stage(
        self,
        iterations: int = 50,
        random_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Two-stage optimization combining global and local search.
        
        Returns: Optimization results with recommendations
        """
        if random_seed:
            self.rng = np.random.RandomState(random_seed)
            self.seed = random_seed
        
        logger.info(f"Starting 2-stage optimization (iterations={iterations})")
        
        # Stage 1: Global search
        logger.info("Stage 1: Differential Evolution (global search)")
        perf_tracker = PerformanceTracker()
        
        global_params, global_score = self.optimize_evolutionary(
            iterations=iterations,
            track_performance=perf_tracker,
        )
        logger.info(f"Stage 1 complete: score={global_score:.4f}")
        
        # Stage 2: Local refinement
        logger.info("Stage 2: L-BFGS-B (local refinement)")
        local_params, local_score = self.optimize_gradient_based(
            initial_params=global_params,
            track_performance=perf_tracker,
        )
        logger.info(f"Stage 2 complete: score={local_score:.4f}")
        
        # Use best result
        if local_score > global_score:
            final_params = local_params
            final_score = local_score
        else:
            final_params = global_params
            final_score = global_score
        
        # Get optimized metrics
        final_param_dict = {
            "wn": float(final_params[0]),
            "wp": float(final_params[1]),
            "vdd": float(final_params[2]),
            "cl": self.baseline_params.get("cl", 1e-12),
            "temp": self.baseline_params.get("temp", 27),
        }
        
        final_sim = create_simulator(final_param_dict)
        final_results = final_sim.simulate()
        final_metrics = final_results["metrics"]
        
        # Get baseline metrics
        baseline_sim = create_simulator(self.baseline_params)
        baseline_results = baseline_sim.simulate()
        baseline_metrics = baseline_results["metrics"]
        
        # Calculate improvement
        baseline_score = self._weighted_objective(
            np.array([self.baseline_params["wn"], self.baseline_params["wp"], self.baseline_params["vdd"]])
        )
        improvement_pct = ((final_score - baseline_score) / abs(baseline_score) * 100) if baseline_score != 0 else 0
        
        # Generate Pareto front solutions (sample some good solutions)
        logger.info("Generating Pareto front solutions")
        self._generate_pareto_solutions(iterations=20)
        
        return {
            "optimized_params": final_param_dict,
            "optimized_metrics": final_metrics,
            "baseline_metrics": baseline_metrics,
            "improvement_percentage": improvement_pct,
            "convergence_info": perf_tracker.convergence_info(),
            "pareto_solutions": self.pareto_solutions[:20],  # Top 20 solutions
            "optimization_summary": {
                "stage1_score": float(global_score),
                "stage2_score": float(local_score),
                "final_score": float(final_score),
                "iterations": iterations,
                "total_evaluations": perf_tracker.total_iterations if hasattr(perf_tracker, "total_iterations") else iterations * 15,
            },
        }
    
    def _generate_pareto_solutions(self, iterations: int = 20):
        """Generate Pareto front of good solutions."""
        solutions = []
        
        # Sample random parameters in valid ranges
        for _ in range(iterations):
            wn = self.rng.uniform(200, 5000)
            wp = self.rng.uniform(400, 10000)
            vdd = self.rng.uniform(0.8, 3.0)
            
            params = np.array([wn, wp, vdd])
            score = self._weighted_objective(params)
            
            # Get metrics
            param_dict = {
                "wn": wn,
                "wp": wp,
                "vdd": vdd,
                "cl": self.baseline_params.get("cl", 1e-12),
                "temp": self.baseline_params.get("temp", 27),
            }
            
            try:
                sim = create_simulator(param_dict)
                results = sim.simulate()
                metrics = results["metrics"]
                
                solutions.append({
                    "params": param_dict,
                    "score": float(score),
                    "frequency": metrics.get("frequency"),
                    "power": metrics.get("power"),
                    "gain": metrics.get("gain"),
                    "delay": metrics.get("delay"),
                    "health_score": results.get("health_score"),
                })
            except Exception as e:
                logger.warning(f"Failed to evaluate solution: {e}")
        
        # Sort by score and keep top solutions
        solutions.sort(key=lambda x: x["score"], reverse=True)
        self.pareto_solutions = solutions[:20]
    
    def suggest_improvements(self, current_params: Dict[str, float]) -> List[Dict[str, Any]]:
        """Suggest parameter improvements via sensitivity analysis."""
        suggestions = []
        
        # Test variations of each parameter
        for param_name in ["wn", "wp", "vdd"]:
            improvements = []
            
            # Test ±10% variation
            for delta_pct in [-0.1, -0.05, 0.05, 0.1]:
                test_params = current_params.copy()
                test_params[param_name] *= (1 + delta_pct)
                
                # Evaluate
                param_array = np.array([test_params["wn"], test_params["wp"], test_params["vdd"]])
                score = self._weighted_objective(param_array)
                improvements.append((delta_pct * 100, score))
            
            # Find best direction
            best_direction = max(improvements, key=lambda x: x[1])
            if best_direction[1] > self._weighted_objective(
                np.array([current_params["wn"], current_params["wp"], current_params["vdd"]])
            ):
                suggestions.append({
                    "parameter": param_name,
                    "direction": "increase" if best_direction[0] > 0 else "decrease",
                    "magnitude_pct": abs(best_direction[0]),
                    "estimated_improvement": best_direction[1],
                })
        
        return sorted(suggestions, key=lambda x: x["estimated_improvement"], reverse=True)
    
    def optimize_ml_based(
        self,
        model_version: str = "default",
        num_candidates: int = 100,
    ) -> Dict[str, Any]:
        """
        ML-based optimization using trained neural network.
        
        Much faster than brute-force search as no simulations needed.
        Uses MC Dropout for uncertainty quantification.
        
        Args:
            model_version: Which ML model checkpoint to use
            num_candidates: Number of candidates to evaluate
        
        Returns:
            Optimization results with confidence scores
        """
        try:
            from app.services.ml_model import MLCircuitOptimizer
        except ImportError:
            logger.warning("ML model not available, falling back to standard optimization")
            return self.optimize_two_stage()
        
        logger.info(f"ML-based optimization (candidates={num_candidates}, model={model_version})")
        
        # Initialize ML optimizer
        ml_opt = MLCircuitOptimizer(model_version=model_version, mc_samples=50)
        
        # Define objectives for ML optimizer
        objectives = self.objectives if self.objectives else {
            "frequency": 0.35,
            "power": -0.20,
            "health_score": 0.25,
            "delay": -0.15,
        }
        
        # Define parameter constraints based on baseline
        parameter_constraints = {
            "wn": (100, 5000),
            "wp": (200, 10000),
            "vdd": (0.5, 3.0),
            "cl": (1e-14, 1e-10),
            "temp": (0, 100),
            "tech_node": (3, 28),
            "corner": (0, 4),
        }
        
        # Run ML-based optimization  
        prediction_result = ml_opt.optimize(
            objectives=objectives,
            parameter_constraints=parameter_constraints,
            num_candidates=num_candidates,
        )
        
        logger.info(
            f"ML optimization complete: "
            f"score={prediction_result.predicted_metrics.get('frequency', 0):.4f}, "
            f"confidence={prediction_result.confidence_score:.4f}"
        )
        
        return {
            "optimized_params": prediction_result.optimized_params,
            "predicted_metrics": prediction_result.predicted_metrics,
            "confidence_score": prediction_result.confidence_score,
            "uncertainty_estimates": prediction_result.uncertainty_estimates,
            "model_version": prediction_result.model_version,
            "optimization_method": "ml_based",
            "is_prediction": True,  # Flag that these are predictions, not simulations
            "timestamp": prediction_result.timestamp.isoformat(),
        }
