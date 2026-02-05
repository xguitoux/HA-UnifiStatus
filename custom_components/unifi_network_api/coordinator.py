"""DataUpdateCoordinator for UniFi Network API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import UnifiApiError, UnifiAuthenticationError, UnifiNetworkApiClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class UnifiNetworkApiCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching UniFi data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: UnifiNetworkApiClient,
        site_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.site_id = site_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the UniFi API."""
        try:
            devices_list, clients_list, wans_list = await asyncio.gather(
                self.client.get_devices(self.site_id),
                self.client.get_clients(self.site_id),
                self.client.get_wans(self.site_id),
            )

            # Fetch statistics for each device in parallel
            devices: dict[str, dict[str, Any]] = {}
            if devices_list:
                stats_results = await asyncio.gather(
                    *(
                        self._fetch_device_data(device)
                        for device in devices_list
                    ),
                    return_exceptions=True,
                )
                for device, result in zip(devices_list, stats_results):
                    device_id = device["id"]
                    if isinstance(result, Exception):
                        _LOGGER.debug(
                            "Failed to fetch stats for device %s: %s",
                            device_id,
                            result,
                        )
                        devices[device_id] = {
                            "info": device,
                            "details": {},
                            "statistics": {},
                        }
                    else:
                        devices[device_id] = result

            # Count clients by type
            client_count_wired = 0
            client_count_wireless = 0
            client_count_vpn = 0
            for client in clients_list:
                client_type = client.get("type", "").upper()
                if client_type == "WIRED":
                    client_count_wired += 1
                elif client_type == "WIRELESS":
                    client_count_wireless += 1
                elif client_type == "VPN":
                    client_count_vpn += 1

            return {
                "devices": devices,
                "clients": clients_list,
                "wans": wans_list,
                "client_count": len(clients_list),
                "client_count_wired": client_count_wired,
                "client_count_wireless": client_count_wireless,
                "client_count_vpn": client_count_vpn,
            }

        except UnifiAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except UnifiApiError as err:
            raise UpdateFailed(f"Error communicating with UniFi API: {err}") from err

    async def _fetch_device_data(
        self, device: dict[str, Any]
    ) -> dict[str, Any]:
        """Fetch details and statistics for a single device."""
        device_id = device["id"]
        details, statistics = await asyncio.gather(
            self.client.get_device_details(self.site_id, device_id),
            self.client.get_device_statistics(self.site_id, device_id),
        )
        return {
            "info": device,
            "details": details,
            "statistics": statistics,
        }
