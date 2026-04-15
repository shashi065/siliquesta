"""Failure mode validations for retries and timeouts."""

from __future__ import annotations

import os
import requests

import pytest

from .utils import wait_for


pytestmark = pytest.mark.skipif(
    os.getenv("SILIQUESTA_ENABLE_TESTING", "0") != "1",
    reason="Testing endpoints disabled. Set SILIQUESTA_ENABLE_TESTING=1 and APP_ENV=testing.",
)


def _await_status(api_v1: str, headers: dict[str, str], job_key: str, target: str) -> dict:
    holder: dict[str, str | dict] = {}

    def _poll() -> bool:
        resp = requests.get(f"{api_v1}/jobs/{job_key}", headers=headers, timeout=20)
        resp.raise_for_status()
        body = resp.json()
        holder.update(body)
        return body["status"] == target

    wait_for(_poll, timeout=120, interval=3)
    return holder


def test_forced_failure_retries(api_v1: str, auth_headers: dict[str, str]) -> None:
    resp = requests.post(
        f"{api_v1}/testing/fail-job",
        json={"message": "Forced failure"},
        headers=auth_headers,
        timeout=20,
    )
    resp.raise_for_status()
    job_key = resp.json()["job_key"]
    result = _await_status(api_v1, auth_headers, job_key, "FAILURE")
    assert result["error"] is not None
    assert result["retry_count"] >= 1


def test_timeout_handling(api_v1: str, auth_headers: dict[str, str]) -> None:
    resp = requests.post(
        f"{api_v1}/testing/sleep-job",
        json={"seconds": 6.0},
        headers=auth_headers,
        timeout=20,
    )
    resp.raise_for_status()
    job_key = resp.json()["job_key"]
    result = _await_status(api_v1, auth_headers, job_key, "FAILURE")
    assert result["error"] is not None
