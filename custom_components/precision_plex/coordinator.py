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
    DEFAULT_PROFILE_ID,
    get_profile,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 12.0
GATT_TIMEOUT = 8.0
RECONNECT_DELAY_SECONDS = 4.0
GENERATOR_RUNTIME_MAX_PLAUSIBLE_TENTHS = 10000  # 1000.0 hours; protects against misdecoded 02AA frames
GENERATOR_RUNTIME_MAX_JUMP_TENTHS = 50  # 5.0 hours between accepted samples is implausible for live telemetry

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
        self.profile_id: str = entry.options.get("coach_profile", DEFAULT_PROFILE_ID)
        self.profile = get_profile(self.profile_id)

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
        self.raw_lp_byte: int | None = None
        self.last_rejected_lp_byte: int | None = None
        self.last_rejected_lp_reason: str | None = None
        self.pending_lp_gas_level: int | None = None
        self.pending_lp_confirmations: int = 0
        self.generator_running: bool | None = None
        self.generator_status: str | None = None
        self.generator_status_key: str | None = None
        self.generator_runtime_hours: float | None = None
        self.raw_generator_status: int | None = None
        self.raw_generator_status_word: int | None = None
        self.raw_generator_runtime_tenths: int | None = None
        self.ignored_generator_runtime_tenths: int | None = None
        self.ignored_generator_runtime_reason: str | None = None
        self.available = False

        self._client: BleakClientWithServiceCache | None = None
        self._task: asyncio.Task | None = None
        self._listeners: list[Callable[[], None]] = []
        self._stopped = False
        self._write_lock = asyncio.Lock()
        self._start_unsub: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Start the BLE connection task.

        During normal Home Assistant startup we defer until HA reaches the
        started/running state. When a config entry is added from the UI after
        HA is already running, async_at_started will not give us another
        startup event, so start the coordinator immediately.
        """
        self._stopped = False

        hass_state = getattr(self.hass, "state", None)
        hass_is_running = bool(getattr(self.hass, "is_running", False))
        if hass_is_running or str(hass_state).lower().endswith("running"):
            _LOGGER.debug(
                "Precision Plex config entry added while Home Assistant is already running; starting BLE monitor immediately"
            )
            self._handle_homeassistant_started(self.hass)
            return

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
            # This BLE monitor is a long-running task for the lifetime of the
            # config entry.  It must be created as a background task; using
            # hass.async_create_task during bootstrap causes Home Assistant to
            # wait for the task to finish, which can leave startup stuck on
            # "Wrapping up startup" until bootstrap times out.
            task_name = f"precision_plex_connection_loop_{self.entry.entry_id}"
            if hasattr(self.hass, "async_create_background_task"):
                self._task = self.hass.async_create_background_task(
                    self._connection_loop(),
                    task_name,
                )
            else:
                self._task = asyncio.create_task(
                    self._connection_loop(),
                    name=task_name,
                )

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
        self.raw_lp_byte = None
        self.last_rejected_lp_byte = None
        self.last_rejected_lp_reason = None
        self.generator_running = None
        self.generator_status = None
        self.generator_status_key = None
        self.generator_runtime_hours = None
        self.raw_generator_status = None
        self.raw_generator_status_word = None
        self.raw_generator_runtime_tenths = None
        self.ignored_generator_runtime_tenths = None
        self.ignored_generator_runtime_reason = None
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

        # Use one Bleak/BlueZ attempt per coordinator loop iteration.
        # The controller can disconnect during service discovery; allowing
        # bleak-retry-connector to perform multiple long attempts in one call
        # delays entity availability after startup. The outer loop retries
        # quickly instead.
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self.address,
            self._disconnected_callback,
            max_attempts=1,
            timeout=CONNECT_TIMEOUT,
        )

        if self._stopped:
            await self._async_disconnect()
            raise BleakError("Precision Plex coordinator stopped during connect")

        await asyncio.sleep(0.25)

        # Precision Plex continuously publishes state through 02BB and 02AA notifications.
        # On fresh HAOS/BlueZ installs, the old startup prime/read sequence could trigger
        # GATT "Unlikely Error" or timeout failures before notifications were subscribed.
        # Subscribe first and let the live notification stream populate coordinator state.
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

    def _is_likely_shifted_02aa_frame(self, raw: bytes) -> bool:
        """Return True when a 02AA telemetry frame appears unsafe to decode.

        The confirmed 02AA telemetry layout for this coach is a 20-byte,
        fixed-position battery/tank/LP/generator frame. Long-duration logging
        showed that the Wireless TP stream can occasionally emit malformed
        samples. Some malformed frames still contain plausible-looking values at
        individual offsets, so reject the entire frame when the surrounding
        frame shape does not match the known telemetry layout.

        Known-good frames for this coach preserve:
          - byte 2 high nibble as 0x0 while fresh uses the low nibble
          - byte 3 low nibble as 0xF while grey uses the high nibble
          - byte 4 low nibble as 0xF while black uses the high nibble

        These checks intentionally validate the frame shape, not the individual
        telemetry values. Field-level validation still happens below.
        """
        if len(raw) != 20:
            return True

        raw_voltage = int.from_bytes(raw[0:2], "big")
        if not 80 <= raw_voltage <= 180:
            return True

        # Observed one-byte-shifted frames can end with 0x55 and otherwise look
        # partially valid. Do not decode them as user-facing telemetry.
        if raw[-1] == 0x55:
            return True

        # Fresh occupies byte 2 low nibble. The high nibble has been 0x0 in all
        # confirmed tank/LP frames for the tested coach. A non-zero high nibble
        # is a strong sign that the frame is shifted or contaminated.
        if (raw[2] & 0xF0) != 0x00:
            return True

        if (raw[3] & 0x0F) != 0x0F:
            return True

        if (raw[4] & 0x0F) != 0x0F:
            return True

        return False

    def _apply_battery_state(self, raw: bytes, source: str, sender: int | None = None) -> None:
        """Decode and store coach battery voltage and tank levels from 02AA telemetry."""
        if self._stopped or len(raw) < 2:
            return

        if self._is_likely_shifted_02aa_frame(raw):
            _LOGGER.debug(
                "Precision Plex rejected misaligned 02AA frame before decode from %s sender=%s raw_len=%s raw=%s",
                source,
                f"0x{sender:04X}" if isinstance(sender, int) else None,
                len(raw),
                raw.hex(" "),
            )
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
            # LP is the high nibble of byte index 5, but the known-good LP
            # captures always carry a clean zero low nibble. Live captures have
            # shown transient byte-5 values such as 0x28, 0x0A, and 0x05 while
            # the coach is otherwise steady. Treat those as invalid LP field
            # encodings and retain the last known good LP percentage instead of
            # publishing suspicious 25%/0% blips.
            lp_map = {0x00: 0, 0x02: 25, 0x05: 50, 0x07: 75, 0x0A: 100}
            valid_lp_bytes = {0x00, 0x20, 0x50, 0x70, 0xA0}
            raw_lp_byte = raw[5]
            raw_lp = (raw_lp_byte & 0xF0) >> 4
            raw_lp_low = raw_lp_byte & 0x0F

            if raw_lp_low != 0:
                self.last_rejected_lp_byte = raw_lp_byte
                self.last_rejected_lp_reason = "nonzero_low_nibble"
                self.pending_lp_gas_level = None
                self.pending_lp_confirmations = 0
                _LOGGER.debug(
                    "Precision Plex 02AA LP byte rejected from %s sender=%s raw=%s raw_lp_byte=0x%02X raw_lp_hi=0x%X raw_lp_low=0x%X previous_lp=%s",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_lp_byte,
                    raw_lp,
                    raw_lp_low,
                    self.lp_gas_level,
                )
            elif raw_lp_byte in valid_lp_bytes and raw_lp in lp_map:
                decoded_lp_level = lp_map[raw_lp]

                # The LP sender is an analog/mechanical pickup, and both our
                # diagnostics and the official app behavior suggest the Wireless
                # TP stream can briefly emit clean-looking but incorrect LP
                # samples. Once a stable LP value is known, require a changed
                # clean LP value to appear in two consecutive accepted 02AA
                # frames before publishing it. This preserves immediate startup
                # population while preventing one-sample 0%/25% blips.
                lp_change_confirmed = (
                    self.lp_gas_level is None
                    or decoded_lp_level == self.lp_gas_level
                    or (
                        self.pending_lp_gas_level == decoded_lp_level
                        and self.pending_lp_confirmations >= 1
                    )
                )

                if lp_change_confirmed:
                    self.raw_lp_byte = raw_lp_byte
                    self.raw_lp_level = raw_lp
                    self.lp_gas_level = decoded_lp_level
                    self.pending_lp_gas_level = None
                    self.pending_lp_confirmations = 0
                    self.last_rejected_lp_reason = None
                    self.raw_battery_state = raw
                    self.available = True
                else:
                    self.pending_lp_gas_level = decoded_lp_level
                    self.pending_lp_confirmations = 1
                    self.last_rejected_lp_byte = raw_lp_byte
                    self.last_rejected_lp_reason = "pending_confirmation"
                    _LOGGER.debug(
                        "Precision Plex 02AA LP clean candidate pending confirmation from %s sender=%s raw=%s raw_lp_byte=0x%02X candidate_lp=%s previous_lp=%s",
                        source,
                        f"0x{sender:04X}" if isinstance(sender, int) else None,
                        raw.hex(" "),
                        raw_lp_byte,
                        decoded_lp_level,
                        self.lp_gas_level,
                    )
            else:
                self.last_rejected_lp_byte = raw_lp_byte
                self.last_rejected_lp_reason = "unknown_high_nibble"
                self.pending_lp_gas_level = None
                self.pending_lp_confirmations = 0
                _LOGGER.debug(
                    "Precision Plex 02AA LP nibble rejected from %s sender=%s raw=%s raw_lp_byte=0x%02X raw_lp_hi=0x%X",
                    source,
                    f"0x{sender:04X}" if isinstance(sender, int) else None,
                    raw.hex(" "),
                    raw_lp_byte,
                    raw_lp,
                )

        if len(raw) >= 9:
            # Controlled Generator app captures from 2026-06-03:
            #   ... 00 04 B5 ... -> Stopped, 120.5 hours
            #   ... 10 04 B5 ... -> Running, 120.5 hours
            #   ... 00 A0 B5 ... -> AutoStart command accepted / transition begins
            #   ... 60 04 B5 ... -> Performing Generator AutoStart
            #   ... 70 04 B5 ... -> Performing Generator AutoStop
            #   ... 20 04 B6 ... -> Will Not Start after failed AutoStart attempts
            # Generator status lives primarily in byte index 6. During one
            # AutoStart transition, the 16-bit word at bytes 6-7 becomes 0x00A0.
            # Generator run time is normally bytes 7-8, big-endian tenths of hours.
            raw_generator_status = raw[6]
            raw_generator_status_word = int.from_bytes(raw[6:8], "big")
            raw_generator_runtime_tenths = int.from_bytes(raw[7:9], "big")

            self.raw_generator_status = raw_generator_status
            self.raw_generator_status_word = raw_generator_status_word

            # Some coaches intermittently set status flag bits while the underlying
            # generator state remains stopped. Known stopped/resting values observed:
            #   0x00 = stopped / recently stopped
            #   0x40 = stopped with idle/resting flag
            #   0x80 = stopped with idle/resting flag
            #   0xC0 = stopped with both observed idle/resting flags
            # Keep raw values for diagnostics, but map these flagged idle states to
            # the same command eligibility as normal stopped.
            generator_status_code = raw_generator_status & 0x7F

            runtime_high_byte = None
            if self.raw_generator_runtime_tenths is not None:
                runtime_high_byte = (self.raw_generator_runtime_tenths >> 8) & 0xFF

            status_is_runtime_artifact = (
                runtime_high_byte is not None
                and raw_generator_status == runtime_high_byte
                and (raw_generator_status_word & 0xFF)
                == (self.raw_generator_runtime_tenths & 0xFF)
            )

            if status_is_runtime_artifact:
                _LOGGER.debug(
                    "Ignoring generator status artifact raw_status=0x%02X runtime=0x%04X raw_word=0x%04X",
                    raw_generator_status,
                    self.raw_generator_runtime_tenths,
                    raw_generator_status_word,
                )
            elif raw_generator_status_word == 0x00A0:
                self.generator_status_key = "auto_start_accepted"
                self.generator_status = "AutoStart Accepted"
            elif raw_generator_status in (0x00, 0x40, 0x80, 0xC0):
                self.generator_status_key = "stopped"
                self.generator_status = "Stopped"
            elif raw_generator_status in (0x10, 0x90):
                self.generator_status_key = "running"
                self.generator_status = "Running"
            elif generator_status_code == 0x50:
                self.generator_status_key = "stop_accepted"
                self.generator_status = "Stop Accepted"
            elif generator_status_code == 0x60:
                self.generator_status_key = "auto_starting"
                self.generator_status = "Performing Generator AutoStart"
            elif generator_status_code == 0x70:
                self.generator_status_key = "auto_stopping"
                self.generator_status = "Performing Generator AutoStop"
            elif generator_status_code == 0x20:
                self.generator_status_key = "will_not_start"
                self.generator_status = "Will Not Start"
            else:
                _LOGGER.warning(
                    "Precision Plex unknown generator status raw_status=0x%02X decoded_status=0x%02X raw_word=0x%04X raw=%s",
                    raw_generator_status,
                    generator_status_code,
                    raw_generator_status_word,
                    raw.hex(" "),
                )

            # Preserve the already-confirmed binary running behavior while the new
            # status sensor exposes managed transitions separately.
            self.generator_running = raw_generator_status in (0x10, 0x90)

            # Avoid overwriting the runtime with transitional command/status words
            # like 0x00A0, which are not actual hour-counter values. v4.3.9 keeps
            # the masked/runtime-stabilized decoder. Field diagnostics showed
            # frames such as 0x04B6 and 0x60B6 where the low byte remained the real
            # runtime low byte while status/flag bits contaminated the high byte.
            if raw_generator_status_word != 0x00A0:
                previous_runtime_tenths = self.raw_generator_runtime_tenths

                b6 = raw[6] if len(raw) > 6 else None
                b7 = raw[7] if len(raw) > 7 else None
                b8 = raw[8] if len(raw) > 8 else None
                b9 = raw[9] if len(raw) > 9 else None

                candidate_6_8 = int.from_bytes(raw[6:8], "big") if len(raw) >= 8 else None
                candidate_7_9 = int.from_bytes(raw[7:9], "big") if len(raw) >= 9 else None
                candidate_8_10 = int.from_bytes(raw[8:10], "big") if len(raw) >= 10 else None
                candidate_7_9_low12 = (((b7 or 0) & 0x0F) << 8 | (b8 or 0)) if b7 is not None and b8 is not None else None
                candidate_7_9_low13 = (((b7 or 0) & 0x1F) << 8 | (b8 or 0)) if b7 is not None and b8 is not None else None
                candidate_7_9_low14 = (((b7 or 0) & 0x3F) << 8 | (b8 or 0)) if b7 is not None and b8 is not None else None

                previous_high_with_current_low = None
                if previous_runtime_tenths is not None and b8 is not None:
                    previous_high_with_current_low = ((previous_runtime_tenths >> 8) << 8) | b8

                accepted_runtime_tenths = raw_generator_runtime_tenths
                decode_mode = "raw_7_9"

                # When the raw 16-bit candidate is implausible but the low byte is
                # consistent with the previously accepted counter high byte, treat
                # byte 7 as status/flag-contaminated and preserve the previous high
                # byte. This is intentionally conservative: it only activates when
                # there is already a valid previous runtime and the reconstructed
                # value is monotonic with a plausible live delta.
                if previous_high_with_current_low is not None:
                    reconstructed_delta = previous_high_with_current_low - previous_runtime_tenths
                    raw_delta = raw_generator_runtime_tenths - previous_runtime_tenths
                    raw_implausible = (
                        raw_generator_runtime_tenths > GENERATOR_RUNTIME_MAX_PLAUSIBLE_TENTHS
                        or raw_delta > GENERATOR_RUNTIME_MAX_JUMP_TENTHS
                    )
                    reconstructed_plausible = (
                        previous_high_with_current_low >= previous_runtime_tenths
                        and reconstructed_delta <= GENERATOR_RUNTIME_MAX_JUMP_TENTHS
                    )
                    if raw_implausible and reconstructed_plausible:
                        accepted_runtime_tenths = previous_high_with_current_low
                        decode_mode = "previous_high_current_low"

                ignore_runtime_reason: str | None = None
                if accepted_runtime_tenths > GENERATOR_RUNTIME_MAX_PLAUSIBLE_TENTHS:
                    ignore_runtime_reason = "implausibly_high"
                elif previous_runtime_tenths is not None and accepted_runtime_tenths < previous_runtime_tenths:
                    ignore_runtime_reason = "decreasing"
                elif (
                    previous_runtime_tenths is not None
                    and accepted_runtime_tenths - previous_runtime_tenths
                    > GENERATOR_RUNTIME_MAX_JUMP_TENTHS
                ):
                    ignore_runtime_reason = "implausible_jump"

                decision = ignore_runtime_reason or "accepted"

                previous_low_byte = (previous_runtime_tenths & 0xFF) if previous_runtime_tenths is not None else None
                low_byte_delta = (b8 - previous_low_byte) if b8 is not None and previous_low_byte is not None else None

                # Keep runtime validation conservative. Dirty 02AA samples can
                # briefly produce decreasing or implausibly high runtime candidates.
                # Retain the last known good runtime unless the candidate is monotonic
                # and plausible.
                # Runtime recovery is normal production behavior.
                # Diagnostic logging for candidate selection was intentionally removed
                # after validation to keep normal Home Assistant logs quiet.

                if ignore_runtime_reason is None:
                    self.raw_generator_runtime_tenths = accepted_runtime_tenths
                    self.generator_runtime_hours = accepted_runtime_tenths / 10
                    self.ignored_generator_runtime_tenths = None
                    self.ignored_generator_runtime_reason = None
                else:
                    self.ignored_generator_runtime_tenths = raw_generator_runtime_tenths
                    self.ignored_generator_runtime_reason = ignore_runtime_reason

            self.raw_battery_state = raw
            self.available = True

        _LOGGER.debug(
            "Precision Plex 02AA decoded from %s sender=%s raw=%s coach_voltage=%s fresh_water_level=%s raw_fresh=%s grey_water_level=%s raw_grey=%s black_water_level=%s raw_black=%s lp_gas_level=%s raw_lp=%s generator_running=%s generator_runtime_hours=%s raw_generator_status=%s raw_generator_status_word=%s raw_generator_runtime_tenths=%s",
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
            f"0x{self.raw_generator_status_word:04X}" if isinstance(self.raw_generator_status_word, int) else None,
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
