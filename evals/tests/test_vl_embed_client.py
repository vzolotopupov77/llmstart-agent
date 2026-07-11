"""Tests for VL embed client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from indexers.caption.pricing import ModelPricing
from indexers.vl_embed.openrouter import OpenRouterVLEmbedClient


def test_embed_image_parses_response(tmp_path: Path) -> None:
    image_path = tmp_path / "slide-01.png"
    image_path.write_bytes(b"fake-png")

    pricing = ModelPricing(
        model_id="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        prompt_per_token=0.0,
        completion_per_token=0.0,
    )
    client = OpenRouterVLEmbedClient(
        "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        pricing=pricing,
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        timeout_s=5.0,
    )

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]
    mock_response.usage = MagicMock(prompt_tokens=100)

    with patch("openai.OpenAI") as openai_cls:
        openai_client = MagicMock()
        openai_client.embeddings.create.return_value = mock_response
        openai_cls.return_value = openai_client

        result = client.embed_image(image_path)

    assert result.vector == [0.1, 0.2, 0.3]
    assert result.prompt_tokens == 100
    assert result.est_cost_usd == 0.0
    openai_client.embeddings.create.assert_called_once()
    call_kwargs = openai_client.embeddings.create.call_args.kwargs
    assert call_kwargs["model"] == "nvidia/llama-nemotron-embed-vl-1b-v2:free"
    assert call_kwargs["encoding_format"] == "float"
    content = call_kwargs["input"][0]["content"]
    assert content[0]["type"] == "image_url"


def test_embed_query_uses_text_content() -> None:
    pricing = ModelPricing(
        model_id="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        prompt_per_token=0.0,
        completion_per_token=0.0,
    )
    client = OpenRouterVLEmbedClient(
        "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        pricing=pricing,
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        timeout_s=5.0,
    )

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.5, 0.6]
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]
    mock_response.usage = MagicMock(prompt_tokens=10)

    with patch("openai.OpenAI") as openai_cls:
        openai_client = MagicMock()
        openai_client.embeddings.create.return_value = mock_response
        openai_cls.return_value = openai_client

        result = client.embed_query("Какие шаги модели Коттера?")

    assert result.vector == [0.5, 0.6]
    content = openai_client.embeddings.create.call_args.kwargs["input"][0]["content"]
    assert content[0]["type"] == "text"
    assert "Коттера" in content[0]["text"]
