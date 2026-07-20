"""Auto-discovery and state access for Precision Plex LIN telemetry."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

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
    "awning_light": "LIN Awning Light Status",
    "water_heater": "LIN Water Heater Status",
    "water_pump": "LIN Water Pump Status",
    "awning_out": "LIN Patio Awning Extending",
    "awning_in": "LIN Patio Awning Retracting",
    "sofa_slide_out": "LIN Sofa Slide Extending",
    "sofa_slide_in": "LIN Sofa Slide Retracting",
    "bed_slide_out": "LIN Bedroom Slide Extending",
    "bed_slide_in": "LIN Bedroom Slide Retracting",
    "wardrobe_slide_out": "LIN Wardrobe Slide Extending",
    "wardrobe_slide_in": "LIN Wardrobe Slide Retracting",
}

_NAME_TO_KEY = {name: key for key, name in LIN_ENTITY_NAMES.items()}
_BAD_STATES = {STATE_UNKNOWN, STATE_UNAVAILABLE, "", None}
_OUTPUT_KEYS = {
    "generator_running",
    "awning_light",
    "water_heater",
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


class PrecisionPlexLinTelemetry:
    """Track a co-located ESPHome LIN bridge without fixed entity IDs."""

    def __init__(self, hass: HomeAssistant, listener: Callable[[], None]) -> None:
        self.hass = hass
        self._listener = listener
        self.entity_ids: dict[str, str] = {}
        self.device_id: str | None = None
        self._unsub_state: Callable[[], None] | None = None

    @callback
    def start(self) -> None:
        """Discover existing bridge entities and watch for late ESPHome setup."""
        self._discover()
        self._unsub_state = self.hass.bus.async_listen(
            EVENT_STATE_CHANGED, self._handle_state_changed
        )

    @callback
    def stop(self) -> None:
        """Stop watching Home Assistant state changes."""
        if self._unsub_state is not None:
            self._unsub_state()
            self._unsub_state = None
        self.entity_ids.clear()
        self.device_id = None

    @callback
    def _discover(self) -> None:
        registry = er.async_get(self.hass)
        candidates: dict[str, dict[str, str]] = {}

        for entry in registry.entities.values():
            if entry.platform != "esphome" or entry.device_id is None:
                continue
            key = _NAME_TO_KEY.get(entry.original_name or "")
            if key is None:
                continue
            candidates.setdefault(entry.device_id, {})[key] = entry.entity_id

        valid = [
            (device_id, entities)
            for device_id, entities in candidates.items()
            if "health" in entities and len(entities) > 1
        ]
        if not valid:
            return

        device_id, entities = max(valid, key=lambda item: len(item[1]))
        if device_id == self.device_id and entities == self.entity_ids:
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
        if entity_id in self.entity_ids.values():
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
            and (registry_entry.original_name or "") in _NAME_TO_KEY
        ):
            self._discover()

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
        return self.core_active or self.outputs_active

    @property
    def core_active(self) -> bool:
        """Return whether battery/tank/generator telemetry is fresh."""
        state = self.state("health")
        return state is not None and state.state == "on"

    @property
    def outputs_active(self) -> bool:
        """Return whether the PID32 output bitmap is fresh."""
        state = self.state("outputs_health")
        return state is not None and state.state == "on"

    def value(self, key: str) -> Any | None:
        """Return a typed LIN value only while coach telemetry is fresh."""
        if key in _OUTPUT_KEYS:
            source_active = self.outputs_active
        else:
            source_active = self.core_active
        if not source_active:
            return None
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
