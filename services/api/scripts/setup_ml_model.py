"""
Quick start script for ML model setup.

Generates dataset, trains model, and saves checkpoint.
Run this before using ML-based optimization.

Usage:
  python setup_ml_model.py  # Generate new dataset
  python setup_ml_model.py --skip-generation  # Use existing dataset
"""

import sys
import argparse
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.dataset_generator import generate_and_save_dataset, DatasetGenerator
from app.services.ml_model import CircuitPredictor, DataNormalizer
from scripts.train_ml_model import CircuitDataset, ModelTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_ml_model(skip_generation: bool = False, use_simulation: bool = False):
    """
    Setup ML model with dataset generation and training.
    
    Args:
        skip_generation: Use existing dataset if available
        use_simulation: Use physics simulator for dataset (slower but more accurate)
    """
    logger.info("=" * 70)
    logger.info("ML MODEL SETUP")
    logger.info("=" * 70)
    
    # Step 1: Generate or load dataset
    logger.info("\n[Step 1] Dataset Preparation")
    logger.info("-" * 70)
    
    if skip_generation:
        # Try to load existing dataset
        datasets = DatasetGenerator.list_datasets()
        if datasets:
            dataset_name = datasets[-1]  # Use most recent
            logger.info(f"Loading existing dataset: {dataset_name}")
            df = DatasetGenerator.load_dataset(dataset_name)
        else:
            logger.warning("No existing datasets found, generating new")
            skip_generation = False
    
    if not skip_generation:
        logger.info("Generating new dataset (5000 samples, synthetic data)")
        logger.info("Note: Use --use-simulation for physics-accurate data (slower)")
        df = generate_and_save_dataset(
            num_samples=5000,
            use_simulation=use_simulation,
            save=True
        )
    
    logger.info(f"Dataset loaded: {len(df)} samples, {df.shape[1]} features")
    logger.info(f"Parameters: {', '.join([c for c in df.columns if c not in ['frequency', 'delay', 'power', 'gain', 'health_score']])}")
    logger.info(f"Targets: frequency, delay, power, gain, health_score")
    
    # Step 2: Prepare data
    logger.info("\n[Step 2] Data Preparation")
    logger.info("-" * 70)
    
    normalizer = DataNormalizer()
    dataset = CircuitDataset(df, normalizer)
    
    logger.info(f"Dataset prepared: {len(dataset)} samples")
    
    # Split into train/val/test
    train_df, val_df, test_df = DatasetGenerator().split_dataset(
        df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    train_dataset = CircuitDataset(train_df, normalizer)
    val_dataset = CircuitDataset(val_df, normalizer)
    test_dataset = CircuitDataset(test_df, normalizer)
    
    # Step 3: Create and train model
    logger.info("\n[Step 3] Model Training")
    logger.info("-" * 70)
    
    import torch
    from torch.utils.data import DataLoader
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    model = CircuitPredictor()
    trainer = ModelTrainer(model, device=device, learning_rate=0.001)
    
    logger.info("Training model (50 epochs)...")
    trainer.train(
        train_loader,
        val_loader,
        num_epochs=50,
        early_stopping_patience=15
    )
    
    # Step 4: Evaluate
    logger.info("\n[Step 4] Model Evaluation")
    logger.info("-" * 70)
    
    test_loss, r2_score = trainer.test(test_loader)
    logger.info(f"Test Loss: {test_loss:.6f}")
    logger.info(f"R² Score: {r2_score:.4f}")
    
    # Step 5: Save model
    logger.info("\n[Step 5] Model Checkpoint")
    logger.info("-" * 70)
    
    model.save(version="default")
    logger.info("Model saved as: circuit_predictor_default.pt")
    
    # Step 6: Quick inference test
    logger.info("\n[Step 6] Inference Test")
    logger.info("-" * 70)
    
    test_params = {
        "wn": 500,
        "wp": 1000,
        "vdd": 1.2,
        "cl": 1e-12,
        "temp": 27,
        "tech_node": 7.0,
        "corner": "TT",
        "corner_factor": 1.0,
    }
    
    from app.services.ml_model import MLCircuitOptimizer
    
    ml_opt = MLCircuitOptimizer(model_version="default")
    pred = ml_opt.predict(test_params, return_uncertainty=True)
    
    logger.info("Sample prediction:")
    logger.info(f"  Parameters: wn={test_params['wn']}nm, wp={test_params['wp']}nm, vdd={test_params['vdd']}V")
    logger.info(f"  Predicted:")
    for key, val in pred.items():
        if key != "uncertainty":
            logger.info(f"    {key}: {val:.4f}")
    
    logger.info("\n" + "=" * 70)
    logger.info("ML MODEL SETUP COMPLETE")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("1. Start backend: cd backend && python -m uvicorn app.main:app --reload")
    logger.info("2. Call API: POST /api/v1/projects/{id}/optimize-ml")
    logger.info("3. Results include confidence_score and uncertainty_estimates")
    

def main():
    parser = argparse.ArgumentParser(description="Setup ML model for circuit optimization")
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip dataset generation, use existing"
    )
    parser.add_argument(
        "--use-simulation",
        action="store_true",
        help="Use physics simulator for dataset (slower)"
    )
    args = parser.parse_args()
    
    try:
        setup_ml_model(
            skip_generation=args.skip_generation,
            use_simulation=args.use_simulation
        )
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
