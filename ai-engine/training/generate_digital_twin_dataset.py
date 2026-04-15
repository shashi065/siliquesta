"""
Generate a Digital Twin dataset for surrogate-model training.
Supports ngspice-backed samples when ngspice is available, otherwise uses
the internal CMOS physics engine.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.digital_twin_ml import DATASET_DIR, DigitalTwinSurrogateService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SILIQUESTA Digital Twin dataset")
    parser.add_argument("--samples", type=int, default=5000, help="Number of random samples")
    parser.add_argument(
        "--prefer-spice",
        action="store_true",
        help="Use ngspice samples when ngspice is installed",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATASET_DIR / "digital_twin_dataset.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()

    rows = DigitalTwinSurrogateService.build_dataset(
        sample_count=max(args.samples, 100),
        prefer_spice=args.prefer_spice,
    )
    output = DigitalTwinSurrogateService.save_dataset_csv(rows, args.output)
    spice_count = sum(1 for row in rows if row.get("source") == "spice")
    print(f"Generated {len(rows)} rows")
    print(f"SPICE-backed rows: {spice_count}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
