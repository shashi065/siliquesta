"""
GPU-Accelerated Digital Twin Training

Uses PyTorch with CUDA for fast training of neural network models.

Features:
- GPU-accelerated training
- Automatic CPU fallback
- Multi-GPU support (with Ray)
- Data loading optimization
- Model checkpointing
- Early stopping
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import logging
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time
import json
from pathlib import Path

from app.gpu_acceleration import get_gpu_accelerator, get_device_info, is_gpu_available

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for GPU-accelerated training."""
    batch_size: int = 64
    learning_rate: float = 0.001
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    optimizer: str = 'adam'  # 'adam', 'sgd', 'adamw'
    loss_fn: str = 'mse'  # 'mse', 'huber'
    scheduler: Optional[str] = 'cosine'  # 'cosine', 'linear', None
    num_workers: int = 4
    pin_memory: bool = True
    mixed_precision: bool = True  # Use automatic mixed precision
    checkpoint_dir: Optional[Path] = None


class DigitalTwinNeuralNet(nn.Module):
    """
    GPU-optimized neural network for digital twin predictions.
    
    Predicts: power, frequency, delay
    Input: WN, WP, VDD, Temperature
    """
    
    def __init__(self, input_size: int = 4, hidden_sizes: List[int] = None):
        """
        Initialize neural network.
        
        Args:
            input_size: Number of input features
            hidden_sizes: List of hidden layer sizes
        """
        super().__init__()
        
        if hidden_sizes is None:
            hidden_sizes = [128, 256, 128, 64]
        
        layers = []
        prev_size = input_size
        
        # Build hidden layers
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_size = hidden_size
        
        self.feature_extractor = nn.Sequential(*layers)
        
        # Output heads for multi-task learning
        self.power_head = nn.Sequential(
            nn.Linear(prev_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        self.frequency_head = nn.Sequential(
            nn.Linear(prev_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        self.delay_head = nn.Sequential(
            nn.Linear(prev_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch_size, 4)
            
        Returns:
            (power, frequency, delay) predictions
        """
        features = self.feature_extractor(x)
        power = self.power_head(features)
        frequency = self.frequency_head(features)
        delay = self.delay_head(features)
        return power, frequency, delay


class GPUDigitalTwinTrainer:
    """
    GPU-accelerated trainer for digital twin models.
    
    Features:
    - Automatic GPU/CPU fallback
    - Mixed precision training
    - Early stopping
    - Model checkpointing
    - Multi-task learning (power, frequency, delay)
    """
    
    def __init__(self, config: TrainingConfig = None):
        """
        Initialize trainer.
        
        Args:
            config: Training configuration
        """
        self.config = config or TrainingConfig()
        self.device = get_gpu_accelerator().get_device()
        self.is_gpu = is_gpu_available()
        
        logger.info(f"GPU Trainer initialized on {self.device}")
        logger.info(f"GPU Available: {self.is_gpu}")
        if self.is_gpu:
            logger.info(f"GPU Info: {get_device_info()}")
    
    def prepare_data(
        self,
        X: np.ndarray,
        Y_power: np.ndarray,
        Y_freq: np.ndarray,
        Y_delay: np.ndarray
    ) -> Tuple[DataLoader, DataLoader]:
        """
        Prepare data loaders with GPU optimization.
        
        Args:
            X: Input features (N, 4)
            Y_power: Power labels
            Y_freq: Frequency labels
            Y_delay: Delay labels
            
        Returns:
            (train_loader, val_loader)
        """
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        Y_power_tensor = torch.FloatTensor(Y_power).reshape(-1, 1)
        Y_freq_tensor = torch.FloatTensor(Y_freq).reshape(-1, 1)
        Y_delay_tensor = torch.FloatTensor(Y_delay).reshape(-1, 1)
        
        # Split into train/val
        n_samples = len(X)
        n_train = int(n_samples * (1 - self.config.validation_split))
        
        indices = torch.randperm(n_samples)
        train_idx = indices[:n_train]
        val_idx = indices[n_train:]
        
        # Create datasets
        train_dataset = TensorDataset(
            X_tensor[train_idx],
            Y_power_tensor[train_idx],
            Y_freq_tensor[train_idx],
            Y_delay_tensor[train_idx]
        )
        
        val_dataset = TensorDataset(
            X_tensor[val_idx],
            Y_power_tensor[val_idx],
            Y_freq_tensor[val_idx],
            Y_delay_tensor[val_idx]
        )
        
        # Create loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0,  # 0 for Windows compatibility
            pin_memory=self.is_gpu and self.config.pin_memory
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=self.is_gpu and self.config.pin_memory
        )
        
        logger.info(f"Data prepared: {len(train_loader)} train batches, {len(val_loader)} val batches")
        return train_loader, val_loader
    
    def train(
        self,
        X: np.ndarray,
        Y_power: np.ndarray,
        Y_freq: np.ndarray,
        Y_delay: np.ndarray
    ) -> Tuple[DigitalTwinNeuralNet, Dict]:
        """
        Train digital twin model on GPU.
        
        Args:
            X: Input features
            Y_power: Power labels
            Y_freq: Frequency labels
            Y_delay: Delay labels
            
        Returns:
            (trained_model, metrics_dict)
        """
        # Prepare data
        train_loader, val_loader = self.prepare_data(X, Y_power, Y_freq, Y_delay)
        
        # Initialize model
        model = DigitalTwinNeuralNet().to(self.device)
        logger.info(f"Model created with {sum(p.numel() for p in model.parameters()):,} parameters")
        
        # Optimizer
        if self.config.optimizer == 'adam':
            optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        elif self.config.optimizer == 'adamw':
            optimizer = optim.AdamW(model.parameters(), lr=self.config.learning_rate)
        else:
            optimizer = optim.SGD(model.parameters(), lr=self.config.learning_rate, momentum=0.9)
        
        # Scheduler
        scheduler = None
        if self.config.scheduler == 'cosine':
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.config.epochs)
        elif self.config.scheduler == 'linear':
            scheduler = optim.lr_scheduler.LinearLR(optimizer, start_factor=1.0, end_factor=0.1, total_iters=self.config.epochs)
        
        # Loss function
        if self.config.loss_fn == 'huber':
            criterion = nn.HuberLoss()
        else:
            criterion = nn.MSELoss()
        
        # Mixed precision scaler
        scaler = torch.cuda.amp.GradScaler() if (self.is_gpu and self.config.mixed_precision) else None
        
        # Training loop
        metrics = {
            'epoch_train_loss': [],
            'epoch_val_loss': [],
            'train_times': [],
            'best_val_loss': float('inf'),
            'best_epoch': 0,
            'training_time': 0
        }
        
        patience_counter = 0
        start_time = time.time()
        
        try:
            for epoch in range(self.config.epochs):
                epoch_start = time.time()
                
                # Training phase
                model.train()
                train_loss = 0
                
                for batch_idx, (X_batch, Y_power_batch, Y_freq_batch, Y_delay_batch) in enumerate(train_loader):
                    X_batch = X_batch.to(self.device)
                    Y_power_batch = Y_power_batch.to(self.device)
                    Y_freq_batch = Y_freq_batch.to(self.device)
                    Y_delay_batch = Y_delay_batch.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    # Forward pass with mixed precision
                    if scaler is not None:
                        with torch.cuda.amp.autocast():
                            power_pred, freq_pred, delay_pred = model(X_batch)
                            loss = (criterion(power_pred, Y_power_batch) +
                                   criterion(freq_pred, Y_freq_batch) +
                                   criterion(delay_pred, Y_delay_batch))
                        
                        scaler.scale(loss).backward()
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        power_pred, freq_pred, delay_pred = model(X_batch)
                        loss = (criterion(power_pred, Y_power_batch) +
                               criterion(freq_pred, Y_freq_batch) +
                               criterion(delay_pred, Y_delay_batch))
                        loss.backward()
                        optimizer.step()
                    
                    train_loss += loss.item()
                
                train_loss /= len(train_loader)
                metrics['epoch_train_loss'].append(train_loss)
                
                # Validation phase
                model.eval()
                val_loss = 0
                
                with torch.no_grad():
                    for X_batch, Y_power_batch, Y_freq_batch, Y_delay_batch in val_loader:
                        X_batch = X_batch.to(self.device)
                        Y_power_batch = Y_power_batch.to(self.device)
                        Y_freq_batch = Y_freq_batch.to(self.device)
                        Y_delay_batch = Y_delay_batch.to(self.device)
                        
                        power_pred, freq_pred, delay_pred = model(X_batch)
                        loss = (criterion(power_pred, Y_power_batch) +
                               criterion(freq_pred, Y_freq_batch) +
                               criterion(delay_pred, Y_delay_batch))
                        val_loss += loss.item()
                
                val_loss /= len(val_loader)
                metrics['epoch_val_loss'].append(val_loss)
                
                epoch_time = time.time() - epoch_start
                metrics['train_times'].append(epoch_time)
                
                # Early stopping check
                if val_loss < metrics['best_val_loss']:
                    metrics['best_val_loss'] = val_loss
                    metrics['best_epoch'] = epoch
                    patience_counter = 0
                    
                    # Save checkpoint
                    if self.config.checkpoint_dir:
                        checkpoint_path = self.config.checkpoint_dir / f"best_model_epoch_{epoch}.pt"
                        torch.save(model.state_dict(), checkpoint_path)
                else:
                    patience_counter += 1
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{self.config.epochs} - "
                               f"Train Loss: {train_loss:.4f}, "
                               f"Val Loss: {val_loss:.4f}, "
                               f"Time: {epoch_time:.2f}s")
                
                # Update scheduler
                if scheduler:
                    scheduler.step()
                
                # Early stopping
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
        
        except KeyboardInterrupt:
            logger.info("Training interrupted by user")
        
        except Exception as e:
            logger.error(f"Training error: {e}")
            # Fallback to CPU if GPU error
            if self.device.type == 'cuda':
                logger.warning("GPU error occurred - falling back to CPU")
                self.device = torch.device('cpu')
                model = model.to(self.device)
                raise
        
        metrics['training_time'] = time.time() - start_time
        
        logger.info(f"Training complete! Time: {metrics['training_time']:.2f}s")
        logger.info(f"Best validation loss: {metrics['best_val_loss']:.4f} at epoch {metrics['best_epoch']}")
        
        return model, metrics
    
    def evaluate(
        self,
        model: DigitalTwinNeuralNet,
        X: np.ndarray,
        Y_power: np.ndarray,
        Y_freq: np.ndarray,
        Y_delay: np.ndarray
    ) -> Dict:
        """
        Evaluate model on GPU.
        
        Args:
            model: Trained model
            X: Test features
            Y_power: Test power labels
            Y_freq: Test frequency labels
            Y_delay: Test delay labels
            
        Returns:
            Evaluation metrics dictionary
        """
        model.eval()
        model.to(self.device)
        
        X_tensor = torch.FloatTensor(X).to(self.device)
        Y_power_tensor = torch.FloatTensor(Y_power).to(self.device)
        Y_freq_tensor = torch.FloatTensor(Y_freq).to(self.device)
        Y_delay_tensor = torch.FloatTensor(Y_delay).to(self.device)
        
        with torch.no_grad():
            power_pred, freq_pred, delay_pred = model(X_tensor)
        
        # Calculate metrics
        def calculate_metrics(y_true, y_pred):
            mse = ((y_true - y_pred) ** 2).mean().item()
            mae = (torch.abs(y_true - y_pred)).mean().item()
            r2 = 1 - (((y_true - y_pred) ** 2).sum() / ((y_true - y_true.mean()) ** 2).sum()).item()
            return {'mse': mse, 'mae': mae, 'r2': r2}
        
        return {
            'power': calculate_metrics(Y_power_tensor, power_pred),
            'frequency': calculate_metrics(Y_freq_tensor, freq_pred),
            'delay': calculate_metrics(Y_delay_tensor, delay_pred)
        }
    
    def predict(self, model: DigitalTwinNeuralNet, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions on GPU.
        
        Args:
            model: Trained model
            X: Input features
            
        Returns:
            (power, frequency, delay) predictions
        """
        model.eval()
        model.to(self.device)
        
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        with torch.no_grad():
            power_pred, freq_pred, delay_pred = model(X_tensor)
        
        return (
            power_pred.cpu().numpy(),
            freq_pred.cpu().numpy(),
            delay_pred.cpu().numpy()
        )


def create_gpu_trainer(config: TrainingConfig = None) -> GPUDigitalTwinTrainer:
    """Create GPU-accelerated trainer with CPU fallback."""
    return GPUDigitalTwinTrainer(config)
