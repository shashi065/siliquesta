"""
Dataset generator for ML model training.

Generates simulation data by varying circuit parameters (W/L ratios)
and collecting performance metrics from the physics engine.

Stores datasets in CSV format for reproducibility.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Configuration for dataset generation."""
    num_samples: int = 5000  # Total samples to generate
    seed: int = 42
    tech_node: float = 7.0  # Default tech node (nm)
    temperature: float = 27.0  # Default temperature (C)
    include_corners: bool = True  # Include process corners
    include_aging: bool = False  # Include aging analysis (slower)
    
    # Parameter ranges
    wn_range: Tuple[float, float] = (100, 10000)  # nMOS width
    wp_range: Tuple[float, float] = (100, 10000)  # pMOS width
    vdd_range: Tuple[float, float] = (0.8, 1.8)  # Supply voltage
    cl_range: Tuple[float, float] = (1e-13, 1e-11)  # Load capacitance
    
    def to_dict(self):
        """Convert config to dict."""
        return {
            "num_samples": self.num_samples,
            "seed": self.seed,
            "tech_node": self.tech_node,
            "temperature": self.temperature,
            "include_corners": self.include_corners,
            "include_aging": self.include_aging,
            "wn_range": self.wn_range,
            "wp_range": self.wp_range,
            "vdd_range": self.vdd_range,
            "cl_range": self.cl_range,
        }


