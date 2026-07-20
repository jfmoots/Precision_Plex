"""Sensors for Precision Plex monitor telemetry."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PrecisionPlexStateCoordinator


MAX_RECORDER_DICT_ENTRIES = 20
MAX_RECORDER_LOG_ENTRIES = 5


def _compact_count_dict(values, limit: int = MAX_RECORDER_DICT_ENTRIES) -> dict:
    """Return a recorder-safe, top-N view of a counter-like dictionary."""
    if not values:
        return {}
    items = list(dict(values).items())
    try:
        items.sort(key=lambda item: item[1], reverse=True)
    except TypeError:
        pass
    return dict(items[:limit])


def _compact_rejected_packet_entry(entry: dict) -> dict:
    """Return a recorder-safe summary of a rejected packet entry."""
    if not entry:
        return {}
    return {
        "timestamp": entry.get("timestamp"),
        "packet_type": entry.get("packet_type"),
        "reason": entry.get("reason"),
        "variant": entry.get("variant"),
        "length": entry.get("length"),
        "seconds_since_last_good": entry.get("seconds_since_last_good"),
        "seconds_since_connect": entry.get("seconds_since_connect"),
        "changed_byte_indices": entry.get("changed_byte_indices"),
        "changed_byte_count": entry.get("changed_byte_count"),
    }


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
            PrecisionPlexFreshWaterHomeKitSensor(coordinator, entry),
            PrecisionPlexGreyWaterHomeKitSensor(coordinator, entry),
            PrecisionPlexBlackWaterHomeKitSensor(coordinator, entry),
            PrecisionPlexPropaneHomeKitSensor(coordinator, entry),
            PrecisionPlexGeneratorRuntimeSensor(coordinator, entry),
            PrecisionPlexGeneratorStatusSensor(coordinator, entry),
            PrecisionPlexTelemetryTransportSensor(coordinator, entry),
            PrecisionPlexAwningControlMethodSensor(coordinator, entry),
            PrecisionPlexBleLastValidPacketSensor(coordinator, entry),
            PrecisionPlexBlePacketAgeSensor(coordinator, entry),
            PrecisionPlexBleReconnectCountSensor(coordinator, entry),
            PrecisionPlexBleDisconnectCountSensor(coordinator, entry),
            PrecisionPlexBlePacketsReceivedSensor(coordinator, entry),
            PrecisionPlexBlePacketsRejectedSensor(coordinator, entry),
            PrecisionPlexBleRejected02AASensor(coordinator, entry),
            PrecisionPlexBleRejected02BBSensor(coordinator, entry),
            PrecisionPlexBleLastRejectReasonSensor(coordinator, entry),
            PrecisionPlexBleLastRejectedPacketSensor(coordinator, entry),
            PrecisionPlexBleLastRejectedPacketLengthSensor(coordinator, entry),
            PrecisionPlexBlePacketRejectionPercentSensor(coordinator, entry),
            PrecisionPlexBleRejectedPacketLogSensor(coordinator, entry),
            PrecisionPlexCommandStreamRecoveriesSensor(coordinator, entry),
            PrecisionPlexCommandStreamInterruptionsSensor(coordinator, entry),
            PrecisionPlexCommandStreamLastErrorSensor(coordinator, entry),
            *[
                PrecisionPlexLinOnlySensor(coordinator, entry, description)
                for description in LIN_ONLY_SENSOR_DESCRIPTIONS
            ],
        ]
    )


LIN_ONLY_SENSOR_DESCRIPTIONS = (
    {"key": "hvac_zone_1_room_temp", "name": "HVAC Zone 1 Room Temperature", "temperature": True},
    {"key": "hvac_zone_1_setpoint", "name": "HVAC Zone 1 Setpoint", "temperature": True},
    {"key": "hvac_zone_1_mode", "name": "HVAC Zone 1 Mode"},
    {"key": "hvac_zone_1_request_phase", "name": "HVAC Zone 1 Request Phase"},
    {"key": "hvac_zone_1_operating_state", "name": "HVAC Zone 1 Operating State"},
    {"key": "hvac_zone_1_fan", "name": "HVAC Zone 1 Fan"},
    {"key": "hvac_zone_1_lockout_seconds", "name": "HVAC Zone 1 Compressor Lockout", "seconds": True},
    {"key": "hvac_zone_2_room_temp", "name": "HVAC Zone 2 Room Temperature", "temperature": True},
    {"key": "hvac_zone_2_setpoint", "name": "HVAC Zone 2 Setpoint", "temperature": True},
    {"key": "hvac_zone_2_mode", "name": "HVAC Zone 2 Mode"},
    {"key": "hvac_zone_2_request_phase", "name": "HVAC Zone 2 Request Phase"},
    {"key": "hvac_zone_2_operating_state", "name": "HVAC Zone 2 Operating State"},
    {"key": "hvac_zone_2_fan", "name": "HVAC Zone 2 Fan"},
    {"key": "hvac_zone_2_lockout_seconds", "name": "HVAC Zone 2 Compressor Lockout", "seconds": True},
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
            "name": "Precision Plex",
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }


class PrecisionPlexLinOnlySensor(PrecisionPlexBaseSensor):
    """A sensor decoded from LIN with no BLE equivalent."""

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.key = description["key"]
        self._attr_name = description["name"]
        self._attr_unique_id = f"{coordinator.address}_lin_{self.key}"
        if description.get("temperature"):
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_suggested_display_precision = 0
        elif description.get("seconds"):
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.coordinator.lin.value(self.key)

    @property
    def available(self) -> bool:
        return self.coordinator.lin.value(self.key) is not None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "telemetry_source": "lin",
            "lin_bridge_id": self.coordinator.lin.bridge_id,
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
        return self.coordinator.coach_voltage_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.coach_voltage_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        raw_word = None
        if raw is not None and len(raw) >= 2:
            raw_word = int.from_bytes(raw[0:2], "big")
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("coach_voltage"),
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_tenths": raw_word,
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "rejected_02aa_count": self.coordinator.rejected_02aa_count,
            "last_rejected_packet_reason": self.coordinator.last_rejected_packet_reason,
            "pending_voltage_tenths": self.coordinator.pending_coach_voltage_tenths,
            "rejected_voltage_tenths": self.coordinator.rejected_coach_voltage_tenths,
            "rejected_voltage_reason": self.coordinator.rejected_coach_voltage_reason,
        }


class PrecisionPlexFreshWaterTankSensor(PrecisionPlexBaseSensor):
    """Fresh water tank level decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Fresh Water Tank"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water-percent"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Fresh Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_fresh_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Fresh Water tank percentage."""
        return self.coordinator.fresh_water_level_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.fresh_water_level_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("fresh_water_level"),
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Grey Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_grey_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Grey Water tank percentage."""
        return self.coordinator.grey_water_level_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.grey_water_level_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("grey_water_level"),
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Black Water tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_black_water_tank"

    @property
    def native_value(self) -> int | None:
        """Return Black Water tank percentage."""
        return self.coordinator.black_water_level_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.black_water_level_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("black_water_level"),
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the LP Gas tank sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_lp_gas_tank"

    @property
    def native_value(self) -> int | None:
        """Return LP Gas tank percentage."""
        return self.coordinator.lp_gas_level_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.lp_gas_level_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("lp_gas_level"),
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "raw_lp_byte": (
                f"0x{self.coordinator.raw_lp_byte:02X}"
                if isinstance(self.coordinator.raw_lp_byte, int)
                else None
            ),
            "raw_lp_nibble": (
                f"0x{self.coordinator.raw_lp_level:X}"
                if isinstance(self.coordinator.raw_lp_level, int)
                else None
            ),
            "last_rejected_lp_byte": (
                f"0x{self.coordinator.last_rejected_lp_byte:02X}"
                if isinstance(self.coordinator.last_rejected_lp_byte, int)
                else None
            ),
            "last_rejected_lp_reason": self.coordinator.last_rejected_lp_reason,
            "source_field": "byte 5 high nibble; byte 5 low nibble must be 0",
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "clean LP bytes: 0x00=0%, 0x20=25%, 0x50=50%, 0x70=75%, 0xA0=100%; nonzero low-nibble LP bytes are ignored",
        }


