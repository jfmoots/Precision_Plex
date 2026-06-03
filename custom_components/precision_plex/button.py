"""Button platform for Precision Plex momentary controls."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    GENERATOR_START_SEQUENCE,
    GENERATOR_STOP_SEQUENCE,
)
from .coordinator import PrecisionPlexStateCoordinator

_LOGGER = logging.getLogger(__name__)


GENERATOR_BUTTONS = {
    "generator_start": {
        "name": "Generator Start",
        "sequence": GENERATOR_START_SEQUENCE,
        "allowed_running_state": False,
        "blocked_message": "Generator start skipped because generator is already running or state is unknown",
    },
    "generator_stop": {
        "name": "Generator Stop",
        "sequence": GENERATOR_STOP_SEQUENCE,
        "allowed_running_state": True,
        "blocked_message": "Generator stop skipped because generator is already stopped or state is unknown",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex button entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PrecisionPlexGeneratorButton(coordinator, entry, key, cfg)
        for key, cfg in GENERATOR_BUTTONS.items()
    )


class PrecisionPlexGeneratorButton(ButtonEntity):
    """Momentary generator command button with telemetry safety interlock."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        key: str,
        cfg: dict[str, Any],
    ) -> None:
        """Initialize the generator button."""
        self.coordinator = coordinator
        self.entry = entry
        self.key = key
        self.cfg = cfg
        self._attr_name = cfg["name"]
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._remove_listener = None
        self._command_lock = asyncio.Lock()

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
        """Handle updated BLE telemetry."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Only expose the button when telemetry confirms it is safe to press."""
        return (
            self.coordinator.available
            and self.coordinator.generator_running
            is self.cfg["allowed_running_state"]
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
            "name": self.entry.title,
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        return {
            "generator_running": self.coordinator.generator_running,
            "safety_interlock": "state_aware",
            "allowed_when_generator_running": self.cfg["allowed_running_state"],
            "command_mode": "momentary_press_then_release",
            "press_payload": self.cfg["sequence"][0].hex(" "),
            "release_payload": self.cfg["sequence"][1].hex(" "),
        }

    async def async_press(self) -> None:
        """Send the momentary generator command when telemetry says it is safe."""
        async with self._command_lock:
            if self.coordinator.generator_running is not self.cfg["allowed_running_state"]:
                _LOGGER.warning("%s", self.cfg["blocked_message"])
                return

            await self.coordinator.async_write_command_sequence(
                self.cfg["sequence"],
                delay_seconds=0.25,
            )
