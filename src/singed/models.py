"""Model registry utilities."""

from __future__ import annotations

import json
from pathlib import Path


def load_models(path: str | Path) -> list[str]:
    data = json.loads(Path(path).read_text())
    models = data.get("models")
    if not isinstance(models, list) or not models or not all(isinstance(x, str) for x in models):
        raise ValueError("model config must contain a non-empty string list named 'models'")
    if data.get("api") != "openrouter":
        raise ValueError("all public SINGED runs must use the OpenRouter API")
    return models
