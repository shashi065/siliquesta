"""Production digital twin ensemble service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import math
import pickle
import random
from typing import Any, Dict, Iterable, List

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.services.cmos_engine import CMOSPhysicsEngine, ProcessCorner
from app.services.model_registry import ModelRegistry
from app.services.spice_engine import SpiceEngine, SpiceNotAvailable

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None
    nn = None

try:
    from xgboost import XGBRegressor  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    XGBRegressor = None


REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = REPO_ROOT / "ai-engine" / "artifacts"
DATASET_DIR = REPO_ROOT / "ai-engine" / "datasets"
DEFAULT_MODEL_PATH = ARTIFACT_DIR / "digital_twin_surrogate.pkl"
CORNER_ORDER = ["SS", "TT", "FF", "SF", "FS", "MC"]
TARGET_NAMES = ["delay_ps", "power_mw", "freq_ghz"]


@dataclass
class TwinPrediction:
    delay_ps: float
    power_mw: float
    freq_ghz: float
    confidence: float
    uncertainty: float
    estimated_error_percent: float
    model_source: str
    training_samples: int
    trained_with_spice: bool
    dataset_version: str
    validation_metrics: dict[str, float]


class _TorchRegressor(nn.Module if nn is not None else object):
    def __init__(self, in_features: int, out_features: int):
        if nn is None:
            raise RuntimeError("torch is not installed")
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(),
            nn.Dropout(0.12),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Dropout(0.12),
            nn.Linear(64, out_features),
        )

    def forward(self, x):
        return self.net(x)


class DigitalTwinSurrogateService:
    def __init__(self, model_path: Path | str = DEFAULT_MODEL_PATH):
        self.model_path = Path(model_path)
        self.registry = ModelRegistry()
        self.scaler = StandardScaler()
        self.xgb_models: list[Any] = []
        self.torch_model: Any = None
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False
        self._cache: Dict[tuple, TwinPrediction] = {}
        self._load_if_available()

    @staticmethod
    def feature_names() -> List[str]:
        return [
            "wn",
            "wp",
            "vdd",
            "temp",
            "cl_ff",
            "tech_node",
            "width_ratio",
            "total_width",
            "inv_tech_node",
            "corner_ss",
            "corner_tt",
            "corner_ff",
            "corner_sf",
            "corner_fs",
            "corner_mc",
        ]

    @staticmethod
    def _feature_row(
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        tech_node: float,
        corner: str,
    ) -> List[float]:
        corner = (corner or "TT").upper()
        flags = [1.0 if c == corner else 0.0 for c in CORNER_ORDER]
        wn = float(wn)
        wp = float(wp)
        tech_node = float(tech_node)
        width_ratio = wp / max(wn, 0.05)
        total_width = wn + wp
        inv_tech = 1.0 / max(tech_node, 0.3)
        return [
            wn,
            wp,
            float(vdd),
            float(temp),
            float(cl_ff),
            tech_node,
            width_ratio,
            total_width,
            inv_tech,
            *flags,
        ]

    @staticmethod
    def _corner_enum(corner: str) -> ProcessCorner:
        try:
            return ProcessCorner[(corner or "TT").upper()]
        except KeyError:
            return ProcessCorner.TT

    def _load_if_available(self) -> None:
        if not self.model_path.exists():
            return
        with self.model_path.open("rb") as f:
            payload = pickle.load(f)
        self.scaler = payload["scaler"]
        self.xgb_models = payload["xgb_models"]
        self.torch_model = payload["torch_model"]
        self.metadata = payload.get("metadata", {})
        self.is_loaded = True

    @classmethod
    def sample_design_space(cls, sample_count: int) -> Iterable[Dict]:
        tech_nodes = [28, 14, 7, 5, 3, 2, 1, 0.7, 0.5, 0.3]
        corners = CORNER_ORDER
        rng = random.Random(42)
        for _ in range(sample_count):
            tech_node = float(rng.choice(tech_nodes))
            if tech_node >= 28:
                vdd_min, vdd_max = 0.8, 1.8
            elif tech_node >= 7:
                vdd_min, vdd_max = 0.65, 1.25
            elif tech_node >= 3:
                vdd_min, vdd_max = 0.5, 1.05
            elif tech_node >= 1:
                vdd_min, vdd_max = 0.4, 0.9
            else:
                vdd_min, vdd_max = 0.35, 0.78
            yield {
                "wn": round(rng.uniform(0.12, 5.0), 3),
                "wp": round(rng.uniform(0.15, 5.0), 3),
                "vdd": round(rng.uniform(vdd_min, vdd_max), 3),
                "temp": round(rng.uniform(-40.0, 125.0), 2),
                "cl_ff": round(rng.uniform(1.0, 200.0), 3),
                "tech_node": tech_node,
                "corner": rng.choice(corners),
            }

    @classmethod
    def build_dataset(cls, sample_count: int = 2000, prefer_spice: bool = False) -> List[Dict]:
        rows: List[Dict] = []
        spice_enabled = False
        if prefer_spice:
            try:
                SpiceEngine.ngspice_path()
                spice_enabled = True
            except SpiceNotAvailable:
                spice_enabled = False

        for sample in cls.sample_design_space(sample_count):
            if spice_enabled:
                result = SpiceEngine.run_inverter_transient(
                    wn=sample["wn"],
                    wp=sample["wp"],
                    vdd=sample["vdd"],
                    temp=sample["temp"],
                    cl_ff=sample["cl_ff"],
                    corner=sample["corner"],
                    tech_node=sample["tech_node"],
                )
                source = "spice"
                row = {
                    **sample,
                    "delay_ps": float(result.delay),
                    "power_mw": float(result.power),
                    "freq_ghz": float(result.freq),
                    "source": source,
                }
            else:
                result = CMOSPhysicsEngine.compute(
                    wn=sample["wn"],
                    wp=sample["wp"],
                    vdd=sample["vdd"],
                    temp=sample["temp"],
                    cl_ff=sample["cl_ff"],
                    corner=cls._corner_enum(sample["corner"]),
                    tech_node=sample["tech_node"],
                )
                row = {
                    **sample,
                    "delay_ps": float(result.delay),
                    "power_mw": float(result.power),
                    "freq_ghz": float(result.freq),
                    "source": "physics",
                }
            rows.append(row)
        return rows

    @classmethod
    def save_dataset_csv(cls, rows: List[Dict], dataset_path: Path | str) -> Path:
        dataset_path = Path(dataset_path)
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "wn", "wp", "vdd", "temp", "cl_ff", "tech_node", "corner",
            "delay_ps", "power_mw", "freq_ghz", "source",
        ]
        with dataset_path.open("w", encoding="utf-8", newline="") as f:
            f.write(",".join(headers) + "\n")
            for row in rows:
                f.write(",".join(str(row[h]) for h in headers) + "\n")
        return dataset_path

    @classmethod
    def _arrays_from_rows(cls, rows: List[Dict]) -> tuple[np.ndarray, np.ndarray]:
        X = np.array([
            cls._feature_row(
                wn=row["wn"],
                wp=row["wp"],
                vdd=row["vdd"],
                temp=row["temp"],
                cl_ff=row["cl_ff"],
                tech_node=row["tech_node"],
                corner=row["corner"],
            )
            for row in rows
        ], dtype=np.float32)
        y = np.array([[row["delay_ps"], row["power_mw"], row["freq_ghz"]] for row in rows], dtype=np.float32)
        return X, y

    def _dataset_version(self, rows: List[Dict]) -> str:
        source = "spice" if any(row.get("source") == "spice" for row in rows) else "physics"
        return f"digital-twin-{source}-{len(rows)}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    def train(self, rows: List[Dict]) -> Dict[str, Any]:
        if XGBRegressor is None or torch is None or nn is None:
            raise RuntimeError("Digital twin training requires xgboost and torch.")

        X, y = self._arrays_from_rows(rows)
        x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        x_train_scaled = self.scaler.fit_transform(x_train)
        x_test_scaled = self.scaler.transform(x_test)

        self.xgb_models = []
        xgb_pred_columns = []
        for idx in range(y.shape[1]):
            model = XGBRegressor(
                n_estimators=240,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=42 + idx,
            )
            model.fit(x_train_scaled, y_train[:, idx])
            self.xgb_models.append(model)
            xgb_pred_columns.append(model.predict(x_test_scaled))
        xgb_pred = np.column_stack(xgb_pred_columns)

        self.torch_model = _TorchRegressor(x_train_scaled.shape[1], y.shape[1])
        optimizer = torch.optim.Adam(self.torch_model.parameters(), lr=0.001)
        loss_fn = nn.MSELoss()
        x_train_tensor = torch.tensor(x_train_scaled, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
        self.torch_model.train()
        for _ in range(140):
            optimizer.zero_grad()
            pred = self.torch_model(x_train_tensor)
            loss = loss_fn(pred, y_train_tensor)
            loss.backward()
            optimizer.step()

        self.torch_model.eval()
        with torch.no_grad():
            torch_pred = self.torch_model(torch.tensor(x_test_scaled, dtype=torch.float32)).numpy()

        ensemble_pred = (xgb_pred + torch_pred) / 2.0
        metrics = self._metrics(y_test, ensemble_pred)
        dataset_version = self._dataset_version(rows)
        self.metadata = {
            "sample_count": len(rows),
            "trained_with_spice": any(row.get("source") == "spice" for row in rows),
            "dataset_version": dataset_version,
            "feature_names": self.feature_names(),
            "target_names": TARGET_NAMES,
            "metrics": metrics,
            "model_family": "xgboost+pytorch-ensemble",
        }
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        versioned_path = self.model_path.parent / f"{dataset_version}.pkl"
        payload = {
            "scaler": self.scaler,
            "xgb_models": self.xgb_models,
            "torch_model": self.torch_model,
            "metadata": self.metadata,
        }
        with self.model_path.open("wb") as f:
            pickle.dump(payload, f)
        with versioned_path.open("wb") as f:
            pickle.dump(payload, f)
        self.registry.register(
            model_family="digital-twin-ensemble",
            artifact_path=str(versioned_path),
            dataset_version=dataset_version,
            metrics=metrics,
            active=True,
        )
        self.is_loaded = True
        return self.metadata

    @staticmethod
    def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
        metric_map: dict[str, float] = {}
        labels = ["delay", "power", "freq"]
        for idx, label in enumerate(labels):
            metric_map[f"r2_{label}"] = round(float(r2_score(y_true[:, idx], y_pred[:, idx])), 6)
            metric_map[f"mae_{label}"] = round(float(mean_absolute_error(y_true[:, idx], y_pred[:, idx])), 6)
            metric_map[f"rmse_{label}"] = round(float(math.sqrt(mean_squared_error(y_true[:, idx], y_pred[:, idx]))), 6)
            denom = np.maximum(np.abs(y_true[:, idx]), 1e-9)
            metric_map[f"mape_{label}_percent"] = round(float(np.mean(np.abs((y_pred[:, idx] - y_true[:, idx]) / denom)) * 100.0), 6)
        metric_map["mean_mape_percent"] = round(float(np.mean([metric_map["mape_delay_percent"], metric_map["mape_power_percent"], metric_map["mape_freq_percent"]])), 6)
        return metric_map

    def ensure_bootstrap_model(self, sample_count: int = 1600) -> Dict[str, Any]:
        if self.is_loaded and self.xgb_models and self.torch_model is not None:
            return self.metadata
        rows = self.build_dataset(sample_count=sample_count, prefer_spice=False)
        dataset_path = DATASET_DIR / "digital_twin_bootstrap.csv"
        self.save_dataset_csv(rows, dataset_path)
        return self.train(rows)

    def predict_with_confidence(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        tech_node: float,
        corner: str,
    ) -> TwinPrediction:
        if XGBRegressor is None or torch is None or nn is None:
            raise RuntimeError("Digital twin inference requires xgboost and torch.")
        self.ensure_bootstrap_model()

        key = (
            round(float(wn), 6),
            round(float(wp), 6),
            round(float(vdd), 6),
            round(float(temp), 4),
            round(float(cl_ff), 6),
            round(float(tech_node), 4),
            str(corner or "TT").upper(),
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        seed = abs(hash(key)) % (2**31 - 1)
        random.seed(seed)
        np.random.seed(seed)
        if torch is not None:
            torch.manual_seed(seed)

        row = np.array([
            self._feature_row(
                wn=wn,
                wp=wp,
                vdd=vdd,
                temp=temp,
                cl_ff=cl_ff,
                tech_node=tech_node,
                corner=corner,
            )
        ], dtype=np.float32)
        row_scaled = self.scaler.transform(row)

        xgb_pred = np.array([model.predict(row_scaled)[0] for model in self.xgb_models], dtype=np.float32)
        xgb_targets = np.array([
            self.xgb_models[0].predict(row_scaled)[0],
            self.xgb_models[1].predict(row_scaled)[0],
            self.xgb_models[2].predict(row_scaled)[0],
        ], dtype=np.float32)

        self.torch_model.train()
        samples = []
        for _ in range(12):
            with torch.no_grad():
                pred = self.torch_model(torch.tensor(row_scaled, dtype=torch.float32)).numpy()[0]
            samples.append(pred)
        self.torch_model.eval()
        torch_samples = np.array(samples, dtype=np.float32)
        torch_mean = torch_samples.mean(axis=0)
        torch_std = torch_samples.std(axis=0)

        ensemble = (xgb_targets + torch_mean) / 2.0
        model_gap = np.abs(xgb_targets - torch_mean)
        uncertainty = float(np.mean(torch_std + model_gap))
        scales = np.maximum(np.abs(ensemble), np.array([0.1, 0.01, 0.1], dtype=np.float32))
        normalized = float(np.mean((torch_std + model_gap) / scales))
        confidence = float(np.clip(1.0 - normalized, 0.0, 0.999))
        estimated_error = float(max(self.metadata.get("metrics", {}).get("mean_mape_percent", 0.0), normalized * 100.0))

        prediction = TwinPrediction(
            delay_ps=round(float(ensemble[0]), 4),
            power_mw=round(float(ensemble[1]), 4),
            freq_ghz=round(float(ensemble[2]), 4),
            confidence=round(confidence, 6),
            uncertainty=round(uncertainty, 6),
            estimated_error_percent=round(estimated_error, 6),
            model_source="digital-twin-ensemble",
            training_samples=int(self.metadata.get("sample_count", 0)),
            trained_with_spice=bool(self.metadata.get("trained_with_spice", False)),
            dataset_version=str(self.metadata.get("dataset_version", "unknown")),
            validation_metrics=self.metadata.get("metrics", {}),
        )
        self._cache[key] = prediction
        return prediction

    def predict(
        self,
        wn: float,
        wp: float,
        vdd: float,
        temp: float,
        cl_ff: float,
        tech_node: float,
        corner: str,
    ) -> TwinPrediction:
        return self.predict_with_confidence(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            cl_ff=cl_ff,
            tech_node=tech_node,
            corner=corner,
        )
