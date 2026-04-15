"""
Agentic Orchestrator Integration Example
========================================

Complete example showing how to use the orchestrator with real services.
Demonstrates execution-based design optimization without chatbot responses.
"""

import asyncio
import logging
from typing import Dict, Any

# The actual orchestrator
from app.agentic_orchestrator import AgenticOrchestrator, DesignIntent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_parse_and_understand_intent():
    """Example 1: Parse natural language to understand design intent"""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Intent Parsing & Understanding")
    print("="*70)
    
    specifications = [
        "minimize power under 100mW with minimum 500MHz frequency",
        "maximize frequency for high performance, 28nm tech node",
        "balanced design: 50mW power budget and 300MHz minimum",
        "reliability focused: 10 year lifetime at 125C temperature",
    ]
    
    for spec in specifications:
        print(f"\nSpecification: {spec}")
        print("-" * 70)
        
        # Parse natural language
        intent = DesignIntent.from_natural_language(spec)
        
        print(f"  Primary Target:     {intent.primary_target.value}")
        print(f"  Wn Range:           {intent.wn_range[0]:.2f} - {intent.wn_range[1]:.2f} um")
        print(f"  Wp Range:           {intent.wp_range[0]:.2f} - {intent.wp_range[1]:.2f} um")
        print(f"  Vdd Range:          {intent.vdd_range[0]:.2f} - {intent.vdd_range[1]:.2f} V")
        print(f"  Constraints:")
        print(f"    - Max Power:      {intent.max_power} mW" if intent.max_power else "    - Max Power:      None")
        print(f"    - Min Frequency:  {intent.min_frequency} MHz" if intent.min_frequency else "    - Min Frequency:  None")
        print(f"    - Min Lifetime:   {intent.min_lifetime} years" if intent.min_lifetime else "    - Min Lifetime:   None")
        print(f"  Process Corner:     {intent.corner}")
        print(f"  Tech Node:          {intent.tech_node} nm")
        print(f"  Optimization:       {intent.optimization_priority}")


async def example_2_orchestrator_execution_plan():
    """Example 2: Show how orchestrator plans its execution"""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: Orchestrator Execution Planning")
    print("="*70)
    
    orchestrator = AgenticOrchestrator()
    
    specifications_and_expected_plans = [
        (
            "minimize power under 100mW with >500MHz",
            "Power optimization with frequency constraint"
        ),
        (
            "maximize frequency, aggressive optimization",
            "Intensive performance optimization"
        ),
        (
            "reliability focused, conservative approach",
            "Careful optimization with reliability emphasis"
        ),
    ]
    
    for spec, description in specifications_and_expected_plans:
        print(f"\n{description}:")
        print(f"  Input: {spec}")
        print("-" * 70)
        
        intent = DesignIntent.from_natural_language(spec)
        execution_plan = orchestrator._plan_execution(intent)
        
        print("  Execution Plan:")
        for i, step in enumerate(execution_plan.steps, 1):
            print(f"    {i}. {step}")
        
        print(f"\n  Optimization Intensity: {execution_plan.optimization_intensity}")
        print(f"  Digital Twin Enabled:   {execution_plan.digital_twin_enabled}")
        print(f"  Optimizer Enabled:      {execution_plan.optimizer_enabled}")
        print(f"  Reliability Enabled:    {execution_plan.reliability_analysis_enabled}")
        
        print(f"\n  Reasoning Summary:")
        for line in execution_plan.reasoning.strip().split('\n'):
            if line.strip():
                print(f"    {line}")


async def example_3_confidence_computation():
    """Example 3: Show confidence scoring methodology"""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: Confidence Scoring")
    print("="*70)
    
    from app.agentic_orchestrator import CircuitDesign
    
    orchestrator = AgenticOrchestrator()
    
    # Create a sample design
    design = CircuitDesign(
        wn=2.5,
        wp=5.2,
        vdd=0.9,
        temperature=25.0,
        power=87.3,
        frequency=542.1,
        delay=1.84,
        power_confidence=0.85,
        frequency_confidence=0.82,
        reliability_confidence=0.78,
        reliability_score=0.81,
        device_lifetime=8.1
    )
    
    intent = DesignIntent.from_natural_language("minimize power under 100mW with >500MHz")
    
    print(f"\nDesign: Wn={design.wn:.2f}um, Wp={design.wp:.2f}um, Vdd={design.vdd:.2f}V")
    print(f"Performance: {design.frequency:.0f}MHz, {design.power:.1f}mW, Reliability={design.reliability_score:.2%}")
    print("-" * 70)
    
    # Compute confidence
    component_results = {
        "digital_twin": {"success": True},
        "optimizer": {"success": True},
        "reliability": {"success": True}
    }
    
    confidence = orchestrator._compute_confidence(
        design, [design], intent, component_results
    )
    
    print(f"\nConfidence Breakdown:")
    print(f"  Prediction Confidence:     0.85 (avg of power={design.power_confidence}, freq={design.frequency_confidence}, reliability={design.reliability_confidence})")
    print(f"  Constraint Satisfaction:   1.00 (power {design.power:.1f} < {intent.max_power}mW, freq {design.frequency:.0f} > {intent.min_frequency}MHz)")
    print(f"  Pareto Ranking:            1.00 (rank 1 = Pareto optimal)")
    print(f"  Component Agreement:       1.00 (all 3 components successful)")
    print(f"  Design Space Coverage:     0.10 (1 design evaluated)")
    print(f"\n  ➜ Overall Confidence:      {confidence['overall']:.1%}")
    
    print(f"\nInterpretation:")
    if confidence['overall'] > 0.9:
        print(f"  ✅ HIGH CONFIDENCE - Trusted recommendation")
    elif confidence['overall'] > 0.7:
        print(f"  ✅ GOOD CONFIDENCE - Reliable design")
    elif confidence['overall'] > 0.5:
        print(f"  ⚠️  MODERATE CONFIDENCE - Consider alternatives")
    else:
        print(f"  ❌ LOW CONFIDENCE - Verify results")


