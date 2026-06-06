"""OpenAI-compatible embedding client."""

import hashlib
import math
from typing import Protocol

from openai import OpenAI

from mcp_server.config import get_settings

EMBEDDING_DIM = 384


class EmbeddingClient(Protocol):
    """Protocol for embedding providers."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for each text."""
        ...


class OpenRouterEmbeddings:
    """Embeddings via OpenAI-compatible API (OpenRouter)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        runtime = get_settings()
        self._api_key = api_key if api_key is not None else runtime.openai_api_key
        self._base_url = base_url if base_url is not None else runtime.openai_base_url
        self._model = model if model is not None else runtime.embedding_model
        if not self._api_key:
            msg = "OPENAI_API_KEY is required for embeddings"
            raise ValueError(msg)
        self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]


class MockEmbeddings:
    """Deterministic local embeddings for tests (no API calls)."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_hash_to_vector(text) for text in texts]


def _hash_to_vector(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(EMBEDDING_DIM):
        byte = digest[index % len(digest)]
        values.append((byte / 255.0) * 2.0 - 1.0)
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]


def get_embedding_client(*, use_mock: bool = False) -> EmbeddingClient:
    """Return embedding client for production or local tests."""
    runtime = get_settings()
    if use_mock or not runtime.openai_api_key or runtime.openai_api_key == "test-key":
        return MockEmbeddings()
    return OpenRouterEmbeddings()
