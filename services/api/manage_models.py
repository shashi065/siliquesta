#!/usr/bin/env python
"""
Management script for training and managing ML prediction models.

Usage:
    python manage_models.py train --samples 10000 --name cmos_predictor_v1
    python manage_models.py list
    python manage_models.py info --name cmos_predictor_v1
"""

import argparse
import sys
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.ml_prediction_model import (
    XGBoostCMOSPredictor,
    train_and_save_model,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def train_model(samples: int, name: str):
    """Train a new model."""
    logger.info(f"Training model: {name} with {samples} samples")
    
    try:
        predictor = train_and_save_model(
            n_samples=samples,
            model_name=name
        )
        
        logger.info(f"✓ Model trained successfully")
        logger.info(f"  Name: {name}")
        logger.info(f"  Samples: {samples}")
        logger.info(f"  Date: {predictor.metadata['training_date']}")
        logger.info(f"  Location: models/{name}")
        
        # Print performance metrics
        logger.info("\nPerformance Metrics:")
        for target, metrics in predictor.metadata["performance_metrics"].items():
            logger.info(f"\n  {target.upper()}:")
            logger.info(f"    R²: {metrics.get('r2', 0):.4f}")
            logger.info(f"    RMSE: {metrics.get('rmse', 0):.6e}")
            logger.info(f"    MAE: {metrics.get('mae', 0):.6e}")
            logger.info(f"    CV R² Mean: {metrics.get('cv_r2_mean', 0):.4f}")
            
    except Exception as e:
        logger.error(f"✗ Training failed: {e}")
        sys.exit(1)


def list_models():
    """List all available models."""
    model_dir = Path("models")
    
    if not model_dir.exists():
        logger.info("No models directory found.")
        return
    
    models = [d for d in model_dir.iterdir() if d.is_dir()]
    
    if not models:
        logger.info("No trained models found.")
        return
    
    logger.info(f"Found {len(models)} trained model(s):\n")
    
    for model_path in sorted(models):
        metadata_file = model_path / "metadata.json"
        
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            logger.info(f"  {model_path.name}:")
            logger.info(f"    Trained: {metadata.get('trained', False)}")
            logger.info(f"    Date: {metadata.get('training_date', 'N/A')}")
            logger.info(f"    Samples: {metadata.get('training_samples', 0)}")
            logger.info(f"    Metrics: {list(metadata.get('performance_metrics', {}).keys())}\n")


def model_info(name: str):
    """Get information about a specific model."""
    model_dir = Path("models")
    model_path = model_dir / name
    metadata_file = model_path / "metadata.json"
    
    if not metadata_file.exists():
        logger.error(f"✗ Model '{name}' not found")
        sys.exit(1)
    
    import json
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    logger.info(f"\nModel: {name}")
    logger.info(f"Trained: {metadata.get('trained')}")
    logger.info(f"Training Date: {metadata.get('training_date')}")
    logger.info(f"Training Samples: {metadata.get('training_samples')}")
    logger.info(f"Features: {metadata.get('feature_names')}")
    
    logger.info("\nPerformance Metrics:")
    for target, metrics in metadata.get("performance_metrics", {}).items():
        logger.info(f"\n  {target.upper()}:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"    {metric}: {value:.6f}")
            else:
                logger.info(f"    {metric}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="ML Model Management Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train a new model")
    train_parser.add_argument(
        "--samples",
        type=int,
        default=10000,
        help="Number of training samples (default: 10000)"
    )
    train_parser.add_argument(
        "--name",
        type=str,
        default="cmos_predictor_v1",
        help="Model name (default: cmos_predictor_v1)"
    )
    
    # List command
    subparsers.add_parser("list", help="List all trained models")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get model information")
    info_parser.add_argument(
        "--name",
        type=str,
        default="cmos_predictor_v1",
        help="Model name (default: cmos_predictor_v1)"
    )
    
    args = parser.parse_args()
    
    if args.command == "train":
        train_model(args.samples, args.name)
    elif args.command == "list":
        list_models()
    elif args.command == "info":
        model_info(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