async def example_4_multi_objective_scoring():
    """Example 4: Multi-objective scoring for different targets"""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: Multi-Objective Design Scoring")
    print("="*70)
    
    from app.agentic_orchestrator import CircuitDesign, OptimizationTarget
    
    # Create three designs representing different tradeoffs
    designs = [
        {
            "name": "Power-Optimized",
            "design": CircuitDesign(
                wn=1.5, wp=3.0, vdd=0.8,
                power=50.0, frequency=300.0, delay=3.33,
                reliability_score=0.88,
                device_lifetime=9.5
            )
        },
        {
            "name": "Performance-Optimized",
            "design": CircuitDesign(
                wn=5.0, wp=10.0, vdd=1.2,
                power=180.0, frequency=800.0, delay=1.25,
                reliability_score=0.65,
                device_lifetime=6.2
            )
        },
        {
            "name": "Balanced",
            "design": CircuitDesign(
                wn=2.5, wp=5.2, vdd=0.9,
                power=87.3, frequency=542.1, delay=1.84,
                reliability_score=0.81,
                device_lifetime=8.1
            )
        },
    ]
    
    targets = [
        OptimizationTarget.POWER_MINIMAL,
        OptimizationTarget.FREQUENCY_MAXIMAL,
        OptimizationTarget.BALANCED,
    ]
    
    for target in targets:
        print(f"\n{'='*70}")
        print(f"Optimization Target: {target.value}")
        print('='*70)
        
        intent = DesignIntent(primary_target=target, max_power=200, min_frequency=300)
        
        for desc in designs:
            design = desc["design"]
            score = design.compute_objective_score(intent)
            
            print(f"\n  {desc['name']}:")
            print(f"    Wn={design.wn:.1f}um, Wp={design.wp:.1f}um, Vdd={design.vdd:.1f}V")
            print(f"    Power: {design.power:.0f}mW, Freq: {design.frequency:.0f}MHz, Reliability: {design.reliability_score:.2%}")
            print(f"    ➜ Multi-Objective Score: {score:.3f} (0-1 scale)")


async def example_5_pareto_front_explanation():
    """Example 5: Explain Pareto front and tradeoff options"""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: Pareto Front - Design Tradeoff Analysis")
    print("="*70)
    
    from app.agentic_orchestrator import CircuitDesign, OptimizationTarget
    
    # Simulate Pareto front with designs at different tradeoff points
    pareto_solutions = [
        {"rank": 1, "performance": "Ultra-Low Power", "power": 45.0, "freq": 250.0, "lifetime": 9.8},
        {"rank": 2, "performance": "Low Power", "power": 65.0, "freq": 380.0, "lifetime": 8.9},
        {"rank": 3, "performance": "Balanced", "power": 87.3, "freq": 542.1, "lifetime": 8.1},
        {"rank": 4, "performance": "High Performance", "power": 120.0, "freq": 720.0, "lifetime": 7.2},
        {"rank": 5, "performance": "Ultra-High Perf", "power": 180.0, "freq": 950.0, "lifetime": 5.8},
    ]
    
    print("\nPareto-Optimal Designs (Non-Dominated Solutions):")
    print("-" * 70)
    print(f"{'Rank':<6} {'Design':<20} {'Power (mW)':<15} {'Freq (MHz)':<15} {'Lifetime (yr)':<15}")
    print("-" * 70)
    
    for sol in pareto_solutions:
        print(f"{sol['rank']:<6} {sol['performance']:<20} {sol['power']:<15.1f} {sol['freq']:<15.0f} {sol['lifetime']:<15.1f}")
    
    print("\n" + "-" * 70)
    print("\nDesign Space Explanation:")
    print(f"  • Rank 1 (Best): Lowest power (45mW) but slower (250MHz)")
    print(f"  • Rank 2-4: Tradeoff region - increasing power for higher frequency")
    print(f"  • Rank 5 (Fastest): Highest frequency (950MHz) but consumes 4x more power")
    print(f"\nReliability Tradeoff:")
    print(f"  • Power-optimized: 9.8 year lifetime (conservative design)")
    print(f"  • Performance-optimized: 5.8 year lifetime (aggressive operation)")
    print(f"\nRecommendation:")
    print(f"  Based on target 'minimize power under 100mW with >300MHz':")
    print(f"  ➜ Select RANK 2: {pareto_solutions[1]['performance']} design")
    print(f"    - Meets constraints: {pareto_solutions[1]['power']:.0f}mW < 100mW? NO")
    print(f"  ➜ Select RANK 1: {pareto_solutions[0]['performance']} design")
    print(f"    - Meets constraints: {pareto_solutions[0]['power']:.0f}mW < 100mW? YES ✓")
    print(f"    - Meets constraints: {pareto_solutions[0]['freq']:.0f}MHz > 300MHz? NO ✗")
    print(f"  ➜ No design perfectly meets constraints, select RANK 2 as best feasible")


