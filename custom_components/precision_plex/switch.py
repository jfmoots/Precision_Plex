"""Switch platform for Precision Plex water pump."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID,
    CONTROL_CHARACTERISTIC_UUID,
    DOMAIN,
    HEX_PAYLOADS,
    PAIRING_CHARACTERISTIC_UUID,
    PAIRING_INIT_PAYLOAD,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 20.0
WRITE_TIMEOUT = 8.0
POST_TOGGLE_SETTLE_SECONDS = 2.0
PRE_CONNECT_SETTLE_SECONDS = 1.0

BLE_EXCEPTIONS = (
    BleakError,
    asyncio.TimeoutError,
    OSError,
    EOFError,
    AssertionError,
)

WATER_PUMP_STATE_BIT = 0x80


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex water pump switch."""
    async_add_entities([PrecisionPlexWaterPumpSwitch(hass, entry)])


class PrecisionPlexWaterPumpSwitch(SwitchEntity):
    """Precision Plex water pump."""

    _attr_has_entity_name = True
    _attr_name = "Water Pump"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the water pump switch."""
        self.hass = hass
        self.entry = entry
        self._address: str = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_water_pump"
        self._attr_is_on = False
        self._attr_available = True

        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._address)},
            "connections": {(CONNECTION_BLUETOOTH, self._address)},
            "name": self.entry.title,
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex BLE RV Control",
        }

    @property
    def available(self) -> bool:
        """Return availability."""
        return self._attr_available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the water pump on."""
        await self._async_set_target_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the water pump off."""
        await self._async_set_target_state(False)

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect when entity is removed."""
        await self._async_disconnect()

    def _disconnected_callback(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Handle BLE client disconnect."""
        _LOGGER.debug("Precision Plex water pump BLE disconnected: %s", self._address)
        self._client = None

    async def _async_set_target_state(self, target_on: bool) -> None:
        """Toggle water pump if needed, then read state."""
        async with self._lock:
            try:
                await self._async_disconnect()
                await asyncio.sleep(PRE_CONNECT_SETTLE_SECONDS)

                client = await self._async_get_client()

                current_on = await self._async_read_state_packet(client, "before_toggle")

                if current_on is target_on:
                    self._attr_is_on = current_on
                    self._attr_available = True
                    self.async_write_ha_state()
                    await self._async_disconnect()
                    return

                control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)

                if control_char is None:
                    raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

                payload = HEX_PAYLOADS["water_pump_toggle"]

                _LOGGER.debug(
                    "Precision Plex water pump toggle payload=%s target_on=%s",
                    payload.hex(" "),
                    target_on,
                )

                await asyncio.wait_for(
                    client.write_gatt_char(control_char, payload, response=True),
                    timeout=WRITE_TIMEOUT,
                )

                await asyncio.sleep(POST_TOGGLE_SETTLE_SECONDS)

                new_on = await self._async_read_state_packet(client, "after_toggle")

                if new_on is not None:
                    self._attr_is_on = new_on
                else:
                    self._attr_is_on = target_on

                self._attr_available = True
                self.async_write_ha_state()

                await self._async_disconnect()

            except BLE_EXCEPTIONS as err:
                self._attr_available = False
                self.async_write_ha_state()

                _LOGGER.warning("Precision Plex water pump command failed: %r", err)

                await self._async_disconnect()

                raise HomeAssistantError(
                    f"Failed to write Precision Plex water pump command: {err!r}"
                ) from err

    async def _async_get_client(self) -> BleakClientWithServiceCache:
        """Create BLE client."""
        if self._client is not None and self._client.is_connected:
            return self._client

        ble_device = bluetooth.async_ble_device_from_address(self.hass, self._address, connectable=True)

        if ble_device is None:
            raise BleakError(f"Precision Plex device {self._address} is not reachable")

        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self._address,
            self._disconnected_callback,
            max_attempts=3,
            timeout=CONNECT_TIMEOUT,
        )

        await asyncio.sleep(0.25)
        await self._async_prime_session(self._client)

        return self._client

    async def _async_prime_session(self, client: BleakClientWithServiceCache) -> None:
        """Prime bonded BLE session."""
        init_char = client.services.get_characteristic(PAIRING_CHARACTERISTIC_UUID)
        if init_char is None:
            raise BleakError(f"Init characteristic {PAIRING_CHARACTERISTIC_UUID} not found")

        await asyncio.wait_for(client.write_gatt_char(init_char, PAIRING_INIT_PAYLOAD, response=False),
                               timeout=WRITE_TIMEOUT)
        await asyncio.sleep(0.25)

    async def _async_read_state_packet(
        self,
        client: BleakClientWithServiceCache,
        source: str,
    ) -> bool | None:
        """Read and decode water pump state from 02bb."""
        state_char = client.services.get_characteristic(AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID)

        if state_char is None:
            _LOGGER.warning(
                "Precision Plex water pump state characteristic not found: %s",
                AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID,
            )
            return None

        data = await asyncio.wait_for(client.read_gatt_char(state_char), timeout=WRITE_TIMEOUT)
        raw = bytes(data)

        if len(raw) < 1:
            return None

        is_on = bool(raw[0] & WATER_PUMP_STATE_BIT)

        _LOGGER.debug(
            "Precision Plex water pump %s 02bb data=%s is_on=%s",
            source,
            raw.hex(" "),
            is_on,
        )

        return is_on

    async def _async_disconnect(self) -> None:
        """Disconnect BLE client."""
        client = self._client
        self._client = None

        if client is not None and client.is_connected:
            try:
                await client.disconnect()
            except BLE_EXCEPTIONS as err:
                _LOGGER.debug(
                    "Error disconnecting from Precision Plex water pump %s: %s",
                    self._address,
                    err,
                )