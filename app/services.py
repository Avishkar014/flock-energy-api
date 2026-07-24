"""
Business service layer.

Responsible for:
- Calling the ``UrjaClient``
- Transforming portal responses
- Merging multiple portal endpoints
- Filtering and aggregating data
- Building nested hierarchy structures
"""

import logging
from typing import Any, Optional

import httpx

from app.client import UrjaClient
from app.exceptions import (
    AppException,
    AuthenticationError,
    BadGatewayError,
    NotFoundError,
    PortalUnavailableError,
)
from app.utils import normalize_export_data

logger = logging.getLogger(__name__)


class MeterService:
    """Business logic for meter, transformer, hierarchy and statistics operations.

    Accepts a shared ``UrjaClient`` via dependency injection so that all
    service instances reuse the same session (cookies, connection pool).
    """

    def __init__(self, client: UrjaClient) -> None:
        self.client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_normalized_export(self, page: int = 1) -> list[dict[str, Any]]:
        """Fetch export data and return a normalised list of meter dicts.

        Supports both response shapes:

        - ``[{...}]`` (plain list)
        - ``{"data": [...], "total": ...}`` (wrapped dict)

        Args:
            page: Page number to fetch (default 1).

        Returns:
            A list of meter dictionaries from the export endpoint.

        Raises:
            NotFoundError: If the export endpoint returns no meters.
            PortalUnavailableError: On HTTP/connection errors.
            BadGatewayError: If the response structure is unexpected.
        """
        try:
            response = await self.client.export_data(page=page)
        except httpx.HTTPStatusError as exc:
            raise self._map_error(exc)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise PortalUnavailableError(detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error fetching export data")
            raise PortalUnavailableError(detail=str(exc))

        try:
            meters = normalize_export_data(response)
        except BadGatewayError:
            raise
        except Exception as exc:
            logger.exception("Failed to normalise export data")
            raise PortalUnavailableError(detail=str(exc))

        if not meters:
            raise NotFoundError(
                resource="Meters",
                detail="No meters found in export data",
            )

        return meters

    # ------------------------------------------------------------------
    # Error mapper (reduces repeated try/except boilerplate)
    # ------------------------------------------------------------------

    @staticmethod
    def _map_error(exc: httpx.HTTPStatusError) -> AppException:
        """Map an ``httpx.HTTPStatusError`` to an application exception."""
        status = exc.response.status_code
        if status == 401:
            return AuthenticationError(detail=str(exc))
        if status == 404:
            return NotFoundError(detail=str(exc))
        return PortalUnavailableError(detail=str(exc))

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    async def get_meters(
        self,
        page: int = 1,
        query: str = "",
        status: Optional[str] = None,
        make: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return a paginated, optionally filtered list of meters.

        Args:
            page:       Page number (1-based).
            query:      Free-text search string.
            status:     Filter by installation status (e.g. ``"Installed"``).
            make:       Filter by manufacturer (e.g. ``"Genus"``).
            phase:      Filter by phase type (e.g. ``"single"``, ``"three"``).

        Returns:
            A dictionary with ``page``, ``total`` and ``meters`` keys.
        """
        try:
            portal_data = await self.client.search_meters(query, page)
        except httpx.HTTPStatusError as exc:
            raise self._map_error(exc)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise PortalUnavailableError(detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error searching meters")
            raise PortalUnavailableError(detail=str(exc))

        meters: list[dict[str, Any]] = portal_data.get("data", [])

        # Client-side filtering (composable filters)
        if status:
            meters = [
                m
                for m in meters
                if m.get("installStatus", "").lower() == status.lower()
            ]

        if make:
            meters = [
                m
                for m in meters
                if m.get("make", "").lower() == make.lower()
            ]

        if phase:
            meters = [
                m
                for m in meters
                if phase.lower() in m.get("phaseType", "").lower()
            ]

        return {
            "page": page,
            "total": len(meters),
            "meters": meters,
        }

    async def get_meter_details(self, meter_id: str) -> dict[str, Any]:
        """Merge geo-location and energy consumption for a single meter.

        Args:
            meter_id: The unique meter identifier.

        Returns:
            A dictionary with ``meterId``, ``geo`` and ``consumption``.

        Raises:
            NotFoundError: If the meter is not found on the portal.
        """
        try:
            geo_task = self.client.get_geo(meter_id)
            energy_task = self.client.get_energy(meter_id)
            geo, energy = await geo_task, energy_task
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise NotFoundError(
                    resource="Meter",
                    detail=f"Meter {meter_id} not found",
                )
            raise self._map_error(exc)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise PortalUnavailableError(detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error fetching meter details")
            raise PortalUnavailableError(detail=str(exc))

        return {
            "meterId": meter_id,
            "geo": geo,
            "consumption": energy,
        }

    async def get_meter_consumption(self, meter_id: str) -> dict[str, Any]:
        """Return energy consumption for a single meter.

        Args:
            meter_id: The unique meter identifier.

        Returns:
            The raw energy consumption data from the portal.
        """
        try:
            energy = await self.client.get_energy(meter_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise NotFoundError(
                    resource="Meter",
                    detail=f"Meter {meter_id} not found",
                )
            raise self._map_error(exc)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise PortalUnavailableError(detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error fetching meter consumption")
            raise PortalUnavailableError(detail=str(exc))

        return energy

    # ------------------------------------------------------------------
    # Transformers
    # ------------------------------------------------------------------

    async def get_transformers(self, page: int = 1) -> dict[str, Any]:
        """Return a paginated list of distribution transformers.

        Args:
            page: Page number (1-based).

        Returns:
            A dictionary with ``page`` and ``transformers`` keys.
        """
        try:
            portal_data = await self.client.get_transformers(page)
        except httpx.HTTPStatusError as exc:
            raise self._map_error(exc)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise PortalUnavailableError(detail=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error fetching transformers")
            raise PortalUnavailableError(detail=str(exc))

        return {
            "page": page,
            "transformers": portal_data.get("data", portal_data),
        }

    async def get_transformer_meters(self, dt_code: str) -> dict[str, Any]:
        """Return all meters belonging to a specific distribution transformer.

        Args:
            dt_code: The DT code (e.g. ``"DT001"``).

        Returns:
            A dictionary with ``dtCode``, ``totalMeters`` and ``meters``.

        Raises:
            NotFoundError: If no meters are found for the given DT code.
        """
        meters = await self._fetch_normalized_export()

        filtered = [meter for meter in meters if meter.get("dtCode") == dt_code]

        if not filtered:
            raise NotFoundError(
                resource="Transformer",
                detail=f"No meters found for DT code {dt_code}",
            )

        return {
            "dtCode": dt_code,
            "totalMeters": len(filtered),
            "meters": filtered,
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_all_meters(self) -> dict[str, Any]:
        """Return all meters from the export endpoint.

        Returns:
            A dictionary with ``total`` and ``meters`` keys.
        """
        meters = await self._fetch_normalized_export()

        return {
            "total": len(meters),
            "meters": meters,
        }

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def get_statistics(self) -> dict[str, Any]:
        """Build aggregated statistics from exported meter data.

        Returns:
            A dictionary with counts for total, installed, faulty,
            decommissioned, single-phase, three-phase meters and a
            manufacturer breakdown.
        """
        meters = await self._fetch_normalized_export()

        installed = 0
        faulty = 0
        decommissioned = 0
        single_phase = 0
        three_phase = 0
        manufacturers: dict[str, int] = {}

        for meter in meters:
            status = meter.get("installStatus", "").lower()

            if status == "installed":
                installed += 1
            elif status == "faulty":
                faulty += 1
            elif status == "decommissioned":
                decommissioned += 1

            phase = meter.get("phaseType", "").lower()
            if "single" in phase:
                single_phase += 1
            if "three" in phase:
                three_phase += 1

            make = meter.get("make", "Unknown") or "Unknown"
            manufacturers[make] = manufacturers.get(make, 0) + 1

        return {
            "totalMeters": len(meters),
            "installed": installed,
            "faulty": faulty,
            "decommissioned": decommissioned,
            "singlePhase": single_phase,
            "threePhase": three_phase,
            "manufacturers": manufacturers,
        }

    # ------------------------------------------------------------------
    # Hierarchy
    # ------------------------------------------------------------------

    async def get_hierarchy(self) -> list[dict[str, Any]]:
        """Build a nested location hierarchy from export data.

        The hierarchy levels are:

        Zone -> Circle -> Division -> Subdivision -> Substation -> Feeder -> DT -> Meters

        Each meter node in the leaf level contains ``meterId``, ``serialNo``,
        ``make`` and ``phaseType``.

        Returns:
            A list of top-level zone nodes, each with nested children.
        """
        meters = await self._fetch_normalized_export()

        # Tree structure: zone -> circle -> division -> subdivision -> substation -> feeder -> dt -> meters
        tree: dict[str, Any] = {}

        for meter in meters:
            zone = meter.get("zone", "Unknown Zone")
            circle = meter.get("circle", "Unknown Circle")
            division = meter.get("division", "Unknown Division")
            subdivision = meter.get("subdivision", "Unknown Subdivision")
            substation = meter.get("substation", "Unknown Substation")
            feeder = meter.get("feeder", "Unknown Feeder")
            dt_code = meter.get("dtCode", "Unknown DT")

            # Build meter leaf node
            meter_node = {
                "meterId": meter.get("meterId", ""),
                "serialNo": meter.get("serialNo", ""),
                "make": meter.get("make", ""),
                "phaseType": meter.get("phaseType", ""),
            }

            # Ensure nested dicts exist
            zone_dict = tree.setdefault(zone, {"name": zone, "children": []})
            circle_dict = _find_or_create_child(zone_dict, circle, "Circle")
            division_dict = _find_or_create_child(circle_dict, division, "Division")
            subdivision_dict = _find_or_create_child(division_dict, subdivision, "Subdivision")
            substation_dict = _find_or_create_child(subdivision_dict, substation, "Substation")
            feeder_dict = _find_or_create_child(substation_dict, feeder, "Feeder")
            dt_dict = _find_or_create_child(feeder_dict, dt_code, "DT")

            # Append meter to DT's meters list
            dt_dict.setdefault("meters", []).append(meter_node)

        return list(tree.values())


def _find_or_create_child(
    parent: dict[str, Any],
    name: str,
    level: str,
) -> dict[str, Any]:
    """Find a child node by name inside *parent*, or create it.

    Args:
        parent: The parent dictionary that holds ``children``.
        name:   The name of the child to find / create.
        level:  The hierarchy level label (used for documentation only).

    Returns:
        The existing or newly created child dictionary.
    """
    children: list[dict[str, Any]] = parent.setdefault("children", [])

    for child in children:
        if child.get("name") == name:
            return child

    new_child: dict[str, Any] = {"name": name, "children": []}
    children.append(new_child)
    return new_child

