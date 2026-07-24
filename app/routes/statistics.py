"""
Statistics REST endpoint.

Aggregates meter data into summary statistics.
"""

from fastapi import APIRouter, Depends

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

router = APIRouter(
    prefix="/api/v1",
    tags=["Statistics"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("/statistics")
async def get_statistics(
    service: MeterService = Depends(get_service),
):
    """Return aggregated statistics for all meters.

    Includes total counts, installation status breakdown,
    phase-type distribution and manufacturer grouping.
    """
    return await service.get_statistics()

