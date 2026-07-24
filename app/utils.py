"""
Utility functions for response formatting, error handling,
and data normalisation.
"""

import logging
from typing import Any

import httpx

from app.exceptions import (
    AppException,
    AuthenticationError,
    BadGatewayError,
    NotFoundError,
    PortalUnavailableError,
)

logger = logging.getLogger(__name__)


def format_response(data: Any, success: bool = True) -> dict[str, Any]:
    """Wrap raw data into a standardised API response envelope."""
    return {
        "success": success,
        "data": data,
    }


def normalize_export_data(response: Any) -> list[dict[str, Any]]:
    """Normalise the export endpoint response into a list of meter dicts.

    The legacy portal may return:

    - A dictionary with a ``data`` key containing the list.
    - A plain list of meter objects.

    Args:
        response: The raw JSON response from the export endpoint.

    Returns:
        A list of normalised meter dictionaries.

    Raises:
        BadGatewayError: If the response is neither a dict with a ``data`` key
            nor a list.
    """
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list):
            return data
        raise BadGatewayError(
            detail="Export response 'data' field is not a list",
        )
    if isinstance(response, list):
        return response
    raise BadGatewayError(
        detail="Export response has an unexpected structure",
    )


def map_httpx_error(exc: httpx.HTTPError) -> AppException:
    """Map an ``httpx`` exception to a typed application exception.

    Args:
        exc: The ``httpx`` exception instance.

    Returns:
        An ``AppException`` subclass with an appropriate status code and message.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 401:
            return AuthenticationError(detail=str(exc))
        if status == 404:
            return NotFoundError(detail=str(exc))
        return PortalUnavailableError(detail=str(exc))

    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return PortalUnavailableError(detail=str(exc))

    return PortalUnavailableError(detail=str(exc))

