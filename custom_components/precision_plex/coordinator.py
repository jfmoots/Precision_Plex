"""Precision Plex read-only BLE state coordinator."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from bleak import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.start import async_at_started

from .const import (
    PAIRING_CHARACTERISTIC_UUID,
    PAIRING_INIT_PAYLOAD,
    STATE_CHARACTERISTIC_UUID,
    CONTROL_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 20.0
GATT_TIMEOUT = 8.0
RECONNECT_DELAY_SECONDS = 15.0

BLE_EXCEPTIONS = (
    BleakError,
    asyncio.TimeoutError,
    OSError,
    EOFError,
    AssertionError,
)


class PrecisionPlexStateCoordinator:
    """Maintain a read-only BLE subscription to Precision Plex state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.address: str = entry.data[CONF_ADDRESS]

        self.state_word: int | None = None
        self.state_words: list[int] = []
        self.raw_state: bytes | None = None
        self.available = False

        self._client: BleakClientWithServiceCache | None = None
        self._task: asyncio.Task | None = None
        self._listeners: list[Callable[[], None]] = []
        self._stopped = False
        self._write_lock = asyncio.Lock()

    async def async_start(self) -> None:
        """Start after Home Assistant startup completes."""
        async_at_started(self.hass, self._handle_homeassistant_started)

    @callback
    def _handle_homeassistant_started(self, hass: HomeAssistant) -> None:
        """Start the BLE connection task after HA has started."""
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_task(self._connection_loop())

    async def async_stop(self) -> None:
        """Stop coordinator and disconnect."""
        self._stopped = True
        if self._task is not None:
            self._task.cancel()
            self._task = None
        await self._async_disconnect()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Add a listener that fires when state changes."""
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    @callback
    def _notify_listeners(self) -> None:
        """Notify subscribed HA entities."""
        for listener in list(self._listeners):
            listener()

    def is_bit_on(self, bit: int, word_index: int = 0) -> bool | None:
        """Return True/False for a decoded 16-bit state bit."""
        if not self.state_words or word_index >= len(self.state_words):
            return None
        return bool(self.state_words[word_index] & bit)

    async def _connection_loop(self) -> None:
        """Keep a read-only BLE subscription active."""
        while not self._stopped:
            try:
                await self._connect_and_subscribe()
                while (
                    not self._stopped
                    and self._client is not None
                    and self._client.is_connected
                ):
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                raise
            except BLE_EXCEPTIONS as err:
                self.available = False
                _LOGGER.debug("Precision Plex monitor BLE error: %r", err)
                self._notify_listeners()
            except Exception as err:
                self.available = False
                _LOGGER.warning("Precision Plex monitor unexpected error: %r", err)
                self._notify_listeners()

            await self._async_disconnect()
            if not self._stopped:
                await asyncio.sleep(RECONNECT_DELAY_SECONDS)


    def _disconnected_callback(self, client: BleakClientWithServiceCache) -> None:
        """Handle BLE disconnection."""
        self.available = False
        self.hass.loop.call_soon_threadsafe(self._notify_listeners)

    async def _connect_and_subscribe(self) -> None:
        """Connect, read current state, then subscribe to notifications."""
        if self._client is not None and self._client.is_connected:
            # Already connected/subscribed by the monitor loop. Do not call
            # start_notify again; BlueZ returns NotPermitted / Notify acquired.
            self.available = True
            self._notify_listeners()
            return

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass,
            self.address,
            connectable=True,
        )
        if ble_device is None:
            raise BleakError(f"Precision Plex device {self.address} is not reachable")

        _LOGGER.info("Precision Plex monitor connecting to %s", self.address)

        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self.address,
            self._disconnected_callback,
            max_attempts=3,
            timeout=CONNECT_TIMEOUT,
        )

        await asyncio.sleep(0.25)
        await self._async_prime_session(self._client)
        await self._async_read_state(self._client)

        state_char = self._client.services.get_characteristic(STATE_CHARACTERISTIC_UUID)
        if state_char is None:
            raise BleakError(f"State characteristic {STATE_CHARACTERISTIC_UUID} not found")

        try:
            await asyncio.wait_for(
                self._client.start_notify(state_char, self._notification_handler),
                timeout=GATT_TIMEOUT,
            )
            _LOGGER.warning("Precision Plex monitor subscribed to 02BB state notifications")
        except BleakError as err:
            # If BlueZ says notifications are already acquired, that means the
            # monitor subscription is alive. Treat it as success instead of
            # tearing down the entity.
            if "Notify acquired" not in repr(err) and "NotPermitted" not in repr(err):
                raise
            _LOGGER.warning("Precision Plex monitor notification already active; continuing")

        self.available = True
        self._notify_listeners()

    async def async_write_command(self, payload: bytes) -> None:
        """Write a known-good Precision Plex command payload."""
        client = self._client
        if client is None or not client.is_connected:
            await self._connect_and_subscribe()
            client = self._client

        if client is None or not client.is_connected:
            raise BleakError("Precision Plex is not connected")

        control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)
        if control_char is None:
            raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

        await asyncio.wait_for(
            client.write_gatt_char(control_char, payload, response=True),
            timeout=GATT_TIMEOUT,
        )


    async def async_write_command_sequence(
        self,
        payloads: list[bytes],
        delay_seconds: float = 0.25,
    ) -> None:
        """Write a sequence of known-good Precision Plex command payloads."""
        client = self._client
        if client is None or not client.is_connected:
            await self._connect_and_subscribe()
            client = self._client

        if client is None or not client.is_connected:
            raise BleakError("Precision Plex is not connected")

        control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)
        if control_char is None:
            raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

        for index, payload in enumerate(payloads):
            await asyncio.wait_for(
                client.write_gatt_char(control_char, payload, response=True),
                timeout=GATT_TIMEOUT,
            )
            if index < len(payloads) - 1:
                await asyncio.sleep(delay_seconds)


    async def async_repeat_command_for_duration(
        self,
        hold_payload: bytes,
        release_payload: bytes,
        duration_seconds: float = 1.0,
        interval_seconds: float = 0.30,
    ) -> None:
        """Repeat a hold payload for a short duration, then send release."""
        client = self._client
        if client is None or not client.is_connected:
            await self._connect_and_subscribe()
            client = self._client

        if client is None or not client.is_connected:
            raise BleakError("Precision Plex is not connected")

        control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)
        if control_char is None:
            raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

        end_time = asyncio.get_running_loop().time() + duration_seconds
        try:
            while asyncio.get_running_loop().time() < end_time:
                await asyncio.wait_for(
                    client.write_gatt_char(control_char, hold_payload, response=True),
                    timeout=GATT_TIMEOUT,
                )
                await asyncio.sleep(interval_seconds)
        finally:
            await asyncio.wait_for(
                client.write_gatt_char(control_char, release_payload, response=True),
                timeout=GATT_TIMEOUT,
            )


    async def async_write_hold_stream(
        self,
        release_payload: bytes,
        hold_payload: bytes,
        stop_event: asyncio.Event,
        interval_seconds: float = 0.30,
        max_duration_seconds: float = 30.0,
    ) -> None:
        """Send release once, then repeat hold until stopped or max duration expires.

        Uses the existing monitor BLE connection whenever possible. This is important
        because the Precision wireless TP appears to allow one active connection and
        BlueZ rejects duplicate notification subscriptions with "Notify acquired".
        """
        async with self._write_lock:
            client = self._client
            control_char = None

            async def _get_control_char():
                nonlocal client, control_char

                if client is None or not client.is_connected:
                    await self._connect_and_subscribe()
                    client = self._client
                    control_char = None

                if client is None or not client.is_connected:
                    raise BleakError("Precision Plex is not connected")

                if control_char is None:
                    control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)

                if control_char is None:
                    raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

                return client, control_char

            async def _write(payload: bytes) -> None:
                active_client, active_char = await _get_control_char()
                await asyncio.wait_for(
                    active_client.write_gatt_char(active_char, payload, response=True),
                    timeout=GATT_TIMEOUT,
                )

            async def _best_effort_release() -> None:
                try:
                    await _write(release_payload)
                except BLE_EXCEPTIONS as err:
                    _LOGGER.warning("Precision Plex awning release write failed safely: %r", err)
                except Exception as err:
                    _LOGGER.warning("Precision Plex awning release unexpected failure: %r", err)

            try:
                # The official app sends the release/neutral frame before starting a hold stream.
                await _write(release_payload)

                end_time = asyncio.get_running_loop().time() + max_duration_seconds

                while not stop_event.is_set() and asyncio.get_running_loop().time() < end_time:
                    await _write(hold_payload)

                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                    except asyncio.TimeoutError:
                        pass

            except BLE_EXCEPTIONS as err:
                # Do not mark the whole device unavailable here; the notification stream
                # may still be alive. The next monitor notification will report truth.
                _LOGGER.warning("Precision Plex awning hold stream stopped after BLE error: %r", err)
            except Exception as err:
                _LOGGER.warning("Precision Plex awning hold stream stopped after unexpected error: %r", err)
            finally:
                await _best_effort_release()

    async def _async_prime_session(self, client: BleakClientWithServiceCache) -> None:
        """Prime bonded BLE session."""
        init_char = client.services.get_characteristic(PAIRING_CHARACTERISTIC_UUID)
        if init_char is None:
            _LOGGER.debug("Precision Plex monitor init characteristic not found")
            return

        await asyncio.wait_for(
            client.write_gatt_char(init_char, PAIRING_INIT_PAYLOAD, response=False),
            timeout=GATT_TIMEOUT,
        )
        await asyncio.sleep(0.25)

    async def _async_read_state(self, client: BleakClientWithServiceCache) -> None:
        """Read initial state from 02BB."""
        state_char = client.services.get_characteristic(STATE_CHARACTERISTIC_UUID)
        if state_char is None:
            raise BleakError(f"State characteristic {STATE_CHARACTERISTIC_UUID} not found")

        data = await asyncio.wait_for(client.read_gatt_char(state_char), timeout=GATT_TIMEOUT)
        self._apply_state(bytes(data), "read")

    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle 02BB notifications."""
        self._apply_state(bytes(data), "notify")

    def _apply_state(self, raw: bytes, source: str) -> None:
        """Decode and store state from 02BB.

        The 02BB payload is a sequence of 16-bit words. Early entities only used
        word 0. Bed Slide movement bits live in word 1, so keep all words.
        """
        if len(raw) < 2:
            return

        self.raw_state = raw
        self.state_words = [
            int.from_bytes(raw[index:index + 2], "big")
            for index in range(0, len(raw) - 1, 2)
        ]
        self.state_word = self.state_words[0] if self.state_words else None
        self.available = True

        _LOGGER.debug(
            "Precision Plex 02BB %s raw=%s state_words=%s",
            source,
            raw.hex(" "),
            [f"0x{word:04X}" for word in self.state_words],
        )

        self.hass.loop.call_soon_threadsafe(self._notify_listeners)

