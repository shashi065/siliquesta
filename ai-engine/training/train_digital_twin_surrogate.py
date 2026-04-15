"""
Train the SILIQUESTA Digital Twin surrogate model.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.digital_twin_ml import (  # noqa: E402
    DATASET_DIR,
    DEFAULT_MODEL_PATH,
    DigitalTwinSurrogateService,
)


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(
                {
                    "wn": float(row["wn"]),
                    "wp": float(row["wp"]),
                    "vdd": float(row["vdd"]),
                    "temp": float(row["temp"]),
                    "cl_ff": float(row["cl_ff"]),
                    "tech_node": float(row["tech_node"]),
                    "corner": row["corner"],
                    "delay_ps": float(row["delay_ps"]),
                    "power_mw": float(row["power_mw"]),
                    "freq_ghz": float(row["freq_ghz"]),
                    "source": row.get("source", "physics"),
                }
            )
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Digital Twin surrogate")
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(DATASET_DIR / "digital_twin_dataset.csv"),
        help="Dataset CSV path",
    )
    parser.add_argument(
        "--model-out",
        type=str,
        default=str(DEFAULT_MODEL_PATH),
        help="Output model artifact path",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=2500,
        help="Generate a dataset when the CSV does not exist",
    )
    parser.add_argument(
        "--prefer-spice",
        action="store_true",
        help="Prefer ngspice-backed data during bootstrap generation",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    service = DigitalTwinSurrogateService(model_path=args.model_out)

    if dataset_path.exists():
        rows = load_rows(dataset_path)
    else:
        rows = DigitalTwinSurrogateService.build_dataset(
            sample_count=max(args.bootstrap_samples, 100),
            prefer_spice=args.prefer_spice,
        )
        DigitalTwinSurrogateService.save_dataset_csv(rows, dataset_path)

    metadata = service.train_from_rows(rows)
    print(f"Trained model: {args.model_out}")
    print(f"Samples: {metadata['sample_count']}")
    print(f"Trained with SPICE: {metadata['trained_with_spice']}")
    print(f"Mean MAPE: {metadata['metrics']['mean_mape_percent']}%")
    print(f"R2 freq: {metadata['metrics']['r2_freq']}")
    print(f"R2 power: {metadata['metrics']['r2_power']}")
    print(f"R2 delay: {metadata['metrics']['r2_delay']}")


if __name__ == "__main__":
    main()
