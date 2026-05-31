"""Number platform for Precision Plex configurable travel times."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import PrecisionPlexStateCoordinator


DEFAULT_TRAVEL_TIMES: dict[str, float] = {
    "awning_open_seconds": 18.0,
    "awning_close_seconds": 25.0,
    "bed_slide_open_seconds": 28.0,
    "bed_slide_close_seconds": 23.0,
}


@dataclass(frozen=True)
class PrecisionPlexNumberDescription:
    """Description for a Precision Plex number entity."""

    key: str
    name: str
    default: float
    minimum: float = 1.0
    maximum: float = 90.0
    step: float = 0.5


NUMBERS: tuple[PrecisionPlexNumberDescription, ...] = (
    PrecisionPlexNumberDescription(
        key="awning_open_seconds",
        name="Awning Open Seconds",
        default=DEFAULT_TRAVEL_TIMES["awning_open_seconds"],
    ),
    PrecisionPlexNumberDescription(
        key="awning_close_seconds",
        name="Awning Close Seconds",
        default=DEFAULT_TRAVEL_TIMES["awning_close_seconds"],
    ),
    PrecisionPlexNumberDescription(
        key="bed_slide_open_seconds",
        name="Bed Slide Open Seconds",
        default=DEFAULT_TRAVEL_TIMES["bed_slide_open_seconds"],
    ),
    PrecisionPlexNumberDescription(
        key="bed_slide_close_seconds",
        name="Bed Slide Close Seconds",
        default=DEFAULT_TRAVEL_TIMES["bed_slide_close_seconds"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex number entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Shared runtime settings read by cover.py. Number entities restore persisted
    # HA state into this dict on startup, then update it live on value changes.
    if not hasattr(coordinator, "runtime_settings"):
        coordinator.runtime_settings = DEFAULT_TRAVEL_TIMES.copy()
    else:
        for key, value in DEFAULT_TRAVEL_TIMES.items():
            coordinator.runtime_settings.setdefault(key, value)

    async_add_entities(
        PrecisionPlexTravelTimeNumber(coordinator, entry, description)
        for description in NUMBERS
    )


class PrecisionPlexTravelTimeNumber(NumberEntity, RestoreEntity):
    """Precision Plex configurable travel-time number."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        description: PrecisionPlexNumberDescription,
    ) -> None:
        """Initialize the number."""
        self.coordinator = coordinator
        self.entry = entry
        self._plex_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step
        self._value = float(description.default)

    async def async_added_to_hass(self) -> None:
        """Restore previous value."""
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                restored = float(last_state.state)
            except (TypeError, ValueError):
                restored = self._plex_description.default
            self._value = self._clamp(restored)
        else:
            self._value = float(self._plex_description.default)

        self.coordinator.runtime_settings[self._plex_description.key] = self._value

    @property
    def native_value(self) -> float:
        """Return current value."""
        return self._value

    @property
    def available(self) -> bool:
        """Return availability.

        Travel-time settings should remain editable even if BLE is temporarily down.
        """
        return True

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
            "setting_key": self._plex_description.key,
            "default_seconds": self._plex_description.default,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set travel time."""
        self._value = self._clamp(float(value))
        self.coordinator.runtime_settings[self._plex_description.key] = self._value
        self.async_write_ha_state()
        self.coordinator._notify_listeners()

    def _clamp(self, value: float) -> float:
        """Clamp value to configured range."""
        return max(
            self._plex_description.minimum,
            min(self._plex_description.maximum, value),
        )