class PrecisionPlexGeneratorRuntimeSensor(PrecisionPlexBaseSensor):
    """Generator runtime decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Generator Runtime"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-outline"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the generator runtime sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_generator_runtime"

    @property
    def native_value(self) -> float | None:
        """Return generator runtime hours."""
        return self.coordinator.generator_runtime_hours_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.generator_runtime_hours_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.generator_runtime_source,
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "source_field": "bytes 7-8 big-endian tenths of hours",
            "raw_runtime_tenths": self.coordinator.raw_generator_runtime_tenths,
            "ignored_runtime_tenths": self.coordinator.ignored_generator_runtime_tenths,
            "ignored_runtime_reason": self.coordinator.ignored_generator_runtime_reason,
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "lin_mapping": "PIDBA data bytes 1-3 little-endian packed BCD whole hours plus page low-nibble tenths",
            "ble_mapping": "0x04B4=1204 tenths=120.4 hours",
            "guard": "ignore >1000.0h, decreases, or jumps over 5.0h between accepted samples",
        }


class PrecisionPlexGeneratorStatusSensor(PrecisionPlexBaseSensor):
    """Generator status decoded from Precision Plex 02AA telemetry."""

    _attr_name = "Generator Status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:generator-stationary"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the generator status sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_generator_status"

    @property
    def native_value(self) -> str | None:
        """Return decoded generator status text."""
        return self.coordinator.generator_status_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.generator_status_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | bool | None]:
        """Return diagnostic attributes."""
        raw = self.coordinator.raw_battery_state
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("generator_status"),
            "source_handle": "0x002B",
            "source_characteristic": "02AA",
            "source_field": "bytes 6-7 generator status/transition word",
            "generator_running": self.coordinator.generator_running_value,
            "generator_status_key": self.coordinator.generator_status_key_value,
            "raw_generator_status": (
                f"0x{self.coordinator.raw_generator_status:02X}"
                if isinstance(self.coordinator.raw_generator_status, int)
                else None
            ),
            "raw_generator_status_word": (
                f"0x{self.coordinator.raw_generator_status_word:04X}"
                if isinstance(self.coordinator.raw_generator_status_word, int)
                else None
            ),
            "raw_02aa": raw.hex(" ") if raw is not None else None,
            "mapping": "0004=Stopped, 1004=Running, 00A0=AutoStart Accepted, 2004=Will Not Start, 6004=Performing Generator AutoStart, 7004=Performing Generator AutoStop",
        }


class PrecisionPlexTelemetryTransportSensor(PrecisionPlexBaseSensor):
    """Show which transport currently supplies preferred coach telemetry."""

    _attr_name = "Telemetry Transport"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:transit-connection-variant"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_telemetry_transport"

    @property
    def native_value(self) -> str:
        return self.coordinator.telemetry_transport

    @property
    def available(self) -> bool:
        return True

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.coordinator.lin.snapshot
        return {
            "lin_bridge_device_id": self.coordinator.lin.device_id,
            "lin_bridge_id": self.coordinator.lin.bridge_id,
            "lin_entity_count": len(self.coordinator.lin.entity_ids),
            "lin_event_snapshot_active": self.coordinator.lin.snapshot_fresh,
            "lin_firmware_version": snapshot.get("firmware_version"),
            "lin_snapshot_sequence": snapshot.get("snapshot_sequence"),
            "lin_snapshot_reason": snapshot.get("snapshot_reason"),
            "lin_bus_active": snapshot.get("bus_active"),
            "lin_packets_per_second": snapshot.get("packets_per_second"),
            "lin_known_packets": snapshot.get("known_packets"),
            "lin_unknown_packets": snapshot.get("unknown_packets"),
            "lin_crc_errors": snapshot.get("crc_errors"),
            "lin_last_pid": snapshot.get("last_pid"),
            "lin_telemetry_active": self.coordinator.lin.active,
            "lin_core_telemetry_active": self.coordinator.lin.core_active,
            "lin_output_state_active": self.coordinator.lin.outputs_active,
            "bluetooth_connected": self.coordinator.ble_connected,
            "generator_runtime_source": "bluetooth",
            "commands_source": "bluetooth",
        }

class PrecisionPlexHomeKitLevelSensor(PrecisionPlexBaseSensor):
    """HomeKit-friendly humidity percentage sensor."""

    # Exact friendly names for HomeKit-facing helper sensors.
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

class PrecisionPlexFreshWaterHomeKitSensor(PrecisionPlexHomeKitLevelSensor):
    _attr_name = "Fresh Water"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_fresh_water_homekit"
    @property
    def native_value(self): return self.coordinator.fresh_water_level_value
    @property
    def available(self): return self.coordinator.fresh_water_level_value is not None

class PrecisionPlexGreyWaterHomeKitSensor(PrecisionPlexHomeKitLevelSensor):
    _attr_name = "Grey Tank"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_grey_water_homekit"
    @property
    def native_value(self): return self.coordinator.grey_water_level_value
    @property
    def available(self): return self.coordinator.grey_water_level_value is not None

class PrecisionPlexBlackWaterHomeKitSensor(PrecisionPlexHomeKitLevelSensor):
    _attr_name = "Black Tank"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_black_water_homekit"
    @property
    def native_value(self): return self.coordinator.black_water_level_value
    @property
    def available(self): return self.coordinator.black_water_level_value is not None

class PrecisionPlexPropaneHomeKitSensor(PrecisionPlexHomeKitLevelSensor):
    _attr_name = "Propane"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_propane_homekit"
    @property
    def native_value(self): return self.coordinator.lp_gas_level_value
    @property
    def available(self): return self.coordinator.lp_gas_level_value is not None


class PrecisionPlexAwningControlMethodSensor(PrecisionPlexBaseSensor):
    """Diagnostic sensor showing whether awning current telemetry is available."""

    _attr_name = "Awning Control Method"
    _attr_icon = "mdi:awning"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the awning control method sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_awning_control_method"

    @property
    def native_value(self) -> str:
        """Return current awning control method."""
        if self._smart_awning_current_state() is not None:
            return "Smart Current Sense"
        return "Timed"

    @property
    def available(self) -> bool:
        """Return availability."""
        return True

    def _smart_awning_current_state(self):
        """Find the ESPHome awning current sensor if it is present and valid."""
        if self.hass is None:
            return None
        invalid_states = ("unknown", "unavailable", None)
        candidates = (
            "sensor.lippert_awning_telemetry_awning_motor_current",
            "sensor.awning_motor_current",
        )
        for entity_id in candidates:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in invalid_states:
                return state
        for state in self.hass.states.async_all():
            if state.state in invalid_states:
                continue
            entity_id = state.entity_id.lower()
            friendly = str(state.attributes.get("friendly_name", "")).lower()
            if (
                entity_id.endswith("_awning_motor_current")
                or friendly == "awning motor current"
                or friendly.endswith(" awning motor current")
            ):
                return state
        return None


class PrecisionPlexDiagnosticCounterSensor(PrecisionPlexBaseSensor):
    """Base class for numeric BLE diagnostic counters."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    @property
    def available(self) -> bool:
        """Return availability."""
        return True


