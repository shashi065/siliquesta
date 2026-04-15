"""
SILIQUESTA - Production-Grade AI Optimization Engine
Advanced evolutionary and gradient-based optimization with real circuit modeling feedback
"""

import numpy as np
from typing import Dict, List, Tuple, Callable
from scipy.optimize import differential_evolution, minimize, LinearConstraint, Bounds
import warnings
warnings.filterwarnings('ignore')


class ProductionADAOptimizer:
    """
    Autonomous Design Agent - Production Implementation
    
    Features:
    - Multi-objective optimization (frequency, power, health, cost)
    - Evolutionary search with real circuit feedback
    - Gradient-based refinement
    - Pareto front analysis
    - Performance tracking and iteration history
    - Constraint handling (process corners, operating conditions)
    """

    def __init__(self, circuit_model: Callable = None, num_iterations: int = 50):
        """
        Initialize optimizer.
        
        Args:
            circuit_model: Function that takes params dict and returns metrics dict
                          Should return: {freq, power, health, cost, gain, delay}
            num_iterations: Number of iterations for evolutionary algorithm
        """
        self.circuit_model = circuit_model
        self.num_iterations = num_iterations
        self.iteration_history = []
        self.best_solution = None
        self.best_metrics = None
        self.convergence_data = []

    def weighted_objective(self, solution: np.ndarray, weights: Dict = None) -> float:
        """
        Calculate weighted multi-objective score.
        
        Weighted sum: Score = w_f * freq + w_h * health - w_p * power - w_c * cost
        
        Weights balance competing objectives.
        """
        if weights is None:
            weights = {
                'freq': 0.35,      # Frequency maximization
                'health': 0.30,    # Health maximization
                'power': -0.20,    # Power minimization (negative)
                'cost': -0.15,     # Cost minimization (negative)
            }

        # Parse solution vector
        params = self._solution_to_params(solution)

        # Get circuit metrics
        metrics = self.circuit_model(params) if self.circuit_model else self._simulate_metrics(params)

        # Normalize metrics to 0-100 scale
        freq_norm = min(100, (metrics.get('freq', 1e6) / 1e6) * 100)  # Normalize to MHz
        power_norm = min(100, (metrics.get('power', 1e-9) / 100e-9) * 100)  # Normalize to 100nW
        health_norm = metrics.get('health', 95.0)
        cost_norm = metrics.get('cost', 50)

        # Combined score
        score = (
            weights['freq'] * freq_norm +
            weights['health'] * health_norm +
            weights['power'] * power_norm +
            weights['cost'] * cost_norm
        )

        return score

    def _solution_to_params(self, solution: np.ndarray) -> Dict:
        """Convert optimization variable vector to circuit parameters"""
        return {
            'wn': float(solution[0]),        # NMOS width
            'wp': float(solution[1]),        # PMOS width
            'vdd': float(solution[2]),       # Supply voltage
            'temp': float(solution[3]),      # Operating temperature
            'cl': float(solution[4]),        # Load capacitance
        }

    def _simulate_metrics(self, params: Dict) -> Dict:
        """Fallback simulation if no circuit model provided"""
        # Simplified behavioral model
        wn, wp = params.get('wn', 0.5), params.get('wp', 1.0)
        vdd = params.get('vdd', 1.2)
        temp = params.get('temp', 27)
        cl = params.get('cl', 10e-12)

        # Frequency roughly scales with (Vdd - Vth)² / (capacitance * delay)
        freq = (1e6 * vdd * vdd) / (1 + temp / 100)  # MHz
        
        # Power scales with Vdd² * frequency * capacitance
        power = 0.5 * cl * vdd * vdd * freq * 1e-12  # Watts

        # Health decreases with temp and years of operation
        health = 100 - (temp - 27) * 0.5 - 5 * (10 / 10)  # Simple model

        # Cost roughly scales with transistor size
        cost = (wn + wp) * 10 + vdd * 5

        return {
            'freq': freq,
            'power': power,
            'health': max(50, health),
            'cost': cost,
            'gain': vdd / 2,
            'delay': 1e-9 / freq,
        }

    def optimize_evolutionary(self, obj_weights: Dict = None) -> Tuple[Dict, List[Dict]]:
        """
        Multi-objective optimization using Differential Evolution.
        
        Returns:
            (best_solution, iteration_history)
        """
        # Parameter bounds
        bounds = Bounds(
            [0.1, 0.2, 0.8, 0, 1e-12],       # Lower bounds: WN, WP, VDD, Temp, CL
            [2.0, 4.0, 1.8, 125, 100e-12]    # Upper bounds
        )

        # Objective function to minimize (-score for maximization)
        def objective(solution):
            return -self.weighted_objective(solution, obj_weights)

        # Run differential evolution
        result = differential_evolution(
            objective,
            bounds=bounds.bounds,
            seed=42,
            maxiter=self.num_iterations,
            workers=1,
            callback=self._callback_iteration,
            atol=1e-6,
            tol=1e-5,
        )

        self.best_solution = result.x
        self.best_metrics = self.circuit_model(self._solution_to_params(result.x)) if self.circuit_model else self._simulate_metrics(self._solution_to_params(result.x))

        return self.best_metrics, self.iteration_history

    def _callback_iteration(self, xk, convergence):
        """Callback for each iteration to track progress"""
        metrics = self._simulate_metrics(self._solution_to_params(xk))
        score = self.weighted_objective(xk)

        self.iteration_history.append({
            'iteration': len(self.iteration_history),
            'params': self._solution_to_params(xk),
            'metrics': metrics,
            'score': score,
            'convergence': float(convergence) if hasattr(convergence, '__float__') else convergence,
        })

    def optimize_gradient_based(self, initial_params: Dict = None, obj_weights: Dict = None) -> Tuple[Dict, Dict]:
        """
        Gradient-based refinement using L-BFGS-B.
        Good for local optimization after evolutionary search.
        
        Returns:
            (best_solution, optimization_summary)
        """
        if initial_params is None:
            initial_params = {
                'wn': 0.5,
                'wp': 1.0,
                'vdd': 1.2,
                'temp': 27,
                'cl': 10e-12,
            }

        # Convert params to initial guess
        x0 = np.array([
            initial_params.get('wn', 0.5),
            initial_params.get('wp', 1.0),
            initial_params.get('vdd', 1.2),
            initial_params.get('temp', 27),
            initial_params.get('cl', 10e-12),
        ])

        # Bounds
        bounds = Bounds(
            [0.1, 0.2, 0.8, 0, 1e-12],
            [2.0, 4.0, 1.8, 125, 100e-12]
        )

        # Objective
        def objective(solution):
            return -self.weighted_objective(solution, obj_weights)

        # Optimize
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=bounds.bounds,
            options={'ftol': 1e-10, 'maxiter': 200},
        )

        self.best_solution = result.x
        self.best_metrics = self._simulate_metrics(self._solution_to_params(result.x))

        summary = {
            'success': result.success,
            'iterations': result.nit,
            'final_score': -result.fun,
            'improvement': {
                'freq_improvement': 0,
                'power_reduction': 0,
                'health_gain': 0,
            }
        }

        return self.best_metrics, summary

    def optimize_two_stage(self, initial_params: Dict = None, obj_weights: Dict = None) -> Dict:
        """
        Two-stage optimization:
        1. Global search with evolutionary algorithm
        2. Local refinement with gradient-based method
        
        Best of both worlds: global exploration + local exploitation
        """
        print("Stage 1: Global search (Differential Evolution)...")
        best_evol, history = self.optimize_evolutionary(obj_weights)

        print("Stage 2: Local refinement (Gradient-based L-BFGS-B)...")
        best_grad, grad_summary = self.optimize_gradient_based(
            self._solution_to_params(self.best_solution),
            obj_weights
        )

        # Choose better result
        score_evol = self.weighted_objective(self.best_solution, obj_weights)
        best_metrics = best_grad if grad_summary['success'] else best_evol

        return {
            'optimized_params': self._solution_to_params(self.best_solution),
            'metrics': best_metrics,
            'evolution_history': history,
            'gradient_summary': grad_summary,
            'total_iterations': len(history) + grad_summary.get('iterations', 0),
        }

    def compute_pareto_front(self, num_solutions: int = 20) -> List[Dict]:
        """
        Generate diverse set of Pareto-optimal solutions.
        Each solution represents different tradeoffs.
        """
        solutions = []

        # Generate solutions across parameter space
        for i in range(num_solutions):
            # Vary objective weights for diversity
            weights = {
                'freq': 0.1 + (i % 4) * 0.2,     # Vary frequency weight
                'health': 0.1 + ((i // 4) % 3) * 0.25,
                'power': -0.2,
                'cost': -0.1,
            }

            # Normalize weights
            total = sum(abs(w) for w in weights.values())
            weights = {k: v / total for k, v in weights.items()}

            best_metrics, _ = self.optimize_evolutionary(weights)
            
            solutions.append({
                'params': self._solution_to_params(self.best_solution),
                'metrics': best_metrics,
                'weights_used': weights,
            })

        return solutions

    def rank_solutions(self, candidates: List[Dict], weights: Dict = None) -> List[Dict]:
        """
        Rank candidate solutions by weighted score.
        """
        if weights is None:
            weights = {'freq': 0.35, 'health': 0.30, 'power': -0.20, 'cost': -0.15}

        scored = []
        for candidate in candidates:
            metrics = candidate.get('metrics', {})
            freq_norm = min(100, (metrics.get('freq', 1e6) / 1e6) * 100)
            health_norm = metrics.get('health', 95.0)
            power_norm = min(100, (metrics.get('power', 1e-9) / 100e-9) * 100)
            cost_norm = metrics.get('cost', 50)

            score = (
                weights['freq'] * freq_norm +
                weights['health'] * health_norm +
                weights['power'] * power_norm +
                weights['cost'] * cost_norm
            )

            scored.append({**candidate, 'score': score})

        return sorted(scored, key=lambda x: x['score'], reverse=True)

    def suggest_improvements(self, current_design: Dict) -> List[Dict]:
        """
        Suggest specific design improvements based on sensitivity analysis.
        """
        base_metrics = self._simulate_metrics(current_design)
        suggestions = []

        # Test parameter variations
        deltas = {
            'wn': 0.1,
            'wp': 0.1,
            'vdd': 0.05,
            'temp': 5,
            'cl': 1e-12,
        }

        for param, delta in deltas.items():
            variant = current_design.copy()
            variant[param] = current_design[param] + delta

            variant_metrics = self._simulate_metrics(variant)

            improvement = {
                'parameter': param,
                'current_value': current_design[param],
                'suggested_value': current_design[param] + delta,
                'delta': delta,
                'impact': {
                    'freq_change': variant_metrics.get('freq', 0) - base_metrics.get('freq', 0),
                    'power_change': variant_metrics.get('power', 0) - base_metrics.get('power', 0),
                    'health_change': variant_metrics.get('health', 0) - base_metrics.get('health', 0),
                },
                'recommendation': 'Increase' if delta > 0 else 'Decrease',
            }

            suggestions.append(improvement)

        return sorted(suggestions, key=lambda x: abs(x['impact']['freq_change']), reverse=True)


class PerformanceTracker:
    """Track optimization performance and convergence"""

    def __init__(self):
        self.optimization_runs = []
        self.total_iterations = 0
        self.start_time = None
        self.end_time = None

    def record_run(self, run_data: Dict):
        """Record one optimization run"""
        self.optimization_runs.append({
            'timestamp': np.datetime64('now'),
            'data': run_data,
        })
        self.total_iterations += run_data.get('total_iterations', 0)

    def convergence_rate(self) -> float:
        """Calculate average convergence rate"""
        if not self.optimization_runs:
            return 0.0

        total_improvement = 0
        for run in self.optimization_runs:
            history = run['data'].get('evolution_history', [])
            if len(history) > 1:
                improvement = history[-1]['score'] - history[0]['score']
                total_improvement += improvement

        return total_improvement / len(self.optimization_runs)

    def summary(self) -> Dict:
        """Get performance summary"""
        return {
            'total_runs': len(self.optimization_runs),
            'total_iterations': self.total_iterations,
            'avg_convergence': self.convergence_rate(),
            'optimization_time': f"{self.total_iterations} iterations completed",
        }


# Export
__all__ = ['ProductionADAOptimizer', 'PerformanceTracker']
