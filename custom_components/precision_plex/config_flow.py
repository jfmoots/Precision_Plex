"""Config flow for Precision Plex integration with pairing guidance."""

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

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Discover BLE service info
        service_infos = bluetooth.async_discovered_service_info(self.hass)

        devices: dict[str, str] = {}
        for info in service_infos:
            service_uuids = [uuid.lower() for uuid in info.service_uuids or []]
            if TARGET_SERVICE_UUID.lower() in service_uuids or (
                info.name and info.name.lower().startswith("precision")
            ):
                display_name = f"{info.name} ({info.address})" if info.name else info.address
                devices[info.address] = display_name

        # Fallback to default if nothing discovered
        if not devices:
            devices[DEFAULT_TARGET_ADDRESS] = f"Precision Plex {DEFAULT_TARGET_ADDRESS}"

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            # Check bonding status
            bonded = False
            device = bluetooth.async_ble_device_from_address(self.hass, address)
            if device:
                bonded = getattr(device.details, "bonded", False)

            if not bonded:
                # Show pairing guidance step
                return await self.async_step_pairing_guidance({CONF_ADDRESS: address})

            return self.async_create_entry(
                title=devices.get(address, f"Precision Plex {address}"),
                data={CONF_ADDRESS: address},
            )

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

    async def async_step_pairing_guidance(self, user_input=None):
        """Show instructions for pairing if not bonded."""
        if user_input is not None:
            # User confirmed pairing done
            return self.async_create_entry(
                title=f"Precision Plex {user_input[CONF_ADDRESS]}",
                data={CONF_ADDRESS: user_input[CONF_ADDRESS]},
            )

        description = (
            "The Precision Plex device is not yet paired with this Home Assistant host.\n\n"
            "1. On the Precision Plex, press 'Pair with Mobile'.\n"
            "2. On the host running Home Assistant, open a terminal.\n"
            "3. Run `bluetoothctl` and pair/trust/connect to the device.\n"
            "4. Once paired, come back and click 'I have paired it' below."
        )

        return self.async_show_form(
            step_id="pairing_guidance",
            description_placeholders={"instructions": description},
            data_schema=vol.Schema({}),
        )