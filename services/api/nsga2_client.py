"""
NSGA-II Optimizer Client Library

Provides Python client for easy interaction with the NSGA-II optimizer API.

Usage:
    from nsga2_client import NSGAIIClient
    
    client = NSGAIIClient("http://localhost:8000")
    result = client.optimize(population_size=50, generations=30)
    pareto_front = result.pareto_front
"""

import requests
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class CircuitParameters:
    """Circuit design parameters."""
    wn: float
    wp: float
    vdd: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(wn=data['wn'], wp=data['wp'], vdd=data['vdd'])


@dataclass
class CircuitPerformance:
    """Circuit performance metrics."""
    frequency: float  # GHz
    power: float      # mW
    delay: float      # ns
    efficiency: float # GHz/mW
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(
            frequency=data['frequency'],
            power=data['power'],
            delay=data['delay'],
            efficiency=data['efficiency']
        )


@dataclass
class ParetoSolution:
    """A solution on the Pareto front."""
    parameters: CircuitParameters
    performance: CircuitPerformance
    rank: int = 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'parameters': self.parameters.to_dict(),
            'performance': self.performance.to_dict(),
            'rank': self.rank
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(
            parameters=CircuitParameters.from_dict(data['parameters']),
            performance=CircuitPerformance.from_dict(data['performance']),
            rank=data.get('rank', 1)
        )


@dataclass
class OptimizationMetrics:
    """Optimization metrics."""
    generations: int
    population_size: int
    execution_time: float
    pareto_front_size: int
    hypervolume: float
    spread: float
    timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(
            generations=data['generations'],
            population_size=data['population_size'],
            execution_time=data['execution_time'],
            pareto_front_size=data['pareto_front_size'],
            hypervolume=data['hypervolume'],
            spread=data['spread'],
            timestamp=data['timestamp']
        )


@dataclass
class OptimizationResult:
    """Complete optimization result."""
    status: str
    pareto_front: List[ParetoSolution]
    metrics: OptimizationMetrics
    best_solutions: Dict[str, Dict]
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(
            status=data['status'],
            pareto_front=[ParetoSolution.from_dict(s) for s in data['pareto_front']],
            metrics=OptimizationMetrics.from_dict(data['metrics']),
            best_solutions=data['best_solutions']
        )
    
    def get_best_power_solution(self) -> Optional[ParetoSolution]:
        """Get the solution with minimum power."""
        if self.pareto_front:
            return min(self.pareto_front, key=lambda s: s.performance.power)
        return None
    
    def get_best_frequency_solution(self) -> Optional[ParetoSolution]:
        """Get the solution with maximum frequency."""
        if self.pareto_front:
            return max(self.pareto_front, key=lambda s: s.performance.frequency)
        return None
    
    def get_best_efficiency_solution(self) -> Optional[ParetoSolution]:
        """Get the solution with maximum efficiency."""
        if self.pareto_front:
            return max(self.pareto_front, key=lambda s: s.performance.efficiency)
        return None


@dataclass
class ComparisonResult:
    """Design comparison result."""
    design1: Dict
    design2: Dict
    comparison: Dict  # Ratios
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(
            design1=data['design1'],
            design2=data['design2'],
            comparison=data['comparison']
        )
    
    def is_design2_faster(self) -> bool:
        """Check if design2 is faster than design1."""
        return self.comparison['frequency_ratio'] > 1.0
    
    def is_design2_lower_power(self) -> bool:
        """Check if design2 has lower power than design1."""
        return self.comparison['power_ratio'] < 1.0


# ============================================================================
# Client
# ============================================================================


