"""Minimal OpenRouter client shared by every evaluated model.

The client intentionally uses one API surface for all model families, including
OpenAI models. It never writes credentials or complete prompts to the audit log.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter returns an invalid or unsuccessful response."""


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: int = 180
    max_output_tokens: int = 2048
    http_referer: str | None = None
    app_title: str = "SINGED"

    @classmethod
    def from_env(cls, *, timeout_seconds: int = 180, max_output_tokens: int = 2048):
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise OpenRouterError("OPENROUTER_API_KEY is not set")
        return cls(
            api_key=key,
            base_url=os.environ.get("OPENROUTER_BASE_URL", cls.base_url).rstrip("/"),
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
            http_referer=os.environ.get("OPENROUTER_HTTP_REFERER") or None,
            app_title=os.environ.get("OPENROUTER_APP_TITLE", "SINGED"),
        )


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig):
        self.config = config

    def chat(self, *, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": self.config.max_output_tokens,
        }
        # Sampling parameters are deliberately omitted so every model uses the
        # endpoint default, matching the paper protocol.
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Title": self.config.app_title,
        }
        if self.config.http_referer:
            headers["HTTP-Referer"] = self.config.http_referer
        request = urllib.request.Request(
            f"{self.config.base_url}/chat/completions",
            data=encoded,
            headers=headers,
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            detail = detail.replace(self.config.api_key, "[REDACTED]")
            raise OpenRouterError(f"OpenRouter HTTP {exc.code}: {detail[:500]}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OpenRouterError(f"OpenRouter request failed: {type(exc).__name__}") from exc
        if not result.get("choices"):
            raise OpenRouterError("OpenRouter response contains no choices")
        result["_singed_audit"] = {
            "request_sha256": hashlib.sha256(encoded).hexdigest(),
            "latency_seconds": round(time.monotonic() - started, 3),
            "model_requested": model,
            "model_returned": result.get("model"),
            "provider": result.get("provider"),
            "usage": result.get("usage"),
        }
        return result
