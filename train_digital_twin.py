"""
Digital Twin Model Training & Dataset Generation

Generates training data with:
- Inputs: WN, WP, VDD, Temperature
- Outputs: Power, Frequency, Delay

Trains XGBoost models with confidence scoring.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error
import pickle
import json
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Tuple, List, Optional
import sys
import shap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReliabilityModel:
    """Physics-based reliability model for CMOS devices."""
    
    # Physical constants
    BOLTZMANN_K = 8.617e-5  # eV/K
    
    # Degradation thresholds
    NBTI_THRESHOLD = 0.05   # 50 mV threshold voltage shift
    HCI_THRESHOLD = 0.10    # 10% current degradation
    EM_THRESHOLD = 0.20     # 20% resistance increase
    
    # Model parameters (extracted from literature)
    NBTI_PARAMS = {
        "A": 2.5e-3,        # Pre-factor
        "n": 0.25,          # Time exponent (t_ox dependent)
        "m": 2.0,           # Voltage exponent
        "Ea": 0.05,         # Activation energy (eV)
    }
    
    HCI_PARAMS = {
        "A": 1.2e-4,        # Pre-factor
        "n": 0.3,           # Time exponent
        "Ea": 0.12,         # Activation energy (eV)
        "Vth": 0.3,         # Threshold voltage (V)
    }
    
    EM_PARAMS = {
        "A": 1e6,           # Pre-factor (hours)
        "n": 2.1,           # Current exponent
        "Ea": 0.75,         # Activation energy (eV)
    }
    
    def __init__(self):
        """Initialize reliability model."""
        self.metadata = {
            "model_type": "physics-based",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "degradation_types": ["NBTI", "HCI", "Electromigration"]
        }
    
    def compute_nbti_degradation(
        self,
        vdd: float,
        temp: float,
        time_years: float = 10
    ) -> float:
        """
        Compute NBTI (Negative Bias Temperature Instability) degradation.
        
        NBTI primarily affects PMOS devices:
        - Threshold voltage increases with stress
        - Exponential dependence on temperature and voltage
        
        Args:
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            time_years: Operating time (years)
            
        Returns:
            Threshold voltage shift (V)
        """
        T_K = temp + 273.15  # Convert to Kelvin
        time_hours = time_years * 365.25 * 24  # Convert to hours
        
        # NBTI degradation: ΔVT = A * (t/t_ref)^n * exp(Ea/(k*T)) * Vdd^m
        A = self.NBTI_PARAMS["A"]
        n = self.NBTI_PARAMS["n"]
        m = self.NBTI_PARAMS["m"]
        Ea = self.NBTI_PARAMS["Ea"]
        
        # Reference time: 1 hour
        t_ref = 1.0
        
        # Temperature factor
        temp_factor = np.exp(Ea / (self.BOLTZMANN_K * T_K))
        
        # Time factor (power law)
        time_factor = (time_hours / t_ref) ** n
        
        # Voltage exponent (higher Vdd → more stress)
        vdd_factor = vdd ** m
        
        delta_vt = A * time_factor * temp_factor * vdd_factor
        
        return float(delta_vt)
    
    def compute_hci_degradation(
        self,
        vdd: float,
        temp: float,
        time_years: float = 10
    ) -> float:
        """
        Compute HCI (Hot Carrier Injection) degradation.
        
        HCI primarily affects NMOS devices:
        - Threshold voltage increases
        - Current decreases
        
        Args:
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            time_years: Operating time (years)
            
        Returns:
            Relative current degradation (0-1, where 1 = 100% loss)
        """
        T_K = temp + 273.15
        time_hours = time_years * 365.25 * 24
        
        # HCI degradation: ΔI/I = A * (t/t_ref)^n * exp(Ea/(k*T)) * (Vdd - Vth)^p
        A = self.HCI_PARAMS["A"]
        n = self.HCI_PARAMS["n"]
        Ea = self.HCI_PARAMS["Ea"]
        Vth = self.HCI_PARAMS["Vth"]
        
        t_ref = 1.0
        
        # Temperature factor
        temp_factor = np.exp(Ea / (self.BOLTZMANN_K * T_K))
        
        # Time factor
        time_factor = (time_hours / t_ref) ** n
        
        # Overdrive voltage: Vgs - Vth = Vdd - Vth
        # (HCI occurs when channel voltage exceeds Vth)
        overdrive = max(0, vdd - Vth)
        
        # Current degradation (power law with overdrive, max at high Vdd)
        hci_degradation = A * time_factor * temp_factor * (overdrive ** 1.5)
        
        # Clamp to [0, 1] range
        return float(min(1.0, max(0.0, hci_degradation)))
    
    def compute_electromigration_degradation(
        self,
        vdd: float,
        temp: float,
        current_ma: float = 1.0,
        time_years: float = 10
    ) -> float:
        """
        Compute electromigration (EM) degradation.
        
        Electromigration causes interconnect resistance increase:
        - Power-law dependence on current
        - Exponential dependence on temperature
        
        Args:
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            current_ma: Average current (mA)
            time_years: Operating time (years)
            
        Returns:
            Resistance increase factor (1.0 = no change, 2.0 = 100% increase)
        """
        T_K = temp + 273.15
        time_hours = time_years * 365.25 * 24
        
        # EM MTF (Mean Time to Failure): TTF = A * J^-n * exp(Ea/(k*T))
        # where J is current density
        A = self.EM_PARAMS["A"]
        n_em = self.EM_PARAMS["n"]
        Ea = self.EM_PARAMS["Ea"]
        
        # Normalize current (typical is 1 mA per interconnect line)
        J_normalized = current_ma / 1.0
        
        # Mean time to failure (in hours)
        mtf_hours = A * (J_normalized ** (-n_em)) * np.exp(Ea / (self.BOLTZMANN_K * T_K))
        
        # Fraction of MTF consumed
        fraction = time_hours / max(mtf_hours, 1e-6)
        
        # Resistance increase (Weibull with shape factor k~1.5)
        # R(t) = R0 * (1 + (t/TTF)^shape)
        shape = 1.5
        resistance_factor = 1.0 + (fraction ** shape)
        
        return float(resistance_factor)
    
    def compute_frequency_degradation(
        self,
        nbti_shift: float,
        hci_degradation: float,
        vdd: float = 1.8
    ) -> float:
        """
        Compute frequency degradation from component degradations.
        
        Frequency is limited by:
        - NBTI: Increased Vth → slower switching
        - HCI: Reduced current → slower switching
        
        Args:
            nbti_shift: NBTI threshold voltage shift (V)
            hci_degradation: HCI current degradation factor
            vdd: Supply voltage (V)
            
        Returns:
            Frequency degradation factor (0.95 = 5% loss)
        """
        # NBTI impact on frequency (typically larger)
        # Each 100mV Vth shift = ~10% frequency loss
        nbti_freq_impact = 1.0 - (nbti_shift / 0.1)
        
        # HCI impact on frequency
        # Current degradation directly impacts delay
        hci_freq_impact = 1.0 - hci_degradation
        
        # Combined effect (multiplicative)
        freq_factor = nbti_freq_impact * hci_freq_impact
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, freq_factor)))
    
    def compute_lifetime(
        self,
        vdd: float,
        temp: float,
        current_ma: float = 1.0,
        max_degradation: float = 0.15
    ) -> Dict:
        """
        Compute device lifetime based on degradation mechanisms.
        
        Lifetime defined as when first mechanism exceeds threshold.
        
        Args:
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            current_ma: Average current (mA)
            max_degradation: Maximum acceptable degradation (as fraction)
            
        Returns:
            Dictionary with lifetime estimates for each mechanism
        """
        lifetimes = {}
        
        # NBTI lifetime: when ΔVt exceeds threshold
        if self.NBTI_PARAMS["A"] > 0:
            # Binary search for lifetime
            t_min, t_max = 0.1, 100
            while t_max - t_min > 0.01:
                t_mid = (t_min + t_max) / 2
                nbti = self.compute_nbti_degradation(vdd, temp, t_mid)
                if nbti < self.NBTI_THRESHOLD:
                    t_min = t_mid
                else:
                    t_max = t_mid
            lifetimes["nbti"] = float(t_min)
        
        # HCI lifetime: when current degradation exceeds threshold
        t_min, t_max = 0.1, 100
        while t_max - t_min > 0.01:
            t_mid = (t_min + t_max) / 2
            hci = self.compute_hci_degradation(vdd, temp, t_mid)
            if hci < self.HCI_THRESHOLD:
                t_min = t_mid
            else:
                t_max = t_mid
        lifetimes["hci"] = float(t_min)
        
        # EM lifetime: when resistance increase exceeds threshold
        t_min, t_max = 0.1, 100
        while t_max - t_min > 0.01:
            t_mid = (t_min + t_max) / 2
            em = self.compute_electromigration_degradation(vdd, temp, current_ma, t_mid)
            if em < (1.0 + self.EM_THRESHOLD):
                t_min = t_mid
            else:
                t_max = t_mid
        lifetimes["em"] = float(t_min)
        
        # Overall lifetime (weakest link - first mechanism to fail)
        overall_lifetime = min(lifetimes.values())
        lifetimes["overall"] = float(overall_lifetime)
        
        return lifetimes
    
    def compute_reliability_score(
        self,
        vdd: float,
        temp: float,
        time_years: float = 10,
        current_ma: float = 1.0
    ) -> Dict:
        """
        Compute reliability score based on accumulated degradation.
        
        Reliability score:
        - 1.0 = Fresh device (0% degradation)
        - 0.9 = 10% degraded
        - 0.5 = 50% of useful lifetime consumed
        - 0.0 = End of life
        
        Args:
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            time_years: Time in operation (years)
            current_ma: Average current (mA)
            
        Returns:
            Reliability metrics dictionary
        """
        # Compute degradation for each mechanism
        nbti = self.compute_nbti_degradation(vdd, temp, time_years)
        hci = self.compute_hci_degradation(vdd, temp, time_years)
        em = self.compute_electromigration_degradation(vdd, temp, current_ma, time_years)
        
        # Compute degradation factors (0 = fresh, 1 = failed)
        nbti_factor = min(1.0, nbti / self.NBTI_THRESHOLD)
        hci_factor = min(1.0, hci / self.HCI_THRESHOLD)
        em_factor = min(1.0, (em - 1.0) / self.EM_THRESHOLD)
        
        # Overall degradation = worst mechanism (conservative)
        overall_degradation = max(nbti_factor, hci_factor, em_factor)
        
        # Reliability score = 1 - overall_degradation
        reliability_score = max(0.0, 1.0 - overall_degradation)
        
        # Compute frequency loss
        freq_loss = 1.0 - self.compute_frequency_degradation(nbti, hci, vdd)
        
        # Compute lifetime for this device
        lifetimes = self.compute_lifetime(vdd, temp, current_ma)
        
        return {
            "reliability_score": float(reliability_score),
            "time_in_operation": float(time_years),
            "nbti_shift_mv": float(nbti * 1000),  # Convert to mV
            "hci_degradation": float(hci),
            "em_resistance_factor": float(em),
            "frequency_loss": float(freq_loss),
            "nbti_factor": float(nbti_factor),
            "hci_factor": float(hci_factor),
            "em_factor": float(em_factor),
            "lifetime_years": {
                "nbti": lifetimes["nbti"],
                "hci": lifetimes["hci"],
                "em": lifetimes["em"],
                "overall": lifetimes["overall"]
            },
            "dominant_failure_mode": str(min(
                (lifetimes["nbti"], "NBTI"),
                (lifetimes["hci"], "HCI"),
                (lifetimes["em"], "Electromigration")
            )[1])
        }


    """Generate synthetic CMOS device data with temperature effects."""
    
    def __init__(self):
        self.feature_names = ["wn", "wp", "vdd", "temp"]
        
    def generate_dataset(
        self,
        n_samples: int = 5000,
        seed: int = 42
    ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """
        Generate comprehensive training dataset.
        
        Args:
            n_samples: Number of training samples
            seed: Random seed
            
        Returns:
            Tuple of (features_df, outputs_dict)
        """
        np.random.seed(seed)
        
        logger.info(f"Generating {n_samples} training samples...")
        
        # Parameter ranges
        wn = np.random.uniform(0.5, 10.0, n_samples)    # NMOS width (µm)
        wp = np.random.uniform(0.5, 10.0, n_samples)    # PMOS width (µm)
        vdd = np.random.uniform(1.0, 5.0, n_samples)    # Supply voltage (V)
        temp = np.random.uniform(-40, 125, n_samples)   # Temperature (°C)
        
        # Create feature dataframe
        X = pd.DataFrame({
            "wn": wn,
            "wp": wp,
            "vdd": vdd,
            "temp": temp
        })
        
        # Simulate outputs using physics equations
        logger.info("Simulating CMOS performance with temperature effects...")
        
        # Gate length (7nm equivalent in µm scale)
        L = 0.1
        
        # Threshold voltage (temperature dependent)
        VT_0 = 0.4  # At 27°C
        VT_temp_coeff = -0.0015  # mV/°C
        VT = VT_0 + (temp - 27) * VT_temp_coeff / 1000.0
        
        # Effective width
        W_eff = wn + wp
        
        # Overdrive voltage
        V_OV = np.maximum(vdd - VT, 0.1)
        
        # Transconductance (temperature dependent)
        kn_0 = 100.0  # µA/V² at 27°C
        kn_temp_coeff = -0.3  # %/°C
        kn = kn_0 * (1 + (temp - 27) * kn_temp_coeff / 100.0)
        
        # Drain current (mA)
        i_drain = kn * (W_eff / L) * (V_OV ** 2) / 1000.0
        i_drain = np.maximum(i_drain, 0.1)
        
        # Load capacitance (pF, proportional to width)
        C_load = W_eff * 0.05
        C_total = C_load + 0.1
        
        # Propagation delay (ns)
        delay_ns = (C_total * vdd) / (2.0 * i_drain)
        
        # Frequency (GHz)
        frequency = 1.0 / (2.0 * delay_ns * 1e-9)
        frequency = np.minimum(frequency, 15.0)  # Cap at 15 GHz
        frequency = np.maximum(frequency, 0.1)
        
        # Dynamic power (mW)
        alpha = 0.3  # Switching activity
        P_dynamic = alpha * C_total * (vdd ** 2) * frequency
        
        # Leakage power (temperature dependent, exponential)
        # Double every ~50°C
        i_leak_ref = (W_eff * 0.001) * np.exp((temp - 27) / 50.0)
        P_leak = i_leak_ref * vdd / 1000.0
        
        # Total power (mW)
        power = P_dynamic + P_leak
        power = np.maximum(power, 0.01)
        
        # Output dictionary
        y_dict = {
            "power": power,
            "frequency": frequency,
            "delay": delay_ns
        }
        
        logger.info(f"\nDataset statistics:")
        logger.info(f"  WN: [{wn.min():.2f}, {wn.max():.2f}] µm")
        logger.info(f"  WP: [{wp.min():.2f}, {wp.max():.2f}] µm")
        logger.info(f"  VDD: [{vdd.min():.2f}, {vdd.max():.2f}] V")
        logger.info(f"  Temp: [{temp.min():.0f}, {temp.max():.0f}] °C")
        logger.info(f"\n  Power: [{power.min():.3f}, {power.max():.3f}] mW")
        logger.info(f"  Frequency: [{frequency.min():.3f}, {frequency.max():.3f}] GHz")
        logger.info(f"  Delay: [{delay_ns.min():.4f}, {delay_ns.max():.4f}] ns")
        
        return X, y_dict


class DigitalTwinTrainer:
    """Train XGBoost models for Digital Twin."""
    
    def __init__(self, model_dir: Path = Path("services/api/models/digital_twin")):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.metrics = {}
        self.explainers = {}  # SHAP explainers
        self.X_background = None  # Training data for SHAP
        self.feature_names = ["wn", "wp", "vdd", "temp"]
        self.metadata = {}
        
    def train_models(
        self,
        X: pd.DataFrame,
        y_dict: Dict[str, np.ndarray],
        test_size: float = 0.2,
        seed: int = 42
    ) -> Dict:
        """
        Train XGBoost models for all outputs.
        
        Args:
            X: Features dataframe
            y_dict: Dictionary of output arrays
            test_size: Train/test split
            seed: Random seed
            
        Returns:
            Dictionary of training metrics
        """
        logger.info("\n" + "="*80)
        logger.info("TRAINING DIGITAL TWIN MODELS")
        logger.info("="*80)
        
        # Prepare features
        X_array = X.values
        self.feature_names = X.columns.tolist()
        
        # Scale features
        self.scalers["features"] = StandardScaler()
        X_scaled = self.scalers["features"].fit_transform(X_array)
        
        # Train-test split
        X_train, X_test, y_train_dict, y_test_dict = self._split_data(
            X_scaled, y_dict, test_size, seed
        )
        
        # XGBoost hyperparameters
        xgb_params = {
            "max_depth": 7,
            "learning_rate": 0.1,
            "n_estimators": 300,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": seed,
            "tree_method": "hist",
            "objective": "reg:squarederror",
        }
        
        # Train model for each output
        all_metrics = {}
        
        for output_name in ["power", "frequency", "delay"]:
            logger.info(f"\n{'='*60}")
            logger.info(f"Training model: {output_name}")
            logger.info(f"{'='*60}")
            
            # Get data for this output
            y_train = y_train_dict[output_name]
            y_test = y_test_dict[output_name]
            
            # Scale output
            scaler = StandardScaler()
            y_train_scaled = scaler.fit_transform(y_train.reshape(-1, 1)).ravel()
            y_test_scaled = scaler.transform(y_test.reshape(-1, 1)).ravel()
            
            # Train model
            model = xgb.XGBRegressor(**xgb_params)
            model.fit(
                X_train, y_train_scaled,
                eval_set=[(X_test, y_test_scaled)],
                verbose=False
            )
            
            # Store model and scaler
            self.models[output_name] = model
            self.scalers[output_name] = scaler
            
            # Create SHAP explainer
            try:
                explainer = shap.TreeExplainer(model)
                self.explainers[output_name] = explainer
                logger.info(f"  ✓ SHAP explainer created for {output_name}")
            except Exception as e:
                logger.warning(f"  ⚠ Failed to create SHAP explainer: {e}")
            
            # Evaluate
            y_pred = model.predict(X_test)
            y_pred_original = scaler.inverse_transform(y_pred.reshape(-1, 1)).ravel()
            
            metrics = {
                "r2": r2_score(y_test, y_pred_original),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred_original)),
                "mape": mean_absolute_percentage_error(y_test, y_pred_original),
                "n_trees": model.n_estimators,
                "max_depth": model.max_depth,
                "feature_importance": dict(zip(self.feature_names, model.feature_importances_)),
            }
            
            self.metrics[output_name] = metrics
            all_metrics[output_name] = metrics
            
            logger.info(f"  R² Score: {metrics['r2']:.4f}")
            logger.info(f"  RMSE: {metrics['rmse']:.6f}")
            logger.info(f"  MAPE: {metrics['mape']:.2%}")
            logger.info(f"  Trees: {metrics['n_trees']}")
            logger.info(f"\n  Feature Importance:")
            for fname, fimportance in sorted(metrics['feature_importance'].items(), 
                                            key=lambda x: x[1], reverse=True):
                logger.info(f"    {fname}: {fimportance:.4f}")
        
        # Store training data for SHAP background
        self.X_background = X_train[:100]  # Use 100 samples as background for speed
        logger.info(f"\n✓ Stored {len(self.X_background)} background samples for SHAP")
        
        return all_metrics
    
    def _split_data(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        test_size: float,
        seed: int
    ) -> Tuple:
        """Split data for train/test."""
        X_train, X_test, indices_train, indices_test = train_test_split(
            X, np.arange(len(X)), test_size=test_size, random_state=seed
        )
        
        y_train_dict = {k: v[indices_train] for k, v in y_dict.items()}
        y_test_dict = {k: v[indices_test] for k, v in y_dict.items()}
        
        return X_train, X_test, y_train_dict, y_test_dict
    
    def predict(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float
    ) -> Dict:
        """
        Make predictions with confidence scores.
        
        Args:
            wn: NMOS width (µm)
            wp: PMOS width (µm)
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            
        Returns:
            Dictionary with predictions and confidence scores
        """
        # Prepare features
        X = np.array([[wn, wp, vdd, temp]])
        X_scaled = self.scalers["features"].transform(X)
        
        predictions = {}
        
        for output_name in ["power", "frequency", "delay"]:
            model = self.models[output_name]
            scaler = self.scalers[output_name]
            
            # Predict
            y_pred_scaled = model.predict(X_scaled)[0]
            y_pred = scaler.inverse_transform(np.array([[y_pred_scaled]]))[0, 0]
            
            # Get metrics for confidence
            metrics = self.metrics[output_name]
            r2 = metrics["r2"]
            mape = metrics["mape"]
            
            # Confidence score: based on R² and MAPE
            # Higher R² and lower MAPE = higher confidence
            confidence = max(0.0, min(1.0, r2 * (1 - min(mape, 0.5) / 0.5)))
            
            # Confidence interval (95%)
            rmse = metrics["rmse"]
            margin = 1.96 * rmse
            
            predictions[output_name] = {
                "value": float(y_pred),
                "confidence": float(confidence),
                "r2_score": float(r2),
                "mape": float(mape),
                "error_margin": float(margin),
                "lower_bound": float(y_pred - margin),
                "upper_bound": float(y_pred + margin),
                "feature_importance": metrics["feature_importance"]
            }
        
        return predictions
    
    def explain_prediction(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        output_name: str = "power"
    ) -> Dict:
        """
        Explain a prediction using SHAP values.
        
        Args:
            wn: NMOS width (µm)
            wp: PMOS width (µm)
            vdd: Supply voltage (V)
            temp: Temperature (°C)
            output_name: Which output to explain ("power", "frequency", or "delay")
            
        Returns:
            Dictionary with SHAP contributions for each feature
        """
        if output_name not in self.explainers:
            return {"error": f"No explainer for {output_name}"}
        
        if self.X_background is None:
            return {"error": "No background data available for SHAP"}
        
        try:
            # Prepare features
            X = np.array([[wn, wp, vdd, temp]])
            X_scaled = self.scalers["features"].transform(X)
            
            # Get SHAP values
            explainer = self.explainers[output_name]
            shap_values = explainer.shap_values(X_scaled)
            
            # Extract contributions for the first (and only) prediction
            if isinstance(shap_values, np.ndarray):
                contributions = shap_values[0] if shap_values.ndim > 1 else shap_values
            else:
                contributions = shap_values[0] if isinstance(shap_values, list) else shap_values
            
            # Get base value (expected model output)
            base_value = explainer.expected_value
            if isinstance(base_value, (list, np.ndarray)):
                base_value = float(base_value[0]) if len(base_value) > 0 else 0.0
            else:
                base_value = float(base_value)
            
            # Create contribution dictionary
            explanations = {
                "base_value": base_value,
                "contributions": {
                    fname: float(contrib) 
                    for fname, contrib in zip(self.feature_names, contributions)
                },
                "total_contribution": float(np.sum(contributions)),
                "prediction_value": float(base_value + np.sum(contributions))
            }
            
            return explanations
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            return {"error": str(e)}
    
    def save_models(self, name: str = "digital_twin_v1"):
        """Save trained models and scalers."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.model_dir / f"{name}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\nSaving models to {run_dir}...")
        
        # Save models
        for output_name, model in self.models.items():
            model_path = run_dir / f"model_{output_name}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            logger.info(f"  Saved: {model_path}")
        
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            scaler_path = run_dir / f"scaler_{scaler_name}.pkl"
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)
            logger.info(f"  Saved: {scaler_path}")
        
        # Save metadata
        metadata = {
            "version": "1.0",
            "timestamp": timestamp,
            "features": self.feature_names,
            "outputs": list(self.models.keys()),
            "metrics": {
                output_name: {
                    "r2": float(metrics["r2"]),
                    "rmse": float(metrics["rmse"]),
                    "mape": float(metrics["mape"]),
                    "n_trees": int(metrics["n_trees"]),
                    "max_depth": int(metrics["max_depth"]),
                    "feature_importance": {k: float(v) for k, v in metrics["feature_importance"].items()}
                }
                for output_name, metrics in self.metrics.items()
            },
            "training_config": {
                "n_estimators": 300,
                "max_depth": 7,
                "learning_rate": 0.1,
            }
        }
        
        metadata_path = run_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"  Saved: {metadata_path}")
        
        # Create symlink to latest
        latest_link = self.model_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(run_dir)
        logger.info(f"  Symlink: {latest_link} -> {run_dir}")
        
        logger.info(f"\n✓ All models saved successfully")
        
        return run_dir
    
    def load_models(self, model_dir: Optional[Path] = None):
        """Load trained models and scalers."""
        if model_dir is None:
            latest_dir = self.model_dir / "latest"
            if latest_dir.exists():
                # Handle symlink by checking if it's actually a symlink
                if latest_dir.is_symlink():
                    # Read the symlink target directly
                    import os
                    target = os.readlink(latest_dir)
                    # If it's a relative path, resolve relative to the symlink's parent
                    if not Path(target).is_absolute():
                        target_path = (latest_dir.parent / target).resolve()
                    else:
                        target_path = Path(target).resolve()
                    model_dir = target_path
                else:
                    model_dir = latest_dir.resolve()
            else:
                # Find the most recent directory
                dirs = sorted([d for d in self.model_dir.iterdir() if d.is_dir() and d.name.startswith("digital_twin")])
                if dirs:
                    model_dir = dirs[-1]
                else:
                    raise FileNotFoundError(f"No trained models found in {self.model_dir}")
        
        logger.info(f"Loading models from {model_dir}...")
        
        # Load models
        for output_name in ["power", "frequency", "delay"]:
            model_path = model_dir / f"model_{output_name}.pkl"
            with open(model_path, "rb") as f:
                self.models[output_name] = pickle.load(f)
            logger.info(f"  Loaded: {model_path}")
        
        # Load scalers
        scalers_to_load = ["features", "power", "frequency", "delay"]
        for scaler_name in scalers_to_load:
            scaler_path = model_dir / f"scaler_{scaler_name}.pkl"
            with open(scaler_path, "rb") as f:
                self.scalers[scaler_name] = pickle.load(f)
            logger.info(f"  Loaded: {scaler_path}")
        
        # Load metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)
            self.feature_names = self.metadata["features"]
            self.metrics = self.metadata["metrics"]
        
        # Create SHAP explainers for each loaded model
        logger.info(f"\n  Creating SHAP explainers...")
        for output_name, model in self.models.items():
            try:
                explainer = shap.TreeExplainer(model)
                self.explainers[output_name] = explainer
                logger.info(f"    ✓ SHAP explainer created for {output_name}")
            except Exception as e:
                logger.warning(f"    ⚠ Failed to create SHAP explainer for {output_name}: {e}")
        
        # Create minimal background data (use model predictions on random data)
        # For SHAP, we need background data, but we can create it on-the-fly if not persisted
        try:
            if self.X_background is None:
                # Create synthetic background data if not available
                np.random.seed(42)
                n_background = 50
                self.X_background = np.random.randn(n_background, len(self.feature_names)) * 2 + 1
                logger.info(f"    ✓ Created {n_background} synthetic background samples")
        except Exception as e:
            logger.warning(f"    ⚠ Failed to create background data: {e}")
        
        logger.info(f"\n✓ Models loaded successfully")


