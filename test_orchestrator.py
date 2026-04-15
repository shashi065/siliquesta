#!/usr/bin/env python3
"""
Test script for the AI Orchestrator endpoint.

Demonstrates:
1. Intent parsing (minimize power, maximize frequency, balance)
2. Design space exploration (20 candidate designs)
3. Multi-objective optimization (Pareto front)
4. SHAP explanations for best design
5. Recommendations
"""

import requests
import json
from typing import Dict, Any

# API endpoint
ORCHESTRATOR_URL = "http://localhost:8000/ts/digital_twin/orchestrate"

def test_orchestrator_minimize_power():
    """Test: Minimize power consumption"""
    print("\n" + "="*80)
    print("TEST 1: Minimize Power Consumption")
    print("="*80)
    
    request_body = {
        "intent": "minimize power consumption",
        "constraints": {
            "max_power_mw": 5.0,
            "min_frequency_ghz": 1.0,
            "min_lifetime_years": 10.0,
        },
        "num_designs": 20,
        "vdd": 1.2,
        "temp": 27.0,
        "cl_ff": 10.0,
    }
    
    print("\nRequest:")
    print(json.dumps(request_body, indent=2))
    
    try:
        response = requests.post(ORCHESTRATOR_URL, json=request_body, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print("\n✅ Response Status:", response.status_code)
        print("\nParsed Intent:", result.get("intent"))
        print("Dominant Metric:", result.get("dominant_metric"))
        print("Designs Evaluated:", result.get("design_count"))
        
        best = result.get("best_design", {})
        print("\n--- BEST DESIGN ---")
        print(f"Design ID: {best.get('design_id')}")
        print(f"Transistor Sizes: wn={best.get('wn'):.2f}um, wp={best.get('wp'):.2f}um")
        print(f"Power: {best.get('power_mw'):.3f} mW")
        print(f"Frequency: {best.get('frequency_ghz'):.3f} GHz")
        print(f"Reliability Score: {best.get('reliability_score'):.3f} [0-1]")
        print(f"Lifetime: {best.get('lifetime_years'):.1f} years")
        print(f"Failure Mode: {best.get('dominant_failure_mode')}")
        
        pareto = result.get("pareto_front", [])
        print(f"\n--- PARETO FRONT ---")
        print(f"Designs on frontier: {len(pareto)}")
        for i, design in enumerate(pareto[:3]):  # Show top 3
            print(f"  [{i+1}] Power={design.get('power_mw'):.3f}mW, "
                  f"Freq={design.get('frequency_ghz'):.3f}GHz, "
                  f"Reliability={design.get('reliability_score'):.3f}")
        
        print("\n--- TRADE-OFF ANALYSIS ---")
        tradeoffs = result.get("trade_offs", {})
        print(f"Power range: {tradeoffs.get('power_range_mw', [0, 0])[0]:.3f} - "
              f"{tradeoffs.get('power_range_mw', [0, 0])[1]:.3f} mW")
        print(f"Frequency range: {tradeoffs.get('frequency_range_ghz', [0, 0])[0]:.3f} - "
              f"{tradeoffs.get('frequency_range_ghz', [0, 0])[1]:.3f} GHz")
        
        print("\n--- EXPLANATIONS (SHAP) ---")
        explanation = result.get("best_design_explanation", {})
        if explanation:
            print(f"Explanation Method: {explanation.get('method')}")
            contributions = explanation.get("contributions", {})
            for feature, value in list(contributions.items())[:3]:  # Top 3 features
                print(f"  {feature}: {value}")
        
        print("\n--- RECOMMENDATIONS ---")
        recs = result.get("recommendations", [])
        for rec in recs:
            print(f"  • {rec}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")


def test_orchestrator_maximize_frequency():
    """Test: Maximize frequency"""
    print("\n" + "="*80)
    print("TEST 2: Maximize Frequency")
    print("="*80)
    
    request_body = {
        "intent": "maximize frequency performance",
        "constraints": {
            "max_power_mw": 15.0,
            "min_frequency_ghz": 2.0,
            "min_lifetime_years": 5.0,
        },
        "num_designs": 20,
        "vdd": 1.8,
        "temp": 85.0,
        "cl_ff": 5.0,
    }
    
    print("\nRequest:")
    print(json.dumps(request_body, indent=2))
    
    try:
        response = requests.post(ORCHESTRATOR_URL, json=request_body, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        best = result.get("best_design", {})
        
        print(f"\n✅ Best Design Found:")
        print(f"  Power: {best.get('power_mw'):.3f} mW")
        print(f"  Frequency: {best.get('frequency_ghz'):.3f} GHz")
        print(f"  Reliability: {best.get('reliability_score'):.3f}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")


def test_orchestrator_balanced():
    """Test: Balanced optimization"""
    print("\n" + "="*80)
    print("TEST 3: Balanced Optimization")
    print("="*80)
    
    request_body = {
        "intent": "find balanced design with good power and performance",
        "num_designs": 25,
        "vdd": 1.5,
        "temp": 50.0,
        "cl_ff": 8.0,
    }
    
    print("\nRequest:")
    print(json.dumps(request_body, indent=2))
    
    try:
        response = requests.post(ORCHESTRATOR_URL, json=request_body, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        best = result.get("best_design", {})
        
        print(f"\n✅ Balanced Design Found:")
        print(f"  Design ID: {best.get('design_id')}")
        print(f"  Power: {best.get('power_mw'):.3f} mW")
        print(f"  Frequency: {best.get('frequency_ghz'):.3f} GHz")
        print(f"  Lifetime: {best.get('lifetime_years'):.1f} years")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AI ORCHESTRATOR ENDPOINT TESTS")
    print("="*80)
    print("\nMake sure the API server is running on http://localhost:8000")
    print("If not, don't panic - these tests just check the API response structure.")
    
    test_orchestrator_minimize_power()
    test_orchestrator_maximize_frequency()
    test_orchestrator_balanced()
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)
