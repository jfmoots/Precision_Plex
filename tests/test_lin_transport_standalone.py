"""Dependency-free smoke tests for LIN selection logic."""

from __future__ import annotations

import importlib.util
import ast
from pathlib import Path
import sys
import types
import unittest


class State:
    def __init__(self, state: str) -> None:
        self.state = state


def _load_module():
    const = types.ModuleType("homeassistant.const")
    const.EVENT_STATE_CHANGED = "state_changed"
    const.STATE_UNAVAILABLE = "unavailable"
    const.STATE_UNKNOWN = "unknown"
    core = types.ModuleType("homeassistant.core")
    core.Event = type("Event", (), {})
    core.HomeAssistant = type("HomeAssistant", (), {})
    core.State = State
    core.callback = lambda func: func
    helpers = types.ModuleType("homeassistant.helpers")
    entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
    event_helper = types.ModuleType("homeassistant.helpers.event")
    event_helper.async_call_later = lambda _hass, _delay, _callback: lambda: None
    helpers.entity_registry = entity_registry
    sys.modules.update(
        {
            "homeassistant": types.ModuleType("homeassistant"),
            "homeassistant.const": const,
            "homeassistant.core": core,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.entity_registry": entity_registry,
            "homeassistant.helpers.event": event_helper,
        }
    )
    path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "precision_plex"
        / "lin_transport.py"
    )
    spec = importlib.util.spec_from_file_location("lin_transport_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, entity_registry


class _Entry:
    platform = "esphome"
    device_id = "bridge-device"

    def __init__(self, entity_id: str, original_name: str) -> None:
        self.entity_id = entity_id
        self.original_name = original_name


class _Registry:
    def __init__(self, module) -> None:
        self.entities = {
            f"sensor.lin_{key}": _Entry(f"sensor.lin_{key}", name)
            for key, name in module.LIN_ENTITY_NAMES.items()
        }

    def async_get(self, entity_id):
        return self.entities.get(entity_id)


class _States:
    def __init__(self) -> None:
        self.values = {}

    def get(self, entity_id):
        return self.values.get(entity_id)


class _Bus:
    def async_listen(self, _event, _listener):
        return lambda: None


class LinTransportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module, registry_module = _load_module()
        registry = _Registry(self.module)
        registry_module.async_get = lambda _hass: registry
        self.hass = types.SimpleNamespace(states=_States(), bus=_Bus())
        self.notifications = 0

        def notified() -> None:
            self.notifications += 1

        self.lin = self.module.PrecisionPlexLinTelemetry(self.hass, notified)
        self.lin.start()

    def _set(self, key: str, value: str) -> None:
        self.hass.states.values[self.lin.entity_ids[key]] = State(value)

    def test_core_values_prefer_fresh_lin_and_stop_when_stale(self) -> None:
        self._set("health", "on")
        self._set("coach_voltage", "13.4")
        self.assertEqual(self.lin.value("coach_voltage"), 13.4)
        self._set("health", "off")
        self.assertIsNone(self.lin.value("coach_voltage"))

    def test_outputs_have_an_independent_freshness_gate(self) -> None:
        self._set("health", "off")
        self._set("outputs_health", "on")
        self._set("awning_out", "on")
        self.assertIs(self.lin.value("awning_out"), True)
        self._set("outputs_health", "off")
        self.assertIsNone(self.lin.value("awning_out"))

    def test_output_off_is_a_valid_lin_value(self) -> None:
        self._set("outputs_health", "on")
        self._set("water_pump", "off")
        self.assertIs(self.lin.value("water_pump"), False)

    def test_event_snapshot_supplies_lin_only_and_core_values(self) -> None:
        payload = {
            "schema": 1,
            "telemetry_active": True,
            "outputs_active": True,
            "power_active": True,
            "hvac_zone_1_active": True,
            "hvac_zone_2_active": False,
            "coach_voltage": 13.6,
            "tank_heater": False,
            "ignition_on": True,
            "hvac_zone_1_room_temp": 74,
            "hvac_zone_1_mode": "cool",
        }
        self.lin._handle_snapshot(
            types.SimpleNamespace(
                data={"bridge_id": "test-lin", "payload": __import__("json").dumps(payload)}
            )
        )
        self.assertEqual(self.lin.value("coach_voltage"), 13.6)
        self.assertIs(self.lin.value("tank_heater"), False)
        self.assertIs(self.lin.value("ignition_on"), True)
        self.assertEqual(self.lin.value("hvac_zone_1_room_temp"), 74)
        self.assertEqual(self.lin.bridge_id, "test-lin")

    def test_inactive_snapshot_source_does_not_publish_stale_value(self) -> None:
        self.lin._handle_snapshot(
            types.SimpleNamespace(
                data={
                    "payload": {
                        "schema": 1,
                        "telemetry_active": False,
                        "outputs_active": False,
                        "power_active": False,
                        "hvac_zone_1_active": False,
                        "hvac_zone_2_active": False,
                        "ignition_on": True,
                    }
                }
            )
        )
        self.assertIsNone(self.lin.value("ignition_on"))

    def test_heartbeat_diagnostics_do_not_rewrite_all_entities(self) -> None:
        base = {
            "schema": 1,
            "telemetry_active": True,
            "outputs_active": True,
            "power_active": True,
            "hvac_zone_1_active": False,
            "hvac_zone_2_active": False,
            "awning_light": False,
            "uptime_ms": 1000,
            "snapshot_sequence": 1,
            "snapshot_reason": "heartbeat",
            "known_packets": 100,
        }
        before = self.notifications
        self.lin._handle_snapshot(
            types.SimpleNamespace(data={"bridge_id": "test-lin", "payload": base})
        )
        self.assertEqual(self.notifications, before + 1)

        heartbeat = dict(base)
        heartbeat.update(
            uptime_ms=3000,
            snapshot_sequence=2,
            known_packets=300,
        )
        self.lin._handle_snapshot(
            types.SimpleNamespace(data={"bridge_id": "test-lin", "payload": heartbeat})
        )
        self.assertEqual(self.notifications, before + 1)

        changed = dict(heartbeat, awning_light=True, snapshot_reason="change")
        self.lin._handle_snapshot(
            types.SimpleNamespace(data={"bridge_id": "test-lin", "payload": changed})
        )
        self.assertEqual(self.notifications, before + 2)


class DeviceInfoContractTest(unittest.TestCase):
    """Prevent entity attributes from leaking into HA device registry data."""

    ALLOWED_DEVICE_INFO_KEYS = {
        "configuration_url",
        "connections",
        "default_manufacturer",
        "default_model",
        "default_name",
        "entry_type",
        "hw_version",
        "identifiers",
        "manufacturer",
        "model",
        "name",
        "serial_number",
        "suggested_area",
        "sw_version",
        "via_device",
        "via_device_id",
    }

    def test_all_literal_device_info_keys_are_valid(self) -> None:
        component_dir = Path(__file__).parents[1] / "custom_components" / "precision_plex"
        checked = 0
        for path in component_dir.glob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name != "device_info":
                    continue
                for child in ast.walk(node):
                    if not isinstance(child, ast.Return) or not isinstance(child.value, ast.Dict):
                        continue
                    keys = {
                        key.value
                        for key in child.value.keys
                        if isinstance(key, ast.Constant) and isinstance(key.value, str)
                    }
                    self.assertLessEqual(keys, self.ALLOWED_DEVICE_INFO_KEYS, path.name)
                    checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
