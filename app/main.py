"""
FastAPI application entry point.

Registers all route modules and global exception handlers.
Uses a single shared ``httpx.AsyncClient`` for the entire application
lifetime so that Better Auth session cookies are preserved across all
incoming requests.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.client import UrjaClient
from app.config import settings
from app.exceptions import AppException
from app.routes.dashboard import router as dashboard_router
from app.routes.export import router as export_router
from app.routes.hierarchy import router as hierarchy_router
from app.routes.meters import router as meter_router
from app.routes.statistics import router as statistics_router
from app.routes.transformers import router as transformer_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared HTTP client (lifetime = application lifetime)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create a single ``httpx.AsyncClient`` + ``UrjaClient`` on startup
    and clean them up on shutdown.

    The shared ``UrjaClient`` is stored in ``app.state.urja_client`` and
    can be injected via the ``get_urja_client()`` dependency defined in
    ``app.dependencies``.
    """
    logger.info("Starting up -- creating shared HTTP client ...")

    shared_client = httpx.AsyncClient(
        base_url=settings.BASE_URL,
        timeout=settings.REQUEST_TIMEOUT,
        verify=settings.VERIFY_SSL,
        follow_redirects=True,
        headers={
            "Accept": "text/html,application/json,*/*",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
        },
    )

    urja_client = UrjaClient(client=shared_client)
    app.state.urja_client = urja_client

    logger.info("Shared UrjaClient created. Base URL: %s", settings.BASE_URL)

    yield  # Application runs here

    logger.info("Shutting down -- closing shared HTTP client ...")
    await shared_client.aclose()
    logger.info("Shared HTTP client closed.")


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Flock Energy Assignment API",
    version="1.0.0",
    description=(
        "Production-ready REST API wrapper for the Flock Energy / Urja portal.\n\n"
        "Features include meter management, transformer details, location hierarchy, "
        "aggregated statistics, and a combined dashboard."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(meter_router)
app.include_router(transformer_router)
app.include_router(export_router)
app.include_router(statistics_router)
app.include_router(hierarchy_router)
app.include_router(dashboard_router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handle all custom ``AppException`` subclasses.

    Returns a structured JSON error envelope without leaking stack traces.
    """
    logger.warning(
        "AppException caught: code=%d message=%s path=%s",
        exc.code,
        exc.message,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.code,
        content=exc.to_dict(),
    )


@app.exception_handler(httpx.HTTPStatusError)
async def httpx_status_error_handler(
    request: Request,
    exc: httpx.HTTPStatusError,
) -> JSONResponse:
    """Handle upstream HTTP status errors (non-2xx responses from legacy portal)."""
    logger.warning(
        "httpx.HTTPStatusError: status=%d path=%s",
        exc.response.status_code,
        request.url.path,
    )

    status = exc.response.status_code
    if status == 401:
        code, message = 401, "Authentication failed"
    elif status == 404:
        code, message = 404, "Resource not found"
    elif status >= 500:
        code, message = 500, "Portal unavailable"
    else:
        code, message = 502, "Bad Gateway"

    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


@app.exception_handler(httpx.ConnectError)
async def httpx_connect_error_handler(
    request: Request,
    exc: httpx.ConnectError,
) -> JSONResponse:
    """Handle connection errors when the upstream portal cannot be reached."""
    logger.error("httpx.ConnectError: cannot reach upstream portal path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Portal unavailable",
            },
        },
    )


@app.exception_handler(httpx.TimeoutException)
async def httpx_timeout_handler(
    request: Request,
    exc: httpx.TimeoutException,
) -> JSONResponse:
    """Handle upstream request timeouts."""
    logger.error("httpx.TimeoutException: upstream timed out path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Portal unavailable",
            },
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
) -> JSONResponse:
    """Handle unexpected ``ValueError`` exceptions."""
    logger.exception("ValueError caught path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
            },
        },
    )


@app.exception_handler(KeyError)
async def key_error_handler(
    request: Request,
    exc: KeyError,
) -> JSONResponse:
    """Handle unexpected ``KeyError`` exceptions."""
    logger.exception("KeyError caught path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
            },
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for any unhandled exception.

    Never exposes raw Python exception details to the client.
    """
    logger.exception("Unhandled exception caught path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
            },
        },
    )


# ---------------------------------------------------------------------------
# Root health-check
# ---------------------------------------------------------------------------


@app.get("/")
async def root() -> dict[str, Any]:
    """Health-check endpoint."""
    return {"message": "API is running"}

