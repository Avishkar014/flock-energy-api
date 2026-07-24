"""
Hierarchy REST endpoint.

Builds a nested location hierarchy from export data.
"""

from fastapi import APIRouter, Depends

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

router = APIRouter(
    prefix="/api/v1/hierarchy",
    tags=["Hierarchy"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("")
async def list_hierarchy(
    service: MeterService = Depends(get_service),
):
    """Return the full nested location hierarchy.

    Structure: Zone -> Circle -> Division -> Subdivision -> Substation -> Feeder -> DT -> Meters
    """
    return await service.get_hierarchy()

