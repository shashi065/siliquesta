"""File-based model and dataset registry for production model lineage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings


class ModelRegistry:
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.MODEL_REGISTRY_PATH)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "registry_manifest.json"

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"artifacts": []}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _save_manifest(self, payload: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def next_version(self, model_family: str) -> str:
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{model_family}-{stamp}"

    def register(
        self,
        model_family: str,
        artifact_path: str,
        dataset_version: str,
        metrics: dict[str, Any],
        active: bool = True,
    ) -> dict[str, Any]:
        manifest = self._load_manifest()
        version = self.next_version(model_family)
        record = {
            "model_family": model_family,
            "version": version,
            "artifact_path": artifact_path,
            "dataset_version": dataset_version,
            "metrics": metrics,
            "active": active,
            "created_at": datetime.utcnow().isoformat(),
        }
        if active:
            for item in manifest["artifacts"]:
                if item.get("model_family") == model_family:
                    item["active"] = False
        manifest["artifacts"].append(record)
        self._save_manifest(manifest)
        return record
