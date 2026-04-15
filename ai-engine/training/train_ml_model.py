#!/usr/bin/env python3
"""
Train Digital Twin ML model with enhanced dataset.

Generates comprehensive simulation dataset and trains ensemble model.
"""

import sys
from pathlib import Path
import logging

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.digital_twin_ml import DigitalTwinSurrogateService, DATASET_DIR
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Train digital twin model with enhanced dataset."""
    
    logger.info("=" * 80)
    logger.info("SILIQUESTA Digital Twin ML Model Training")
    logger.info("=" * 80)
    
    # Step 1: Generate dataset
    logger.info("\n[1/4] Generating enhanced training dataset...")
    
    try:
        # Try to use SPICE if available, otherwise use physics engine
        try:
            from app.services.spice_engine import SpiceEngine
            spice_available = True
            try:
                SpiceEngine.ngspice_path()
                logger.info("✓ ngspice found - will generate SPICE-backed samples")
                prefer_spice = True
            except:
                logger.info("⚠ ngspice not available - using physics engine")
                prefer_spice = False
        except:
            prefer_spice = False
            logger.info("⚠ SPICE engine not available - using physics engine")
        
        # Generate 5000 samples with diverse parameter combinations
        logger.info("Generating 5000 diverse circuit samples...")
        rows = DigitalTwinSurrogateService.build_dataset(
            sample_count=5000,
            prefer_spice=prefer_spice,
        )
        logger.info(f"✓ Generated {len(rows)} samples")
        
        # Save dataset
        dataset_path = DATASET_DIR / "digital_twin_dataset.csv"
        output_path = DigitalTwinSurrogateService.save_dataset_csv(rows, dataset_path)
        logger.info(f"✓ Saved dataset to {output_path}")
        
        spice_count = sum(1 for row in rows if row.get("source") == "spice")
        physics_count = len(rows) - spice_count
        logger.info(f"  Dataset composition: {spice_count} SPICE + {physics_count} physics")
        
    except Exception as e:
        logger.error(f"✗ Dataset generation failed: {e}")
        return 1
    
    # Step 2: Initialize service and train
    logger.info("\n[2/4] Initializing Digital Twin service...")
    try:
        service = DigitalTwinSurrogateService()
        logger.info("✓ Service initialized")
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        return 1
    
    # Step 3: Train model
    logger.info("\n[3/4] Training ensemble model (XGBoost + PyTorch)...")
    try:
        metadata = service.train(rows)
        logger.info("✓ Model training complete")
        logger.info(f"  Model family: {metadata.get('model_family')}")
        logger.info(f"  Samples: {metadata.get('sample_count')}")
        logger.info(f"  Trained with SPICE: {metadata.get('trained_with_spice')}")
        logger.info(f"  Dataset version: {metadata.get('dataset_version')}")
    except Exception as e:
        logger.error(f"✗ Model training failed: {e}")
        logger.error("Check that xgboost and torch are installed")
        return 1
    
    # Step 4: Validate model
    logger.info("\n[4/4] Validating model performance...")
    try:
        metrics = metadata.get("metrics", {})
        logger.info("✓ Validation metrics:")
        logger.info(f"  Delay prediction:")
        logger.info(f"    R² Score: {metrics.get('r2_delay', 0):.6f}")
        logger.info(f"    MAPE: {metrics.get('mape_delay_percent', 0):.2f}%")
        logger.info(f"  Power prediction:")
        logger.info(f"    R² Score: {metrics.get('r2_power', 0):.6f}")
        logger.info(f"    MAPE: {metrics.get('mape_power_percent', 0):.2f}%")
        logger.info(f"  Frequency prediction:")
        logger.info(f"    R² Score: {metrics.get('r2_freq', 0):.6f}")
        logger.info(f"    MAPE: {metrics.get('mape_freq_percent', 0):.2f}%")
        logger.info(f"  Mean MAPE: {metrics.get('mean_mape_percent', 0):.2f}%")
        
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        return 1
    
    # Step 5: Test prediction
    logger.info("\n[5/4] Testing prediction capability...")
    try:
        test_pred = service.predict_with_confidence(
            wn=1.0,
            wp=2.0,
            vdd=1.8,
            temp=27.0,
            cl_ff=10.0,
            tech_node=7.0,
            corner="TT",
        )
        logger.info("✓ Test prediction successful:")
        logger.info(f"  Delay: {test_pred.delay_ps:.4f} ps")
        logger.info(f"  Power: {test_pred.power_mw:.4f} mW")
        logger.info(f"  Frequency: {test_pred.freq_ghz:.4f} GHz")
        logger.info(f"  Confidence: {test_pred.confidence:.4f}")
        logger.info(f"  Uncertainty: {test_pred.uncertainty:.6f}")
        logger.info(f"  Est. Error: {test_pred.estimated_error_percent:.2f}%")
        
    except Exception as e:
        logger.error(f"✗ Prediction test failed: {e}")
        return 1
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ TRAINING COMPLETE")
    logger.info("Digital Twin model is ready for production optimization!")
    logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
