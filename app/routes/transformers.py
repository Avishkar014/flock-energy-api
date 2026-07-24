"""
Transformer-related REST endpoints.

All business logic is delegated to ``MeterService``.
"""

from fastapi import APIRouter, Depends, Query

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

router = APIRouter(
    prefix="/api/v1/transformers",
    tags=["Transformers"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("")
async def get_transformers(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    service: MeterService = Depends(get_service),
):
    """Return a paginated list of distribution transformers."""
    return await service.get_transformers(page)


@router.get("/{dt_code}/meters")
async def get_transformer_meters(
    dt_code: str,
    service: MeterService = Depends(get_service),
):
    """Return all meters belonging to a specific distribution transformer."""
    return await service.get_transformer_meters(dt_code)

