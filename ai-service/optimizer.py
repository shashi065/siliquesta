import numpy as np
from scipy.optimize import minimize, differential_evolution
from typing import Dict, Tuple, Any
import time
import logging
from config import (
    OPTIMIZATION_MAX_ITERATIONS,
    OPTIMIZATION_TIMEOUT,
)

logger = logging.getLogger(__name__)


class CircuitOptimizer:
    """Circuit parameter optimizer using SciPy"""

    # Physical constants
    K_BOLTZMANN = 1.38e-23  # Boltzmann constant
    Q = 1.602e-19  # Elementary charge

    def __init__(self):
        self.iteration_count = 0
        self.start_time = None
        self.timeout = OPTIMIZATION_TIMEOUT / 1000  # Convert to seconds

    def calculate_metrics(
        self,
        parameters: Dict[str, float],
        original_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate circuit metrics based on parameters
        """
        W_L = parameters.get("W_L_ratio", 10)
        V_dd = parameters.get("supply_voltage", 1.8)
        f_op = parameters.get("operating_frequency", 1e9)
        C_load = parameters.get("load_capacitance", 1e-12)
        T = parameters.get("temperature", 27) + 273.15  # Convert to Kelvin
        I_bias = parameters.get("bias_current", 1e-6)
        
        # Technology parameters (simplified for 28nm)
        Cox = 10e-3  # F/m^2
        mu_n = 400e-4  # m^2/Vs
        V_th = 0.4  # V

        # Calculate power consumption
        # Dynamic power: P_dyn = C_load * V_dd^2 * f
        P_dynamic = C_load * V_dd**2 * f_op * 0.5  # 0.5 activity factor

        # Static power (simplified)
        I_leak = I_bias * 1e-9 * (W_L / 10)  # Scaling with W/L
        P_static = I_leak * V_dd

        # Total power
        power = P_dynamic + P_static

        # Propagation delay (simplified RC delay model)
        # t_d = ln(2) * R * C = 0.693 * V_dd / (mu_n * Cox * W/L * (V_dd - V_th)^2) * C_load
        if (V_dd - V_th) > 0:
            R_channel = V_dd / (mu_n * Cox * W_L * (V_dd - V_th)**2)
            delay = 0.693 * R_channel * C_load
        else:
            delay = 1e-6

        # Slew rate (V/t)
        slew_rate = V_dd / (delay * 10)

        # Gain (simplified)
        g_m = 2 * mu_n * Cox * (W_L / 2) * I_bias
        gain = 20 * np.log10(max(g_m, 1))  # dB

        # Noise margin (simplified)
        noise_margin = V_dd * 0.3

        # Area (approximate in square micrometers)
        area = (W_L * 0.5e-6 * 0.028e-6) + (1e-12)  # W/L feature + capacitance

        return {
            "power_consumption": power,
            "propagation_delay": delay,
            "gain": gain,
            "slew_rate": slew_rate,
            "noise_margin": noise_margin,
            "area": area,
        }

    def objective_function(
        self,
        param_vector: np.ndarray,
        param_names: list,
        objectives: Dict[str, bool],
        original_metrics: Dict[str, float],
        constraints: Dict[str, float]
    ) -> float:
        """
        Objective function for optimization
        """
        # Check timeout
        if time.time() - self.start_time > self.timeout:
            raise TimeoutError("Optimization timeout exceeded")

        self.iteration_count += 1

        # Convert vector to parameter dict
        params = {name: value for name, value in zip(param_names, param_vector)}
        params.update({
            "temperature": 27,  # Keep fixed
        })

        # Calculate metrics
        try:
            metrics = self.calculate_metrics(params, original_metrics)
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return 1e10  # Large penalty

        # Check constraints
        if constraints.get("power_budget") and metrics["power_consumption"] > constraints["power_budget"]:
            return 1e10 + (metrics["power_consumption"] - constraints["power_budget"]) * 1e9

        if constraints.get("area_budget") and metrics["area"] > constraints["area_budget"]:
            return 1e10 + (metrics["area"] - constraints["area_budget"]) * 1e15

        # Weighted objective function
        cost = 0
        weights = {
            "power": 1.0 if objectives.get("minimize_power") else 0.1,
            "delay": 1.0 if objectives.get("maximize_speed") else 0.1,
            "gain": 0.5 if objectives.get("maximize_gain") else 0.1,
            "area": 0.5 if objectives.get("minimize_area") else 0.1,
        }

        # Normalize and weight contributions
        cost += weights["power"] * (metrics["power_consumption"] / original_metrics.get("power_consumption", 1))
        cost += weights["delay"] * (original_metrics.get("propagation_delay", 1) / metrics["propagation_delay"])
        cost += weights["gain"] * (1 - metrics["gain"] / 100)
        cost += weights["area"] * (metrics["area"] / original_metrics.get("area", 1e-12))

        return cost

    def optimize(
        self,
        initial_parameters: Dict[str, float],
        objectives: Dict[str, bool],
        constraints: Dict[str, float],
        max_iterations: int = 500,
        method: str = "differential_evolution"
    ) -> Tuple[Dict[str, float], Dict[str, float], int, bool]:
        """
        Optimize circuit parameters
        """
        self.start_time = time.time()
        self.iteration_count = 0

        # Extract optimizable parameters
        param_names = ["W_L_ratio", "finger_ratio", "supply_voltage", "bias_current"]
        initial_values = [
            initial_parameters.get("W_L_ratio", 10),
            initial_parameters.get("finger_ratio", 1),
            initial_parameters.get("supply_voltage", 1.8),
            initial_parameters.get("bias_current", 1e-6),
        ]

        # Set bounds for optimization
        bounds = [
            (0.5, 100),  # W_L_ratio
            (0.1, 10),   # finger_ratio
            (0.9, 3.3),  # supply_voltage
            (1e-8, 1e-3),  # bias_current
        ]

        # Calculate original metrics
        original_metrics = self.calculate_metrics(initial_parameters, {})

        try:
            if method == "differential_evolution":
                # Global optimization
                result = differential_evolution(
                    self.objective_function,
                    bounds,
                    args=(param_names, objectives, original_metrics, constraints),
                    maxiter=max_iterations,
                    seed=42,
                    workers=1,
                    updating="deferred",
                    atol=1e-7,
                    tol=1e-7,
                )
            else:
                # Local optimization
                result = minimize(
                    self.objective_function,
                    initial_values,
                    args=(param_names, objectives, original_metrics, constraints),
                    bounds=bounds,
                    method="L-BFGS-B",
                    options={"maxiter": max_iterations},
                )

            # Create optimized parameters dict
            optimized_values = result.x
            optimized_params = {
                name: value for name, value in zip(param_names, optimized_values)
            }
            optimized_params.update({
                "operating_frequency": initial_parameters.get("operating_frequency", 1e9),
                "load_capacitance": initial_parameters.get("load_capacitance", 1e-12),
                "technology_node": initial_parameters.get("technology_node", 28e-9),
                "temperature": 27,
            })

            # Calculate optimized metrics
            optimized_metrics = self.calculate_metrics(optimized_params, original_metrics)

            execution_time = time.time() - self.start_time
            converged = result.success

            return optimized_params, optimized_metrics, self.iteration_count, converged

        except TimeoutError:
            logger.warning("Optimization timeout reached")
            return initial_parameters, original_metrics, self.iteration_count, False
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return initial_parameters, original_metrics, self.iteration_count, False

    @staticmethod
    def calculate_improvement(
        original_metrics: Dict[str, float],
        optimized_metrics: Dict[str, float]
    ) -> Tuple[Dict[str, float], float]:
        """
        Calculate improvement percentages
        """
        improvements = {}
        valid_improvements = []

        # Calculate percentage improvements
        for key in ["power_consumption", "propagation_delay", "area"]:
            if original_metrics.get(key) and optimized_metrics.get(key):
                if key == "propagation_delay":  # Lower is better
                    improvement = (
                        (original_metrics[key] - optimized_metrics[key]) /
                        original_metrics[key] * 100
                    )
                else:  # Lower is better
                    improvement = (
                        (original_metrics[key] - optimized_metrics[key]) /
                        original_metrics[key] * 100
                    )
                improvements[key] = improvement
                valid_improvements.append(improvement)

        # For gain, higher is better
        if original_metrics.get("gain") and optimized_metrics.get("gain"):
            improvement = (
                (optimized_metrics["gain"] - original_metrics["gain"]) /
                max(abs(original_metrics["gain"]), 1) * 100
            )
            improvements["gain"] = improvement
            valid_improvements.append(improvement)

        # Overall improvement (average)
        overall_improvement = np.mean(valid_improvements) if valid_improvements else 0

        return improvements, overall_improvement
