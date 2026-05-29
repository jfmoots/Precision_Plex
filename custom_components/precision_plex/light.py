"""Light platform for Precision Plex."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONTROL_CHARACTERISTIC_UUID,
    DOMAIN,
    HEX_PAYLOADS,
    PAIRING_CHARACTERISTIC_UUID,
    PAIRING_INIT_PAYLOAD,
    STATUS_READ_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 20.0
WRITE_TIMEOUT = 3.0
KEEPALIVE_SECONDS = 60.0
ON_SEQUENCE_DELAY = 0.5

BLE_EXCEPTIONS = (
    BleakError,
    asyncio.TimeoutError,
    OSError,
    EOFError,
    AssertionError,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex light entities."""
    async_add_entities([PrecisionPlexAwningLight(hass, entry)])


class PrecisionPlexAwningLight(LightEntity):
    """Precision Plex awning light."""

    _attr_has_entity_name = True
    _attr_name = "Awning Light"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the awning light."""
        self.hass = hass
        self.entry = entry
        self._address: str = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_awning_light"
        self._attr_is_on = False
        self._attr_available = True

        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._last_used: float = 0.0

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
        """Send OFF then ON in one bonded BLE session."""
        await self._async_write_payload_sequence(
            [
                HEX_PAYLOADS["awning_light_off"],
                HEX_PAYLOADS["awning_light_on"],
            ]
        )

        self._attr_is_on = True
        self._attr_available = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Send awning light OFF command."""
        await self._async_write_payload_sequence([HEX_PAYLOADS["awning_light_off"]])

        self._attr_is_on = False
        self._attr_available = True
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect when entity is removed."""
        await self._async_disconnect()

    def _disconnected_callback(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Handle BLE client disconnect."""
        _LOGGER.debug("Precision Plex BLE client disconnected: %s", self._address)
        self._client = None

    async def _async_get_client(self) -> BleakClientWithServiceCache:
        """Get or create a persistent BLE client."""
        if self._client is not None and self._client.is_connected:
            return self._client

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass,
            self._address,
            connectable=True,
        )

        if ble_device is None:
            raise BleakError(f"Precision Plex device {self._address} is not reachable")

        _LOGGER.debug("Connecting to Precision Plex %s", self._address)

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

    async def _async_prime_session(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Prime the bonded BLE session without notify setup."""
        init_char = client.services.get_characteristic(PAIRING_CHARACTERISTIC_UUID)

        if init_char is None:
            raise BleakError(
                f"Init characteristic {PAIRING_CHARACTERISTIC_UUID} not found"
            )

        _LOGGER.debug(
            "Writing Precision Plex init uuid=%s handle=0x%04X payload=%s",
            init_char.uuid,
            init_char.handle,
            PAIRING_INIT_PAYLOAD.hex(" "),
        )

        await asyncio.wait_for(
            client.write_gatt_char(
                init_char,
                PAIRING_INIT_PAYLOAD,
                response=False,
            ),
            timeout=WRITE_TIMEOUT,
        )

        await asyncio.sleep(0.25)

        status_char = client.services.get_characteristic(STATUS_READ_CHARACTERISTIC_UUID)

        if status_char is None:
            _LOGGER.debug(
                "Precision Plex status characteristic not found: %s",
                STATUS_READ_CHARACTERISTIC_UUID,
            )
            return

        data = await asyncio.wait_for(
            client.read_gatt_char(status_char),
            timeout=WRITE_TIMEOUT,
        )

        _LOGGER.debug(
            "Precision Plex status read uuid=%s handle=0x%04X data=%s",
            status_char.uuid,
            status_char.handle,
            bytes(data).hex(" "),
        )

    async def _async_write_payload_sequence(self, payloads: list[bytes]) -> None:
        """Write one or more Precision Plex commands in the same BLE session."""
        async with self._lock:
            try:
                client = await self._async_get_client()

                control_char = client.services.get_characteristic(
                    CONTROL_CHARACTERISTIC_UUID
                )

                if control_char is None:
                    available = [
                        f"0x{characteristic.handle:04X} "
                        f"{characteristic.uuid} "
                        f"{characteristic.properties}"
                        for service in client.services
                        for characteristic in service.characteristics
                    ]
                    raise BleakError(
                        f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} "
                        f"not found. Available characteristics: {available}"
                    )

                _LOGGER.debug(
                    "Sending Precision Plex command sequence count=%s",
                    len(payloads),
                )

                for index, payload in enumerate(payloads, start=1):
                    await asyncio.wait_for(
                        client.write_gatt_char(
                            control_char,
                            payload,
                            response=True,
                        ),
                        timeout=WRITE_TIMEOUT,
                    )

                    _LOGGER.debug(
                        "Precision Plex command write completed %s/%s uuid=%s handle=0x%04X",
                        index,
                        len(payloads),
                        control_char.uuid,
                        control_char.handle,
                    )

                    if index < len(payloads):
                        await asyncio.sleep(ON_SEQUENCE_DELAY)

                self._last_used = asyncio.get_running_loop().time()
                self.hass.async_create_task(self._async_disconnect_later())

            except BLE_EXCEPTIONS as err:
                self._attr_available = False
                self.async_write_ha_state()
                _LOGGER.warning("Precision Plex BLE command failed: %r", err)

                await self._async_disconnect()

                raise HomeAssistantError(
                    f"Failed to write Precision Plex BLE command: {err!r}"
                ) from err

    async def _async_disconnect_later(self) -> None:
        """Disconnect after the keepalive window if unused."""
        await asyncio.sleep(KEEPALIVE_SECONDS)

        if (
            self._client is not None
            and self._client.is_connected
            and asyncio.get_running_loop().time() - self._last_used >= KEEPALIVE_SECONDS
        ):
            await self._async_disconnect()

    async def _async_disconnect(self) -> None:
        """Disconnect the persistent BLE client."""
        client = self._client
        self._client = None

        if client is not None and client.is_connected:
            try:
                _LOGGER.debug("Disconnecting Precision Plex BLE client")
                await client.disconnect()
            except BLE_EXCEPTIONS as err:
                _LOGGER.debug(
                    "Error disconnecting from Precision Plex %s: %s",
                    self._address,
                    err,
                )
