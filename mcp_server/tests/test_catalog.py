"""Tests for catalog data access."""

from mcp_server.data_access.catalog import load_catalog
from mcp_server.tools.list_b2c_products import handle_list_b2c_products


def test_load_catalog_has_six_products(
    settings_env: object, sample_catalog_items: list[dict[str, object]]
) -> None:
    catalog = load_catalog()
    assert len(catalog.items) == 6
    codes = {item.code for item in catalog.items}
    expected = {str(item["code"]) for item in sample_catalog_items}
    assert codes == expected


def test_list_b2c_products_returns_items(settings_env: object) -> None:
    result = handle_list_b2c_products()
    assert "items" in result
    assert len(result["items"]) == 6
    first = result["items"][0]
    assert {"code", "title", "price", "price_display", "currency", "description"} <= set(
        first.keys(),
    )
    assert isinstance(first["price_display"], str)
