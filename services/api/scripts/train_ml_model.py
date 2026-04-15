#!/usr/bin/env python3
"""
Train ML model on circuit simulation dataset.

Usage:
  python train_ml_model.py --dataset dataset_5000_<timestamp> --epochs 100
  python train_ml_model.py --generate --num-samples 5000 --epochs 100
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.ml_model import CircuitPredictor, DataNormalizer
from app.services.dataset_generator import DatasetGenerator, DatasetConfig, generate_and_save_dataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitDataset:
    """PyTorch dataset for circuit data."""
    
    def __init__(self, df: pd.DataFrame, normalizer: DataNormalizer):
        """
        Args:
            df: DataFrame with parameters and metrics
            normalizer: DataNormalizer instance
        """
        self.df = df
        self.normalizer = normalizer
        
        # Prepare data
        self.x_data = []
        self.y_data = []
        
        corner_map = {"TT": 0, "SS": 1, "FF": 2, "SF": 3, "FS": 4}
        corner_factors = {"TT": 1.0, "SS": 0.78, "FF": 1.25, "SF": 0.82, "FS": 1.18}
        
        for _, row in df.iterrows():
            params = {
                "wn": row["wn"],
                "wp": row["wp"],
                "vdd": row["vdd"],
                "cl": row["cl"],
                "temp": row["temp"],
                "tech_node": row["tech_node"],
                "corner": row["corner"],
                "corner_factor": corner_factors.get(row["corner"], 1.0),
            }
            
            metrics = {
                "frequency": row["frequency"],
                "delay": row["delay"],
                "power": row["power"],
                "gain": row["gain"],
                "health_score": row["health_score"],
            }
            
            x_norm = self.normalizer.normalize_params(params)
            y_norm = self.normalizer.normalize_metrics(metrics)
            
            self.x_data.append(x_norm)
            self.y_data.append(y_norm)
        
        self.x_data = torch.stack(self.x_data)
        self.y_data = torch.stack(self.y_data)
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        return self.x_data[idx], self.y_data[idx]


class ModelTrainer:
    """Train circuit predictor model."""
    
    def __init__(
        self,
        model: CircuitPredictor,
        device: str = "cpu",
        learning_rate: float = 0.001,
    ):
        """
        Args:
            model: CircuitPredictor to train
            device: "cpu" or "cuda"
            learning_rate: Initial learning rate
        """
        self.model = model
        self.device = device
        self.model.to(device)
        
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=10,
            verbose=True
        )
        self.criterion = nn.MSELoss()
        
        self.train_losses = []
        self.val_losses = []
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        
        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            # Forward
            self.optimizer.zero_grad()
            y_pred = self.model(x_batch)
            loss = self.criterion(y_pred, y_batch)
            
            # Backward
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item() * len(x_batch)
        
        avg_loss = total_loss / len(train_loader.dataset)
        return avg_loss
    
    def validate(self, val_loader: DataLoader) -> float:
        """Validate model."""
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for x_batch, y_batch in val_loader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                y_pred = self.model(x_batch)
                loss = self.criterion(y_pred, y_batch)
                
                total_loss += loss.item() * len(x_batch)
        
        avg_loss = total_loss / len(val_loader.dataset)
        return avg_loss
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 100,
        early_stopping_patience: int = 20,
    ) -> Tuple[float, float]:
        """
        Train model for specified epochs.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Total epochs
            early_stopping_patience: Stop if validation loss doesn't improve
        
        Returns:
            (final_train_loss, final_val_loss)
        """
        best_val_loss = np.inf
        patience_counter = 0
        
        for epoch in range(num_epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)
            
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            
            self.scheduler.step(val_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1:3d}/{num_epochs} | "
                    f"Train Loss: {train_loss:.6f} | "
                    f"Val Loss: {val_loss:.6f}"
                )
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
        
        logger.info(f"Training complete: train_loss={train_loss:.6f}, val_loss={val_loss:.6f}")
        return train_loss, val_loss
    
    def test(self, test_loader: DataLoader) -> Tuple[float, float]:
        """
        Evaluate on test set and compute metrics.
        
        Returns:
            (test_loss, r2_score)
        """
        self.model.eval()
        total_loss = 0.0
        y_all = []
        y_pred_all = []
        
        with torch.no_grad():
            for x_batch, y_batch in test_loader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                y_pred = self.model(x_batch)
                loss = self.criterion(y_pred, y_batch)
                
                total_loss += loss.item() * len(x_batch)
                y_all.append(y_batch.cpu())
                y_pred_all.append(y_pred.cpu())
        
        avg_loss = total_loss / len(test_loader.dataset)
        
        # Compute R² score
        y_all = torch.cat(y_all)
        y_pred_all = torch.cat(y_pred_all)
        ss_res = torch.sum((y_all - y_pred_all) ** 2)
        ss_tot = torch.sum((y_all - y_all.mean()) ** 2)
        r2_score = 1.0 - (ss_res / ss_tot).item()
        
        logger.info(f"Test Loss: {avg_loss:.6f}, R² Score: {r2_score:.4f}")
        
        return avg_loss, r2_score


def main():
    parser = argparse.ArgumentParser(description="Train circuit predictor model")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Dataset name (from data/ml_datasets/)"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate new dataset before training"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=5000,
        help="Number of samples to generate (if --generate)"
    )
    parser.add_argument(
        "--use-simulation",
        action="store_true",
        help="Use physics simulator for generation (slower)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="Learning rate"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device (cpu or cuda)"
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default="default",
        help="Model version name"
    )
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("CIRCUIT PREDICTOR MODEL TRAINING")
    logger.info("=" * 70)
    
    # Generate or load dataset
    if args.generate:
        logger.info(f"Generating dataset with {args.num_samples} samples...")
        df = generate_and_save_dataset(
            num_samples=args.num_samples,
            use_simulation=args.use_simulation,
            save=True
        )
    else:
        if not args.dataset:
            logger.error("Either --dataset or --generate must be specified")
            return 1
        
        logger.info(f"Loading dataset: {args.dataset}")
        df = DatasetGenerator.load_dataset(args.dataset)
    
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Samples: {len(df)}")
    
    # Initialize normalizer and dataset
    normalizer = DataNormalizer()
    dataset = CircuitDataset(df, normalizer)
    
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
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0
    )
    
    logger.info(f"Train/Val/Test split: {len(train_dataset)}/{len(val_dataset)}/{len(test_dataset)}")
    
    # Create and train model
    logger.info("Creating model...")
    model = CircuitPredictor()
    
    logger.info(f"Training on {args.device}...")
    trainer = ModelTrainer(
        model,
        device=args.device,
        learning_rate=args.learning_rate
    )
    
    trainer.train(
        train_loader,
        val_loader,
        num_epochs=args.epochs,
        early_stopping_patience=20
    )
    
    # Test
    logger.info("Evaluating on test set...")
    test_loss, r2_score = trainer.test(test_loader)
    
    # Save model
    logger.info(f"Saving model (version={args.model_version})...")
    model.save(version=args.model_version)
    
    logger.info("=" * 70)
    logger.info("TRAINING COMPLETE")
    logger.info(f"Model saved as: circuit_predictor_{args.model_version}.pt")
    logger.info(f"Test Loss: {test_loss:.6f}")
    logger.info(f"R² Score: {r2_score:.4f}")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
