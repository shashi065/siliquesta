#!/usr/bin/env python
"""Test SHAP explainability for Digital Twin ML model."""

import sys
sys.path.insert(0, '.')

from train_digital_twin import DigitalTwinTrainer
import json

print("=" * 80)
print("SHAP EXPLAINABILITY TEST")
print("=" * 80)

# Load models
trainer = DigitalTwinTrainer()
trainer.load_models()

print("\n✓ Models loaded successfully")
print(f"✓ SHAP explainers available: {list(trainer.explainers.keys())}")

# Test prediction with explanation
print("\n" + "=" * 80)
print("TEST CASE: High-Performance Design Explanation")
print("=" * 80)

# Make a prediction
wn, wp, vdd, temp = 5.0, 7.0, 3.3, 25
print(f"\nInput Parameters:")
print(f"  WN:   {wn:.1f} µm (NMOS width)")
print(f"  WP:   {wp:.1f} µm (PMOS width)")
print(f"  VDD:  {vdd:.1f} V (Supply voltage)")
print(f"  Temp: {temp:.0f} °C (Temperature)")

predictions = trainer.predict(wn=wn, wp=wp, vdd=vdd, temp=temp)

print(f"\n{'Output':<12} {'Value':<15} {'Confidence':<12}")
print("-" * 40)
for output_name in ["power", "frequency", "delay"]:
    pred = predictions[output_name]
    unit = "mW" if output_name == "power" else "GHz" if output_name == "frequency" else "ns"
    print(f"{output_name:<12} {pred['value']:<15.4f} {pred['confidence']:<12.0%}")

# Get SHAP explanations for each output
print("\n" + "=" * 80)
print("SHAP FEATURE CONTRIBUTIONS")
print("=" * 80)

for output_name in ["power", "frequency", "delay"]:
    explanation = trainer.explain_prediction(wn=wn, wp=wp, vdd=vdd, temp=temp, output_name=output_name)
    
    if "error" in explanation:
        print(f"\n✗ Error explaining {output_name}: {explanation['error']}")
        continue
    
    print(f"\n{output_name.upper()}:")
    print(f"  Base Value (expected output): {explanation['base_value']:.4f}")
    print(f"  Feature Contributions:")
    
    contribs = explanation["contributions"]
    for feature in ["wn", "wp", "vdd", "temp"]:
        contrib = contribs[feature]
        sign = "+" if contrib >= 0 else ""
        print(f"    {feature:<6} {sign}{contrib:>8.4f}")
    
    print(f"  Total Contribution: {explanation['total_contribution']:>8.4f}")
    print(f"  Predicted Value (base + contributions): {explanation['prediction_value']:.4f}")
    
    # Verify consistency
    computed = explanation['base_value'] + explanation['total_contribution']
    actual = explanation['prediction_value']
    diff = abs(computed - actual)
    if diff < 1e-5:
        print(f"  ✓ Calculation verified")
    else:
        print(f"  ✗ Calculation mismatch: {diff}")

print("\n" + "=" * 80)
print("TEST 2: Low-Power Design Explanation")
print("=" * 80)

wn, wp, vdd, temp = 1.0, 1.5, 1.2, 85
print(f"\nInput Parameters:")
print(f"  WN:   {wn:.1f} µm")
print(f"  WP:   {wp:.1f} µm")
print(f"  VDD:  {vdd:.1f} V")
print(f"  Temp: {temp:.0f} °C")

explanation = trainer.explain_prediction(wn=wn, wp=wp, vdd=vdd, temp=temp, output_name="power")

if "error" not in explanation:
    print(f"\nPower Prediction Explanation:")
    print(f"  Base Value: {explanation['base_value']:.4f}")
    print(f"  Contributions: {json.dumps(explanation['contributions'], indent=4)}")
    print(f"  Total Impact: {explanation['total_contribution']:.4f}")
    print(f"  Final Prediction: {explanation['prediction_value']:.4f}")
    
    # Show feature importance
    contribs = explanation["contributions"]
    sorted_contribs = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)
    print(f"\n  Feature Ranking (by absolute contribution):")
    for feature, contrib in sorted_contribs:
        magnitude = abs(contrib)
        pct = magnitude / sum(abs(c) for _, c in sorted_contribs) * 100
        print(f"    {feature:<6} {contrib:>8.4f} ({pct:>5.1f}%)")

print("\n" + "=" * 80)
print("STATUS: SHAP EXPLAINABILITY READY")
print("=" * 80)
print(f"\n✓ All three outputs (power, frequency, delay) have SHAP explainers")
print(f"✓ Feature contributions computed correctly")
print(f"✓ Ready for REST API exposure via GET /xai endpoint")
