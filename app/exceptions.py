"""
Custom exception classes for structured error handling.

All custom exceptions inherit from AppException and carry
a numeric code and human-readable message for the API response.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, code: int, message: str, detail: Any = None) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to a standardised error envelope."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }


class AuthenticationError(AppException):
    """Raised when authentication with the Urja portal fails (401)."""

    def __init__(self, detail: Any = None) -> None:
        super().__init__(
            code=401,
            message="Authentication failed",
            detail=detail,
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, resource: str = "Resource", detail: Any = None) -> None:
        super().__init__(
            code=404,
            message=f"{resource} not found",
            detail=detail,
        )


class PortalUnavailableError(AppException):
    """Raised when the upstream Urja portal is unreachable or returns 5xx (500)."""

    def __init__(self, detail: Any = None) -> None:
        super().__init__(
            code=500,
            message="Portal unavailable",
            detail=detail,
        )


class BadGatewayError(AppException):
    """Raised when the upstream portal returns unexpected or malformed data (502)."""

    def __init__(self, detail: Any = None) -> None:
        super().__init__(
            code=502,
            message="Bad Gateway",
            detail=detail,
        )

