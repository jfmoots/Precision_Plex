"""Light platform for Precision Plex."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AWNING_LIGHT_TAP_SEQUENCE,
    DOMAIN,
    STATE_BITS,
)
from .coordinator import PrecisionPlexStateCoordinator


TAP_DELAY_SECONDS = 0.25
COMMAND_CONFIRMATION_TIMEOUT_SECONDS = 10.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex light entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PrecisionPlexAwningLight(coordinator, entry)])


class PrecisionPlexAwningLight(LightEntity):
    """Precision Plex awning light control using official app momentary packets."""

    _attr_has_entity_name = True
    _attr_name = "Awning Light"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{coordinator.address}_awning_light_control"
        self._remove_listener = None
        self._command_lock = asyncio.Lock()
        self._pending_state: bool | None = None
        self._pending_until: float = 0.0

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates."""
        self._remove_listener = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from coordinator updates."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated BLE state."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return current awning light state from 02BB."""
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
        """Return the latest confirmed transport state, bypassing optimism."""
        bit = STATE_BITS["awning_light"]["bit"]
        return self.coordinator.is_bit_on(bit)

    def _clear_pending_state(self) -> None:
        self._pending_state = None
        self._pending_until = 0.0

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.is_on is not None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
            "name": "Precision Plex",
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("awning_light"),
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
            "command_mode": "momentary_release_then_press",
            "command_confirmation_pending": self._pending_state is not None,
            "command_requested_state": self._pending_state,
            "confirmed_state": self._confirmed_is_on,
            "command_confirmation_timeout_seconds": COMMAND_CONFIRMATION_TIMEOUT_SECONDS,
            "command_channel": "03726f62-6f74-7061-6a61-6d61732e6361",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the awning light if it is currently off."""
        await self._async_set_desired_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the awning light if it is currently on."""
        await self._async_set_desired_state(False)

    async def _async_set_desired_state(self, desired_state: bool) -> None:
        """Toggle the momentary button only when the current state differs."""
        async with self._command_lock:
            current_state = self.is_on

            if current_state is desired_state:
                return

            self._pending_state = desired_state
            self._pending_until = (
                time.monotonic() + COMMAND_CONFIRMATION_TIMEOUT_SECONDS
            )
            self.async_write_ha_state()
            try:
                await self.coordinator.async_write_command_sequence(
                    AWNING_LIGHT_TAP_SEQUENCE,
                    delay_seconds=TAP_DELAY_SECONDS,
                )
            except Exception:
                self._clear_pending_state()
                self.async_write_ha_state()
                raise
