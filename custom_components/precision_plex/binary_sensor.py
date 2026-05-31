"""Binary sensors for Precision Plex read-only monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATE_BITS
from .coordinator import PrecisionPlexStateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex binary sensors."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PrecisionPlexStateBinarySensor(coordinator, entry, key, description)
            for key, description in STATE_BITS.items()
        ]
    )


class PrecisionPlexStateBinarySensor(BinarySensorEntity):
    """Read-only binary sensor decoded from 02BB state bitmap."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialize sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self.key = key
        self.bit = description["bit"]
        self.word_index = description.get("word_index", 0)
        self._attr_name = description["name"]
        self._attr_unique_id = f"{coordinator.address}_{key}_state"

        device_class = description.get("device_class")
        if device_class == "light":
            self._attr_device_class = BinarySensorDeviceClass.LIGHT
        elif device_class == "moving":
            self._attr_device_class = BinarySensorDeviceClass.MOVING
        elif device_class == "power":
            self._attr_device_class = BinarySensorDeviceClass.POWER

        self._remove_listener = None

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
        """Return decoded bit state."""
        return self.coordinator.is_bit_on(self.bit, self.word_index)

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.state_word is not None

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
            "state_word": (
                f"0x{self.coordinator.state_word:04X}"
                if self.coordinator.state_word is not None
                else None
            ),
            "word_index": self.word_index,
            "state_words": [f"0x{word:04X}" for word in self.coordinator.state_words],
            "raw_02bb": (
                self.coordinator.raw_state.hex(" ")
                if self.coordinator.raw_state is not None
                else None
            ),
        }
