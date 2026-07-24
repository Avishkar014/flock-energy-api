"""
Meter-related REST endpoints.

All business logic is delegated to ``MeterService``.
Routes remain thin — no filtering or data transformation here.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

router = APIRouter(
    prefix="/api/v1/meters",
    tags=["Meters"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("")
async def get_meters(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    search: str = Query("", description="Free-text search term"),
    status: Optional[str] = Query(None, description="Filter by installation status"),
    make: Optional[str] = Query(None, description="Filter by manufacturer"),
    phase: Optional[str] = Query(None, description="Filter by phase type (single / three)"),
    service: MeterService = Depends(get_service),
):
    """Return a paginated, optionally filtered list of meters.

    Multiple filters can be combined; they are applied conjunctively.
    """
    return await service.get_meters(
        page=page,
        query=search,
        status=status,
        make=make,
        phase=phase,
    )


@router.get("/{meter_id}")
async def get_meter(
    meter_id: str,
    service: MeterService = Depends(get_service),
):
    """Return detailed information for a single meter (geo + consumption)."""
    return await service.get_meter_details(meter_id)


@router.get("/{meter_id}/consumption")
async def get_consumption(
    meter_id: str,
    service: MeterService = Depends(get_service),
):
    """Return energy consumption history for a single meter.

    Delegates to ``MeterService.get_meter_consumption()`` so that the
    business logic layer handles authentication, error mapping and
    response normalisation.
    """
    return await service.get_meter_consumption(meter_id)

