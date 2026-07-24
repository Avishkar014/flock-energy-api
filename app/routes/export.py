"""
Export-related REST endpoints.

Provides a single endpoint to retrieve all available meter data
from the legacy portal in a cleaned, normalised format.
"""

from fastapi import APIRouter, Depends

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

router = APIRouter(
    prefix="/api/v1",
    tags=["Export"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("/export")
async def export_data(
    service: MeterService = Depends(get_service),
):
    """Return all meters from the export endpoint."""
    return await service.export_all_meters()