class PrecisionPlexBleLastValidPacketSensor(PrecisionPlexBaseSensor):
    """Timestamp of the last accepted Precision Plex BLE packet."""

    _attr_name = "BLE Last Valid Packet"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:bluetooth-transfer"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_last_valid_packet"

    @property
    def native_value(self):
        """Return timestamp of last accepted BLE packet."""
        return self.coordinator.last_valid_packet_time

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.last_valid_packet_time is not None

    @property
    def extra_state_attributes(self) -> dict:
        """Return diagnostic details."""
        return {
            "last_valid_source": self.coordinator.last_valid_packet_source,
            "last_valid_02aa": self.coordinator.last_valid_02aa_time,
            "last_valid_02bb": self.coordinator.last_valid_02bb_time,
            "last_packet_age_seconds": self.coordinator.last_valid_packet_age_seconds,
        }


class PrecisionPlexBlePacketAgeSensor(PrecisionPlexBaseSensor):
    """Age of the last accepted Precision Plex BLE packet."""

    _attr_name = "BLE Last Packet Age"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_last_packet_age"

    @property
    def native_value(self) -> int | None:
        """Return packet age in seconds."""
        return self.coordinator.last_valid_packet_age_seconds

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.last_valid_packet_time is not None


class PrecisionPlexBleReconnectCountSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Reconnect Count"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_reconnect_count"
    @property
    def native_value(self): return self.coordinator.ble_reconnect_count
    @property
    def extra_state_attributes(self): return {"last_ble_connect_time": self.coordinator.last_ble_connect_time}


class PrecisionPlexBleDisconnectCountSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Disconnect Count"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_disconnect_count"
    @property
    def native_value(self): return self.coordinator.ble_disconnect_count
    @property
    def extra_state_attributes(self): return {"last_ble_disconnect_time": self.coordinator.last_ble_disconnect_time}


class PrecisionPlexBlePacketsReceivedSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Packets Accepted"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_packets_accepted"
    @property
    def native_value(self): return self.coordinator.packets_received_count
    @property
    def extra_state_attributes(self):
        return {
            "accepted_02aa": self.coordinator.received_02aa_count,
            "accepted_02bb": self.coordinator.received_02bb_count,
        }


class PrecisionPlexBlePacketsRejectedSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Packets Rejected"
    _attr_icon = "mdi:packet-remove"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_packets_rejected"
    @property
    def native_value(self): return self.coordinator.packets_rejected_count
    @property
    def extra_state_attributes(self):
        return {
            "rejected_02aa": self.coordinator.rejected_02aa_count,
            "rejected_02bb": self.coordinator.rejected_02bb_count,
            "acceptance_percent": self.coordinator.packet_acceptance_percent,
            "rejection_percent": self.coordinator.packet_rejection_percent,
            "last_rejected_packet_type": self.coordinator.last_rejected_packet_type,
            "last_rejected_packet_reason": self.coordinator.last_rejected_packet_reason,
            "last_rejected_packet_source": self.coordinator.last_rejected_packet_source,
            "last_rejected_packet_length": self.coordinator.last_rejected_packet_length,
            "last_rejected_packet_sender": self.coordinator.last_rejected_packet_sender,
            "last_rejected_packet_hex": self.coordinator.last_rejected_packet_hex,
            "last_rejected_packet_changed_byte_indices": self.coordinator.last_rejected_packet_changed_byte_indices,
            "last_rejected_packet_changed_byte_count": self.coordinator.last_rejected_packet_changed_byte_count,
            "last_rejected_packet_changed_bytes": self.coordinator.last_rejected_packet_changed_bytes,
            "last_rejected_packet_seconds_since_last_good": self.coordinator.last_rejected_packet_seconds_since_last_good,
            "last_rejected_packet_seconds_since_connect": self.coordinator.last_rejected_packet_seconds_since_connect,
            "last_rejected_packet_variant": self.coordinator.last_rejected_packet_variant,
            "rejected_packet_variant_counts_top": _compact_count_dict(self.coordinator.rejected_packet_variant_counts),
            "rejected_packet_changed_byte_counts": dict(self.coordinator.rejected_packet_changed_byte_counts),
            "rejected_packet_changed_value_counts_top": _compact_count_dict(self.coordinator.rejected_packet_changed_value_counts),
            "last_rejected_02aa_length": self.coordinator.last_rejected_02aa_length,
            "last_rejected_02aa_hex": self.coordinator.last_rejected_02aa_hex,
            "last_rejected_02bb_length": self.coordinator.last_rejected_02bb_length,
            "last_rejected_02bb_hex": self.coordinator.last_rejected_02bb_hex,
            "reject_reason_counts": dict(self.coordinator.reject_reason_counts),
            "packet_length_counts": dict(self.coordinator.packet_length_counts),
            "packet_type_counts": dict(self.coordinator.packet_type_counts),
            "suppressed_02bb_glitch_count": self.coordinator.suppressed_02bb_glitch_count,
        }


