"""
Shared FastAPI dependencies.

Holding ``get_urja_client`` here avoids the circular import that would
occur if routes imported from ``app.main`` (which itself imports routes).
"""

from fastapi import Request

from app.client import UrjaClient


async def get_urja_client(request: Request) -> UrjaClient:
    """FastAPI dependency that yields the application-wide ``UrjaClient``.

    Usage::

        @router.get("/...")
        async def my_endpoint(
            client: UrjaClient = Depends(get_urja_client),
        ):
            ...
    """
    return request.app.state.urja_client

