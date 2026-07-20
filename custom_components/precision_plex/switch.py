"""Switch platform for Precision Plex."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATE_BITS, WATER_PUMP_TAP, WATER_HEATER_TAP
from .coordinator import PrecisionPlexStateCoordinator


COMMAND_CONFIRMATION_TIMEOUT_SECONDS = 10.0


SWITCHES = {
    "water_pump": {
        "name": "Water Pump",
        "state_key": "water_pump",
        "payload": WATER_PUMP_TAP,
    },
    "water_heater": {
        "name": "Water Heater",
        "state_key": "water_heater",
        "payload": WATER_HEATER_TAP,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex switch entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PrecisionPlexToggleSwitch(coordinator, entry, key, cfg)
        for key, cfg in SWITCHES.items()
    )


class PrecisionPlexToggleSwitch(SwitchEntity):
    """State-aware toggle switch using Precision app tap packets."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        key: str,
        cfg: dict[str, Any],
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self.key = key
        self.cfg = cfg
        self._attr_name = cfg["name"]
        self._attr_unique_id = f"{coordinator.address}_{key}_control"
        self._remove_listener = None
        self._command_lock = asyncio.Lock()
        self._pending_state: bool | None = None
        self._pending_until: float = 0.0

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        confirmed = self._confirmed_is_on
        if self._pending_state is not None:
            if confirmed is self._pending_state:
                self._clear_pending_state()
            elif time.monotonic() < self._pending_until:
                return self._pending_state
            else:
                self._clear_pending_state()
        return confirmed

    @property
    def _confirmed_is_on(self) -> bool | None:
        bit = STATE_BITS[self.cfg["state_key"]]["bit"]
        return self.coordinator.is_bit_on(bit)

    def _clear_pending_state(self) -> None:
        self._pending_state = None
        self._pending_until = 0.0

    @property
    def available(self) -> bool:
        return self.coordinator.available and self.is_on is not None

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
            "name": "Precision Plex",
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "telemetry_source": self.coordinator.telemetry_source_for(self.cfg["state_key"]),
            "state_word": (
                f"0x{self.coordinator.state_word:04X}"
                if self.coordinator.state_word is not None
                else None
            ),
            "raw_02bb": (
                self.coordinator.raw_state.hex(" ")
                if self.coordinator.raw_state is not None
                else None
            ),
            "rejected_02bb_count": self.coordinator.rejected_02bb_count,
            "suppressed_02bb_glitch_count": self.coordinator.suppressed_02bb_glitch_count,
            "last_rejected_packet_reason": self.coordinator.last_rejected_packet_reason,
            "pending_02bb_confirmations": self.coordinator.pending_02bb_confirmations,
            "command_mode": "state_aware_toggle",
            "command_confirmation_pending": self._pending_state is not None,
            "command_requested_state": self._pending_state,
            "confirmed_state": self._confirmed_is_on,
            "command_confirmation_timeout_seconds": COMMAND_CONFIRMATION_TIMEOUT_SECONDS,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_desired_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_desired_state(False)

    async def _async_set_desired_state(self, desired_state: bool) -> None:
        async with self._command_lock:
            if self.is_on is desired_state:
                return
            self._pending_state = desired_state
            self._pending_until = (
                time.monotonic() + COMMAND_CONFIRMATION_TIMEOUT_SECONDS
            )
            self.async_write_ha_state()
            try:
                await self.coordinator.async_write_command(self.cfg["payload"])
            except Exception:
                self._clear_pending_state()
                self.async_write_ha_state()
                raise
