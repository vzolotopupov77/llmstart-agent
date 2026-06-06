"""Integration tests for GET /api/v1/products."""

from mcp_server.data_access.catalog import list_products as mcp_list_products


def test_products_returns_catalog(client: object) -> None:
    """GET /products returns paginated B2C catalog."""
    response = client.get("/api/v1/products")  # type: ignore[attr-defined]

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 6

    mcp_items = mcp_list_products()
    api_codes = {item["code"] for item in body["items"]}
    mcp_codes = {item["code"] for item in mcp_items}
    assert api_codes == mcp_codes


def test_products_pagination(client: object) -> None:
    """Pagination returns slice with stable total."""
    response = client.get(  # type: ignore[attr-defined]
        "/api/v1/products",
        params={"limit": 2, "offset": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert len(body["items"]) == 2


def test_products_empty_page(client: object) -> None:
    """Offset beyond total returns empty items."""
    response = client.get(  # type: ignore[attr-defined]
        "/api/v1/products",
        params={"offset": 100},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 6


def test_products_invalid_limit_returns_422(client: object) -> None:
    """Invalid limit is rejected."""
    response = client.get(  # type: ignore[attr-defined]
        "/api/v1/products",
        params={"limit": 0},
    )
    assert response.status_code == 422


def test_products_invalid_offset_returns_422(client: object) -> None:
    """Negative offset is rejected."""
    response = client.get(  # type: ignore[attr-defined]
        "/api/v1/products",
        params={"offset": -1},
    )
    assert response.status_code == 422
