"""B2C product catalog access."""

import json
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, Field, ValidationError

from mcp_server.data_access.price_format import format_price_display
from mcp_server.paths import catalog_path

EXPECTED_PRODUCT_COUNT = 6


class ProductItem(BaseModel):
    """Single B2C catalog product."""

    code: str
    title: str
    price: int = Field(ge=0, description="Price in minor units (kopecks for RUB)")
    currency: str = "RUB"
    description: str = ""


class Catalog(BaseModel):
    """Full B2C catalog."""

    items: list[ProductItem]

    def get_by_code(self, code: str) -> ProductItem | None:
        """Find product by code."""
        return next((item for item in self.items if item.code == code), None)


class CatalogCache(TypedDict):
    """In-process catalog cache entry."""

    mtime: float
    catalog: Catalog


_cache: CatalogCache | None = None


def _load_catalog(path: Path) -> Catalog:
    raw = json.loads(path.read_text(encoding="utf-8"))
    catalog = Catalog.model_validate(raw)
    if len(catalog.items) != EXPECTED_PRODUCT_COUNT:
        msg = f"catalog must contain {EXPECTED_PRODUCT_COUNT} products, got {len(catalog.items)}"
        raise ValueError(msg)
    return catalog


def load_catalog(*, force: bool = False) -> Catalog:
    """Load catalog with in-process cache invalidated by file mtime."""
    global _cache  # noqa: PLW0603

    path = catalog_path()
    if not path.exists():
        msg = f"catalog not found: {path}"
        raise FileNotFoundError(msg)

    mtime = path.stat().st_mtime
    if not force and _cache is not None and _cache["mtime"] == mtime:
        return _cache["catalog"]

    catalog = _load_catalog(path)
    _cache = {"mtime": mtime, "catalog": catalog}
    return catalog


def list_products() -> list[dict[str, str | int]]:
    """Return catalog items as dicts for tool response."""
    items: list[dict[str, str | int]] = []
    for item in load_catalog().items:
        row = item.model_dump()
        row["price_display"] = format_price_display(item.price, item.currency)
        items.append(row)
    return items


def validate_product_id(product_id: str) -> ProductItem:
    """Ensure product exists in catalog."""
    product = load_catalog().get_by_code(product_id)
    if product is None:
        msg = f"unknown product_id: {product_id}"
        raise ValueError(msg)
    return product


def clear_cache() -> None:
    """Clear in-process catalog cache (for tests)."""
    global _cache  # noqa: PLW0603
    _cache = None


class CatalogError(Exception):
    """Catalog validation or IO error."""


def safe_load_catalog() -> Catalog:
    """Load catalog wrapping validation errors."""
    try:
        return load_catalog()
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise CatalogError(str(exc)) from exc
