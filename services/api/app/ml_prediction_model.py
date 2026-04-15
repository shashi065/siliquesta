"""
XGBoost-based ML Model for CMOS Parameter Prediction

Trains on simulation data to predict:
- Frequency (GHz)
- Power (mW)
- Delay (ns)

Includes confidence scoring and model persistence.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from pathlib import Path
import pickle
import json
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Container for prediction results with confidence scores."""
    predicted_value: float
    confidence: float  # 0-1, higher is better
    upper_bound: float  # 95% confidence interval
    lower_bound: float  # 95% confidence interval
    model_r2: float
    feature_importance: Dict[str, float]
    timestamp: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class XGBoostCMOSPredictor:
    """XGBoost-based predictor for CMOS simulation parameters."""

    def __init__(self, model_dir: Path = Path("models")):
        """
        Initialize predictor.

        Args:
            model_dir: Directory to store/load models.
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)

        # Models for different outputs
        self.models = {
            "frequency": None,
            "power": None,
            "delay": None,
        }

        # Scalers for feature normalization
        self.scalers = {
            "features": None,
            "targets": {
                "frequency": None,
                "power": None,
                "delay": None,
            }
        }

        # Model metadata
        self.metadata = {
            "trained": False,
            "training_date": None,
            "training_samples": 0,
            "feature_names": None,
            "performance_metrics": {},
        }

        # Feature names
        self.feature_names = ["C", "Id", "VDD"]

    def generate_training_data(self, n_samples: int = 10000, seed: int = 42) -> Tuple[np.ndarray, Dict]:
        """
        Generate synthetic training data from CMOS equations.

        Args:
            n_samples: Number of training samples.
            seed: Random seed for reproducibility.

        Returns:
            Tuple of (X, y_dict) where y_dict contains frequency, power, delay.
        """
        try:
            from cmos_simulation_engine import CMOSEngine
        except ImportError:
            # If cmos_simulation_engine not available, use simple equations
            logger.warning("CMOS simulation engine not found. Using simplified CMOS equations.")
            return self._generate_data_simplified(n_samples, seed)

        logger.info(f"Generating {n_samples} training samples...")
        np.random.seed(seed)

        # Parameter ranges
        C = np.random.uniform(1e-12, 10e-12, n_samples)
        Id = np.random.uniform(0.5e-3, 10e-3, n_samples)
        VDD = np.random.uniform(1.2, 5.0, n_samples)

        X = np.column_stack([C, Id, VDD])

        # Generate outputs using CMOS equations
        engine = CMOSEngine()
        results = engine.simulate(C, Id, VDD)

        y_dict = {
            "frequency": results.frequency,
            "power": results.power,
            "delay": results.delay,
        }

        logger.info(f"Generated data shapes:")
        logger.info(f"  X: {X.shape}")
        for key, val in y_dict.items():
            logger.info(f"  y_{key}: {val.shape}")

        return X, y_dict

    def _generate_data_simplified(self, n_samples: int, seed: int) -> Tuple[np.ndarray, Dict]:
        """Simplified data generation for when CMOS engine unavailable."""
        np.random.seed(seed)

        C = np.random.uniform(1e-12, 10e-12, n_samples)
        Id = np.random.uniform(0.5e-3, 10e-3, n_samples)
        VDD = np.random.uniform(1.2, 5.0, n_samples)

        X = np.column_stack([C, Id, VDD])

        # Simplified CMOS equations
        delay = (C * VDD) / (2 * Id)  # ns-like units
        frequency = 1 / (delay * 1e-9)  # Convert to GHz
        power = C * VDD * VDD * frequency / 1e9  # mW units

        # Add some realistic noise
        frequency += np.random.normal(0, frequency * 0.05, n_samples)
        power += np.random.normal(0, power * 0.05, n_samples)
        delay += np.random.normal(0, delay * 0.05, n_samples)

        y_dict = {
            "frequency": np.abs(frequency),
            "power": np.abs(power),
            "delay": np.abs(delay),
        }

        logger.info(f"Generated synthetic data (no CMOS engine):")
        logger.info(f"  X: {X.shape}")
        for key, val in y_dict.items():
            logger.info(f"  y_{key}: {val.shape}")

        return X, y_dict

    def train(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        test_size: float = 0.2,
        hyperparams: Optional[Dict] = None,
    ):
        """
        Train XGBoost models for each output variable.

        Args:
            X: Feature matrix (n_samples, n_features).
            y_dict: Dictionary of output arrays {frequency, power, delay}.
            test_size: Fraction for test set.
            hyperparams: XGBoost hyperparameters.
        """
        logger.info("Starting model training...")

        # Default hyperparameters
        if hyperparams is None:
            hyperparams = {
                "max_depth": 6,
                "learning_rate": 0.1,
                "n_estimators": 200,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "random_state": 42,
                "objective": "reg:squarederror",
                "tree_method": "hist",
            }

        # Feature scaling
        self.scalers["features"] = StandardScaler()
        X_scaled = self.scalers["features"].fit_transform(X)

        # Train model for each output
        for target_name, y_values in y_dict.items():
            logger.info(f"\nTraining model for {target_name}...")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_values, test_size=test_size, random_state=42
            )

            # Scale target
            scaler = StandardScaler()
            y_train_scaled = scaler.fit_transform(y_train.reshape(-1, 1)).ravel()
            y_test_scaled = scaler.transform(y_test.reshape(-1, 1)).ravel()

            self.scalers["targets"][target_name] = scaler

            # Train model
            model = xgb.XGBRegressor(**hyperparams)
            model.fit(
                X_train,
                y_train_scaled,
                eval_set=[(X_test, y_test_scaled)],
                verbose=False,
            )

            self.models[target_name] = model

            # Evaluate
            y_pred_scaled = model.predict(X_test)
            y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            self.metadata["performance_metrics"][target_name] = {
                "mse": float(mse),
                "rmse": float(rmse),
                "mae": float(mae),
                "r2": float(r2),
                "test_size": int(len(X_test)),
            }

            logger.info(f"  MSE: {mse:.6e}")
            logger.info(f"  RMSE: {rmse:.6e}")
            logger.info(f"  MAE: {mae:.6e}")
            logger.info(f"  R²: {r2:.4f}")

        # Cross-validation scores
        for target_name in y_dict.keys():
            cv_scores = cross_val_score(
                self.models[target_name],
                X_scaled,
                y_dict[target_name],
                cv=5,
                scoring="r2",
            )
            logger.info(
                f"{target_name} CV R² scores: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})"
            )
            self.metadata["performance_metrics"][target_name]["cv_r2_mean"] = float(
                cv_scores.mean()
            )
            self.metadata["performance_metrics"][target_name]["cv_r2_std"] = float(
                cv_scores.std()
            )

        # Update metadata
        self.metadata["trained"] = True
        self.metadata["training_date"] = datetime.now().isoformat()
        self.metadata["training_samples"] = len(X)
        self.metadata["feature_names"] = self.feature_names

        logger.info("\nTraining complete!")

    def predict(self, C: float, Id: float, VDD: float) -> Dict[str, PredictionResult]:
        """
        Predict CMOS parameters and confidence scores.

        Args:
            C: Capacitance (farads).
            Id: Drain current (amperes).
            VDD: Supply voltage (volts).

        Returns:
            Dictionary with predictions for each target variable.
        """
        if not self.metadata["trained"]:
            raise ValueError("Model not trained yet. Call train() first.")

        # Prepare input
        X = np.array([[C, Id, VDD]])
        X_scaled = self.scalers["features"].transform(X)

        results = {}

        for target_name in self.models.keys():
            model = self.models[target_name]
            scaler = self.scalers["targets"][target_name]

            # Get prediction
            y_pred_scaled = model.predict(X_scaled)[0]
            y_pred = scaler.inverse_transform(
                np.array([[y_pred_scaled]])
            )[0, 0]

            # Get feature importance
            feature_importance = dict(
                zip(
                    self.feature_names,
                    model.feature_importances_,
                )
            )

            # Get confidence from model R² and prediction uncertainty
            metrics = self.metadata["performance_metrics"].get(target_name, {})
            model_r2 = metrics.get("r2", 0.0)
            rmse = metrics.get("rmse", 0.0)

            # Confidence = R² score (model reliability)
            confidence = max(0.0, min(1.0, model_r2))

            # 95% confidence interval (±1.96 * RMSE)
            margin = 1.96 * rmse
            upper_bound = y_pred + margin
            lower_bound = max(0, y_pred - margin)

            results[target_name] = PredictionResult(
                predicted_value=float(y_pred),
                confidence=float(confidence),
                upper_bound=float(upper_bound),
                lower_bound=float(lower_bound),
                model_r2=float(model_r2),
                feature_importance={k: float(v) for k, v in feature_importance.items()},
                timestamp=datetime.now().isoformat(),
            )

        return results

    def save(self, name: str = "cmos_predictor"):
        """Save trained models and scalers to disk."""
        if not self.metadata["trained"]:
            raise ValueError("Cannot save untrained model")

        model_path = self.model_dir / name
        model_path.mkdir(exist_ok=True)

        # Save models
        for target_name, model in self.models.items():
            model.save_model(str(model_path / f"{target_name}_model.json"))

        # Save scalers
        for key, scaler in self.scalers.items():
            if isinstance(scaler, dict) and key == "targets":
                continue
            if scaler is not None:
                with open(model_path / f"scaler_{key}.pkl", "wb") as f:
                    pickle.dump(scaler, f)

        for target_name, scaler in self.scalers["targets"].items():
            if scaler is not None:
                with open(model_path / f"scaler_target_{target_name}.pkl", "wb") as f:
                    pickle.dump(scaler, f)

        # Save metadata
        with open(model_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Models saved to {model_path}")

    def load(self, name: str = "cmos_predictor"):
        """Load trained models and scalers from disk."""
        model_path = self.model_dir / name

        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        # Load models
        for target_name in self.models.keys():
            model_file = model_path / f"{target_name}_model.json"
            if model_file.exists():
                self.models[target_name] = xgb.XGBRegressor()
                self.models[target_name].load_model(str(model_file))

        # Load scalers
        feature_scaler_file = model_path / "scaler_features.pkl"
        if feature_scaler_file.exists():
            with open(feature_scaler_file, "rb") as f:
                self.scalers["features"] = pickle.load(f)

        for target_name in self.models.keys():
            scaler_file = model_path / f"scaler_target_{target_name}.pkl"
            if scaler_file.exists():
                with open(scaler_file, "rb") as f:
                    self.scalers["targets"][target_name] = pickle.load(f)

        # Load metadata
        metadata_file = model_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                self.metadata = json.load(f)

        logger.info(f"Models loaded from {model_path}")


# ============================================================================
# Utility Functions
# ============================================================================


def train_and_save_model(
    n_samples: int = 10000,
    model_name: str = "cmos_predictor_v1",
) -> XGBoostCMOSPredictor:
    """
    Train a new model from scratch and save it.

    Args:
        n_samples: Number of training samples.
        model_name: Name for saved model.

    Returns:
        Trained predictor instance.
    """
    predictor = XGBoostCMOSPredictor()

    # Generate data
    X, y_dict = predictor.generate_training_data(n_samples=n_samples)

    # Train
    predictor.train(X, y_dict)

    # Save
    predictor.save(model_name)

    return predictor


def load_predictor(model_name: str = "cmos_predictor_v1") -> XGBoostCMOSPredictor:
    """Load a pre-trained predictor."""
    predictor = XGBoostCMOSPredictor()
    predictor.load(model_name)
    return predictor


if __name__ == "__main__":
    # Example: Train new model
    print("Training XGBoost CMOS Predictor...")
    predictor = train_and_save_model(n_samples=5000, model_name="cmos_predictor_demo")

    # Example: Make predictions
    print("\n" + "=" * 70)
    print("PREDICTIONS")
    print("=" * 70)

    test_cases = [
        {"C": 5e-12, "Id": 2e-3, "VDD": 3.3, "name": "Nominal"},
        {"C": 1e-12, "Id": 5e-3, "VDD": 5.0, "name": "High Performance"},
        {"C": 10e-12, "Id": 1e-3, "VDD": 1.8, "name": "Low Power"},
    ]

    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  Input: C={case['C']*1e12:.1f}pF, Id={case['Id']*1e3:.1f}mA, VDD={case['VDD']:.1f}V")

        predictions = predictor.predict(case["C"], case["Id"], case["VDD"])

        for target_name, result in predictions.items():
            print(f"\n  {target_name.upper()}:")
            print(f"    Predicted: {result.predicted_value:.6f}")
            print(f"    Confidence: {result.confidence:.2%}")
            print(f"    95% CI: [{result.lower_bound:.6f}, {result.upper_bound:.6f}]")
            print(f"    Model R²: {result.model_r2:.4f}")
            print(f"    Feature Importance:")
            for feat, imp in result.feature_importance.items():
                print(f"      {feat}: {imp:.4f}")
