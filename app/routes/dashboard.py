"""
Dashboard REST endpoint.

Combines multiple service methods into a single overview response.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.client import UrjaClient
from app.dependencies import get_urja_client
from app.services import MeterService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


async def get_service(client: UrjaClient = Depends(get_urja_client)) -> MeterService:
    """Dependency provider for ``MeterService``.

    Injects the shared ``UrjaClient`` so that session cookies are
    preserved across all requests.
    """
    return MeterService(client=client)


@router.get("")
async def get_dashboard(
    service: MeterService = Depends(get_service),
) -> dict[str, Any]:
    """Return a combined dashboard overview.

    Aggregates statistics, recent meters, manufacturer distribution
    and total transformer count into a single response.

    If any sub-call fails (e.g. authentication error), the exception
    propagates so the client receives a proper error response.
    """
    statistics = await service.get_statistics()
    export = await service.export_all_meters()
    meters = export.get("meters", [])
    recent_meters = meters[-10:] if len(meters) > 10 else meters

    transformers_data = await service.get_transformers(page=1)
    total_transformers = len(transformers_data.get("transformers", []))

    manufacturer_distribution = statistics.get("manufacturers")

    return {
        "statistics": statistics,
        "recentMeters": recent_meters,
        "manufacturerDistribution": manufacturer_distribution,
        "totalTransformers": total_transformers,
    }
