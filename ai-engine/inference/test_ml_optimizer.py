#!/usr/bin/env python3
"""
Test ML-powered optimization engine.

Demonstrates circuit parameter optimization using the digital twin model
with confidence scores and improvement metrics.
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai_ml_optimizer import MLOptimizer
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_optimization():
    """Run optimization test."""
    
    logger.info("=" * 80)
    logger.info("ML-Powered Circuit Optimization Test")
    logger.info("=" * 80)
    
    # Test case: Inverter for max frequency
    baseline_params = {
        "wn": 1.0,        # NMOS width (um)
        "wp": 2.0,        # PMOS width (um)
        "vdd": 1.8,       # Supply voltage (V)
        "temp": 27.0,     # Temperature (C)
        "cl_ff": 10.0,    # Load capacitance (fF)
        "tech_node": 7.0, # Technology node (nm)
    }
    
    logger.info("\n[1] Baseline Parameters:")
    logger.info(f"  WN: {baseline_params['wn']:.2f} um")
    logger.info(f"  WP: {baseline_params['wp']:.2f} um")
    logger.info(f"  VDD: {baseline_params['vdd']:.2f} V")
    logger.info(f"  Temp: {baseline_params['temp']:.0f}°C")
    logger.info(f"  CL: {baseline_params['cl_ff']:.1f} fF")
    logger.info(f"  Tech Node: {baseline_params['tech_node']:.1f} nm")
    
    # Initialize optimizer
    logger.info("\n[2] Initializing ML Optimizer...")
    objectives = {
        "freq": 0.4,         # 40% weight on frequency
        "power": 0.3,        # 30% weight on power efficiency
        "delay": 0.1,        # 10% weight on delay
        "efficiency": 0.2,   # 20% weight on overall efficiency
    }
    optimizer = MLOptimizer(objectives=objectives)
    logger.info("✓ Optimizer ready")
    
    # Run optimization
    logger.info("\n[3] Running Optimization (two-stage: global + local search)...")
    result = optimizer.optimize(
        baseline_params=baseline_params,
        method="two_stage",
        iterations=100,
        verbose=True,
    )
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("OPTIMIZATION RESULTS")
    logger.info("=" * 80)
    
    logger.info("\n[Optimized Parameters]")
    for param, value in result.optimized_params.items():
        baseline_val = baseline_params.get(param, 0)
        if baseline_val > 0:
            pct_change = (value - baseline_val) / baseline_val * 100
            logger.info(f"  {param.upper()}: {value:.4f} (baseline: {baseline_val:.4f}, {pct_change:+.1f}%)")
        else:
            logger.info(f"  {param.upper()}: {value:.4f}")
    
    logger.info("\n[Predicted Metrics]")
    for metric, value in result.predicted_metrics.items():
        logger.info(f"  {metric}: {value:.4f}")
    
    logger.info("\n[Model Confidence & Uncertainty]")
    logger.info(f"  Confidence Score: {result.confidence_score:.4f} ({result.confidence_score*100:.1f}%)")
    logger.info(f"  Uncertainty: {result.uncertainty:.6f}")
    logger.info(f"  Est. Error: {result.estimated_error_percent:.2f}%")
    
    logger.info("\n[Performance Improvements]")
    for improvement, value in result.improvement_vs_baseline.items():
        if "percent" in improvement:
            logger.info(f"  {improvement}: {value:+.2f}%")
        else:
            logger.info(f"  {improvement}: {value:.4f}")
    
    logger.info("\n[Recommendations]")
    for i, rec in enumerate(optimizer.get_optimization_report(result)["recommendations"], 1):
        logger.info(f"  {i}. {rec}")
    
    logger.info("\n[Model Information]")
    for key, value in result.model_metadata.items():
        logger.info(f"  {key}: {value}")
    
    # Generate detailed report
    logger.info("\n" + "=" * 80)
    report = optimizer.get_optimization_report(result)
    
    logger.info("Full Report (JSON):")
    logger.info(json.dumps(report, indent=2, default=str))
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ TEST COMPLETE")
    logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_optimization())
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
