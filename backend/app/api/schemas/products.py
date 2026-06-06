"""Pydantic schemas for GET /api/v1/products."""

from pydantic import BaseModel, Field

from app.api.schemas.product import ProductItem


class ProductListResponse(BaseModel):
    """Paginated B2C catalog response."""

    items: list[ProductItem]
    total: int
    limit: int
    offset: int


class ProductListQuery(BaseModel):
    """Validated query parameters for product listing."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
