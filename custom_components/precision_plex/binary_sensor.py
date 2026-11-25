"""Binary sensors for Precision Plex read-only monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, STATE_BITS
from .coordinator import PrecisionPlexStateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex binary sensors."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        PrecisionPlexStateBinarySensor(coordinator, entry, key, description)
        for key, description in STATE_BITS.items()
    ]
    entities.append(PrecisionPlexGeneratorRunningBinarySensor(coordinator, entry))
    entities.append(PrecisionPlexBleConnectedBinarySensor(coordinator, entry))
    entities.extend(
        PrecisionPlexLinCommandProblem(coordinator, path, name, unique_id_suffix)
        for path, name, unique_id_suffix in (
            # Keep the existing entity and its dashboard and automation references.
            ("bridge", "LIN Command Path Problem", "lin_command_path_problem"),
            ("generator", "LIN Generator Command Problem", "lin_generator_command_problem"),
            ("outputs", "LIN Output and Motion Command Problem", "lin_output_motion_command_problem"),
        )
    )
    entities.extend(
        PrecisionPlexLinOnlyBinarySensor(coordinator, entry, key, name, device_class)
        for key, name, device_class in (
            ("tank_heater", "Tank Heater", BinarySensorDeviceClass.POWER),
            ("ac_converter_present", "AC / Converter Present", BinarySensorDeviceClass.POWER),
            ("ignition_on", "Ignition", BinarySensorDeviceClass.POWER),
            (
                "hvac_zone_1_compressor_lockout",
                "HVAC Zone 1 Compressor Lockout",
                BinarySensorDeviceClass.PROBLEM,
            ),
            (
                "hvac_zone_2_compressor_lockout",
                "HVAC Zone 2 Compressor Lockout",
                BinarySensorDeviceClass.PROBLEM,
            ),
        )
    )
    async_add_entities(entities)


class PrecisionPlexLinCommandProblem(BinarySensorEntity, RestoreEntity):
    """A dashboard-ready problem sensor for one LIN command path."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: PrecisionPlexStateCoordinator, path: str,
        name: str, unique_id_suffix: str,
    ) -> None:
        self.coordinator = coordinator
        self._path = path
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.address}_{unique_id_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "connections": {(CONNECTION_BLUETOOTH, coordinator.address)},
            "name": "Precision Plex",
            "manufacturer": "Precision Circuits",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._path == "bridge":
            previous = await self.async_get_last_state()
            if previous is not None and previous.state in ("on", "off"):
                self.coordinator.lin_commands_expected = True
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return self.coordinator.lin_command_problems[self._path] is not None

    @property
    def is_on(self) -> bool | None:
        problems = self.coordinator.lin_command_problems[self._path]
        return bool(problems) if problems is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"missing_command_paths": list(self.coordinator.lin_command_problems[self._path] or ())}


class PrecisionPlexLinOnlyBinarySensor(BinarySensorEntity):
    """A read-only value that exists only on the LIN transport."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, device_class) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_unique_id = f"{coordinator.address}_lin_{key}"
        self._remove_listener = None

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
        value = self.coordinator.effective_lin_binary_value(self.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        return isinstance(self.coordinator.lin.value(self.key), bool)

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
            "telemetry_source": "lin",
            "lin_bridge_id": self.coordinator.lin.bridge_id,
        }


class PrecisionPlexStateBinarySensor(BinarySensorEntity):
    """Read-only binary sensor decoded from 02BB state bitmap."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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
        return self.coordinator.is_bit_on(self.bit, self.word_index) is not None

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
        """Return stable operational attributes."""
        confirmed = self.coordinator.confirmed_bit_on(self.bit, self.word_index)
        requested = self.coordinator.provisional_state_for(self.key)
        return {
            "telemetry_source": self.coordinator.telemetry_source_for(self.key),
            "confirmed_state": confirmed,
            "command_confirmation_pending": requested is not None,
            "command_requested_state": requested,
        }


class PrecisionPlexGeneratorRunningBinarySensor(BinarySensorEntity):
    """Generator running status decoded from Precision Plex 02AA telemetry."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Generator Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{coordinator.address}_generator_running"
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
        """Return decoded generator running state."""
        return self.coordinator.generator_running_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.generator_running_value is not None

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
        """Return stable operational attributes."""
        return {
            "telemetry_source": self.coordinator.telemetry_source_for("generator_running"),
            "generator_status": self.coordinator.generator_status_value,
            "generator_status_key": self.coordinator.generator_status_key_value,
        }


class PrecisionPlexBleConnectedBinarySensor(BinarySensorEntity):
    """Diagnostic binary sensor showing BLE connection health."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "BLE Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: PrecisionPlexStateCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{coordinator.address}_ble_connected"
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
        """Handle updated BLE health."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return BLE connection state."""
        return self.coordinator.ble_connected

    @property
    def available(self) -> bool:
        """BLE health sensor should always be visible."""
        return True

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
            "last_ble_connect_time": self.coordinator.last_ble_connect_time,
            "last_ble_disconnect_time": self.coordinator.last_ble_disconnect_time,
            "ble_reconnect_count": self.coordinator.ble_reconnect_count,
            "ble_disconnect_count": self.coordinator.ble_disconnect_count,
            "last_valid_packet_time": self.coordinator.last_valid_packet_time,
            "last_valid_packet_age_seconds": self.coordinator.last_valid_packet_age_seconds,
        }
