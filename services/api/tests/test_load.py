"""Minimal concurrent load test."""

from __future__ import annotations

import concurrent.futures

import requests

from .utils import wait_for


def test_concurrent_simulations(api_v1: str, auth_headers: dict[str, str]) -> None:
    payload = {
        "wn": 0.6,
        "wp": 1.2,
        "vdd": 1.1,
        "temp": 25,
        "cl_ff": 8.0,
        "corner": "TT",
        "tech_node": 28,
    }

    def _submit() -> str:
        resp = requests.post(f"{api_v1}/simulate", json=payload, headers=auth_headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["job_key"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        job_keys = list(executor.map(lambda _: _submit(), range(10)))

    def _all_done() -> bool:
        for job_key in job_keys:
            resp = requests.get(f"{api_v1}/jobs/{job_key}", headers=auth_headers, timeout=20)
            resp.raise_for_status()
            if resp.json()["status"] != "SUCCESS":
                return False
        return True

    wait_for(_all_done, timeout=240, interval=4)