def train_digital_twin(n_samples: int = 5000) -> Path:
    """
    Complete training pipeline: generate data, train models, save.
    
    Returns:
        Path to saved models
    """
    # Generate data
    generator = DigitalTwinDataGenerator()
    X, y_dict = generator.generate_dataset(n_samples=n_samples, seed=42)
    
    # Train models
    trainer = DigitalTwinTrainer()
    metrics = trainer.train_models(X, y_dict)
    
    # Save models
    model_dir = trainer.save_models("digital_twin_v1")
    
    logger.info("\n" + "="*80)
    logger.info("DIGITAL TWIN TRAINING COMPLETE")
    logger.info("="*80)
    logger.info(f"✓ Models saved to: {model_dir}")
    logger.info(f"✓ Training samples: {n_samples}")
    logger.info(f"✓ Features: {trainer.feature_names}")
    logger.info(f"✓ Outputs: {list(trainer.models.keys())}")
    
    return model_dir


if __name__ == "__main__":
    test_only = "test" in sys.argv or "--test-only" in sys.argv
    
    if not test_only:
        # Train digital twin
        model_dir = train_digital_twin(n_samples=5000)
    
    # Test predictions
    logger.info("\n" + "="*80)
    logger.info("TEST PREDICTIONS")
    logger.info("="*80)
    
    trainer = DigitalTwinTrainer()
    trainer.load_models()
    
    # Test case 1: Low power design
    logger.info("\nTest 1: Low-power design (small W, low VDD, high T)")
    pred = trainer.predict(wn=1.0, wp=1.5, vdd=1.2, temp=85)
    for output, result in pred.items():
        logger.info(f"  {output}: {result['value']:.4f} ± {result['error_margin']:.4f} (conf: {result['confidence']:.2%})")
    
    # Test case 2: High performance design
    logger.info("\nTest 2: High-performance design (large W, high VDD, cool T)")
    pred = trainer.predict(wn=5.0, wp=7.0, vdd=3.3, temp=25)
    for output, result in pred.items():
        logger.info(f"  {output}: {result['value']:.4f} ± {result['error_margin']:.4f} (conf: {result['confidence']:.2%})")
    
    # Test case 3: Balanced design
    logger.info("\nTest 3: Balanced design (medium W, nominal VDD, room T)")
    pred = trainer.predict(wn=3.0, wp=4.0, vdd=1.8, temp=27)
    for output, result in pred.items():
        logger.info(f"  {output}: {result['value']:.4f} ± {result['error_margin']:.4f} (conf: {result['confidence']:.2%})")
