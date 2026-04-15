"""Stripe integration validation (requires Stripe keys)."""

from __future__ import annotations

import json
import os
import time
import hmac
import hashlib

import pytest
import requests


pytestmark = pytest.mark.skipif(
    not os.getenv("STRIPE_SECRET_KEY"),
    reason="STRIPE_SECRET_KEY not configured.",
)


def test_checkout_session(api_v1: str, auth_headers: dict[str, str]) -> None:
    payload = {
        "plan": "GO",
        "billing_cycle": "monthly",
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
    }
    resp = requests.post(f"{api_v1}/billing/checkout-session", json=payload, headers=auth_headers, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    assert body["checkout_session_id"]
    assert body["checkout_url"].startswith("https://")


@pytest.mark.skipif(
    not os.getenv("STRIPE_WEBHOOK_SECRET"),
    reason="STRIPE_WEBHOOK_SECRET not configured.",
)
def test_webhook_verification(api_v1: str) -> None:
    event = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_123", "customer_email": "test@siliquesta.local", "metadata": {"plan": "GO", "billing_cycle": "monthly"}}},
    }
    payload = json.dumps(event).encode("utf-8")
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"

    resp = requests.post(
        f"{api_v1}/billing/webhook/stripe",
        data=payload,
        headers={"Stripe-Signature": header},
        timeout=20,
    )
    resp.raise_for_status()
    assert resp.json().get("received") is True
