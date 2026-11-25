"""Auto-discovery and state access for Precision Plex LIN telemetry."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import slugify
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

LIN_SNAPSHOT_EVENT = "esphome.precision_plex_lin_snapshot"
SNAPSHOT_MAX_AGE_SECONDS = 4.0
OUTPUT_COMMAND_TIMEOUT_SECONDS = 7.0
LIN_CONTROL_KEYS = frozenset({"awning_light", "water_heater", "water_pump"})
SOURCE_GRACE_SECONDS = 30.0
COMMAND_INTENT_MAX_AGE_MS = 5000
_SNAPSHOT_SOURCE_KEYS = {
    "core": "telemetry_active",
    "outputs": "outputs_active",
    "power": "power_active",
    "hvac_zone_1": "hvac_zone_1_active",
    "hvac_zone_2": "hvac_zone_2_active",
}
_VOLATILE_SNAPSHOT_KEYS = {
    "uptime_ms",
    "outputs_age_ms",
    "snapshot_sequence",
    "snapshot_reason",
    "packets_per_second",
    "known_packets",
    "unknown_packets",
    "crc_errors",
    "last_pid",
}

LIN_ENTITY_NAMES = {
    "health": "LIN Telemetry Active",
    "outputs_health": "LIN Output State Active",
    "coach_voltage": "LIN House Battery Voltage",
    "fresh_water_level": "LIN Fresh Tank",
    "grey_water_level": "LIN Grey Tank",
    "black_water_level": "LIN Black Tank",
    "lp_gas_level": "LIN Propane",
    "generator_running": "LIN Generator Running",
    "generator_status": "LIN Generator State",
    "generator_runtime_hours": "LIN Generator Runtime",
    "awning_light": "LIN Awning Light Status",
    "water_heater": "LIN Water Heater Status",
    "tank_heater": "LIN Tank Heater Status",
    "water_pump": "LIN Water Pump Status",
    "ac_converter_present": "LIN AC Converter Present",
    "ignition_on": "LIN Ignition On",
    "awning_out": "LIN Patio Awning Extending",
    "awning_in": "LIN Patio Awning Retracting",
    "sofa_slide_out": "LIN Sofa Slide Extending",
    "sofa_slide_in": "LIN Sofa Slide Retracting",
    "bed_slide_out": "LIN Bedroom Slide Extending",
    "bed_slide_in": "LIN Bedroom Slide Retracting",
    "wardrobe_slide_out": "LIN Wardrobe Slide Extending",
    "wardrobe_slide_in": "LIN Wardrobe Slide Retracting",
    "hvac_zone_1_room_temp": "HVAC Zone 1 Room Temperature",
    "hvac_zone_1_setpoint": "HVAC Zone 1 Setpoint",
    "hvac_zone_1_mode": "HVAC Zone 1 Mode",
    "hvac_zone_1_request_phase": "HVAC Zone 1 Request Phase",
    "hvac_zone_1_operating_state": "HVAC Zone 1 Operating State",
    "hvac_zone_1_fan": "HVAC Zone 1 Fan",
    "hvac_zone_1_compressor_lockout": "HVAC Zone 1 Compressor Lockout",
    "hvac_zone_1_lockout_seconds": "HVAC Zone 1 PID37 Lockout Seconds",
    "hvac_zone_2_room_temp": "HVAC Zone 2 Room Temperature",
    "hvac_zone_2_setpoint": "HVAC Zone 2 Setpoint",
    "hvac_zone_2_mode": "HVAC Zone 2 Mode",
    "hvac_zone_2_request_phase": "HVAC Zone 2 Request Phase",
    "hvac_zone_2_operating_state": "HVAC Zone 2 Operating State",
    "hvac_zone_2_fan": "HVAC Zone 2 Fan",
    "hvac_zone_2_compressor_lockout": "HVAC Zone 2 Compressor Lockout",
    "hvac_zone_2_lockout_seconds": "HVAC Zone 2 PID37 Lockout Seconds",
}

LIN_COMMAND_ENTITY_NAMES = {
    "awning_light": "LIN Test PID5E Muted Awning Light Toggle",
    "water_heater": "LIN Command PID5E Water Heater Toggle",
    "water_pump": "LIN Command PID5E Water Pump Toggle",
}

_NAME_TO_KEY = {name: key for key, name in LIN_ENTITY_NAMES.items()}
_COMMAND_NAME_TO_KEY = {
    name: key for key, name in LIN_COMMAND_ENTITY_NAMES.items()
}
_BAD_STATES = {STATE_UNKNOWN, STATE_UNAVAILABLE, "", None}
_OUTPUT_KEYS = {
    "generator_running",
    "awning_light",
    "water_heater",
    "tank_heater",
    "water_pump",
    "awning_out",
    "awning_in",
    "sofa_slide_out",
    "sofa_slide_in",
    "bed_slide_out",
    "bed_slide_in",
    "wardrobe_slide_out",
    "wardrobe_slide_in",
}
_POWER_KEYS = {"ac_converter_present", "ignition_on"}
_HVAC_ZONE_1_KEYS = {key for key in LIN_ENTITY_NAMES if key.startswith("hvac_zone_1_")}
_HVAC_ZONE_2_KEYS = {key for key in LIN_ENTITY_NAMES if key.startswith("hvac_zone_2_")}


class PrecisionPlexLinTelemetry:
    """Track a co-located ESPHome LIN bridge without fixed entity IDs."""

    def __init__(self, hass: HomeAssistant, listener: Callable[[], None]) -> None:
        self.hass = hass
        self._listener = listener
        self.entity_ids: dict[str, str] = {}
        self.command_entity_ids: dict[str, str] = {}
        self.device_id: str | None = None
        self._unsub_state: Callable[[], None] | None = None
        self._unsub_snapshot: Callable[[], None] | None = None
        self._unsub_expiry: Callable[[], None] | None = None
        self._unsub_source_expiry: dict[str, Callable[[], None] | None] = {
            source: None for source in _SNAPSHOT_SOURCE_KEYS
        }
        self._snapshot: dict[str, Any] = {}
        self._snapshot_received: float | None = None
        self._source_last_active: dict[str, float | None] = {
            source: None for source in _SNAPSHOT_SOURCE_KEYS
        }
        self.bridge_id: str | None = None
        self._legacy_initial_command_identity: tuple[str, int] | None = None
        self._last_uptime_ms: int | None = None
        self._output_waiters: dict[tuple[str, str], asyncio.Future[str]] = {}

    @callback
    def start(self) -> None:
        """Discover existing bridge entities and watch for late ESPHome setup."""
        self._discover()
        self._unsub_state = self.hass.bus.async_listen(
            EVENT_STATE_CHANGED, self._handle_state_changed
        )
        self._unsub_snapshot = self.hass.bus.async_listen(
            LIN_SNAPSHOT_EVENT, self._handle_snapshot
        )

    @callback
    def stop(self) -> None:
        """Stop watching Home Assistant state changes."""
        if self._unsub_state is not None:
            self._unsub_state()
            self._unsub_state = None
        if self._unsub_snapshot is not None:
            self._unsub_snapshot()
            self._unsub_snapshot = None
        if self._unsub_expiry is not None:
            self._unsub_expiry()
            self._unsub_expiry = None
        for source in _SNAPSHOT_SOURCE_KEYS:
            if self._unsub_source_expiry[source] is not None:
                self._unsub_source_expiry[source]()
                self._unsub_source_expiry[source] = None
        for waiter in self._output_waiters.values():
            waiter.cancel()
        self._output_waiters.clear()
        self.entity_ids.clear()
        self.command_entity_ids.clear()
        self.device_id = None
        self._snapshot.clear()
        self._snapshot_received = None
        self._source_last_active = {
            source: None for source in _SNAPSHOT_SOURCE_KEYS
        }
        self.bridge_id = None
        self._legacy_initial_command_identity = None
        self._last_uptime_ms = None

    @callback
    def _handle_snapshot(self, event: Event) -> None:
        """Accept a versioned snapshot emitted by the ESPHome LIN component."""
        payload = event.data.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (TypeError, ValueError):
                _LOGGER.warning("Ignoring malformed Precision Plex LIN snapshot")
                return
        if not isinstance(payload, dict) or payload.get("schema") != 1:
            return

        # Firmware v0.6.4+ sends compact heartbeat payloads so Home Assistant
        # does not receive the complete telemetry snapshot every two seconds.
        # Merge those liveness fields into the last change snapshot while
        # retaining compatibility with older firmware's full heartbeats.
        bridge_id = str(event.data.get("bridge_id") or "unknown")
        if (
            payload.get("snapshot_reason") == "heartbeat"
            and self._snapshot
            and bridge_id == self.bridge_id
            and isinstance(payload.get("uptime_ms"), int)
            and self._last_uptime_ms is not None
            and payload["uptime_ms"] >= self._last_uptime_ms
        ):
            payload = {**self._snapshot, **payload}

        meaningful_changed = self._meaningful_snapshot(payload) != self._meaningful_snapshot(
            self._snapshot
        )
        bridge_changed = bridge_id != self.bridge_id
        uptime_ms = payload.get("uptime_ms")
        bridge_restarted = (
            isinstance(uptime_ms, int)
            and self._last_uptime_ms is not None
            and uptime_ms < self._last_uptime_ms
        )
        if bridge_changed or bridge_restarted:
            self._legacy_initial_command_identity = None
            self._source_last_active = {
                source: None for source in _SNAPSHOT_SOURCE_KEYS
            }
            for source in _SNAPSHOT_SOURCE_KEYS:
                if self._unsub_source_expiry[source] is not None:
                    self._unsub_source_expiry[source]()
                    self._unsub_source_expiry[source] = None
        if isinstance(uptime_ms, int):
            self._last_uptime_ms = uptime_ms
        sequence = payload.get("command_sequence")
        if (
            self._legacy_initial_command_identity is None
            and isinstance(sequence, int)
            and sequence > 0
            and not isinstance(payload.get("command_age_ms"), int)
        ):
            # Firmware before v0.6.5 has no command age. Its first complete
            # snapshot can contain an arbitrarily old intent retained across
            # a Home Assistant restart, so establish a baseline without
            # replaying that intent.
            self._legacy_initial_command_identity = (bridge_id, sequence)

        self._snapshot = payload
        received = time.monotonic()
        self._snapshot_received = received
        self.bridge_id = bridge_id
        for source, active_key in _SNAPSHOT_SOURCE_KEYS.items():
            if payload.get(active_key) is not True:
                continue
            self._source_last_active[source] = received
            if self._unsub_source_expiry[source] is not None:
                self._unsub_source_expiry[source]()
            self._unsub_source_expiry[source] = async_call_later(
                self.hass,
                SOURCE_GRACE_SECONDS,
                lambda _now, source=source: self._handle_source_expired(source),
            )
        if self._unsub_expiry is not None:
            self._unsub_expiry()
        self._unsub_expiry = async_call_later(
            self.hass,
            SNAPSHOT_MAX_AGE_SECONDS,
            self._handle_snapshot_expired,
        )
        request_id = payload.get("output_request_id")
        status = payload.get("output_request_status")
        if isinstance(request_id, str) and isinstance(status, str):
            waiter = self._output_waiters.get((bridge_id, request_id))
            if waiter is not None and not waiter.done():
                waiter.set_result(status)
        if meaningful_changed or bridge_changed:
            self._listener()

    def fresh_output_value(self, key: str) -> bool | None:
        """Read an output from a recent PID32 frame, excluding display grace."""
        age_ms = self._snapshot.get("outputs_age_ms")
        if isinstance(age_ms, int) and self._snapshot_received is not None:
            age_seconds = age_ms / 1000 + time.monotonic() - self._snapshot_received
            value = self._snapshot.get(key)
            if self.snapshot_fresh and self._snapshot.get("outputs_active") is True:
                if age_seconds <= 3.0 and isinstance(value, bool):
                    return value
        return None

    @property
    def output_control_capable(self) -> bool:
        """Return whether the most recent bridge advertises desired-state control."""
        return self._snapshot.get("output_control_capable") is True

    @property
    def output_control_available(self) -> bool:
        """Return whether the active bridge offers the desired-state action."""
        return self._output_action is not None

    @property
    def _output_action(self) -> str | None:
        if (
            not self.snapshot_fresh
            or not self.output_control_capable
            or self._snapshot.get("outputs_active") is not True
            or self.bridge_id in (None, "unknown")
        ):
            return None
        service = f"{slugify(self.bridge_id)}_precision_plex_set_output"
        return service if self.hass.services.has_service("esphome", service) else None

    async def async_set_output(self, key: str, desired: bool) -> bool:
        """Return false only when LIN is unavailable or the bridge sent nothing."""
        service = self._output_action
        bridge_id = self.bridge_id
        if service is None or bridge_id is None or key not in LIN_CONTROL_KEYS:
            return False

        request_id = uuid4().hex
        request = (bridge_id, request_id)
        future = asyncio.get_running_loop().create_future()
        self._output_waiters[request] = future
        async def dispatch() -> str:
            await self.hass.services.async_call(
                "esphome",
                service,
                {"output_key": key, "desired_state": desired, "request_id": request_id},
                blocking=True,
            )
            return await future

        try:
            status = await asyncio.wait_for(dispatch(), timeout=OUTPUT_COMMAND_TIMEOUT_SECONDS)
        except (asyncio.TimeoutError, HomeAssistantError) as err:
            raise HomeAssistantError(
                f"LIN command outcome for {key} is unknown. Check the reported output state."
            ) from err
        finally:
            self._output_waiters.pop(request, None)
            if not future.done():
                future.cancel()

        if status == "confirmed":
            return True
        if status == "not_sent":
            return False
        raise HomeAssistantError(
            f"LIN command for {key} reported {status}. Check the reported output state."
        )

    def motion_action(self, key: str) -> str | None:
        """Find the native leased motion action on the active bridge."""
        if (
            not self.snapshot_fresh
            or self._snapshot.get(f"{key}_motion_capable") is not True
            or self._snapshot.get("outputs_active") is not True
            or self.bridge_id in (None, "unknown")
        ):
            return None
        service = f"{slugify(self.bridge_id)}_precision_plex_{key}_motion"
        return service if self.hass.services.has_service("esphome", service) else None

    async def async_motion_hold(
        self, key: str, service: str, extend: bool, stop_event: asyncio.Event, duration: float
    ) -> bool:
        """Return False only when the bridge confirms no motion command was sent."""
        request_id = uuid4().hex
        bridge_id = self.bridge_id
        max_ms = max(1, min(90000, round(duration * 1000)))

        def status() -> str | None:
            if self.bridge_id != bridge_id or not self.snapshot_fresh:
                return None
            if self._snapshot.get(f"{key}_motion_request") != request_id:
                return None
            return self._snapshot.get(f"{key}_motion_status")

        async def send(operation: str) -> None:
            await asyncio.wait_for(
                self.hass.services.async_call(
                    "esphome",
                    service,
                    {
                        "operation": operation,
                        "extend": extend,
                        "request_id": request_id,
                        "max_ms": max_ms,
                    },
                    blocking=True,
                ),
                timeout=0.6,
            )

        if stop_event.is_set():
            return True
        loop = asyncio.get_running_loop()
        started = loop.time()
        finish_by = started + max_ms / 1000 + 1.5
        terminal = {"stopped", "duration_complete", "motion_ended", "canceled"}
        running = {None, "armed", "moving"}
        try:
            await send("start")
            while loop.time() < finish_by:
                current = status()
                if current == "not_sent":
                    return False
                if current in terminal:
                    if current == "motion_ended" and not stop_event.is_set():
                        raise HomeAssistantError(f"LIN {key} motion ended before the requested stop")
                    return True
                if current not in running:
                    raise HomeAssistantError(f"LIN {key} reported {current}")
                if stop_event.is_set():
                    break
                if loop.time() - started > 1.2 and current is None:
                    raise HomeAssistantError(f"LIN {key} did not acknowledge the motion request")
                # The bridge lease starts when it receives start. Its status
                # event can take longer to arrive, so renew the same request
                # while waiting for acknowledgement as well. The bridge only
                # renews an already active request with this ID.
                await send("renew")
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.2)
                except asyncio.TimeoutError:
                    pass
        finally:
            if status() in running:
                try:
                    await send("stop")
                except (HomeAssistantError, asyncio.TimeoutError):
                    _LOGGER.warning("LIN %s stop dispatch failed; bridge lease will expire", key)

        confirm_by = loop.time() + 1.0
        while loop.time() < confirm_by:
            current = status()
            if current == "not_sent":
                return False
            if current in terminal:
                return True
            if current not in running:
                break
            await asyncio.sleep(0.05)
        raise HomeAssistantError(f"PID32 did not confirm that LIN {key} stopped")

    @staticmethod
    def _meaningful_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
        """Remove heartbeat-only diagnostics before deciding to update entities."""
        return {
            key: value
            for key, value in payload.items()
            if key not in _VOLATILE_SNAPSHOT_KEYS
        }

    @callback
    def _handle_snapshot_expired(self, _now: Any) -> None:
        """Refresh entity availability when the snapshot heartbeat stops."""
        self._unsub_expiry = None
        self._listener()

    @callback
    def _handle_source_expired(self, source: str) -> None:
        """Refresh entities after one decoded LIN source grace period expires."""
        self._unsub_source_expiry[source] = None
        self._listener()

    def _snapshot_source_active(self, source: str) -> bool:
        """Return effective freshness for one source while snapshots are alive."""
        active_key = _SNAPSHOT_SOURCE_KEYS[source]
        if self._snapshot.get(active_key) is True:
            return True
        last_active = self._source_last_active[source]
        return (
            last_active is not None
            and time.monotonic() - last_active <= SOURCE_GRACE_SECONDS
        )

    @callback
    def _discover(self) -> None:
        registry = er.async_get(self.hass)
        candidates: dict[str, dict[str, str]] = {}
        command_candidates: dict[str, dict[str, str]] = {}
        previous_command_entities = self.command_entity_ids

        for entry in registry.entities.values():
            if entry.platform != "esphome" or entry.device_id is None:
                continue
            original_name = entry.original_name or ""
            if key := _NAME_TO_KEY.get(original_name):
                candidates.setdefault(entry.device_id, {})[key] = entry.entity_id
            if command_key := _COMMAND_NAME_TO_KEY.get(original_name):
                command_candidates.setdefault(entry.device_id, {})[
                    command_key
                ] = entry.entity_id

        if command_candidates:
            _command_device_id, command_entities = max(
                command_candidates.items(), key=lambda item: len(item[1])
            )
            self.command_entity_ids = command_entities
        else:
            self.command_entity_ids = {}
        commands_changed = self.command_entity_ids != previous_command_entities

        valid = [
            (device_id, entities)
            for device_id, entities in candidates.items()
            if "health" in entities and len(entities) > 1
        ]
        if not valid:
            if commands_changed:
                _LOGGER.info(
                    "Precision Plex discovered %s ESPHome LIN command controls",
                    len(self.command_entity_ids),
                )
                self._listener()
            return

        device_id, entities = max(valid, key=lambda item: len(item[1]))
        if device_id == self.device_id and entities == self.entity_ids:
            if commands_changed:
                self._listener()
            return

        self.device_id = device_id
        self.entity_ids = entities
        _LOGGER.info(
            "Precision Plex discovered ESPHome LIN telemetry bridge with %s mapped entities",
            len(entities),
        )
        self._listener()

    @callback
    def _handle_state_changed(self, event: Event) -> None:
        entity_id = event.data.get("entity_id")
        if (
            entity_id in self.entity_ids.values()
            or entity_id in self.command_entity_ids.values()
        ):
            self._listener()
            return

        # ESPHome may finish setting up after this integration. Only rescan
        # when the changed entity is one of the bridge names we understand.
        new_state = event.data.get("new_state")
        if not isinstance(new_state, State):
            return
        registry_entry = er.async_get(self.hass).async_get(entity_id)
        if (
            registry_entry is not None
            and registry_entry.platform == "esphome"
            and (
                (registry_entry.original_name or "") in _NAME_TO_KEY
                or (registry_entry.original_name or "") in _COMMAND_NAME_TO_KEY
            )
        ):
            self._discover()

    def command_available(self, key: str) -> bool:
        """Return whether a preferred PID5E command can be queued safely."""
        if not self.snapshot_fresh or self._snapshot.get("bus_active") is not True:
            return False
        if not self.command_intent_capable:
            return False
        entity_id = self.command_entity_ids.get(key)
        if entity_id is None:
            return False
        state = self.hass.states.get(entity_id)
        return state is not None and state.state != STATE_UNAVAILABLE

    async def async_send_toggle(self, key: str) -> None:
        """Queue one named PID5E toggle through its ESPHome bridge button."""
        entity_id = self.command_entity_ids.get(key)
        if entity_id is None or not self.command_available(key):
            raise RuntimeError(f"LIN command path is unavailable for {key}")
        await self.hass.services.async_call(
            "button",
            "press",
            {"entity_id": entity_id},
            blocking=True,
        )

    def state(self, key: str) -> State | None:
        """Return a usable LIN entity state."""
        entity_id = self.entity_ids.get(key)
        if entity_id is None:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in _BAD_STATES:
            return None
        return state

    @property
    def active(self) -> bool:
        """Return whether the bridge reports any fresh preferred telemetry."""
        return (
            self.core_active
            or self.outputs_active
            or self.power_active
            or self.hvac_active(1)
            or self.hvac_active(2)
        )

    @property
    def core_active(self) -> bool:
        """Return whether battery/tank/generator telemetry is fresh."""
        if self.snapshot_fresh:
            return self._snapshot_source_active("core")
        state = self.state("health")
        return state is not None and state.state == "on"

    @property
    def outputs_active(self) -> bool:
        """Return whether the PID32 output bitmap is fresh."""
        if self.snapshot_fresh:
            return self._snapshot_source_active("outputs")
        state = self.state("outputs_health")
        return state is not None and state.state == "on"

    @property
    def power_active(self) -> bool:
        """Return whether PIDEC coach flags are fresh."""
        if self.snapshot_fresh:
            return self._snapshot_source_active("power")
        return any(self.state(key) is not None for key in _POWER_KEYS)

    def hvac_active(self, zone: int) -> bool:
        """Return whether one PID37 HVAC zone is fresh."""
        if self.snapshot_fresh:
            return self._snapshot_source_active(f"hvac_zone_{zone}")
        keys = _HVAC_ZONE_1_KEYS if zone == 1 else _HVAC_ZONE_2_KEYS
        return any(self.state(key) is not None for key in keys)

    @property
    def snapshot_fresh(self) -> bool:
        """Return whether the event heartbeat is still current."""
        return (
            self._snapshot_received is not None
            and time.monotonic() - self._snapshot_received <= SNAPSHOT_MAX_AGE_SECONDS
        )

    @property
    def snapshot(self) -> dict[str, Any]:
        """Return the current snapshot for diagnostic attributes."""
        return dict(self._snapshot) if self.snapshot_fresh else {}

    @property
    def command_intent_capable(self) -> bool:
        """Return whether the live bridge publishes normalized command intent."""
        return self.snapshot_fresh and self._snapshot.get("command_intent_capable") is True

    @property
    def command_intent(self) -> dict[str, Any] | None:
        """Return the latest normalized PID1F/PID5E command event."""
        if not self.command_intent_capable:
            return None
        sequence = self._snapshot.get("command_sequence")
        if not isinstance(sequence, int) or sequence <= 0:
            return None
        command_age_ms = self._snapshot.get("command_age_ms")
        if isinstance(command_age_ms, int):
            if command_age_ms > COMMAND_INTENT_MAX_AGE_MS:
                return None
        elif self._legacy_initial_command_identity == (self.bridge_id, sequence):
            return None
        return {
            "sequence": sequence,
            "source": self._snapshot.get("command_source"),
            "key": self._snapshot.get("command_key"),
            "action": self._snapshot.get("command_action"),
            "phase": self._snapshot.get("command_phase"),
            "opcode": self._snapshot.get("command_opcode"),
            "argument": self._snapshot.get("command_argument"),
        }

    def value(self, key: str) -> Any | None:
        """Return a typed LIN value only while coach telemetry is fresh."""
        if key in _OUTPUT_KEYS:
            source_active = self.outputs_active
        elif key in _POWER_KEYS:
            source_active = self.power_active
        elif key in _HVAC_ZONE_1_KEYS:
            source_active = self.hvac_active(1)
        elif key in _HVAC_ZONE_2_KEYS:
            source_active = self.hvac_active(2)
        else:
            source_active = self.core_active
        if not source_active:
            return None
        if self.snapshot_fresh and key in self._snapshot:
            return self._snapshot[key]
        state = self.state(key)
        if state is None:
            return None
        if state.state == "on":
            return True
        if state.state == "off":
            return False
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return state.state

    def source_for(self, key: str) -> str:
        """Return the selected source label for a telemetry field."""
        return "lin" if self.value(key) is not None else "bluetooth"
