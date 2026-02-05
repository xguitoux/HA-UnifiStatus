"""UniFi Network API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_PATH = "/proxy/network/integration"


class UnifiApiError(Exception):
    """Base exception for UniFi API errors."""


class UnifiAuthenticationError(UnifiApiError):
    """Authentication error."""


class UnifiConnectionError(UnifiApiError):
    """Connection error."""


class UnifiNetworkApiClient:
    """Async client for the UniFi Local Network API."""

    def __init__(
        self,
        host: str,
        api_key: str,
        verify_ssl: bool,
        session: aiohttp.ClientSession,
    ) -> None:
        self._host = host.rstrip("/")
        self._api_key = api_key
        self._verify_ssl = verify_ssl
        self._session = session
        self._base_url = f"https://{self._host}{BASE_PATH}"

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request."""
        url = f"{self._base_url}{path}"
        headers = {"X-API-Key": self._api_key}
        ssl = None if self._verify_ssl else False

        try:
            async with self._session.request(
                method, url, headers=headers, params=params, ssl=ssl
            ) as resp:
                if resp.status in (401, 403):
                    raise UnifiAuthenticationError(
                        f"Authentication failed: {resp.status}"
                    )
                if resp.status != 200:
                    text = await resp.text()
                    raise UnifiApiError(
                        f"API request failed ({resp.status}): {text}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise UnifiConnectionError(
                f"Cannot connect to UniFi controller at {self._host}: {err}"
            ) from err

    async def _paginate(
        self, path: str, data_key: str = "data"
    ) -> list[dict[str, Any]]:
        """Auto-paginate through all results."""
        results: list[dict[str, Any]] = []
        offset = 0
        limit = 200
        while True:
            resp = await self._request(
                "GET", path, params={"offset": offset, "limit": limit}
            )
            page_data = resp.get(data_key, [])
            results.extend(page_data)
            total = resp.get("totalCount", len(results))
            if len(results) >= total or not page_data:
                break
            offset += limit
        return results

    async def get_info(self) -> dict[str, Any]:
        """Get application info."""
        return await self._request("GET", "/v1/info")

    async def get_sites(self) -> list[dict[str, Any]]:
        """Get all sites."""
        return await self._paginate("/v1/sites")

    async def get_devices(self, site_id: str) -> list[dict[str, Any]]:
        """Get all devices for a site."""
        return await self._paginate(f"/v1/sites/{site_id}/devices")

    async def get_device_details(
        self, site_id: str, device_id: str
    ) -> dict[str, Any]:
        """Get full device details."""
        return await self._request(
            "GET", f"/v1/sites/{site_id}/devices/{device_id}"
        )

    async def get_device_statistics(
        self, site_id: str, device_id: str
    ) -> dict[str, Any]:
        """Get latest device statistics."""
        return await self._request(
            "GET",
            f"/v1/sites/{site_id}/devices/{device_id}/statistics/latest",
        )

    async def get_clients(self, site_id: str) -> list[dict[str, Any]]:
        """Get all connected clients for a site."""
        return await self._paginate(f"/v1/sites/{site_id}/clients")

    async def get_wans(self, site_id: str) -> list[dict[str, Any]]:
        """Get WAN interfaces for a site."""
        resp = await self._request("GET", f"/v1/sites/{site_id}/wans")
        return resp if isinstance(resp, list) else resp.get("data", [])
