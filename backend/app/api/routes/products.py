"""GET /api/v1/products endpoint."""

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.schemas.products import ProductListResponse
from app.core.exceptions import CatalogUnavailableError
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get("/products", response_model=ProductListResponse)
def list_products(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    """Return paginated B2C catalog for the web widget."""
    catalog_service: CatalogService = request.app.state.catalog_service
    try:
        return catalog_service.list_products(limit=limit, offset=offset)
    except CatalogUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=CatalogUnavailableError.DEFAULT_MESSAGE,
        ) from exc