class PrecisionPlexBleRejected02AASensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE 02AA Rejected"
    _attr_icon = "mdi:packet-remove"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_02aa_rejected"
    @property
    def native_value(self): return self.coordinator.rejected_02aa_count


class PrecisionPlexBleRejected02BBSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE 02BB Rejected"
    _attr_icon = "mdi:packet-remove"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_02bb_rejected"
    @property
    def native_value(self): return self.coordinator.rejected_02bb_count
    @property
    def extra_state_attributes(self): return {"suppressed_02bb_glitch_count": self.coordinator.suppressed_02bb_glitch_count}


class PrecisionPlexBleLastRejectReasonSensor(PrecisionPlexBaseSensor):
    """Last BLE packet rejection reason."""

    _attr_name = "BLE Last Reject Reason"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_last_reject_reason"

    @property
    def native_value(self):
        return self.coordinator.last_rejected_packet_reason or "none"

    @property
    def available(self): return True

    @property
    def extra_state_attributes(self):
        return {
            "source": self.coordinator.last_rejected_packet_source,
            "raw": self.coordinator.last_rejected_packet_hex,
            "changed_byte_indices": self.coordinator.last_rejected_packet_changed_byte_indices,
            "changed_byte_count": self.coordinator.last_rejected_packet_changed_byte_count,
            "seconds_since_last_good": self.coordinator.last_rejected_packet_seconds_since_last_good,
            "seconds_since_connect": self.coordinator.last_rejected_packet_seconds_since_connect,
            "variant": self.coordinator.last_rejected_packet_variant,
        }