class DatasetGenerator:
    """Generate training dataset for ML model."""
    
    @staticmethod
    def dataset_dir() -> Path:
        """Get dataset storage directory."""
        data_root = Path(__file__).parent.parent.parent / "data" / "ml_datasets"
        data_root.mkdir(parents=True, exist_ok=True)
        return data_root
    
    def __init__(self, config: Optional[DatasetConfig] = None):
        """Initialize generator."""
        self.config = config or DatasetConfig()
        self.data_samples = []
        self.dataset_name = None
        np.random.seed(self.config.seed)
    
    def generate(self, use_simulation: bool = True) -> pd.DataFrame:
        """
        Generate dataset by sampling parameters and running simulations.
        
        Args:
            use_simulation: Use physics simulator (True) or synthetic data (False)
        
        Returns:
            DataFrame with parameters and metrics
        """
        logger.info(f"Generating {self.config.num_samples} samples...")
        
        if use_simulation:
            df = self._generate_with_simulation()
        else:
            df = self._generate_synthetic()
        
        logger.info(f"Generated dataset: {df.shape[0]} samples, {df.shape[1]} features")
        return df
    
    def _generate_with_simulation(self) -> pd.DataFrame:
        """Generate dataset using actual circuit simulator."""
        # Import here to avoid circular dependency
        try:
            from .simulation_engine import create_simulator
        except ImportError:
            logger.warning("simulation_engine not available, falling back to synthetic")
            return self._generate_synthetic()
        
        samples = []
        corners = ["TT"] if not self.config.include_corners else ["TT", "SS", "FF", "SF", "FS"]
        samples_per_corner = self.config.num_samples // len(corners)
        
        for corner_idx, corner in enumerate(corners):
            logger.info(f"  Generating {corner} corner ({corner_idx+1}/{len(corners)})...")
            
            for i in range(samples_per_corner):
                try:
                    # Sample random parameters
                    wn = np.random.uniform(*self.config.wn_range)
                    wp = np.random.uniform(*self.config.wp_range)
                    vdd = np.random.uniform(*self.config.vdd_range)
                    cl = np.random.uniform(*self.config.cl_range)
                    
                    # Create simulator
                    sim_params = {
                        "w_n": wn / 1000.0,  # Convert to µm
                        "w_p": wp / 1000.0,
                        "l": self.config.tech_node / 1000.0,
                        "vdd": vdd,
                        "c_load": cl,
                        "temp": self.config.temperature,
                        "tech_node": self.config.tech_node,
                    }
                    
                    simulator = create_simulator(sim_params)
                    result = simulator.simulate(
                        include_aging_years=1 if self.config.include_aging else None
                    )
                    
                    # Extract metrics
                    metrics = result.get("metrics", {})
                    
                    sample = {
                        "wn": wn,
                        "wp": wp,
                        "vdd": vdd,
                        "cl": cl,
                        "temp": self.config.temperature,
                        "tech_node": self.config.tech_node,
                        "corner": corner,
                        "frequency": metrics.get("frequency", 0),
                        "delay": metrics.get("delay", 0),
                        "power": metrics.get("power", 0),
                        "gain": metrics.get("gain", 1.0),
                        "health_score": result.get("health_score", 0.9),
                    }
                    samples.append(sample)
                    
                    if (i + 1) % 500 == 0:
                        logger.info(f"    {i+1}/{samples_per_corner} samples done")
                
                except Exception as e:
                    logger.warning(f"Simulation failed for sample {i}: {e}")
                    continue
        
        return pd.DataFrame(samples)
    
    def _generate_synthetic(self) -> pd.DataFrame:
        """Generate synthetic dataset (for testing without simulator)."""
        logger.info("Generating synthetic dataset...")
        
        samples = []
        corners = ["TT"] if not self.config.include_corners else ["TT", "SS", "FF", "SF", "FS"]
        samples_per_corner = self.config.num_samples // len(corners)
        
        corner_multipliers = {
            "TT": 1.0,
            "SS": 0.78,
            "FF": 1.25,
            "SF": 0.82,
            "FS": 1.18,
        }
        
        for corner in corners:
            mult = corner_multipliers.get(corner, 1.0)
            
            for i in range(samples_per_corner):
                wn = np.random.uniform(*self.config.wn_range)
                wp = np.random.uniform(*self.config.wp_range)
                vdd = np.random.uniform(*self.config.vdd_range)
                cl = np.random.uniform(*self.config.cl_range)
                
                # Physics-based synthetic model
                w_ratio = wp / wn if wn > 0 else 1.0
                
                # Frequency: higher W/L → higher, higher CL → lower
                freq_base = mult * 2.0 * (1000 / (wn + wp)) / (1 + np.log10(cl * 1e12 + 1)) * vdd
                frequency = np.clip(freq_base, 0.1, 10.0)
                
                # Delay: inverse of frequency (simplified)
                delay = np.clip(50 / (frequency + 0.1) + np.random.normal(0, 2), 10, 1000)
                
                # Power: higher freq, higher Vdd → higher power
                power = np.clip(
                    mult * 0.1 *(wn + wp) / 1000 * frequency * vdd ** 2 * (1 + 5 * np.log10(cl * 1e12 + 1)),
                    0.01, 10
                )
                
                # Gain: for inverter, typically 1-2
                gain = np.clip(np.sqrt(w_ratio) * 1.5, 0.5, 2.0) + np.random.normal(0, 0.1)
                
                # Health score: degradation with power
                health = np.clip(1.0 - 0.1 * np.log10(power + 0.01), 0.5, 1.0)
                
                sample = {
                    "wn": wn,
                    "wp": wp,
                    "vdd": vdd,
                    "cl": cl,
                    "temp": self.config.temperature,
                    "tech_node": self.config.tech_node,
                    "corner": corner,
                    "frequency": frequency,
                    "delay": delay,
                    "power": power,
                    "gain": gain,
                    "health_score": health,
                }
                samples.append(sample)
        
        return pd.DataFrame(samples)
    
    def save_dataset(self, df: pd.DataFrame, name: Optional[str] = None) -> Path:
        """
        Save dataset to CSV.
        
        Args:
            df: Dataset DataFrame
            name: Dataset name (auto-generated if None)
        
        Returns:
            Path to saved CSV file
        """
        if name is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"dataset_{self.config.num_samples}_{timestamp}"
        
        self.dataset_name = name
        save_path = self.dataset_dir() / f"{name}.csv"
        
        df.to_csv(save_path, index=False)
        logger.info(f"Dataset saved: {save_path}")
        
        # Save config
        config_path = self.dataset_dir() / f"{name}_config.json"
        with open(config_path, "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        return save_path
    
    @staticmethod
    def load_dataset(name: str) -> pd.DataFrame:
        """Load dataset from CSV."""
        load_path = DatasetGenerator.dataset_dir() / f"{name}.csv"
        
        if not load_path.exists():
            raise FileNotFoundError(f"Dataset not found: {load_path}")
        
        df = pd.read_csv(load_path)
        logger.info(f"Dataset loaded: {load_path} ({len(df)} samples)")
        return df
    
    @staticmethod
    def list_datasets() -> List[str]:
        """List available datasets."""
        dataset_dir = DatasetGenerator.dataset_dir()
        csv_files = list(dataset_dir.glob("dataset_*.csv"))
        return [f.stem for f in csv_files]
    
    def split_dataset(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split dataset into train/val/test.
        
        Args:
            df: Dataset to split
            train_ratio, val_ratio, test_ratio: Split ratios
        
        Returns:
            (train_df, val_df, test_df)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
        
        n = len(df)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        # Shuffle
        df = df.sample(frac=1, random_state=self.config.seed).reset_index(drop=True)
        
        train_df = df[:train_size]
        val_df = df[train_size:train_size + val_size]
        test_df = df[train_size + val_size:]
        
        logger.info(f"Dataset split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
        
        return train_df, val_df, test_df


def generate_and_save_dataset(
    num_samples: int = 5000,
    use_simulation: bool = True,
    save: bool = True,
) -> pd.DataFrame:
    """
    Convenience function to generate and save dataset.
    
    Args:
        num_samples: Number of samples
        use_simulation: Use physics simulator or synthetic data
        save: Save to disk
    
    Returns:
        Generated DataFrame
    """
    config = DatasetConfig(num_samples=num_samples)
    generator = DatasetGenerator(config)
    df = generator.generate(use_simulation=use_simulation)
    
    if save:
        generator.save_dataset(df)
    
    return df
