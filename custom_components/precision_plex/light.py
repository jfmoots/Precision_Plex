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
from homeassistant.helpers.start import async_at_started

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
WRITE_TIMEOUT = 3.0
ON_SEQUENCE_DELAY = 0.5
NOTIFY_WINDOW_SECONDS = 5.0

POLL_START_DELAY_SECONDS = 120.0
POLL_INTERVAL_SECONDS = 300.0

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
        self._disconnect_task: asyncio.Task | None = None
        self._poll_task: asyncio.Task | None = None
        self._poll_starter_task: asyncio.Task | None = None
        self._notify_started = False

    async def async_added_to_hass(self) -> None:
        """Register polling startup after Home Assistant has fully started."""
        async_at_started(self.hass, self._handle_homeassistant_started)

    def _handle_homeassistant_started(self, hass: HomeAssistant) -> None:
        """Start periodic state polling after Home Assistant startup completes."""
        self.hass.loop.call_soon_threadsafe(self._schedule_polling_start)

    def _schedule_polling_start(self) -> None:
        """Schedule polling startup from the Home Assistant event loop."""
        if self._poll_starter_task is None or self._poll_starter_task.done():
            self._poll_starter_task = self.hass.async_create_task(
                self._async_start_polling_after_delay()
            )

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
        """Disconnect and stop polling when entity is removed."""
        for task in (
            self._poll_starter_task,
            self._poll_task,
            self._disconnect_task,
        ):
            if task is not None:
                task.cancel()

        self._poll_starter_task = None
        self._poll_task = None
        self._disconnect_task = None

        await self._async_disconnect()

    def _disconnected_callback(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Handle BLE client disconnect."""
        _LOGGER.debug("Precision Plex BLE client disconnected: %s", self._address)
        self._client = None
        self._notify_started = False

    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle Precision Plex awning light state notifications."""
        self._apply_state_packet(bytes(data), "notification")

    def _apply_state_packet(self, raw: bytes, source: str) -> None:
        """Decode and apply an awning light state packet."""
        if len(raw) < 1:
            return

        # Observed on characteristic 02bb:
        #   10 00 ... 4d = OFF
        #   11 00 ... 4c = ON
        is_on = bool(raw[0] & 0x01)

        _LOGGER.debug(
            "Precision Plex 02bb %s data=%s decoded is_on=%s",
            source,
            raw.hex(" "),
            is_on,
        )

        if is_on == self._attr_is_on:
            self._attr_available = True
            return

        self._attr_is_on = is_on
        self._attr_available = True
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    async def _async_start_polling_after_delay(self) -> None:
        """Delay polling startup after Home Assistant has fully started."""
        try:
            await asyncio.sleep(POLL_START_DELAY_SECONDS)

            if self._poll_task is None or self._poll_task.done():
                self._poll_task = self.hass.async_create_task(self._async_poll_loop())

        except asyncio.CancelledError:
            raise
        except Exception as err:
            _LOGGER.debug("Precision Plex failed to start polling: %s", err)

    async def _async_poll_loop(self) -> None:
        """Periodically read awning state without keeping BLE connected."""
        while True:
            try:
                await self._async_poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.debug("Precision Plex poll failed: %s", err)

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _async_poll_once(self) -> None:
        """Connect, read current awning state, then disconnect."""
        async with self._lock:
            created_connection = not (
                self._client is not None and self._client.is_connected
            )

            try:
                client = await self._async_get_client(start_notify=False)
                await asyncio.sleep(0.25)
                await self._async_read_awning_state(client, "poll")

            except BLE_EXCEPTIONS as err:
                _LOGGER.debug("Precision Plex poll read failed: %s", err)

            finally:
                if created_connection:
                    await self._async_disconnect()

    async def _async_get_client(
        self,
        start_notify: bool = True,
    ) -> BleakClientWithServiceCache:
        """Create a BLE client for this command or poll."""
        if self._client is not None and self._client.is_connected:
            if start_notify:
                await self._async_start_notify(self._client)
            return self._client

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass,
            self._address,
            connectable=True,
        )

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
        await self._async_read_awning_state(self._client, "connect")

        if start_notify:
            await self._async_start_notify(self._client)

        return self._client

    async def _async_prime_session(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Prime the bonded BLE session."""
        init_char = client.services.get_characteristic(PAIRING_CHARACTERISTIC_UUID)

        if init_char is None:
            raise BleakError(
                f"Init characteristic {PAIRING_CHARACTERISTIC_UUID} not found"
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

    async def _async_read_awning_state(
        self,
        client: BleakClientWithServiceCache,
        source: str,
    ) -> None:
        """Read current awning light state from 02bb."""
        state_char = client.services.get_characteristic(
            AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID
        )

        if state_char is None:
            _LOGGER.warning(
                "Precision Plex state read characteristic not found: %s",
                AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID,
            )
            return

        data = await asyncio.wait_for(
            client.read_gatt_char(state_char),
            timeout=WRITE_TIMEOUT,
        )

        self._apply_state_packet(bytes(data), source)

    async def _async_start_notify(
        self,
        client: BleakClientWithServiceCache,
    ) -> None:
        """Start awning light state notifications."""
        if self._notify_started:
            return

        notify_char = client.services.get_characteristic(
            AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID
        )

        if notify_char is None:
            _LOGGER.warning(
                "Precision Plex state notify characteristic not found: %s",
                AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID,
            )
            return

        await asyncio.wait_for(
            client.start_notify(notify_char, self._notification_handler),
            timeout=WRITE_TIMEOUT,
        )

        self._notify_started = True
        _LOGGER.debug(
            "Precision Plex state notifications started uuid=%s handle=0x%04X",
            notify_char.uuid,
            notify_char.handle,
        )

    async def _async_write_payload_sequence(self, payloads: list[bytes]) -> None:
        """Write one or more Precision Plex commands, then listen briefly."""
        async with self._lock:
            try:
                client = await self._async_get_client(start_notify=True)

                control_char = client.services.get_characteristic(
                    CONTROL_CHARACTERISTIC_UUID
                )

                if control_char is None:
                    raise BleakError(
                        f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found"
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

                    if index < len(payloads):
                        await asyncio.sleep(ON_SEQUENCE_DELAY)

                self._schedule_disconnect()

            except BLE_EXCEPTIONS as err:
                self._attr_available = False
                self.async_write_ha_state()

                _LOGGER.warning("Precision Plex BLE command failed: %r", err)

                await self._async_disconnect()

                raise HomeAssistantError(
                    f"Failed to write Precision Plex BLE command: {err!r}"
                ) from err

    def _schedule_disconnect(self) -> None:
        """Disconnect after the notification window."""
        if self._disconnect_task is not None:
            self._disconnect_task.cancel()

        self._disconnect_task = self.hass.async_create_task(
            self._async_disconnect_after_notify_window()
        )

    async def _async_disconnect_after_notify_window(self) -> None:
        """Disconnect after listening for wall-switch changes."""
        try:
            await asyncio.sleep(NOTIFY_WINDOW_SECONDS)
            await self._async_disconnect()
        except asyncio.CancelledError:
            raise

    async def _async_disconnect(self) -> None:
        """Disconnect the BLE client."""
        client = self._client
        self._client = None
        self._notify_started = False

        if client is not None and client.is_connected:
            try:
                notify_char = client.services.get_characteristic(
                    AWNING_LIGHT_STATE_NOTIFY_CHARACTERISTIC_UUID
                )

                if notify_char is not None:
                    try:
                        await client.stop_notify(notify_char)
                    except BLE_EXCEPTIONS:
                        pass

                await client.disconnect()

            except BLE_EXCEPTIONS as err:
                _LOGGER.debug(
                    "Error disconnecting from Precision Plex %s: %s",
                    self._address,
                    err,
                )
