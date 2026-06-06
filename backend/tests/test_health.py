"""Smoke tests for health endpoint."""


def test_health_returns_ok(client: object) -> None:
    """GET /health returns 200 with status and version."""
    response = client.get("/health")  # type: ignore[attr-defined]

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
