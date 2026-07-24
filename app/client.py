"""
HTTP client for the Urja Meter Ops portal.

Uses a shared ``httpx.AsyncClient`` to maintain session cookies across
all requests.  Automatically re-authenticates when the session expires.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class UrjaClient:
    """HTTP client for the Urja Meter Ops portal.

    Wraps an ``httpx.AsyncClient`` so that cookies (session) are
    persisted across every request made through this instance.

    If no *client* is provided a brand new one will be created (useful for
    standalone testing).
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        if client is not None:
            self.client = client
        else:
            self.client = httpx.AsyncClient(
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

        self._authenticated = False

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    async def ensure_authenticated(self) -> bool:
        """Ensure the session has a valid authentication cookie.

        If the session is not yet authenticated, or if a previous request
        received a 401, this method will attempt to log in.

        Returns:
            ``True`` after a successful login.
        """
        if not self._authenticated:
            return await self.login()

        # Even if we think we're authenticated, verify with a real request
        session_valid = await self._validate_session()
        if not session_valid:
            logger.warning("Session validation failed — re-logging in.")
            self._authenticated = False
            return await self.login()

        return True

    async def _validate_session(self) -> bool:
        """Validate the current session by calling a real portal endpoint.

        ``GET /portal/meters/search?q=&page=1``

        Returns:
            ``True`` if the response is HTTP 200 (session is valid).
        """
        try:
            resp = await self.client.get(
                f"{settings.API_PREFIX}/meters/search",
                params={"q": "", "page": 1},
                follow_redirects=False,
            )
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self) -> bool:
        """Authenticate with the Urja portal.

        The login flow per HAR:

        1. ``POST /login`` with ``application/x-www-form-urlencoded``
        2. Headers: Content-Type, Accept (application/json), Origin, Referer
        3. Body: ``email=<EMAIL>&password=<PASSWORD>``
        4. Log every detail for diagnosability
        5. Verify session cookies exist AND validate with meters/search

        Returns:
            ``True`` if login succeeded (session cookies + valid meters/search).
        """
        email = settings.EMAIL
        password = settings.PASSWORD

        if not email or not password:
            logger.error(
                "UrjaClient.login: EMAIL and PASSWORD must be set "
                "in the environment or .env file."
            )
            return False

        # ------------------------------------------------------------------
        # POST /login with application/x-www-form-urlencoded
        # ------------------------------------------------------------------
        login_url = settings.LOGIN_URL  # "/login"

        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Origin": settings.BASE_URL,
            "Referer": f"{settings.BASE_URL}/login",
        }

        login_payload = {"email": email, "password": password}

        logger.info("=" * 60)
        logger.info("LOGIN ATTEMPT")
        logger.info("Login URL: %s%s", settings.BASE_URL, login_url)
        logger.info("Request headers: %s", login_headers)
        logger.info(
            "Request payload: email=%s, password=****",
            email,
        )

        response = await self.client.post(
            login_url,
            data=login_payload,
            headers=login_headers,
        )

        logger.info("Response status: %d", response.status_code)
        logger.info("Response URL: %s", response.url)
        logger.info("Response headers: %s", dict(response.headers))
        logger.info("Response cookies: %s", dict(self.client.cookies))
        logger.info("Response body (first 2000 chars): %s", response.text[:2000])
        logger.info(
            "Redirect history: %s",
            [str(r.url) for r in response.history],
        )

        # --------------------------------------------------------------
        # Determine success
        # --------------------------------------------------------------

        # Login is ONLY successful if:
        # 1. Session cookies exist on the client
        # 2. A subsequent GET /portal/meters/search returns HTTP 200

        session_cookies = dict(self.client.cookies)

        if not session_cookies:
            logger.error(
                "LOGIN FAILED — No session cookies received.\n"
                "Status: %d\n"
                "Response body: %s\n"
                "Cookies: %s",
                response.status_code,
                response.text[:2000],
                session_cookies,
            )
            self._authenticated = False
            return False

        # Validate with meters/search
        session_valid = await self._validate_session()
        if not session_valid:
            logger.error(
                "LOGIN FAILED — Session validation (meters/search) did not return 200.\n"
                "Status: %d\n"
                "Cookies: %s\n"
                "Body: %s",
                response.status_code,
                session_cookies,
                response.text[:2000],
            )
            self._authenticated = False
            return False

        # Success
        logger.info("=" * 60)
        logger.info("LOGIN SUCCESSFUL")
        logger.info("Status: %d", response.status_code)
        logger.info("Cookies: %s", session_cookies)
        logger.info("=" * 60)

        self._authenticated = True
        return True

    # ------------------------------------------------------------------
    # General-purpose request with auto re-auth
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auto_auth: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an authenticated request, re-logging in on 401.

        Args:
            method:     HTTP method (``"GET"``, ``"POST"``, ...).
            path:       URL path relative to ``settings.BASE_URL``.
            auto_auth:  If ``True`` (default), attempt re-login on 401.
            **kwargs:   Extra arguments forwarded to ``self.client.request``.

        Returns:
            The ``httpx.Response`` object.
        """
        if auto_auth:
            await self.ensure_authenticated()

        response = await self.client.request(method, path, **kwargs)

        # If the portal returns 401, the session probably expired.
        # Re-authenticate and retry the request **once**.
        if auto_auth and response.status_code == 401:
            logger.warning(
                "Session expired (401) on %s %s \u2014 re-logging in.",
                method,
                path,
            )
            self._authenticated = False
            login_ok = await self.login()
            if login_ok:
                logger.info(
                    "Retrying %s %s after re-login.",
                    method,
                    path,
                )
                response = await self.client.request(method, path, **kwargs)
                logger.info(
                    "Retry after re-login: %s %s \u2192 status=%d",
                    method,
                    path,
                    response.status_code,
                )
            else:
                logger.error("Re-login failed \u2014 cannot recover session.")

        logger.debug(
            "UrjaClient %s %s \u2192 %d",
            method,
            str(response.url),
            response.status_code,
        )
        return response

    async def _request_json(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Send an authenticated request and decode the JSON body.

        Raises:
            httpx.HTTPStatusError: If the response status is 4xx or 5xx.
        """
        response = await self._request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Portal API methods
    # ------------------------------------------------------------------

    async def search_meters(self, query: str = "", page: int = 1) -> dict[str, Any]:
        """Search meters by query string.

        ``GET {API_PREFIX}/meters/search?q={query}&page={page}``
        """
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/meters/search",
            params={"q": query, "page": page},
        )

    async def get_geo(self, meter_id: str) -> dict[str, Any]:
        """Get geo-location data for a specific meter.

        ``GET {API_PREFIX}/meters/{meter_id}/geo``
        """
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/meters/{meter_id}/geo",
        )

    async def get_energy(self, meter_id: str) -> dict[str, Any]:
        """Get energy consumption data for a specific meter.

        ``GET {API_PREFIX}/meters/{meter_id}/energy``
        """
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/meters/{meter_id}/energy",
        )

    async def get_transformers(self, page: int = 1) -> dict[str, Any]:
        """Get a paginated list of distribution transformers.

        ``GET {API_PREFIX}/dts?page={page}``
        """
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/dts",
            params={"page": page},
        )

    async def get_keys(self) -> dict[str, Any]:
        """Retrieve signing keys from the portal.

        ``GET {API_PREFIX}/keys``

        Returns:
            The JSON response containing the signing secret.
        """
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/keys",
        )

    async def export_data(self, page: int = 1) -> Any:
        """Get paginated export data with request signing.

        The portal requires an HMAC-SHA256 signature for export requests.

        Flow:
        1. Ensure the session is authenticated.
        2. Fetch the signing secret from ``GET {API_PREFIX}/keys``.
        3. Build a canonical message:
           ``GET\n{API_PREFIX}/export\npage={page}\n{timestamp}``
        4. Compute ``HMAC-SHA256(message, signingSecret).hexdigest()``.
        5. Send ``GET {API_PREFIX}/export?page={page}`` with headers
           ``x-timestamp`` and ``x-signature``.

        Args:
            page: Page number to fetch (default 1).

        Returns:
            A list of meter dicts **or** a dict with a ``"data"`` key
            containing the list.
        """
        # Step 1: ensure we have a valid session
        await self.ensure_authenticated()

        # Step 2: fetch the signing secret
        keys_response = await self.client.get(
            f"{settings.API_PREFIX}/keys",
        )
        keys_response.raise_for_status()
        keys_data = keys_response.json()
        signing_secret: str = keys_data["data"]["signingSecret"]

        # Step 3: build the canonical message
        timestamp = str(int(time.time()))
        query = f"page={page}"
        message = "\n".join([
            "GET",
            "/portal/export",
            query,
            timestamp,
        ])

        # Step 4: compute HMAC-SHA256 signature
        signature = hmac.new(
            signing_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        logger.info(
            "Export signature computed — timestamp=%s signature=%s",
            timestamp,
            signature,
        )

        # Step 5: send the signed request
        return await self._request_json(
            "GET",
            f"{settings.API_PREFIX}/export",
            params={"page": page},
            headers={
                "x-timestamp": timestamp,
                "x-signature": signature,
            },
        )

    async def logout(self) -> bool:
        """Sign out of the Urja portal and clear the session."""
        response = await self._request("POST", "/logout")
        self._authenticated = False
        self.client.cookies.clear()
        logger.info("Logged out \u2014 session cookies cleared.")
        return response.status_code < 400

    async def close(self) -> None:
        """Close the underlying HTTP client (only if **we** created it)."""
        await self.client.aclose()
