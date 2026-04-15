#!/bin/bash
# AI Orchestrator Endpoint - cURL Examples

echo "================================================================================"
echo "AI ORCHESTRATOR - Design Space Exploration"
echo "================================================================================"
echo ""
echo "Endpoint: POST /ts/digital_twin/orchestrate"
echo "Base URL: http://localhost:8000"
echo ""

# Test 1: Minimize Power
echo "TEST 1: Minimize Power Consumption"
echo "================================================================================"
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "minimize power consumption",
    "constraints": {
      "max_power_mw": 5.0,
      "min_frequency_ghz": 1.0,
      "min_lifetime_years": 10.0
    },
    "num_designs": 20,
    "vdd": 1.2,
    "temp": 27.0,
    "cl_ff": 10.0
  }' \
  -w "\n\nStatus: %{http_code}\n" | jq .
echo ""

# Test 2: Maximize Frequency
echo ""
echo "TEST 2: Maximize Frequency"
echo "================================================================================"
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "maximize frequency for high performance",
    "constraints": {
      "max_power_mw": 15.0,
      "min_frequency_ghz": 2.0,
      "min_lifetime_years": 5.0
    },
    "num_designs": 20,
    "vdd": 1.8,
    "temp": 85.0,
    "cl_ff": 5.0
  }' \
  -w "\n\nStatus: %{http_code}\n" | jq .
echo ""

# Test 3: Balanced Design
echo ""
echo "TEST 3: Balanced Optimization (Power & Frequency)"
echo "================================================================================"
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "find balanced design with good power and performance",
    "num_designs": 25,
    "vdd": 1.5,
    "temp": 50.0,
    "cl_ff": 8.0
  }' \
  -w "\n\nStatus: %{http_code}\n" | jq .
echo ""

# Test 4: Maximize Reliability
echo ""
echo "TEST 4: Maximize Device Reliability"
echo "================================================================================"
curl -X POST http://localhost:8000/ts/digital_twin/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "maximize device reliability and lifetime",
    "constraints": {
      "min_lifetime_years": 20.0
    },
    "num_designs": 20,
    "vdd": 1.0,
    "temp": 27.0,
    "cl_ff": 10.0
  }' \
  -w "\n\nStatus: %{http_code}\n" | jq .
echo ""

echo "================================================================================"
echo "EXPECTED RESPONSE STRUCTURE:"
echo "================================================================================"
cat << 'EOF'
{
  "intent": "parsed intent (power/frequency/reliability/balanced)",
  "constraints": {
    "max_power_mw": float,
    "min_frequency_ghz": float,
    "min_lifetime_years": float,
    ...
  },
  "best_design": {
    "design_id": "design_N",
    "wn": float,
    "wp": float,
    "vdd": float,
    "temp": float,
    "cl_ff": float,
    "power_mw": float,
    "frequency_ghz": float,
    "delay_ps": float,
    "reliability_score": float (0-1),
    "lifetime_years": float,
    "dominant_failure_mode": "NBTI|HCI|Electromigration",
    "prediction_confidence": float
  },
  "pareto_front": [
    { ... design 1 ... },
    { ... design 2 ... },
    ...
  ],
  "best_design_explanation": {
    "method": "shap",
    "output": "power",
    "contributions": {
      "wn": float,
      "wp": float,
      "vdd": float,
      "temp": float
    }
  },
  "design_count": int,
  "dominant_metric": "power|frequency|reliability|balanced",
  "trade_offs": {
    "power_range_mw": [min, max],
    "frequency_range_ghz": [min, max],
    "reliability_range": [min, max],
    "designs_on_frontier": int
  },
  "recommendations": [
    "✓ Low-power design...",
    "✓ High-performance design...",
    "✓ N alternative designs available...",
    ...
  ]
}
EOF
echo ""
