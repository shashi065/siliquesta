"""Validation engine comparing ML predictions against SPICE references."""

from __future__ import annotations

import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, ValidationRun
from app.services.digital_twin_ml import DigitalTwinSurrogateService
from app.services.spice_engine import SpiceEngine, SpiceNotAvailable


class ValidationEngine:
    def __init__(self, twin_service: DigitalTwinSurrogateService | None = None) -> None:
        self.twin_service = twin_service or DigitalTwinSurrogateService()

    async def validate_design(
        self,
        db: AsyncSession,
        user: User | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        prediction = self.twin_service.predict_with_confidence(
            wn=payload["wn"],
            wp=payload["wp"],
            vdd=payload["vdd"],
            temp=payload["temp"],
            cl_ff=payload["cl_ff"],
            tech_node=payload["tech_node"],
            corner=payload["corner"],
        )
        try:
            reference = SpiceEngine.run_inverter_transient(
                wn=payload["wn"],
                wp=payload["wp"],
                vdd=payload["vdd"],
                temp=payload["temp"],
                cl_ff=payload["cl_ff"],
                tech_node=payload["tech_node"],
                corner=payload["corner"],
            )
            reference_payload = reference.__dict__
            metrics = self._compare(prediction.__dict__, reference_payload)
            reference_source = "spice"
        except SpiceNotAvailable:
            reference_payload = None
            metrics = None
            reference_source = "unavailable"

        error_percent = None
        if metrics and "percent_error_mean" in metrics:
            error_percent = float(metrics["percent_error_mean"])
        model_confidence = float(prediction.__dict__.get("confidence", 0.0)) * 100.0
        if error_percent is None:
            confidence_score = round(max(0.0, min(100.0, model_confidence)), 2)
        else:
            confidence_score = round(max(0.0, min(100.0, 100.0 - error_percent)), 2)
        trusted = bool(error_percent is not None and error_percent <= 5.0 and confidence_score >= 85.0)

        ml_prediction = {
            "freq": prediction.freq_ghz,
            "power": prediction.power_mw,
            "delay": prediction.delay_ps,
        }
        simulation_result = None
        if reference_payload:
            simulation_result = {
                "freq": reference_payload.get("freq"),
                "power": reference_payload.get("power"),
                "delay": reference_payload.get("delay"),
            }

        result = {
            "ml_prediction": ml_prediction,
            "simulation_result": simulation_result,
            "error_percent": error_percent,
            "confidence_score": confidence_score,
            "trusted": trusted,
            "prediction": prediction.__dict__,
            "reference_source": reference_source,
            "reference": reference_payload,
            "metrics": metrics,
        }
        db.add(
            ValidationRun(
                user_id=user.id if user is not None else None,
                scope="validate_design",
                input_json=payload,
                prediction_json=prediction.__dict__,
                reference_json=reference_payload,
                metrics_json=metrics,
            )
        )
        await db.flush()
        return result

    @staticmethod
    def _compare(prediction: dict[str, Any], reference: dict[str, Any]) -> dict[str, float]:
        pairs = [
            ("freq_ghz", "freq", "freq"),
            ("power_mw", "power", "power"),
            ("delay_ps", "delay", "delay"),
        ]
        out: dict[str, float] = {}
        maes = []
        rmses = []
        pcts = []
        for pred_key, ref_key, label in pairs:
            pred = float(prediction[pred_key])
            ref = float(reference[ref_key])
            err = pred - ref
            mae = abs(err)
            rmse = math.sqrt(err * err)
            pct = abs(err) / max(abs(ref), 1e-9) * 100.0
            out[f"mae_{label}"] = round(mae, 6)
            out[f"rmse_{label}"] = round(rmse, 6)
            out[f"percent_error_{label}"] = round(pct, 6)
            maes.append(mae)
            rmses.append(rmse)
            pcts.append(pct)
        out["mae_mean"] = round(sum(maes) / len(maes), 6)
        out["rmse_mean"] = round(sum(rmses) / len(rmses), 6)
        out["percent_error_mean"] = round(sum(pcts) / len(pcts), 6)
        return out
