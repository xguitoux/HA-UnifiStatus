"""Config flow for UniFi Network API integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    UnifiAuthenticationError,
    UnifiConnectionError,
    UnifiNetworkApiClient,
)
from .const import CONF_API_KEY, CONF_SITE_ID, CONF_SITE_NAME, CONF_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)


class UnifiNetworkApiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Network API."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str = ""
        self._api_key: str = ""
        self._verify_ssl: bool = False
        self._sites: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._api_key = user_input[CONF_API_KEY]
            self._verify_ssl = user_input.get(CONF_VERIFY_SSL, False)

            session = async_create_clientsession(
                self.hass, verify_ssl=self._verify_ssl
            )
            client = UnifiNetworkApiClient(
                self._host, self._api_key, self._verify_ssl, session
            )

            try:
                await client.get_info()
                self._sites = await client.get_sites()
            except UnifiAuthenticationError:
                errors["base"] = "invalid_auth"
            except UnifiConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                if len(self._sites) == 1:
                    site = self._sites[0]
                    return await self._create_entry(
                        site["id"], site.get("name", site["id"])
                    )
                if len(self._sites) > 1:
                    return await self.async_step_site()
                errors["base"] = "no_sites"

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    async def async_step_site(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle site selection step."""
        if user_input is not None:
            site_id = user_input[CONF_SITE_ID]
            site_name = next(
                (s.get("name", s["id"]) for s in self._sites if s["id"] == site_id),
                site_id,
            )
            return await self._create_entry(site_id, site_name)

        site_options = {
            site["id"]: site.get("name", site["id"]) for site in self._sites
        }
        site_schema = vol.Schema(
            {vol.Required(CONF_SITE_ID): vol.In(site_options)}
        )
        return self.async_show_form(step_id="site", data_schema=site_schema)

    async def _create_entry(
        self, site_id: str, site_name: str
    ) -> ConfigFlowResult:
        """Create a config entry."""
        await self.async_set_unique_id(f"{self._host}_{site_id}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"UniFi {site_name} ({self._host})",
            data={
                CONF_HOST: self._host,
                CONF_API_KEY: self._api_key,
                CONF_VERIFY_SSL: self._verify_ssl,
                CONF_SITE_ID: site_id,
                CONF_SITE_NAME: site_name,
            },
        )
