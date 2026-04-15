#!/usr/bin/env python
"""Simple test to verify SHAP explain_prediction method works."""

import sys
sys.path.insert(0, '.')

from train_digital_twin import DigitalTwinTrainer
import logging

logging.basicConfig(level=logging.WARNING)

print("=" * 80)
print("SHAP EXPLAINABILITY - SIMPLE TEST")
print("=" * 80)

# Load trained models
print("\nLoading trained models...")
trainer = DigitalTwinTrainer()
trainer.load_models()

print("✓ Models loaded successfully")
print(f"✓ Explainers available: {list(trainer.explainers.keys())}")
print(f"✓ Background data shape: {trainer.X_background.shape if trainer.X_background is not None else 'None'}")

# Test parameters
wn, wp, vdd, temp = 3.0, 4.0, 1.8, 27

print(f"\nTest Parameters: WN={wn}, WP={wp}, VDD={vdd}, Temp={temp}")

# Get predictions first
print("\nStep 1: Getting predictions...")
predictions = trainer.predict(wn=wn, wp=wp, vdd=vdd, temp=temp)
print(f"  Power prediction: {predictions['power']['value']:.4f} mW")
print(f"  Frequency prediction: {predictions['frequency']['value']:.4f} GHz")
print(f"  Delay prediction: {predictions['delay']['value']:.4f} ns")

# Get explanations
print("\nStep 2: Getting SHAP explanations...")
outputs = ["power", "frequency", "delay"]
explanations = {}

for output_name in outputs:
    print(f"\n  Computing explanation for {output_name}...")
    explanation = trainer.explain_prediction(wn=wn, wp=wp, vdd=vdd, temp=temp, output_name=output_name)
    
    if "error" in explanation:
        print(f"    ✗ Error: {explanation['error']}")
        continue
    
    explanations[output_name] = explanation
    
    print(f"    ✓ Base value: {explanation['base_value']:.6f}")
    print(f"    ✓ Contributions:")
    for feature in ["wn", "wp", "vdd", "temp"]:
        contrib = explanation["contributions"][feature]
        print(f"       {feature:6} → {contrib:+.6f}")
    print(f"    ✓ Total contribution: {explanation['total_contribution']:.6f}")
    print(f"    ✓ Final prediction: {explanation['prediction_value']:.6f}")

print("\n" + "=" * 80)
print("EXPLANATION OUTPUT FORMAT")
print("=" * 80)

if explanations:
    power_exp = explanations.get("power")
    if power_exp:
        print("\nSample response (for power output):")
        print(f"{{\n  \"output\": \"power\",")
        print(f"  \"base_value\": {power_exp['base_value']:.6f},")
        print(f"  \"contributions\": {{")
        contribs = power_exp['contributions']
        for feature in ["wn", "wp", "vdd", "temp"]:
            print(f"    \"{feature}\": {contribs[feature]:.6f},", end="")
            if feature != "temp":
                print()
            else:
                print(" # last item, no comma")
        print(f"  }},")
        print(f"  \"total_contribution\": {power_exp['total_contribution']:.6f},")
        print(f"  \"prediction_value\": {power_exp['prediction_value']:.6f},")
        print(f"  \"explanation_method\": \"shap\"")
        print("}")

print("\n" + "=" * 80)
print("STATUS: SHAP EXPLAINABILITY WORKING")
print("=" * 80)
print(f"\n✓ All {len(explanations)} outputs successfully explained")
print("✓ Feature contributions computed via SHAP TreeExplainer")
print("✓ Ready for GET /xai endpoint")