class NSGAIIClient:
    """
    Python client for NSGA-II Optimization API.
    
    Example:
        client = NSGAIIClient("http://localhost:8000")
        
        # Health check
        health = client.health_check()
        
        # Get optimizer info
        info = client.get_info()
        
        # Run optimization
        result = client.optimize(population_size=50, generations=30)
        
        # Compare designs
        result = client.compare(
            {"wn": 2.5, "wp": 5.0, "vdd": 2.8},
            {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
        )
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60):
        """
        Initialize client.
        
        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1/nsga2"
        self.timeout = timeout
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
        
        Returns:
            Response JSON
        
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        logger.debug(f"{method} {url}")
        response = self.session.request(method, url, **kwargs)
        
        if not response.ok:
            logger.error(f"Request failed: {response.status_code} {response.text}")
            response.raise_for_status()
        
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if optimizer is available.
        
        Returns:
            Health status dictionary
        """
        return self._request("GET", "/health")
    
    def is_available(self) -> bool:
        """Check if optimizer is available."""
        try:
            health = self.health_check()
            return health.get('nsga2_available', False)
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get optimizer information.
        
        Returns:
            Optimizer info dictionary
        """
        return self._request("GET", "/info")
    
    def optimize(
        self,
        population_size: int = 50,
        generations: int = 30,
        use_ml: bool = False,
        seed: int = 42
    ) -> OptimizationResult:
        """
        Run NSGA-II optimization.
        
        Args:
            population_size: Population size (10-1000)
            generations: Number of generations (5-500)
            use_ml: Use ML model for prediction
            seed: Random seed
        
        Returns:
            Optimization result with Pareto front
        
        Raises:
            requests.RequestException: If optimization fails
        """
        logger.info(f"Starting optimization: pop={population_size}, gen={generations}")
        
        data = {
            "population_size": population_size,
            "generations": generations,
            "use_ml": use_ml,
            "seed": seed
        }
        
        response_data = self._request("POST", "/optimize", json=data)
        result = OptimizationResult.from_dict(response_data)
        
        logger.info(f"Optimization complete: {result.metrics.pareto_front_size} solutions, "
                   f"time={result.metrics.execution_time:.2f}s")
        
        return result
    
    def compare(
        self,
        design1: Dict[str, float],
        design2: Dict[str, float]
    ) -> ComparisonResult:
        """
        Compare two designs.
        
        Args:
            design1: First design {"wn": ..., "wp": ..., "vdd": ...}
            design2: Second design
        
        Returns:
            Comparison result
        
        Raises:
            requests.RequestException: If comparison fails
        """
        logger.info(f"Comparing designs")
        
        data = {"design1": design1, "design2": design2}
        response_data = self._request("POST", "/compare", json=data)
        
        return ComparisonResult.from_dict(response_data)
    
    def close(self):
        """Close session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


# ============================================================================
# Helper Functions
# ============================================================================


def quick_optimize(
    base_url: str = "http://localhost:8000",
    population_size: int = 30,
    generations: int = 10
) -> OptimizationResult:
    """
    Quick optimization with minimal setup.
    
    Args:
        base_url: API base URL
        population_size: Population size
        generations: Number of generations
    
    Returns:
        Optimization result
    """
    with NSGAIIClient(base_url) as client:
        return client.optimize(
            population_size=population_size,
            generations=generations
        )


def compare_designs(
    design1: Dict[str, float],
    design2: Dict[str, float],
    base_url: str = "http://localhost:8000"
) -> ComparisonResult:
    """
    Quick design comparison.
    
    Args:
        design1: First design
        design2: Second design
        base_url: API base URL
    
    Returns:
        Comparison result
    """
    with NSGAIIClient(base_url) as client:
        return client.compare(design1, design2)


# ============================================================================
# Example Usage
# ============================================================================


def example_basic_optimization():
    """Example: Basic optimization."""
    print("=" * 70)
    print("Example 1: Basic Optimization")
    print("=" * 70)
    
    with NSGAIIClient() as client:
        # Check availability
        if not client.is_available():
            print("Optimizer not available!")
            return
        
        # Run optimization
        result = client.optimize(population_size=50, generations=30)
        
        # Display results
        print(f"\nOptimization Results:")
        print(f"  Status: {result.status}")
        print(f"  Pareto Front Size: {result.metrics.pareto_front_size}")
        print(f"  Execution Time: {result.metrics.execution_time:.2f}s")
        print(f"  Hypervolume: {result.metrics.hypervolume:.2f}")
        print(f"  Spread: {result.metrics.spread:.4f}")
        
        # Display best solutions
        best_power = result.get_best_power_solution()
        if best_power:
            print(f"\nBest Power Solution:")
            print(f"  WN={best_power.parameters.wn:.2f}, "
                  f"WP={best_power.parameters.wp:.2f}, "
                  f"VDD={best_power.parameters.vdd:.2f}")
            print(f"  Power={best_power.performance.power:.2f}mW, "
                  f"Frequency={best_power.performance.frequency:.4f}GHz")


def example_compare_designs():
    """Example: Design comparison."""
    print("\n" + "=" * 70)
    print("Example 2: Design Comparison")
    print("=" * 70)
    
    design1 = {"wn": 2.5, "wp": 5.0, "vdd": 2.8}
    design2 = {"wn": 5.0, "wp": 8.0, "vdd": 3.5}
    
    with NSGAIIClient() as client:
        result = client.compare(design1, design2)
        
        print(f"\nDesign 1: {design1}")
        print(f"  Frequency: {result.design1['performance']['frequency']:.4f} GHz")
        print(f"  Power: {result.design1['performance']['power']:.2f} mW")
        
        print(f"\nDesign 2: {design2}")
        print(f"  Frequency: {result.design2['performance']['frequency']:.4f} GHz")
        print(f"  Power: {result.design2['performance']['power']:.2f} mW")
        
        print(f"\nComparison (Design2 / Design1):")
        print(f"  Frequency Ratio: {result.comparison['frequency_ratio']:.2f}x")
        print(f"  Power Ratio: {result.comparison['power_ratio']:.2f}x")
        print(f"  Efficiency Ratio: {result.comparison['efficiency_ratio']:.4f}x")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    try:
        example_basic_optimization()
        example_compare_designs()
        print("\n" + "=" * 70)
        print("Examples completed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
