"""Minimal production Stripe REST integration without SDK dependency."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.config import settings


class StripeGatewayError(RuntimeError):
    """Raised when Stripe interaction fails."""


@dataclass
class CheckoutSession:
    id: str
    url: str
    customer_email: str | None
    status: str | None


class StripeGateway:
    API_BASE = "https://api.stripe.com/v1"

    @staticmethod
    def enabled() -> bool:
        return bool(settings.STRIPE_SECRET_KEY.strip())

    @classmethod
    def _request(cls, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if not cls.enabled():
            raise StripeGatewayError("Stripe is not configured. Set STRIPE_SECRET_KEY.")
        body = None
        headers = {
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
        }
        if data is not None:
            body = urllib.parse.urlencode(cls._flatten(data), doseq=True).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(f"{cls.API_BASE}{path}", data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise StripeGatewayError(f"Stripe API request failed: {exc}") from exc

    @staticmethod
    def _flatten(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        flat: dict[str, Any] = {}
        for key, value in payload.items():
            full = f"{prefix}[{key}]" if prefix else key
            if isinstance(value, dict):
                flat.update(StripeGateway._flatten(value, full))
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        flat.update(StripeGateway._flatten(item, f"{full}[{idx}]"))
                    else:
                        flat[f"{full}[{idx}]"] = item
            else:
                flat[full] = value
        return flat

    @classmethod
    def create_checkout_session(
        cls,
        *,
        price_inr: int,
        plan: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        billing_cycle: str,
    ) -> CheckoutSession:
        payload = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": customer_email,
            "metadata": {
                "plan": plan,
                "billing_cycle": billing_cycle,
            },
            "line_items": [
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {"name": f"SILIQUESTA {plan}"},
                        "unit_amount": int(price_inr * 100),
                    },
                    "quantity": 1,
                }
            ],
        }
        response = cls._request("POST", "/checkout/sessions", payload)
        return CheckoutSession(
            id=response["id"],
            url=response["url"],
            customer_email=response.get("customer_details", {}).get("email") or customer_email,
            status=response.get("status"),
        )

    @staticmethod
    def verify_webhook(payload: bytes, stripe_signature: str) -> dict[str, Any]:
        secret = settings.STRIPE_WEBHOOK_SECRET.strip()
        if not secret:
            raise StripeGatewayError("Stripe webhook secret is not configured.")
        components = dict(
            item.split("=", 1)
            for item in stripe_signature.split(",")
            if "=" in item
        )
        timestamp = components.get("t")
        signature = components.get("v1")
        if not timestamp or not signature:
            raise StripeGatewayError("Invalid Stripe signature header.")
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise StripeGatewayError("Stripe signature verification failed.")
        if abs(time.time() - int(timestamp)) > 300:
            raise StripeGatewayError("Stripe webhook timestamp is too old.")
        return json.loads(payload.decode("utf-8"))