class PrecisionPlexBleLastRejectedPacketSensor(PrecisionPlexBaseSensor):
    """Last rejected BLE packet as hex."""

    _attr_name = "BLE Last Rejected Packet"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:code-braces"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_last_rejected_packet"

    @property
    def native_value(self):
        return self.coordinator.last_rejected_packet_hex or "none"

    @property
    def available(self): return True

    @property
    def extra_state_attributes(self):
        return {
            "packet_type": self.coordinator.last_rejected_packet_type,
            "length": self.coordinator.last_rejected_packet_length,
            "reason": self.coordinator.last_rejected_packet_reason,
            "source": self.coordinator.last_rejected_packet_source,
            "sender": self.coordinator.last_rejected_packet_sender,
            "changed_byte_indices": self.coordinator.last_rejected_packet_changed_byte_indices,
            "changed_byte_count": self.coordinator.last_rejected_packet_changed_byte_count,
            "changed_bytes": self.coordinator.last_rejected_packet_changed_bytes,
            "seconds_since_last_good": self.coordinator.last_rejected_packet_seconds_since_last_good,
            "seconds_since_connect": self.coordinator.last_rejected_packet_seconds_since_connect,
            "variant": self.coordinator.last_rejected_packet_variant,
            "variant_counts_top": _compact_count_dict(self.coordinator.rejected_packet_variant_counts),
            "changed_value_counts_top": _compact_count_dict(self.coordinator.rejected_packet_changed_value_counts),
            "last_02aa_hex": self.coordinator.last_rejected_02aa_hex,
            "last_02bb_hex": self.coordinator.last_rejected_02bb_hex,
        }


