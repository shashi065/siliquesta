"""Simulation output validation and normalization"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math


@dataclass
class SimulationMetrics:
    """Validated simulation metrics"""
    freq: float  # GHz
    power: float  # mW
    delay: float  # ps
    dynamic_power: Optional[float] = None
    static_power: Optional[float] = None
    energy_per_cycle: Optional[float] = None
    power_delay_product: Optional[float] = None
    corner: str = "tt"
    vdd: float = 1.2
    temp: float = 25
    tech_node: float = 28
    source: str = "simulation"
    valid: bool = True
    validation_warnings: list = None

    def __post_init__(self):
        if self.validation_warnings is None:
            self.validation_warnings = []


def validate_simulation_output(raw_result: Dict[str, Any]) -> SimulationMetrics:
    """Validate and normalize simulation output
    
    Ensures:
    - All required fields present
    - Values are numeric and not NaN/Inf
    - Values are physically realistic
    - Derived metrics calculated correctly
    """
    warnings = []
    
    # Extract and validate required fields
    try:
        freq = float(raw_result.get('freq', 0) or 0)
        power = float(raw_result.get('power', raw_result.get('dynamic_power', 0)) or 0)
        delay = float(raw_result.get('delay', 0) or 0)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Missing or invalid required fields: {e}")
    
    # Check for NaN or Inf
    for name, value in [('freq', freq), ('power', power), ('delay', delay)]:
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Invalid {name}: {value}")
    
    # Validate physical bounds
    if freq <= 0:
        warnings.append("Frequency should be positive (GHz)")
    elif freq > 5:
        warnings.append(f"Frequency unusually high: {freq} GHz (typical < 5 GHz)")
    
    if power < 0:
        warnings.append("Power cannot be negative (mW)")
    elif power > 100:
        warnings.append(f"Power unusually high: {power} mW (typical < 100 mW)")
    
    if delay <= 0:
        warnings.append("Delay should be positive (ps)")
    elif delay > 1000:
        warnings.append(f"Delay unusually high: {delay} ps (typical < 1000 ps)")
    
    # Extract optional fields
    dynamic_power = float(raw_result.get('dynamic_power', power) or power)
    static_power = float(raw_result.get('static_power', 0) or 0)
    
    # Validate power breakdown
    total_measured = dynamic_power + static_power
    if abs(total_measured - power) > power * 0.1:  # Allow 10% deviation
        warnings.append(f"Power mismatch: total={total_measured}, dynamic+static={power}")
    
    # Calculate derived metrics
    energy_per_cycle = power / freq if freq > 0 else 0
    power_delay_product = power * delay if (power > 0 and delay > 0) else 0
    
    # Get other parameters
    corner = str(raw_result.get('corner', 'tt')).upper()
    vdd = float(raw_result.get('vdd', 1.2) or 1.2)
    temp = float(raw_result.get('temp', 25) or 25)
    tech_node = float(raw_result.get('tech_node', 28) or 28)
    
    # Determine if results are valid
    is_valid = freq > 0 and power >= 0 and delay > 0 and len(warnings) == 0
    
    return SimulationMetrics(
        freq=freq,
        power=power,
        delay=delay,
        dynamic_power=dynamic_power,
        static_power=static_power,
        energy_per_cycle=energy_per_cycle,
        power_delay_product=power_delay_product,
        corner=corner,
        vdd=vdd,
        temp=temp,
        tech_node=tech_node,
        source="simulation",
        valid=is_valid,
        validation_warnings=warnings,
    )


@dataclass
class OptimizationResult:
    """Validated optimization result"""
    optimized_params: Dict[str, float]
    predicted_metrics: SimulationMetrics
    confidence_score: float  # 0-1
    uncertainty: float  # Percentage
    improvement_percent: Dict[str, float]  # freq, power, etc
    baseline_metrics: Optional[SimulationMetrics] = None
    algorithm: str = "ml"
    iterations: int = 0
    valid: bool = True
    validation_warnings: list = None

    def __post_init__(self):
        if self.validation_warnings is None:
            self.validation_warnings = []
        
        # Validate confidence score
        if not (0 <= self.confidence_score <= 1):
            self.validation_warnings.append(f"Confidence score out of range: {self.confidence_score}")
            self.valid = False


def validate_optimization_output(raw_result: Dict[str, Any]) -> OptimizationResult:
    """Validate and normalize optimization output
    
    Ensures:
    - All required fields present
    - Metrics are internally consistent
    - Confidence score is in [0, 1]
    - Improvement calculations are realistic
    - Not returning random or invalid improvements
    """
    warnings = []
    
    # Validate optimized parameters
    opt_params = raw_result.get('optimized_params', {})
    if not opt_params:
        raise ValueError("Missing optimized_params")
    
    required_params = ['wn', 'wp', 'vdd']
    for param in required_params:
        if param not in opt_params:
            warnings.append(f"Missing parameter: {param}")
        elif opt_params[param] <= 0:
            warnings.append(f"Invalid parameter value: {param}={opt_params[param]}")
    
    # Validate predicted metrics
    try:
        pred_metrics = validate_simulation_output(
            raw_result.get('predicted_metrics', raw_result.get('predictedMetrics', {}))
        )
    except ValueError as e:
        raise ValueError(f"Invalid predicted metrics: {e}")
    
    # Validate confidence score
    confidence = float(raw_result.get('confidence_score', raw_result.get('confidenceScore', 0.5)) or 0.5)
    if not (0 <= confidence <= 1):
        raise ValueError(f"Invalid confidence score: {confidence}")
    
    uncertainty = float(raw_result.get('uncertainty', 0.1) or 0.1)
    
    # Validate improvement metrics
    improvements = raw_result.get('improvements', raw_result.get('improvement_percent', {}))
    if not improvements:
        # Calculate from baseline if available
        baseline = raw_result.get('baseline_metrics')
        if baseline:
            try:
                baseline_metrics = validate_simulation_output(baseline)
                improvements = {
                    'freq': ((pred_metrics.freq - baseline_metrics.freq) / baseline_metrics.freq * 100)
                             if baseline_metrics.freq > 0 else 0,
                    'power': ((baseline_metrics.power - pred_metrics.power) / baseline_metrics.power * 100)
                             if baseline_metrics.power > 0 else 0,
                    'delay': ((baseline_metrics.delay - pred_metrics.delay) / baseline_metrics.delay * 100)
                             if baseline_metrics.delay > 0 else 0,
                }
            except:
                improvements = {'freq': 0, 'power': 0, 'delay': 0}
                warnings.append("Could not calculate improvements from baseline")
        else:
            improvements = {'freq': 0, 'power': 0, 'delay': 0}
    
    # Validate improvements are realistic (not random)
    for metric, imp in improvements.items():
        if abs(imp) > 99:
            warnings.append(f"Unusual improvement: {metric}={imp}% (typically < 50%)")
        if imp < -50:
            warnings.append(f"Negative improvement: {metric}={imp}% (optimization made metrics worse)")
    
    # Overall validation
    is_valid = confidence > 0.3 and len(warnings) <= 2
    
    return OptimizationResult(
        optimized_params=opt_params,
        predicted_metrics=pred_metrics,
        confidence_score=confidence,
        uncertainty=uncertainty,
        improvement_percent=improvements,
        algorithm=raw_result.get('algorithm', 'ml'),
        iterations=raw_result.get('iterations', 0),
        valid=is_valid,
        validation_warnings=warnings,
    )


def format_simulation_for_api(metrics: SimulationMetrics) -> Dict[str, Any]:
    """Format validated simulation metrics for API response"""
    return {
        'freq': round(metrics.freq, 4),
        'power': round(metrics.power, 4),
        'dynamic_power': round(metrics.dynamic_power or metrics.power, 4),
        'static_power': round(metrics.static_power or 0, 6),
        'delay': round(metrics.delay, 4),
        'energy_per_cycle': round(metrics.energy_per_cycle or 0, 6),
        'power_delay_product': round(metrics.power_delay_product or 0, 6),
        'corner': metrics.corner,
        'vdd': metrics.vdd,
        'temp': metrics.temp,
        'tech_node': metrics.tech_node,
        'valid': metrics.valid,
        'warnings': metrics.validation_warnings,
        'source': metrics.source,
    }


def format_optimization_for_api(result: OptimizationResult) -> Dict[str, Any]:
    """Format validated optimization result for API response"""
    return {
        'optimized_params': result.optimized_params,
        'predicted_metrics': format_simulation_for_api(result.predicted_metrics),
        'confidence_score': round(result.confidence_score, 3),
        'uncertainty': round(result.uncertainty, 3),
        'improvements': {k: round(v, 2) for k, v in result.improvement_percent.items()},
        'algorithm': result.algorithm,
        'iterations': result.iterations,
        'valid': result.valid,
        'warnings': result.validation_warnings,
    }
