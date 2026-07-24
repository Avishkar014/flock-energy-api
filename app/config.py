"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    BASE_URL: str = os.getenv(
        "BASE_URL",
        "https://urja-ops.flockenergy.tech"
    )

    # Support both EMAIL and USERNAME env vars, preferring EMAIL
    EMAIL: str = os.getenv("EMAIL") or os.getenv("USERNAME", "")
    PASSWORD: str = os.getenv("PASSWORD", "")

    REQUEST_TIMEOUT: int = int(
        os.getenv("REQUEST_TIMEOUT", "30")
    )

    VERIFY_SSL: bool = (
        os.getenv("VERIFY_SSL", "true").lower() == "true"
    )

    # Better Auth login endpoint — try common patterns
    LOGIN_URL: str = os.getenv("LOGIN_URL", "/login")

    # Portal API prefix for protected routes
    API_PREFIX: str = os.getenv("API_PREFIX", "/portal")


settings = Settings()