class PrecisionPlexBleLastRejectedPacketLengthSensor(PrecisionPlexDiagnosticCounterSensor):
    """Length of the last rejected BLE packet."""

    _attr_name = "BLE Last Rejected Packet Length"
    _attr_icon = "mdi:ruler"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_last_rejected_packet_length"

    @property
    def native_value(self):
        return self.coordinator.last_rejected_packet_length

    @property
    def available(self): return self.coordinator.last_rejected_packet_length is not None

    @property
    def extra_state_attributes(self):
        return {
            "packet_type": self.coordinator.last_rejected_packet_type,
            "reason": self.coordinator.last_rejected_packet_reason,
            "packet_length_counts": dict(self.coordinator.packet_length_counts),
        }


class PrecisionPlexBlePacketRejectionPercentSensor(PrecisionPlexBaseSensor):
    """Rejected BLE packet percentage."""

    _attr_name = "BLE Packet Rejection Percent"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_packet_rejection_percent"

    @property
    def native_value(self):
        return self.coordinator.packet_rejection_percent

    @property
    def available(self): return self.coordinator.packet_rejection_percent is not None

    @property
    def extra_state_attributes(self):
        return {
            "accepted": self.coordinator.packets_received_count,
            "rejected": self.coordinator.packets_rejected_count,
            "acceptance_percent": self.coordinator.packet_acceptance_percent,
            "reject_reason_counts": dict(self.coordinator.reject_reason_counts),
            "changed_byte_counts": dict(self.coordinator.rejected_packet_changed_byte_counts),
        }


class PrecisionPlexBleRejectedPacketLogSensor(PrecisionPlexBaseSensor):
    """Rolling forensic log of recently rejected BLE packets."""

    _attr_name = "BLE Rejected Packet Log"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clipboard-text-clock-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_rejected_packet_log"

    @property
    def native_value(self):
        count = len(getattr(self.coordinator, "rejected_packet_log", []) or [])
        return count

    @property
    def available(self):
        return True

    @property
    def extra_state_attributes(self):
        log = list(getattr(self.coordinator, "rejected_packet_log", []) or [])
        recent = log[-MAX_RECORDER_LOG_ENTRIES:]
        return {
            "stored_entries": len(log),
            "max_entries": getattr(self.coordinator, "max_rejected_packet_log_entries", 100),
            "recorder_entries_exposed": len(recent),
            "oldest_entry_summary": _compact_rejected_packet_entry(log[0]) if log else None,
            "newest_entry_summary": _compact_rejected_packet_entry(log[-1]) if log else None,
            "recent_entries_compact": [_compact_rejected_packet_entry(entry) for entry in recent],
            "full_log_available_in_diagnostics": True,
        }


class PrecisionPlexCommandStreamRecoveriesSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Command Stream Recoveries"
    _attr_icon = "mdi:bluetooth-connect"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_command_stream_recoveries"
    @property
    def native_value(self): return self.coordinator.hold_stream_recoveries


class PrecisionPlexCommandStreamInterruptionsSensor(PrecisionPlexDiagnosticCounterSensor):
    _attr_name = "BLE Command Stream Interruptions"
    _attr_icon = "mdi:bluetooth-off"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_command_stream_interruptions"
    @property
    def native_value(self): return self.coordinator.hold_stream_interruption_count


class PrecisionPlexCommandStreamLastErrorSensor(PrecisionPlexBaseSensor):
    _attr_name = "BLE Command Stream Last Error"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:alert-outline"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.address}_ble_command_stream_last_error"
    @property
    def native_value(self): return self.coordinator.last_hold_stream_error or "none"
    @property
    def available(self): return True
