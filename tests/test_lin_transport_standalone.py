"""Dependency-free smoke tests for LIN selection logic."""

from __future__ import annotations

import importlib.util
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
    helpers.entity_registry = entity_registry
    sys.modules.update(
        {
            "homeassistant": types.ModuleType("homeassistant"),
            "homeassistant.const": const,
            "homeassistant.core": core,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.entity_registry": entity_registry,
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
        self.lin = self.module.PrecisionPlexLinTelemetry(self.hass, lambda: None)
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


if __name__ == "__main__":
    unittest.main()
