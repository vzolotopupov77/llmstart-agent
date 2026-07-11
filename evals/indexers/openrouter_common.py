"""Shared OpenRouter helpers for eval indexers."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from scripts.langfuse_helpers import load_env_file


def require_openrouter_key() -> str:
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        msg = "Missing OPENAI_API_KEY for OpenRouter API (set in .env)"
        raise RuntimeError(msg)
    return api_key


def image_to_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower().lstrip(".")
    mime = "image/png" if suffix == "png" else f"image/{suffix}"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