async def example_6_execution_trace():
    """Example 6: Show execution trace with timing"""
    
    print("\n" + "="*70)
    print("EXAMPLE 6: Orchestrator Execution Trace")
    print("="*70)
    
    print("""
Execution Trace for: "minimize power under 100mW with >500MHz"
Request ID: req_1712000000000
Timestamp: 2024-04-14T10:30:00

Timeline:
┌─────────────────────────────────────────────────────────────────┐
│ T+0ms:   Parse input specification                              │
│          → Primary target: POWER_MINIMAL                         │
│          → Constraints: max_power=100mW, min_freq=500MHz         │
│          → Optimization intensity: STANDARD                      │
│                                                                   │
│ T+1ms:   Execute plan                                            │
│          → Initialize NSGA-II (100 pop, 50 gen)                  │
│          → Enable Digital Twin enhancement                       │
│          → Enable Reliability analysis                           │
│          → Enable GPU acceleration                               │
│                                                                   │
│ T+2ms:   Call NSGA-II Optimizer                                  │
│          [██████████████████████] 100%                           │
│          → 100 population candidates generated                   │
│          → 50 generations evaluated                              │
│          → 23 non-dominated solutions found                      │
│          Duration: 2347ms                                        │
│                                                                   │
│ T+2349ms: Enhance with Digital Twin                              │
│          [██████████████████████] 100%                           │
│          → 23 designs predicted (GPU accelerated)                │
│          → Avg confidence: 0.84                                  │
│          Duration: 87ms                                          │
│                                                                   │
│ T+2436ms: Analyze Reliability                                    │
│          [██████████████████████] 100%                           │
│          → NBTI, HCI, EM degradation computed                    │
│          → Device lifetimes estimated                            │
│          Duration: 142ms                                         │
│                                                                   │
│ T+2578ms: Filter and Rank                                        │
│          → Constraint satisfaction: 18/23 designs valid          │
│          → Pareto ranking completed                              │
│          → Best design selected                                  │
│                                                                   │
│ T+2585ms: Compute Confidence                                     │
│          → Predictions: 0.84                                     │
│          → Constraints: 1.00                                     │
│          → Pareto ranking: 1.00                                  │
│          → Component agreement: 1.00                             │
│          → Overall: 0.847                                        │
│                                                                   │
│ T+2587ms: Generate Reasoning                                     │
│          → Selection rationale documented                        │
│          → Tradeoff analysis completed                           │
│                                                                   │
│ T+2589ms: ✅ COMPLETE - Return results                           │
│          Duration: 2589ms                                        │
└─────────────────────────────────────────────────────────────────┘

Execution Summary:
  • Components Evaluated: 3/3 (Optimizer, Digital Twin, Reliability)
  • Designs Generated: 100 → Optimized → 23 Pareto → 5 Final
  • Confidence: 0.847 (HIGH)
  • Best Design Score: 0.823 (normalized multi-objective)
  • Execution Time: 2589ms (within budget)
""")


async def main():
    """Run all examples"""
    
    print("\n" + "="*70)
    print("SILIQUESTA AGENTIC ORCHESTRATOR - COMPLETE EXAMPLES")
    print("="*70)
    print("\nDemonstrating execution-based autonomous design optimization")
    print("with natural language understanding and multi-component coordination.")
    
    # Run examples
    await example_1_parse_and_understand_intent()
    await example_2_orchestrator_execution_plan()
    await example_3_confidence_computation()
    await example_4_multi_objective_scoring()
    await example_5_pareto_front_explanation()
    await example_6_execution_trace()
    
    print("\n" + "="*70)
    print("EXAMPLES COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Start the API server: uvicorn services.api.app.main:app --reload")
    print("  2. Open Swagger UI: http://localhost:8000/docs")
    print("  3. Try the /api/v1/orchestrator/optimize endpoint")
    print("  4. Experiment with different design specifications")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
