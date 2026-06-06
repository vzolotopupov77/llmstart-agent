"""Shared product schemas for chat and catalog APIs."""

from pydantic import BaseModel


class ProductItem(BaseModel):
    """B2C product card."""

    code: str
    title: str
    price: int
    currency: str
