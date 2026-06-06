"""list_b2c_products tool handler."""

from mcp_server.data_access.catalog import CatalogError, list_products


def handle_list_b2c_products() -> dict[str, list[dict[str, str | int]]]:
    """Return B2C catalog items."""
    try:
        return {"items": list_products()}
    except (CatalogError, FileNotFoundError) as exc:
        raise ValueError(str(exc)) from exc
