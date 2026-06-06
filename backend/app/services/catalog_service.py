"""B2C catalog access for GET /api/v1/products."""

from mcp_server.data_access.catalog import CatalogError, list_products

from app.api.schemas.product import ProductItem
from app.api.schemas.products import ProductListResponse
from app.core.exceptions import CatalogUnavailableError


class CatalogService:
    """Read-only catalog backed by mcp_server data access."""

    def list_products(self, *, limit: int, offset: int) -> ProductListResponse:
        """Return paginated catalog items."""
        try:
            raw_items = list_products()
        except (CatalogError, FileNotFoundError, OSError, ValueError) as exc:
            raise CatalogUnavailableError(str(exc)) from exc

        items = [
            ProductItem(
                code=item["code"],
                title=item["title"],
                price=item["price"],
                currency=item["currency"],
            )
            for item in raw_items
            if _is_valid_product_dict(item)
        ]
        total = len(items)
        page = items[offset : offset + limit]

        return ProductListResponse(
            items=page,
            total=total,
            limit=limit,
            offset=offset,
        )


def _is_valid_product_dict(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    code = item.get("code")
    title = item.get("title")
    price = item.get("price")
    currency = item.get("currency")
    return (
        isinstance(code, str)
        and isinstance(title, str)
        and isinstance(price, int)
        and isinstance(currency, str)
    )
