"""Pytest fixtures for SILIQUESTA backend tests."""

from __future__ import annotations

import os
import uuid

import pytest
import requests


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("SILIQUESTA_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_v1(base_url: str) -> str:
    return f"{base_url}/api/v1"


@pytest.fixture(scope="session")
def auth_token(api_v1: str) -> str:
    email = f"test_{uuid.uuid4().hex[:8]}@siliquesta.local"
    payload = {
        "email": email,
        "password": "TestPassword!123",
        "name": "Test User",
    }
    resp = requests.post(f"{api_v1}/auth/signup", json=payload, timeout=20)
    if resp.status_code == 409:
        resp = requests.post(
            f"{api_v1}/auth/login",
            json={"email": email, "password": payload["password"]},
            timeout=20,
        )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}
