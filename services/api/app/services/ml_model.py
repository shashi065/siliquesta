"""
Neural network-based ML model for circuit parameter prediction.

Maps design parameters (W/L, Vdd, CL, temp, tech_node, corner) 
to performance metrics (frequency, delay, power, gain, health).

Uses PyTorch with uncertainty quantification via MC Dropout.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """ML model prediction with uncertainty."""
    optimized_params: Dict[str, float]  # Best predicted parameters
    predicted_metrics: Dict[str, float]  # Frequency, delay, power, etc.
    confidence_score: float  # 0-1, prediction uncertainty
    uncertainty_estimates: Dict[str, float]  # Per-metric MC dropout variance
    model_version: str  # Model identifier
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        """Convert to API response format."""
        return {
            "optimized_params": self.optimized_params,
            "predicted_metrics": self.predicted_metrics,
            "confidence_score": round(self.confidence_score, 4),
            "uncertainty_estimates": {k: round(v, 6) for k, v in self.uncertainty_estimates.items()},
            "model_version": self.model_version,
            "timestamp": self.timestamp.isoformat(),
        }


class CircuitPredictor(nn.Module):
    """
    Neural network for circuit performance prediction.
    
    Architecture:
    - Input: 8 normalized parameters (wn, wp, vdd, cl, temp, tech_node, corner, corner_factor)
    - Hidden: 3 layers with 128 → 256 → 128 neurons, LeakyReLU, MC Dropout (0.3)
    - Output: 5 metrics (frequency, delay, power, gain, health_score)
    - Uncertainty: Via MC Dropout sampling
    """
    
    INPUT_SIZE = 8
    OUTPUT_SIZE = 5  # freq, delay, power, gain, health
    DROPOUT_RATE = 0.3
    
    OUTPUT_NAMES = ["frequency", "delay", "power", "gain", "health_score"]
    
    def __init__(self, hidden_sizes: List[int] = None, dropout_rate: float = 0.3):
        """Initialize predictor network."""
        super().__init__()
        
        if hidden_sizes is None:
            hidden_sizes = [128, 256, 128]
        
        self.dropout_rate = dropout_rate
        
        # Input layer
        layers = []
        prev_size = self.INPUT_SIZE
        
        # Hidden layers with dropout
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.LeakyReLU(0.2))
            layers.append(nn.Dropout(dropout_rate))
            prev_size = hidden_size
        
        # Output layer (no dropout here for deterministic forward)
        layers.append(nn.Linear(prev_size, self.OUTPUT_SIZE))
        
        self.network = nn.Sequential(*layers)
        
        # Output scaling (learned)
        self.register_parameter(
            'output_scale',
            nn.Parameter(torch.ones(self.OUTPUT_SIZE) * 0.1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with dropout.
        
        Args:
            x: Batch of normalized parameters [batch_size, 8]
        
        Returns:
            Predicted metrics [batch_size, 5]
        """
        output = self.network(x)
        # Scale outputs to reasonable ranges
        output = output * (self.output_scale + 0.001)
        return output
    
    def forward_mc(
        self,
        x: torch.Tensor,
        num_samples: int = 50,
        keep_dropout: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass with MC Dropout for uncertainty.
        
        Args:
            x: Input parameters [batch_size, 8]
            num_samples: Number of stochastic forward passes
            keep_dropout: Keep dropout active during inference
        
        Returns:
            mean: Predicted mean [batch_size, 5]
            std: Predicted std (uncertainty) [batch_size, 5]
        """
        if keep_dropout:
            # Keep model in training mode for dropout
            self.train()
        
        # Collect multiple forward passes
        predictions = []
        with torch.no_grad():
            for _ in range(num_samples):
                pred = self.forward(x)
                predictions.append(pred)
        
        # Restore eval mode if needed
        if not keep_dropout:
            self.eval()
        
        predictions = torch.stack(predictions)  # [num_samples, batch_size, 5]
        
        # Compute mean and std
        mean = predictions.mean(dim=0)  # [batch_size, 5]
        std = predictions.std(dim=0)    # [batch_size, 5]
        
        return mean, std
    
    @classmethod
    def model_dir(cls) -> Path:
        """Get model storage directory."""
        model_root = Path(__file__).parent.parent.parent / "models" / "ml"
        model_root.mkdir(parents=True, exist_ok=True)
        return model_root
    
    def save(self, version: str = "default"):
        """Save model checkpoint."""
        save_path = self.model_dir() / f"circuit_predictor_{version}.pt"
        torch.save(self.state_dict(), save_path)
        logger.info(f"Model saved: {save_path}")
        return save_path
    
    @classmethod
    def load(cls, version: str = "default") -> CircuitPredictor:
        """Load saved model."""
        load_path = cls.model_dir() / f"circuit_predictor_{version}.pt"
        if not load_path.exists():
            logger.warning(f"Model not found: {load_path}, creating new")
            return cls()
        
        model = cls()
        state_dict = torch.load(load_path, map_location='cpu')
        model.load_state_dict(state_dict)
        logger.info(f"Model loaded: {load_path}")
        return model


class DataNormalizer:
    """Normalize/denormalize circuit parameters and metrics."""
    
    # Parameter ranges (observed from typical designs)
    PARAM_RANGES = {
        "wn": (100, 10000),           # nm
        "wp": (100, 10000),           # nm
        "vdd": (0.5, 3.0),            # V
        "cl": (1e-15, 1e-9),          # F
        "temp": (-40, 125),           # C
        "tech_node": (3, 28),         # nm
        "corner": (0, 4),             # Corner index 0-4
        "corner_factor": (0.7, 1.25), # Multiplier range
    }
    
    # Metric ranges (from simulation results)
    METRIC_RANGES = {
        "frequency": (0.1, 10.0),      # GHz
        "delay": (10, 1000),           # ps
        "power": (0.01, 10),           # mW
        "gain": (0.5, 2.0),            # V/V
        "health_score": (0.0, 1.0),    # 0-1
    }
    
    @classmethod
    def normalize_params(cls, params: Dict[str, float]) -> torch.Tensor:
        """
        Normalize design parameters to [-1, 1] range.
        
        Args:
            params: Dict with wn, wp, vdd, cl, temp, tech_node, corner
        
        Returns:
            Normalized tensor [8]
        """
        values = []
        corner_map = {"TT": 0, "SS": 1, "FF": 2, "SF": 3, "FS": 4}
        
        for key in ["wn", "wp", "vdd", "cl", "temp", "tech_node"]:
            if key == "cl":
                # Log scale for capacitance
                val = np.log10(params[key])
                min_val = np.log10(cls.PARAM_RANGES[key][0])
                max_val = np.log10(cls.PARAM_RANGES[key][1])
            else:
                val = params[key]
                min_val, max_val = cls.PARAM_RANGES[key]
            
            # Normalize to [-1, 1]
            normalized = 2 * (val - min_val) / (max_val - min_val) - 1
            normalized = np.clip(normalized, -1, 1)
            values.append(normalized)
        
        # Corner as index
        corner_idx = corner_map.get(params.get("corner", "TT"), 0)
        corner_norm = 2 * (corner_idx / 4) - 1
        values.append(corner_norm)
        
        # Corner factor (mu multiplier)
        corner_factor = params.get("corner_factor", 1.0)
        cf_min, cf_max = cls.PARAM_RANGES["corner_factor"]
        cf_norm = 2 * (corner_factor - cf_min) / (cf_max - cf_min) - 1
        cf_norm = np.clip(cf_norm, -1, 1)
        values.append(cf_norm)
        
        return torch.tensor(values, dtype=torch.float32)
    
    @classmethod
    def denormalize_metrics(cls, metrics_norm: torch.Tensor) -> Dict[str, float]:
        """
        Convert normalized metrics back to physical units.
        
        Args:
            metrics_norm: Normalized tensor [5]
        
        Returns:
            Dict with frequency (GHz), delay (ps), power (mW), gain (V/V), health (0-1)
        """
        result = {}
        for i, key in enumerate(CircuitPredictor.OUTPUT_NAMES):
            norm_val = metrics_norm[i].item()
            min_val, max_val = cls.METRIC_RANGES[key]
            # Denormalize from [-1, 1]
            physical_val = (norm_val + 1) / 2 * (max_val - min_val) + min_val
            physical_val = np.clip(physical_val, min_val, max_val)
            result[key] = physical_val
        
        return result
    
    @classmethod
    def normalize_metrics(cls, metrics: Dict[str, float]) -> torch.Tensor:
        """Normalize physical metrics to [-1, 1] range."""
        values = []
        for key in CircuitPredictor.OUTPUT_NAMES:
            val = metrics[key]
            min_val, max_val = cls.METRIC_RANGES[key]
            # Normalize to [-1, 1]
            normalized = 2 * (val - min_val) / (max_val - min_val) - 1
            normalized = np.clip(normalized, -1, 1)
            values.append(normalized)
        
        return torch.tensor(values, dtype=torch.float32)


class MLCircuitOptimizer:
    """ML-based circuit parameter optimizer using pre-trained model."""
    
    def __init__(self, model_version: str = "default", mc_samples: int = 50):
        """
        Initialize optimizer with trained model.
        
        Args:
            model_version: Which model checkpoint to load
            mc_samples: Number of MC dropout samples for uncertainty
        """
        self.model = CircuitPredictor.load(model_version)
        self.model.eval()
        self.normalizer = DataNormalizer()
        self.mc_samples = mc_samples
        self.model_version = model_version
    
    def predict(
        self,
        params: Dict[str, float],
        return_uncertainty: bool = True
    ) -> Dict[str, float]:
        """
        Predict performance metrics for given parameters.
        
        Args:
            params: Circuit parameters (wn, wp, vdd, cl, temp, tech_node, corner)
            return_uncertainty: Include uncertainty estimates
        
        Returns:
            Dict with predicted metrics and confidence
        """
        # Normalize input
        params_norm = self.normalizer.normalize_params(params)
        params_batch = params_norm.unsqueeze(0)  # [1, 8]
        
        # Get predictions with uncertainty
        with torch.no_grad():
            mean_norm, std_norm = self.model.forward_mc(
                params_batch,
                num_samples=self.mc_samples,
                keep_dropout=True
            )
        
        # Remove batch dimension
        mean_norm = mean_norm.squeeze(0)  # [5]
        std_norm = std_norm.squeeze(0)    # [5]
        
        # Denormalize
        metrics = self.normalizer.denormalize_metrics(mean_norm)
        
        if return_uncertainty:
            # Uncertainty in physical units (approximate)
            uncertainty = {}
            for i, key in enumerate(CircuitPredictor.OUTPUT_NAMES):
                _, max_val = self.normalizer.METRIC_RANGES[key]
                _, min_val = self.normalizer.METRIC_RANGES[key]
                # Convert normalized std to physical units
                phys_std = std_norm[i].item() * (max_val - min_val) / 2
                uncertainty[key] = max(phys_std, 0.001)
            
            metrics["uncertainty"] = uncertainty
        
        return metrics
    
    def optimize(
        self,
        objectives: Dict[str, float] = None,
        parameter_constraints: Dict[str, Tuple[float, float]] = None,
        num_candidates: int = 100,
    ) -> PredictionResult:
        """
        Find optimal parameters using model predictions.
        
        Strategy: Sample from parameter space, predict metrics, score by objectives.
        
        Args:
            objectives: Multi-objective weights {freq: 0.35, power: -0.20, ...}
            parameter_constraints: Min/max for each parameter
            num_candidates: Number of candidates to evaluate
        
        Returns:
            PredictionResult with best parameters and metrics
        """
        if objectives is None:
            objectives = {
                "frequency": 0.35,
                "delay": -0.15,
                "power": -0.20,
                "gain": 0.05,
                "health_score": 0.25,
            }
        
        if parameter_constraints is None:
            parameter_constraints = {
                "wn": (200, 2000),
                "wp": (400, 4000),
                "vdd": (0.8, 1.5),
                "cl": (1e-13, 1e-11),
                "temp": (0, 80),
                "tech_node": (5, 14),
                "corner": (0, 4),
            }
        
        best_score = -np.inf
        best_params = None
        best_metrics = None
        all_uncertainties = []
        
        # Generate candidates
        candidates = self._generate_candidates(num_candidates, parameter_constraints)
        
        for candidate_params in candidates:
            # Predict metrics
            pred = self.predict(candidate_params, return_uncertainty=True)
            uncertainty = pred.pop("uncertainty", {})
            all_uncertainties.append(uncertainty)
            
            # Score by objectives
            score = self._compute_score(pred, objectives)
            
            if score > best_score:
                best_score = score
                best_params = candidate_params
                best_metrics = pred
        
        # Compute confidence from uncertainty
        confidence = self._compute_confidence(
            best_metrics,
            np.mean([u for u in all_uncertainties], axis=0)
        )
        
        return PredictionResult(
            optimized_params=best_params,
            predicted_metrics=best_metrics,
            confidence_score=confidence,
            uncertainty_estimates={k: v for k, v in best_metrics.items() if k != "uncertainty"},
            model_version=self.model_version,
        )
    
    def _generate_candidates(
        self,
        num_candidates: int,
        constraints: Dict[str, Tuple[float, float]]
    ) -> List[Dict[str, float]]:
        """Generate random parameter candidates within constraints."""
        candidates = []
        corners = ["TT", "SS", "FF", "SF", "FS"]
        
        for _ in range(num_candidates):
            candidate = {}
            for param, (min_val, max_val) in constraints.items():
                if param == "corner":
                    candidate[param] = corners[int(np.random.uniform(0, 5))]
                else:
                    candidate[param] = np.random.uniform(min_val, max_val)
            
            # Add corner factor
            corner = candidate.get("corner", "TT")
            corner_factors = {"TT": 1.0, "SS": 0.78, "FF": 1.25, "SF": 0.82, "FS": 1.18}
            candidate["corner_factor"] = corner_factors.get(corner, 1.0)
            
            candidates.append(candidate)
        
        return candidates
    
    def _compute_score(self, metrics: Dict[str, float], objectives: Dict[str, float]) -> float:
        """Compute multi-objective score."""
        score = 0.0
        for obj_name, obj_weight in objectives.items():
            if obj_name in metrics:
                # Normalize metrics to 0-1 range for scoring
                val = metrics[obj_name]
                if obj_name == "frequency":
                    normalized = min(val / 10.0, 1.0)  # GHz
                elif obj_name == "power":
                    normalized = min(1.0 / (val + 0.01), 1.0)  # Inverse (lower is better)
                elif obj_name == "delay":
                    normalized = min(1.0 / (val + 1), 1.0)  # Inverse (lower is better)
                elif obj_name == "gain":
                    normalized = val  # 0-2 range
                elif obj_name == "health_score":
                    normalized = val  # Already 0-1
                else:
                    normalized = 0.5
                
                score += obj_weight * normalized
        
        return score
    
    def _compute_confidence(
        self,
        metrics: Dict[str, float],
        uncertainty: Dict[str, float]
    ) -> float:
        """
        Compute confidence score based on model uncertainty.
        
        Higher uncertainty → lower confidence.
        Formula: confidence = 1 / (1 + avg_relative_uncertainty)
        """
        relative_uncertainties = []
        for metric_name, metric_val in metrics.items():
            if metric_name in uncertainty and metric_val != 0:
                rel_unc = uncertainty[metric_name] / (abs(metric_val) + 0.001)
                relative_uncertainties.append(min(rel_unc, 1.0))  # Cap at 1.0
        
        if not relative_uncertainties:
            return 0.7  # Default confidence
        
        avg_rel_unc = np.mean(relative_uncertainties)
        confidence = 1.0 / (1.0 + avg_rel_unc)
        return np.clip(confidence, 0.0, 1.0)


def create_ml_optimizer(model_version: str = "default") -> MLCircuitOptimizer:
    """Factory function to create ML optimizer."""
    try:
        return MLCircuitOptimizer(model_version=model_version)
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        raise
