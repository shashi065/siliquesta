from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class OptimizationMethod(str, Enum):
    """Optimization methods"""
    SCIPY = "scipy"
    ML = "ml"
    HYBRID = "hybrid"


class CircuitParameters(BaseModel):
    """Circuit parameters for optimization"""
    # Transistor sizing
    W_L_ratio: float = Field(..., gt=0, description="Width to Length ratio")
    finger_ratio: float = Field(default=1, gt=0, description="Finger ratio")
    
    # Supply voltage
    supply_voltage: float = Field(..., gt=0, description="Supply voltage in volts")
    
    # Operating parameters
    operating_frequency: float = Field(default=1e9, gt=0, description="Operating frequency in Hz")
    load_capacitance: float = Field(default=1e-12, gt=0, description="Load capacitance in Farads")
    
    # Process parameters
    technology_node: float = Field(default=28e-9, gt=0, description="Technology node in meters")
    temperature: float = Field(default=27, description="Operating temperature in Celsius")
    
    # Additional parameters
    bias_current: Optional[float] = Field(default=1e-6, gt=0, description="Bias current in Amperes")
    device_mismatch: Optional[float] = Field(default=0.01, ge=0, description="Device mismatch percentage")
    
    # Optimization constraints
    power_budget: Optional[float] = Field(default=1e-3, gt=0, description="Power budget in Watts")
    area_budget: Optional[float] = Field(default=1e-9, gt=0, description="Area budget in square meters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "W_L_ratio": 10,
                "finger_ratio": 1,
                "supply_voltage": 1.8,
                "operating_frequency": 1e9,
                "load_capacitance": 1e-12,
                "technology_node": 28e-9,
                "temperature": 27,
                "bias_current": 1e-6,
                "power_budget": 1e-3,
                "area_budget": 1e-9
            }
        }


class OptimizationObjective(BaseModel):
    """Optimization objectives"""
    minimize_power: bool = Field(default=True, description="Minimize power consumption")
    minimize_area: bool = Field(default=False, description="Minimize chip area")
    maximize_speed: bool = Field(default=False, description="Maximize operating speed")
    maximize_gain: bool = Field(default=False, description="Maximize circuit gain")
    
    class Config:
        json_schema_extra = {
            "example": {
                "minimize_power": True,
                "maximize_speed": True,
                "minimize_area": False,
                "maximize_gain": False
            }
        }


class OptimizeRequest(BaseModel):
    """Optimize endpoint request"""
    parameters: CircuitParameters
    objectives: OptimizationObjective = Field(default_factory=OptimizationObjective)
    method: OptimizationMethod = Field(default=OptimizationMethod.SCIPY)
    max_iterations: int = Field(default=500, gt=0)
    tolerance: float = Field(default=1e-6, gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "W_L_ratio": 10,
                    "supply_voltage": 1.8,
                    "operating_frequency": 1e9,
                    "load_capacitance": 1e-12
                },
                "objectives": {
                    "minimize_power": True,
                    "maximize_speed": True
                },
                "method": "scipy"
            }
        }


class OptimizationMetrics(BaseModel):
    """Optimization metrics"""
    power_consumption: float = Field(description="Power consumption in Watts")
    propagation_delay: float = Field(description="Propagation delay in seconds")
    gain: Optional[float] = Field(default=None, description="Circuit gain in dB")
    area: Optional[float] = Field(default=None, description="Circuit area in square meters")
    slew_rate: Optional[float] = Field(default=None, description="Slew rate in V/s")
    noise_margin: Optional[float] = Field(default=None, description="Noise margin in volts")


class OptimizedCircuitParameters(BaseModel):
    """Optimized circuit parameters output"""
    W_L_ratio: float = Field(description="Optimized Width to Length ratio")
    finger_ratio: float = Field(description="Optimized finger ratio")
    supply_voltage: float = Field(description="Optimized supply voltage")
    operating_frequency: Optional[float] = Field(default=None)
    bias_current: Optional[float] = Field(default=None)
    other_params: Dict[str, Any] = Field(default_factory=dict)


class OptimizationMetricsComparison(BaseModel):
    """Comparison between original and optimized metrics"""
    original: OptimizationMetrics
    optimized: OptimizationMetrics
    improvements: Dict[str, float] = Field(description="Percentage improvement for each metric")


class OptimizeResponse(BaseModel):
    """Optimize endpoint response"""
    success: bool = Field(description="Whether optimization was successful")
    optimized_parameters: OptimizedCircuitParameters
    metrics_comparison: OptimizationMetricsComparison
    overall_improvement: float = Field(description="Overall improvement percentage")
    iterations_used: int = Field(description="Number of iterations used")
    convergence: bool = Field(description="Whether algorithm converged")
    execution_time: float = Field(description="Execution time in seconds")
    method_used: OptimizationMethod
    notes: Optional[str] = Field(default=None)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
