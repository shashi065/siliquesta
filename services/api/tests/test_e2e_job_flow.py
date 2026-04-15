"""End-to-end job lifecycle validation."""

from __future__ import annotations

import requests

from .utils import wait_for


def test_simulation_job_flow(api_v1: str, auth_headers: dict[str, str]) -> None:
    payload = {
        "wn": 0.5,
        "wp": 1.0,
        "vdd": 1.2,
        "temp": 27,
        "cl_ff": 10.0,
        "corner": "TT",
        "tech_node": 28,
    }
    resp = requests.post(f"{api_v1}/simulate", json=payload, headers=auth_headers, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    job_key = body["job_key"]

    status_holder = {"status": None, "result": None}

    def _poll() -> bool:
        status_resp = requests.get(f"{api_v1}/jobs/{job_key}", headers=auth_headers, timeout=20)
        status_resp.raise_for_status()
        status_body = status_resp.json()
        status_holder["status"] = status_body["status"]
        status_holder["result"] = status_body.get("result")
        return status_body["status"] == "SUCCESS"

    wait_for(_poll, timeout=180, interval=3)
    assert status_holder["result"] is not None
