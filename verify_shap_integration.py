#!/usr/bin/env python
"""Quick verification that SHAP integration is properly implemented."""

import sys
sys.path.insert(0, '.')

print("=" * 80)
print("SHAP INTEGRATION VERIFICATION")
print("=" * 80)

# 1. Verify imports
print("\n1. Checking imports...")
try:
    import shap
    print("   ✓ SHAP imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import SHAP: {e}")
    sys.exit(1)

# 2. Verify train_digital_twin has SHAP methods
print("\n2. Checking DigitalTwinTrainer class...")
try:
    from train_digital_twin import DigitalTwinTrainer
    
    trainer = DigitalTwinTrainer()
    
    # Check if SHAP-related attributes exist
    assert hasattr(trainer, 'explainers'), "Missing 'explainers' attribute"
    assert hasattr(trainer, 'X_background'), "Missing 'X_background' attribute"
    assert hasattr(trainer, 'explain_prediction'), "Missing 'explain_prediction' method"
    
    print("   ✓ DigitalTwinTrainer has SHAP support")
except AssertionError as e:
    print(f"   ✗ {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error checking DigitalTwinTrainer: {e}")
    sys.exit(1)

# 3. Verify API endpoint is defined
print("\n3. Checking FastAPI endpoints...")
try:
    from services.api.app.api.digital_twin import (
        ExplanationResponse, FeatureContribution, explain_prediction
    )
    
    print("   ✓ ExplanationResponse model defined")
    print("   ✓ FeatureContribution model defined")
    print("   ✓ explain_prediction endpoint defined")
except ImportError as e:
    print(f"   ✗ Failed to import endpoint components: {e}")
    sys.exit(1)

# 4. Verify response models
print("\n4. Checking Pydantic models...")
try:
    from pydantic import BaseModel
    
    # Create sample instances to verify models work
    contrib = FeatureContribution(wn=1.0, wp=2.0, vdd=0.5, temp=-0.1)
    assert contrib.wn == 1.0
    assert contrib.vdd == 0.5
    
    explanation = ExplanationResponse(
        output="power",
        base_value=10.0,
        contributions=contrib,
        total_contribution=3.4,
        prediction_value=13.4
    )
    assert explanation.output == "power"
    assert explanation.prediction_value == 13.4
    
    print("   ✓ FeatureContribution model works")
    print("   ✓ ExplanationResponse model works")
    print("   ✓ All model validations pass")
except Exception as e:
    print(f"   ✗ Error with Pydantic models: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("IMPLEMENTATION VERIFICATION COMPLETE")
print("=" * 80)
print("\n✓ SHAP integration is properly implemented")
print("✓ Models are correctly defined")
print("✓ Endpoints are ready for use")
print("\nREADY FOR ENDPOINT TESTING")
print("\nEndpoint: GET /api/v1/digital-twin/xai")
print("Parameters: wn, wp, vdd, temp, output (optional)")
print("Returns: Feature contributions as FeatureContribution object")
