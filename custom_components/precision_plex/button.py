"""Button platform for Precision Plex momentary and cover utility controls."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    GENERATOR_AUTO_START_SEQUENCE,
    GENERATOR_AUTO_STOP_SEQUENCE,
    GENERATOR_START_SEQUENCE,
    GENERATOR_STOP_SEQUENCE,
)
from .coordinator import PrecisionPlexStateCoordinator
from .cover import COVERS, PrecisionPlexCoverDescription

_LOGGER = logging.getLogger(__name__)


GENERATOR_BUTTONS = {
    "generator_start": {
        "name": "Generator Start",
        "sequence": GENERATOR_START_SEQUENCE,
        "allowed_status_keys": {"stopped", "will_not_start"},
        "blocked_message": "Generator start skipped because generator is not stopped or state is unknown",
    },
    "generator_stop": {
        "name": "Generator Stop",
        "sequence": GENERATOR_STOP_SEQUENCE,
        "allowed_status_keys": {"running"},
        "blocked_message": "Generator stop skipped because generator is not running or state is unknown",
    },
    "generator_auto_start": {
        "name": "Generator AutoStart",
        "sequence": GENERATOR_AUTO_START_SEQUENCE,
        "allowed_status_keys": {"stopped", "will_not_start"},
        "blocked_message": "Generator AutoStart skipped because generator is not stopped or state is unknown",
    },
    "generator_auto_stop": {
        "name": "Generator AutoStop",
        "sequence": GENERATOR_AUTO_STOP_SEQUENCE,
        "allowed_status_keys": {"stopped", "running", "auto_start_accepted", "auto_starting"},
        "blocked_message": "Generator AutoStop skipped because generator is not running or state is unknown",
    },
}


@dataclass(frozen=True)
class PrecisionPlexCoverButtonDescription:
    """Description for a Precision Plex cover utility button."""

    key: str
    name: str
    cover_key: str
    action: str


COVER_BUTTONS: tuple[PrecisionPlexCoverButtonDescription, ...] = tuple(
    button
    for cover in COVERS
    for button in (
        PrecisionPlexCoverButtonDescription(
            key=f"{cover.key}_jog_extend",
            name=f"{cover.name} Jog Extend",
            cover_key=cover.key,
            action="jog_out",
        ),
        PrecisionPlexCoverButtonDescription(
            key=f"{cover.key}_jog_retract",
            name=f"{cover.name} Jog Retract",
            cover_key=cover.key,
            action="jog_in",
        ),
        PrecisionPlexCoverButtonDescription(
            key=f"{cover.key}_reset_extended",
            name=f"{cover.name} Reset Fully Extended",
            cover_key=cover.key,
            action="reset_extended",
        ),
        PrecisionPlexCoverButtonDescription(
            key=f"{cover.key}_reset_retracted",
            name=f"{cover.name} Reset Fully Retracted",
            cover_key=cover.key,
            action="reset_retracted",
        ),
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex button entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PrecisionPlexResetBleDiagnosticsButton(coordinator, entry),
            *(PrecisionPlexGeneratorButton(coordinator, entry, key, cfg) for key, cfg in GENERATOR_BUTTONS.items()),
            *(PrecisionPlexCoverUtilityButton(coordinator, entry, description) for description in COVER_BUTTONS),
        ]
    )


class PrecisionPlexResetBleDiagnosticsButton(ButtonEntity):
    """Reset BLE diagnostic counters."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Reset BLE Diagnostics"
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the reset diagnostics button."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{coordinator.address}_reset_ble_diagnostics"

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
            "accepted_packets": self.coordinator.packets_received_count,
            "rejected_packets": self.coordinator.packets_rejected_count,
            "last_reject_reason": self.coordinator.last_rejected_packet_reason,
        }

    async def async_press(self) -> None:
        """Reset BLE diagnostic counters."""
        self.coordinator.reset_ble_diagnostics()


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
        self._command_lock = asyncio.Lock()
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates so availability refreshes after BLE connects."""
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
        """Refresh entity state when BLE availability or generator status changes."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return whether the button is currently safe to press."""
        return (
            self.coordinator.available
            and self.coordinator.generator_status_key_value in self.cfg["allowed_status_keys"]
        )

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
            "telemetry_source": self.coordinator.telemetry_source_for("generator_status"),
            "generator_running": self.coordinator.generator_running_value,
            "generator_status": self.coordinator.generator_status_value,
            "generator_status_key": self.coordinator.generator_status_key_value,
            "safety_interlock": "status_aware",
            "allowed_status_keys": sorted(self.cfg["allowed_status_keys"]),
            "command_mode": "momentary_press_then_release",
            "press_payload": self.cfg["sequence"][0].hex(" "),
            "release_payload": self.cfg["sequence"][1].hex(" "),
        }

    async def async_press(self) -> None:
        """Send the momentary generator command when telemetry says it is safe."""
        async with self._command_lock:
            if self.coordinator.generator_status_key_value not in self.cfg["allowed_status_keys"]:
                _LOGGER.warning("%s", self.cfg["blocked_message"])
                return

            await self.coordinator.async_write_command_sequence(
                self.cfg["sequence"],
                delay_seconds=0.25,
            )


class PrecisionPlexCoverUtilityButton(ButtonEntity):
    """Jog or reset a Precision Plex cover while preserving estimated position logic."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        description: PrecisionPlexCoverButtonDescription,
    ) -> None:
        """Initialize the cover utility button."""
        self.coordinator = coordinator
        self.entry = entry
        self._plex_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._command_lock = asyncio.Lock()
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates so jog availability refreshes after BLE connects."""
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
        """Refresh entity state when BLE availability or cover registration changes."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return availability."""
        if self._plex_description.action.startswith("reset_"):
            return True
        return self.coordinator.available and self._cover is not None

    @property
    def _cover(self):
        """Return the live cover entity registered by cover.py, if available."""
        return getattr(self.coordinator, "cover_entities", {}).get(
            self._plex_description.cover_key
        )

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
        cover = self._cover
        return {
            "cover_key": self._plex_description.cover_key,
            "action": self._plex_description.action,
            "command_mode": "cover_engine_jog_or_position_reset",
            "cover_registered": cover is not None,
            "jog_seconds": getattr(cover, "_jog_seconds", lambda: None)(),
        }

    async def async_press(self) -> None:
        """Perform the requested cover utility action."""
        async with self._command_lock:
            cover = self._cover
            if cover is None:
                _LOGGER.warning(
                    "Precision Plex cover button %s could not find registered cover %s",
                    self._plex_description.key,
                    self._plex_description.cover_key,
                )
                return

            action = self._plex_description.action
            if action == "jog_out":
                await cover.async_jog("out")
            elif action == "jog_in":
                await cover.async_jog("in")
            elif action == "reset_extended":
                await cover.async_reset_estimated_position(100.0)
            elif action == "reset_retracted":
                await cover.async_reset_estimated_position(0.0)
            else:
                raise ValueError(f"Unsupported Precision Plex cover button action: {action}")
