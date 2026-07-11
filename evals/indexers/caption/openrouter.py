"""OpenRouter vision caption client."""

from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

from indexers.caption.base import CAPTION_PROMPT, CaptionResult
from indexers.caption.pricing import ModelPricing, estimate_cost_usd
from scripts.langfuse_helpers import load_env_file

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_BACKOFF_S = 3.0
DEFAULT_MAX_TOKENS = 1500


def require_openrouter_key() -> str:
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        msg = "Missing OPENAI_API_KEY for VLM caption (set in .env)"
        raise RuntimeError(msg)
    return api_key


def _image_to_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower().lstrip(".")
    mime = "image/png" if suffix == "png" else f"image/{suffix}"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class OpenRouterCaptionClient:
    """Caption slides via OpenRouter OpenAI-compatible vision API."""

    def __init__(
        self,
        model_id: str,
        *,
        pricing: ModelPricing,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.model_id = model_id
        self._pricing = pricing
        load_env_file()
        self._api_key = api_key or require_openrouter_key()
        self._base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").strip()
        )
        timeout_raw = timeout_s
        if timeout_raw is None:
            timeout_raw = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "120"))
        self._timeout_s = timeout_raw
        self._max_tokens = max_tokens

    def caption_image(self, image_path: Path) -> CaptionResult:
        from openai import APIError, OpenAI  # noqa: PLC0415

        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout_s,
        )
        data_url = _image_to_data_url(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CAPTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.perf_counter()
            try:
                completion = client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=0,
                    max_tokens=self._max_tokens,
                )
                latency_s = time.perf_counter() - start
                choices = completion.choices
                if not choices:
                    msg = (
                        f"No choices in API response for {image_path.name} "
                        f"(model={self.model_id})"
                    )
                    raise RuntimeError(msg)
                choice = choices[0].message
                text = (choice.content or "").strip()
                if not text:
                    msg = f"Empty caption for {image_path.name} (model={self.model_id})"
                    raise RuntimeError(msg)

                usage = completion.usage
                prompt_tokens = int(usage.prompt_tokens if usage else 0)
                completion_tokens = int(usage.completion_tokens if usage else 0)
                est_cost = estimate_cost_usd(
                    self._pricing,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
                return CaptionResult(
                    text=text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_s=latency_s,
                    est_cost_usd=est_cost,
                )
            except APIError as exc:
                last_error = exc
                logger.warning(
                    "Caption API error %s (attempt %d/%d): %s",
                    image_path.name,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)
            except RuntimeError as exc:
                last_error = exc
                logger.warning(
                    "Caption failed %s (attempt %d/%d): %s",
                    image_path.name,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)

        msg = f"Caption failed for {image_path.name} after {MAX_RETRIES} attempts: {last_error}"
        raise RuntimeError(msg) from last_error
