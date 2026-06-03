"""Precision Plex read-only BLE state coordinator."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress

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
    BATTERY_CHARACTERISTIC_UUID,
    CONTROL_CHARACTERISTIC_UUID,
    COACH_BATTERY_NOTIFY_HANDLE,
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
        self.raw_battery_state: bytes | None = None
        self.coach_voltage: float | None = None
        self.fresh_water_level: int | None = None
        self.raw_fresh_level: int | None = None
        self.grey_water_level: int | None = None
        self.raw_grey_level: int | None = None
        self.black_water_level: int | None = None
        self.raw_black_level: int | None = None
        self.lp_gas_level: int | None = None
        self.raw_lp_level: int | None = None
        self.generator_running: bool | None = None
        self.generator_runtime_hours: float | None = None
        self.raw_generator_status: int | None = None
        self.raw_generator_runtime_tenths: int | None = None
        self.available = False

        self._client: BleakClientWithServiceCache | None = None
        self._task: asyncio.Task | None = None
        self._listeners: list[Callable[[], None]] = []
        self._stopped = False
        self._write_lock = asyncio.Lock()
        self._start_unsub: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Start after Home Assistant startup completes."""
        self._stopped = False

        self._start_unsub = async_at_started(
            self.hass,
            self._handle_homeassistant_started,
        )

    @callback
    def _handle_homeassistant_started(self, hass: HomeAssistant) -> None:
        """Start the BLE connection task after HA has started."""
        if self._stopped:
            return

        if self._task is None or self._task.done():
            self._task = self.hass.async_create_task(self._connection_loop())

    async def async_stop(self) -> None:
        """Stop coordinator, cancel the monitor task, and disconnect BLE cleanly."""
        self._stopped = True

        if self._start_unsub is not None:
            self._start_unsub()
            self._start_unsub = None

        task = self._task
        self._task = None

        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        await self._async_disconnect()

        self.available = False
        self.coach_voltage = None
        self.fresh_water_level = None
        self.raw_fresh_level = None
        self.grey_water_level = None
        self.raw_grey_level = None
        self.black_water_level = None
        self.raw_black_level = None
        self.lp_gas_level = None
        self.raw_lp_level = None
        self.generator_running = None
        self.generator_runtime_hours = None
        self.raw_generator_status = None
        self.raw_generator_runtime_tenths = None
        self.raw_battery_state = None
        self._notify_listeners()
        self._listeners.clear()

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
        try:
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

        finally:
            await self._async_disconnect()
            self.available = False
            self._notify_listeners()

    def _disconnected_callback(self, client: BleakClientWithServiceCache) -> None:
        """Handle BLE disconnection."""
        self.available = False

        if self._stopped or self.hass.loop.is_closed():
            return

        self.hass.loop.call_soon_threadsafe(self._notify_listeners)

    async def _connect_and_subscribe(self) -> None:
        """Connect, read current state, then subscribe to notifications."""
        if self._stopped:
            raise BleakError("Precision Plex coordinator is stopping")

        if self._client is not None and self._client.is_connected:
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

        if self._stopped:
            await self._async_disconnect()
            raise BleakError("Precision Plex coordinator stopped during connect")

        await asyncio.sleep(0.25)
        await self._async_prime_session(self._client)

        await self._async_read_state(self._client)
        await self._async_read_battery_state(self._client)

        await self._async_start_state_notify(self._client)
        await self._async_start_battery_notify(self._client)

        self.available = True
        self._notify_listeners()

    async def async_write_command(self, payload: bytes) -> None:
        """Write a known-good Precision Plex command payload."""
        if self._stopped:
            raise BleakError("Precision Plex coordinator is stopped")

        async with self._write_lock:
            client, control_char = await self._async_get_control_char()
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
        if self._stopped:
            raise BleakError("Precision Plex coordinator is stopped")

        async with self._write_lock:
            client, control_char = await self._async_get_control_char()

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
        if self._stopped:
            raise BleakError("Precision Plex coordinator is stopped")

        async with self._write_lock:
            client, control_char = await self._async_get_control_char()

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
        """Send release once, then repeat hold until stopped or max duration expires."""
        if self._stopped:
            raise BleakError("Precision Plex coordinator is stopped")

        async with self._write_lock:
            client = self._client
            control_char = None

            async def _get_control_char():
                nonlocal client, control_char

                if self._stopped:
                    raise BleakError("Precision Plex coordinator is stopped")

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
                    if not self._stopped:
                        await _write(release_payload)
                except BLE_EXCEPTIONS as err:
                    _LOGGER.warning("Precision Plex hold stream release write failed safely: %r", err)
                except Exception as err:
                    _LOGGER.warning("Precision Plex hold stream release unexpected failure: %r", err)

            try:
                await _write(release_payload)

                end_time = asyncio.get_running_loop().time() + max_duration_seconds

                while not stop_event.is_set() and asyncio.get_running_loop().time() < end_time:
                    await _write(hold_payload)

                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                    except asyncio.TimeoutError:
                        pass

            except BLE_EXCEPTIONS as err:
                _LOGGER.warning("Precision Plex hold stream stopped after BLE error: %r", err)
            except Exception as err:
                _LOGGER.warning("Precision Plex hold stream stopped after unexpected error: %r", err)
            finally:
                await _best_effort_release()

    async def _async_get_control_char(self):
        """Return connected client and control characteristic."""
        client = self._client
        if client is None or not client.is_connected:
            await self._connect_and_subscribe()
            client = self._client

        if client is None or not client.is_connected:
            raise BleakError("Precision Plex is not connected")

        control_char = client.services.get_characteristic(CONTROL_CHARACTERISTIC_UUID)
        if control_char is None:
            raise BleakError(f"Control characteristic {CONTROL_CHARACTERISTIC_UUID} not found")

        return client, control_char

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
        self._apply_state(bytes(data), "02BB read", None)

    async def _async_read_battery_state(self, client: BleakClientWithServiceCache) -> None:
        """Read initial coach battery telemetry from 02AA."""
        battery_char = client.services.get_characteristic(BATTERY_CHARACTERISTIC_UUID)
        if battery_char is None:
            _LOGGER.warning("Precision Plex battery characteristic not found: %s", BATTERY_CHARACTERISTIC_UUID)
            return

        try:
            data = await asyncio.wait_for(client.read_gatt_char(battery_char), timeout=GATT_TIMEOUT)
        except BLE_EXCEPTIONS as err:
            _LOGGER.warning("Precision Plex battery read failed: %r", err)
            return

        self._apply_battery_state(bytes(data), "02AA read", getattr(battery_char, "handle", None))

    async def _async_start_state_notify(self, client: BleakClientWithServiceCache) -> None:
        """Subscribe to 02BB wall-panel/control state notifications."""
        state_char = client.services.get_characteristic(STATE_CHARACTERISTIC_UUID)
        if state_char is None:
            raise BleakError(f"State characteristic {STATE_CHARACTERISTIC_UUID} not found")

        try:
            await asyncio.wait_for(
                client.start_notify(state_char, self._notification_handler),
                timeout=GATT_TIMEOUT,
            )
            _LOGGER.warning(
                "Precision Plex monitor subscribed to 02BB state notifications uuid=%s handle=0x%04X",
                state_char.uuid,
                state_char.handle,
            )
        except BleakError as err:
            if "Notify acquired" not in repr(err) and "NotPermitted" not in repr(err):
                raise
            _LOGGER.warning("Precision Plex 02BB notification already active; continuing")

    async def _async_start_battery_notify(self, client: BleakClientWithServiceCache) -> None:
        """Subscribe to 02AA coach battery telemetry notifications."""
        battery_char = client.services.get_characteristic(BATTERY_CHARACTERISTIC_UUID)
        if battery_char is None:
            _LOGGER.warning("Precision Plex battery characteristic not found: %s", BATTERY_CHARACTERISTIC_UUID)
            return

        try:
            await asyncio.wait_for(
                client.start_notify(battery_char, self._battery_notification_handler),
                timeout=GATT_TIMEOUT,
            )
            _LOGGER.warning(
                "Precision Plex monitor subscribed to 02AA battery notifications uuid=%s handle=0x%04X",
                battery_char.uuid,
                battery_char.handle,
            )
        except BleakError as err:
            if "Notify acquired" not in repr(err) and "NotPermitted" not in repr(err):
                raise
            _LOGGER.warning("Precision Plex 02AA battery notification already active; continuing")

    def _notification_handler(self, sender, data: bytearray) -> None:
        """Handle Precision Plex notifications.

        Bleak may pass either an integer handle or a BleakGATTCharacteristic
        object as sender, depending on the Home Assistant/Bleak version.
        Normalize it so handle-based telemetry decoding works reliably.
        """
        if self._stopped:
            return

        sender_handle = sender if isinstance(sender, int) else getattr(sender, "handle", None)
        self._apply_state(bytes(data), "02BB notify", sender_handle)

    def _battery_notification_handler(self, sender, data: bytearray) -> None:
        """Handle Precision Plex 02AA coach battery telemetry notifications."""
        if self._stopped:
            return

        sender_handle = sender if isinstance(sender, int) else getattr(sender, "handle", None)
        self._apply_battery_state(bytes(data), "02AA notify", sender_handle)

    def _apply_state(self, raw: bytes, source: str, sender: int | None = None) -> None:
        """Decode and store state from Precision Plex monitor notifications."""
        if self._stopped or len(raw) < 2:
            return

        self.raw_state = raw
        self.state_words = [
            int.from_bytes(raw[index:index + 2], "big")
            for index in range(0, len(raw) - 1, 2)
        ]
        self.state_word = self.state_words[0] if self.state_words else None
        self.available = True

        _LOGGER.debug(
            "Precision Plex 02BB %s sender=%s raw=%s state_words=%s coach_voltage=%s",
            source,
            f"0x{sender:04X}" if isinstance(sender, int) else None,
            raw.hex(" "),
            [f"0x{word:04X}" for word in self.state_words],
            self.coach_voltage,
        )

        if not self.hass.loop.is_closed():
            self.hass.loop.call_soon_threadsafe(self._notify_listeners)

    def _apply_battery_state(self, raw: bytes, source: str, sender: int | None = None) -> None:
        """Decode and store coach battery voltage and tank levels from 02AA telemetry."""
        if self._stopped or len(raw) < 2:
            return

        raw_voltage = int.from_bytes(raw[0:2], "big")

        # Confirmed captures:
        #   00 88 -> 136 -> 13.6 V
        #   00 7D -> 125 -> 12.5 V
        #   00 83 -> 131 -> 13.1 V
        if 80 <= raw_voltage <= 180:
            self.coach_voltage = raw_voltage / 10
            self.raw_battery_state = raw
            self.available = True
        else:
            _LOGGER.debug(
                "Precision Plex 02AA voltage field ignored from %s sender=%s raw=%s raw_word=0x%04X",
                source,
                f"0x{sender:04X}" if isinstance(sender, int) else None,
                raw.hex(" "),
                raw_voltage,
            )

        tank_map = {0x00: 0, 0x03: 33, 0x06: 67, 0x0A: 100}

        if len(raw) >= 3:
            # Controlled jumper/app captures from 2026-06-02:
            #   00 83 00 0F... -> Fresh Empty
            #   00 83 03 0F... -> Fresh 1/3
            #   00 83 06 0F... -> Fresh 2/3
            #   00 83 0A 0F... -> Fresh Full
            # Fresh is the low nibble of byte index 2.
            raw_fresh = raw[2] & 0x0F
            if raw_fresh in tank_map:
                self.raw_fresh_level = raw_fresh
                self.fresh_water_level = tank_map[raw_fresh]
                self.raw_battery_state = raw
                self.available = True
            else:
                _LOGGER.debug(
                    "Precision Plex 02AA fresh nibble ignored from %s sender=%s raw=%s raw_fresh=0x%X",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_fresh,
                )

        if len(raw) >= 4:
            # Controlled Grey app captures from 2026-06-02:
            #   00 83 00 0F... -> Grey Empty
            #   00 83 00 3F... -> Grey 1/3
            # Grey is the high nibble of byte index 3.
            raw_grey = (raw[3] & 0xF0) >> 4
            if raw_grey in tank_map:
                self.raw_grey_level = raw_grey
                self.grey_water_level = tank_map[raw_grey]
                self.raw_battery_state = raw
                self.available = True
            else:
                _LOGGER.debug(
                    "Precision Plex 02AA grey nibble ignored from %s sender=%s raw=%s raw_grey=0x%X",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_grey,
                )

        if len(raw) >= 5:
            # Controlled Black app captures from 2026-06-02:
            #   00 83 00 0F 0F 50... -> Black Empty
            #   00 83 00 0F 3F 50... -> Black 1/3
            # Assuming same tank nibble scale as Fresh/Grey:
            #   0x0=Empty, 0x3=1/3, 0x6=2/3, 0xA=Full
            # Black is the high nibble of byte index 4.
            raw_black = (raw[4] & 0xF0) >> 4
            if raw_black in tank_map:
                self.raw_black_level = raw_black
                self.black_water_level = tank_map[raw_black]
                self.raw_battery_state = raw
                self.available = True
            else:
                _LOGGER.debug(
                    "Precision Plex 02AA black nibble ignored from %s sender=%s raw=%s raw_black=0x%X",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_black,
                )


        if len(raw) >= 6:
            # Controlled LP app captures from 2026-06-02:
            #   00 83 06 3F 3F 00... -> LP Empty
            #   00 83 06 3F 3F 20... -> LP 1/4
            #   00 83 06 3F 3F 50... -> LP 1/2
            #   00 83 06 3F 3F 70... -> LP 3/4
            #   00 83 06 3F 3F A0... -> LP Full
            # LP is the high nibble of byte index 5.
            lp_map = {0x00: 0, 0x02: 25, 0x05: 50, 0x07: 75, 0x0A: 100}
            raw_lp = (raw[5] & 0xF0) >> 4
            if raw_lp in lp_map:
                self.raw_lp_level = raw_lp
                self.lp_gas_level = lp_map[raw_lp]
                self.raw_battery_state = raw
                self.available = True
            else:
                _LOGGER.debug(
                    "Precision Plex 02AA LP nibble ignored from %s sender=%s raw=%s raw_lp=0x%X",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_lp,
                )

        if len(raw) >= 9:
            # Controlled Generator app captures from 2026-06-03:
            #   00 83 00 0F 0F 50 00 04 B4... -> Generator stopped, 120.4 hours
            #   00 88 00 0F 0F 50 10 04 B4... -> Generator running, 120.4 hours
            # Generator running flag is bit 0x10 of byte index 6.
            # Generator run time is bytes 7-8, big-endian tenths of hours.
            raw_generator_status = raw[6]
            raw_generator_runtime_tenths = int.from_bytes(raw[7:9], "big")

            self.raw_generator_status = raw_generator_status
            self.generator_running = bool(raw_generator_status & 0x10)
            self.raw_generator_runtime_tenths = raw_generator_runtime_tenths
            self.generator_runtime_hours = raw_generator_runtime_tenths / 10
            self.raw_battery_state = raw
            self.available = True

        _LOGGER.debug(
            "Precision Plex 02AA decoded from %s sender=%s raw=%s coach_voltage=%s fresh_water_level=%s raw_fresh=%s grey_water_level=%s raw_grey=%s black_water_level=%s raw_black=%s lp_gas_level=%s raw_lp=%s generator_running=%s generator_runtime_hours=%s raw_generator_status=%s raw_generator_runtime_tenths=%s",
            source,
            f"0x{sender:04X}" if isinstance(sender, int) else None,
            raw.hex(" "),
            self.coach_voltage,
            self.fresh_water_level,
            f"0x{self.raw_fresh_level:X}" if isinstance(self.raw_fresh_level, int) else None,
            self.grey_water_level,
            f"0x{self.raw_grey_level:X}" if isinstance(self.raw_grey_level, int) else None,
            self.black_water_level,
            f"0x{self.raw_black_level:X}" if isinstance(self.raw_black_level, int) else None,
            self.lp_gas_level,
            f"0x{self.raw_lp_level:X}" if isinstance(self.raw_lp_level, int) else None,
            self.generator_running,
            self.generator_runtime_hours,
            f"0x{self.raw_generator_status:02X}" if isinstance(self.raw_generator_status, int) else None,
            self.raw_generator_runtime_tenths,
        )

        if not self.hass.loop.is_closed():
            self.hass.loop.call_soon_threadsafe(self._notify_listeners)

    async def _async_disconnect(self) -> None:
        """Disconnect the BLE client."""
        client = self._client
        self._client = None

        if client is not None and client.is_connected:
            try:
                _LOGGER.debug("Disconnecting Precision Plex BLE client")
                await client.disconnect()
            except BLE_EXCEPTIONS as err:
                _LOGGER.debug(
                    "Error disconnecting from Precision Plex %s: %r",
                    self.address,
                    err,
                )
