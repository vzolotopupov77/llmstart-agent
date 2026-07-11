"""OpenRouter VL embeddings client (text query + image document)."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from indexers.caption.pricing import ModelPricing, estimate_cost_usd
from indexers.openrouter_common import image_to_data_url, require_openrouter_key
from indexers.vl_embed.base import VLEmbedResult
from scripts.langfuse_helpers import load_env_file

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_BACKOFF_S = 3.0


class OpenRouterVLEmbedClient:
    """Embed images and text queries via OpenRouter /embeddings API."""

    def __init__(
        self,
        model_id: str,
        *,
        pricing: ModelPricing,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
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

    def _create_embedding(self, content: list[dict[str, object]]) -> VLEmbedResult:
        from openai import APIError, OpenAI  # noqa: PLC0415

        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout_s,
        )
        payload_input = [{"content": content}]

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.perf_counter()
            try:
                response = client.embeddings.create(
                    model=self.model_id,
                    input=payload_input,
                    encoding_format="float",
                )
                latency_s = time.perf_counter() - start
                data = response.data
                if not data:
                    msg = f"No embedding data in API response (model={self.model_id})"
                    raise RuntimeError(msg)
                vector = list(data[0].embedding)
                if not vector:
                    msg = f"Empty embedding vector (model={self.model_id})"
                    raise RuntimeError(msg)

                usage = response.usage
                prompt_tokens = int(usage.prompt_tokens if usage else 0)
                est_cost = estimate_cost_usd(
                    self._pricing,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                )
                return VLEmbedResult(
                    vector=vector,
                    prompt_tokens=prompt_tokens,
                    latency_s=latency_s,
                    est_cost_usd=est_cost,
                )
            except APIError as exc:
                last_error = exc
                logger.warning(
                    "VL embed API error (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)
            except RuntimeError as exc:
                last_error = exc
                logger.warning(
                    "VL embed failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)

        msg = f"VL embed failed after {MAX_RETRIES} attempts: {last_error}"
        raise RuntimeError(msg) from last_error

    def embed_image(self, image_path: Path) -> VLEmbedResult:
        data_url = image_to_data_url(image_path)
        content: list[dict[str, object]] = [
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
        return self._create_embedding(content)

    def embed_query(self, text: str) -> VLEmbedResult:
        content: list[dict[str, object]] = [
            {"type": "text", "text": text},
        ]
        return self._create_embedding(content)
