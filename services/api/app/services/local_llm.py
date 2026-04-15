"""Optional local LLM wrapper for SILIQUESTA."""

from __future__ import annotations

import asyncio
import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings

logger = logging.getLogger(__name__)


class LocalLLMService:
    """Call a local Ollama model when available."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def generate(self, prompt: str, system_prompt: str, temperature: float = 0.15) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        return await asyncio.to_thread(self._generate_sync, payload)

    def _generate_sync(self, payload: dict) -> str:
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=40) as response:
                data = json.loads(response.read().decode("utf-8"))
            return (data.get("response") or "").strip()
        except URLError:
            raise
