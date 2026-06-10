"""Live integration tests for Langfuse v3 (skipped without env)."""

import base64
import os

import httpx
import pytest
from langfuse import Langfuse

pytestmark = pytest.mark.live


def _langfuse_configured() -> bool:
    return bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY")
        and os.environ.get("LANGFUSE_SECRET_KEY")
        and os.environ.get("LANGFUSE_HOST"),
    )


@pytest.mark.skipif(not _langfuse_configured(), reason="LANGFUSE_* env not set")
def test_langfuse_health_endpoint() -> None:
    """Langfuse v3 UI health responds."""
    host = os.environ["LANGFUSE_HOST"].rstrip("/")
    response = httpx.get(f"{host}/api/public/health", timeout=10.0)
    assert response.status_code == 200


@pytest.mark.skipif(not _langfuse_configured(), reason="LANGFUSE_* env not set")
def test_langfuse_otlp_endpoint_exists() -> None:
    """OTLP traces endpoint is available on v3 (v2 returned 404)."""
    host = os.environ["LANGFUSE_HOST"].rstrip("/")
    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()

    response = httpx.post(
        f"{host}/api/public/otel/v1/traces",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
        content=b"[]",
        timeout=10.0,
    )
    assert response.status_code != 404


@pytest.mark.skipif(not _langfuse_configured(), reason="LANGFUSE_* env not set")
def test_langfuse_sdk_lists_traces() -> None:
    """Langfuse Python SDK can query traces API."""
    client = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.environ["LANGFUSE_HOST"],
    )
    traces = client.api.trace.list(limit=1)
    assert traces is not None
    client.shutdown()
