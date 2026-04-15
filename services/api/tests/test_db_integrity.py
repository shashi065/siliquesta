"""Database consistency checks for job records."""

from __future__ import annotations

import requests

from .utils import wait_for


def test_job_record_integrity(api_v1: str, auth_headers: dict[str, str]) -> None:
    payload = {
        "wn": 0.7,
        "wp": 1.4,
        "vdd": 1.0,
        "temp": 30,
        "cl_ff": 12.0,
        "corner": "TT",
        "tech_node": 28,
    }
    resp = requests.post(f"{api_v1}/simulate", json=payload, headers=auth_headers, timeout=30)
    resp.raise_for_status()
    job_key = resp.json()["job_key"]

    holder: dict = {}

    def _done() -> bool:
        status_resp = requests.get(f"{api_v1}/jobs/{job_key}", headers=auth_headers, timeout=20)
        status_resp.raise_for_status()
        body = status_resp.json()
        holder.update(body)
        return body["status"] == "SUCCESS"

    wait_for(_done, timeout=180, interval=3)

    assert holder["created_at"] is not None
    assert holder["completed_at"] is not None
    assert holder["result"] is not None
