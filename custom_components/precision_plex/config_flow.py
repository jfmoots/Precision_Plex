"""Config flow for Precision Plex integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS

from .const import DEFAULT_TARGET_ADDRESS, DOMAIN, TARGET_SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class PrecisionPlexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Precision Plex."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        service_infos = bluetooth.async_discovered_service_info(self.hass)

        devices: dict[str, str] = {}
        for info in service_infos:
            service_uuids = [uuid.lower() for uuid in info.service_uuids or []]
            name = info.name or info.address

            if (
                TARGET_SERVICE_UUID.lower() in service_uuids
                or name.lower().startswith("precision")
            ):
                display_name = f"{name} ({info.address})"
                devices[info.address] = display_name

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=devices.get(address, f"Precision Plex {address}"),
                data={CONF_ADDRESS: address},
            )

        if not devices:
            devices[DEFAULT_TARGET_ADDRESS] = f"Precision Plex {DEFAULT_TARGET_ADDRESS}"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ADDRESS,
                        default=next(iter(devices)),
                    ): vol.In(devices),
                }
            ),
            errors=errors,
        )
