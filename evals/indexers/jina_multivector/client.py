"""Jina Embeddings API client for multivector (late interaction)."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

from indexers.jina_multivector.base import JinaMultivectorResult
from indexers.jina_multivector.preprocess import png_to_jina_image_input
from scripts.langfuse_helpers import load_env_file

logger = logging.getLogger(__name__)

JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
DEFAULT_MODEL = "jina-embeddings-v4"
COST_PER_MILLION_TOKENS_USD = 0.05
MAX_RETRIES = 5
RETRY_BACKOFF_S = 3.0


def require_jina_key() -> str:
    """Get your Jina AI API key for free: https://jina.ai/?sui=apikey"""
    load_env_file()
    raw = os.environ.get("JINA_API_KEY", "").strip()
    # Strip accidental inline comments copied from .env.example
    if " #" in raw:
        raw = raw.split(" #", 1)[0].strip()
    api_key = raw
    if not api_key:
        msg = (
            "Missing JINA_API_KEY for Jina Embeddings API. "
            "Get a key at https://jina.ai (API Keys) and set JINA_API_KEY in .env"
        )
        raise RuntimeError(msg)
    try:
        api_key.encode("ascii")
    except UnicodeEncodeError as exc:
        msg = (
            "JINA_API_KEY must be ASCII-only (no inline comments after the key in .env)"
        )
        raise RuntimeError(msg) from exc
    return api_key


def _estimate_cost_usd(total_tokens: int) -> float:
    return (total_tokens / 1_000_000) * COST_PER_MILLION_TOKENS_USD


def _parse_multivector_embedding(raw: object, *, token_dim: int) -> list[list[float]]:
    if not isinstance(raw, list) or not raw:
        msg = "Jina multivector response: empty or non-list embedding"
        raise RuntimeError(msg)

    if isinstance(raw[0], list):
        vectors = [[float(v) for v in row] for row in raw]
    elif isinstance(raw[0], (int, float)):
        if token_dim <= 0 or len(raw) % token_dim != 0:
            msg = f"Jina flat multivector length {len(raw)} not divisible by token_dim={token_dim}"
            raise RuntimeError(msg)
        vectors = [
            [float(raw[index]) for index in range(offset, offset + token_dim)]
            for offset in range(0, len(raw), token_dim)
        ]
    else:
        msg = f"Unexpected Jina multivector element type: {type(raw[0])}"
        raise RuntimeError(msg)

    for row in vectors:
        if len(row) != token_dim:
            msg = f"Jina vector dim {len(row)} != expected token_dim={token_dim}"
            raise RuntimeError(msg)
    return vectors


class JinaMultivectorClient:
    """Embed images and text queries via Jina v4 multivector API."""

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        *,
        token_dim: int = 128,
        api_key: str | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.model_id = model_id
        self.token_dim = token_dim
        self._api_key = api_key or require_jina_key()
        self._timeout_s = timeout_s

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.perf_counter()
            try:
                with httpx.Client(timeout=self._timeout_s) as client:
                    response = client.post(JINA_EMBEDDINGS_URL, headers=headers, json=payload)
                latency_s = time.perf_counter() - start
                if response.status_code == 429 and attempt < MAX_RETRIES:
                    sleep_s = RETRY_BACKOFF_S * attempt
                    logger.warning(
                        "Jina rate limit (429), retry %d/%d in %.1fs",
                        attempt,
                        MAX_RETRIES,
                        sleep_s,
                    )
                    time.sleep(sleep_s)
                    continue
                response.raise_for_status()
                body = response.json()
                body["_latency_s"] = latency_s
                return body
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)
                else:
                    raise
        if last_error:
            raise last_error
        msg = "Jina API request failed without error detail"
        raise RuntimeError(msg)

    def _parse_response(self, body: dict[str, Any]) -> JinaMultivectorResult:
        data = body.get("data")
        if not isinstance(data, list) or not data:
            msg = "Jina API response missing data array"
            raise RuntimeError(msg)
        first = data[0]
        if not isinstance(first, dict):
            msg = "Jina API response data[0] is not an object"
            raise RuntimeError(msg)

        raw_embedding: object | None = first.get("embedding")
        if raw_embedding is None and "embeddings" in first:
            raw_embeddings = first["embeddings"]
            if isinstance(raw_embeddings, list) and raw_embeddings:
                if isinstance(raw_embeddings[0], list):
                    raw_embedding = raw_embeddings
                elif isinstance(raw_embeddings[0], dict):
                    raw_embedding = [
                        row.get("embedding") or row.get("vector")
                        for row in raw_embeddings
                        if isinstance(row, dict)
                    ]

        if raw_embedding is None:
            msg = "Jina API response missing embedding/embeddings field"
            raise RuntimeError(msg)

        vectors = _parse_multivector_embedding(raw_embedding, token_dim=self.token_dim)
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        total_tokens = int(usage.get("total_tokens") or usage.get("prompt_tokens") or 0)
        latency_s = float(body.get("_latency_s", 0.0))
        return JinaMultivectorResult(
            vectors=vectors,
            total_tokens=total_tokens,
            latency_s=latency_s,
            est_cost_usd=_estimate_cost_usd(total_tokens),
        )

    def embed_image(self, image_path: Path, *, max_side: int) -> JinaMultivectorResult:
        payload = {
            "model": self.model_id,
            "task": "retrieval.passage",
            "return_multivector": True,
            "input": [png_to_jina_image_input(image_path, max_side)],
        }
        return self._parse_response(self._post(payload))

    def embed_query(self, text: str) -> JinaMultivectorResult:
        payload = {
            "model": self.model_id,
            "task": "retrieval.query",
            "return_multivector": True,
            "input": [text],
        }
        return self._parse_response(self._post(payload))
