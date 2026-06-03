"""Sensors for Precision Plex monitor telemetry."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PrecisionPlexStateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex sensors."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PrecisionPlexCoachBatterySensor(coordinator, entry),
            PrecisionPlexFreshWaterTankSensor(coordinator, entry),
            PrecisionPlexGreyWaterTankSensor(coordinator, entry),
            PrecisionPlexBlackWaterTankSensor(coordinator, entry),
            PrecisionPlexLPGasTankSensor(coordinator, entry),
            PrecisionPlexGeneratorRuntimeSensor(coordinator, entry),
        ]
    )


class PrecisionPlexBaseSensor(SensorEntity):
    """Base class for Precision Plex telemetry sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the base telemetry sensor."""
        self.coordinator = coordinator
        self.entry = entry
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
        """Handle updated BLE telemetry."""
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "connections": {(CONNECTION_BLUETOOTH, self.coordinator.address)},
            "name": self.entry.title,
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }


class PrecisionPlexCoachBatterySensor(PrecisionPlexBaseSensor):
    """Coach battery voltage decoded from Precision Plex monitor telemetry."""

    _attr_name = "Coach Battery"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the coach battery sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_coach_battery_voltage"

    @property
    def native_value(self) -> float | None:
        """Return coach battery voltage."""
        return self.coordinator.coach_voltage

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.coach_voltage is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        raw_word = None
        if raw is not None and len(raw) >= 2:
            raw_word = int.from_bytes(raw[0:2], "big")
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_tenths": raw_word,
            "raw_02aa": raw.hex(" ") if raw is not None else None,
        }


class PrecisionPlexFreshWaterTankSensor(PrecisionPlexBaseSensor):
    """Fresh water tank level decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Fresh Water Tank"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Fresh Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_fresh_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Fresh Water tank percentage."""
        return self.coordinator.fresh_water_level

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.fresh_water_level is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_fresh_nibble": (
                f"0x{self.coordinator.raw_fresh_level:X}"
                if isinstance(self.coordinator.raw_fresh_level, int)
                else None
            ),
            "source_field": "byte 2 low nibble",
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0x0=0%, 0x3=33%, 0x6=67%, 0xA=100%",
        }


class PrecisionPlexGreyWaterTankSensor(PrecisionPlexBaseSensor):
    """Grey water tank level decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Grey Water Tank"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Grey Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_grey_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Grey Water tank percentage."""
        return self.coordinator.grey_water_level

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.grey_water_level is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_grey_nibble": (
                f"0x{self.coordinator.raw_grey_level:X}"
                if isinstance(self.coordinator.raw_grey_level, int)
                else None
            ),
            "source_field": "byte 3 high nibble",
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0x0=0%, 0x3=33%, 0x6=67%, 0xA=100%",
        }


class PrecisionPlexBlackWaterTankSensor(PrecisionPlexBaseSensor):
    """Black water tank level decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Black Water Tank"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Black Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_black_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Black Water tank percentage."""
        return self.coordinator.black_water_level

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.black_water_level is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_black_nibble": (
                f"0x{self.coordinator.raw_black_level:X}"
                if isinstance(self.coordinator.raw_black_level, int)
                else None
            ),
            "source_field": "byte 4 high nibble",
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0x0=0%, 0x3=33%, 0x6=67%, 0xA=100%",
        }


class PrecisionPlexLPGasTankSensor(PrecisionPlexBaseSensor):
    """LP gas tank level decoded from Precision Plex 02AA telemetry."""

    _attr_name = "LP Gas Tank"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:propane-tank"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the LP Gas tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_lp_gas_tank"

    @property
    def native_value(self) -> int | None:
        """Return LP Gas tank percentage."""
        return self.coordinator.lp_gas_level

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.lp_gas_level is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_lp_nibble": (
                f"0x{self.coordinator.raw_lp_level:X}"
                if isinstance(self.coordinator.raw_lp_level, int)
                else None
            ),
            "source_field": "byte 5 high nibble",
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0x0=0%, 0x2=25%, 0x5=50%, 0x7=75%, 0xA=100%",
        }


class PrecisionPlexGeneratorRuntimeSensor(PrecisionPlexBaseSensor):
    """Generator runtime decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Generator Runtime"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:timer-outline"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the generator runtime sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_generator_runtime"

    @property
    def native_value(self) -> float | None:
        """Return generator runtime hours."""
        return self.coordinator.generator_runtime_hours

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.generator_runtime_hours is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "source_field": "bytes 7-8 big-endian tenths of hours",
            "raw_runtime_tenths": self.coordinator.raw_generator_runtime_tenths,
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0x04B4=1204 tenths=120.4 hours",
        }
