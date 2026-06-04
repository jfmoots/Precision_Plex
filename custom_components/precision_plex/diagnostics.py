"""Diagnostics support for the Precision Plex integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .const import (
    BATTERY_CHARACTERISTIC_UUID,
    CONTROL_CHARACTERISTIC_UUID,
    DOMAIN,
    PAIRING_CHARACTERISTIC_UUID,
    STATE_BITS,
    STATE_CHARACTERISTIC_UUID,
    TARGET_SERVICE_UUID,
)

TO_REDACT = {
    CONF_ADDRESS,
    "address",
    "unique_id",
}


def _hex_bytes(value: bytes | bytearray | None) -> str | None:
    """Return bytes as a space-separated hex string."""
    if value is None:
        return None
    return bytes(value).hex(" ")


def _hex_int(value: int | None, width: int = 2) -> str | None:
    """Return an integer as a fixed-width hex string."""
    if value is None:
        return None
    return f"0x{value:0{width}X}"


def _state_bit_diagnostics(coordinator: Any) -> dict[str, Any]:
    """Build a decoded state-bit summary from 02BB telemetry."""
    decoded: dict[str, Any] = {}

    for key, description in STATE_BITS.items():
        word_index = description.get("word_index", 0)
        bit = description.get("bit", 0)
        decoded[key] = {
            "name": description.get("name"),
            "word_index": word_index,
            "bit": _hex_int(bit, 4),
            "value": coordinator.is_bit_on(bit, word_index),
        }

    return decoded


def _client_diagnostics(coordinator: Any) -> dict[str, Any]:
    """Build a small BLE client/service summary when available."""
    client = getattr(coordinator, "_client", None)
    connected = bool(client is not None and getattr(client, "is_connected", False))
    data: dict[str, Any] = {
        "connected": connected,
        "expected_service_uuid": TARGET_SERVICE_UUID,
        "expected_characteristics": {
            "pairing": PAIRING_CHARACTERISTIC_UUID,
            "state_02bb": STATE_CHARACTERISTIC_UUID,
            "telemetry_02aa": BATTERY_CHARACTERISTIC_UUID,
            "control": CONTROL_CHARACTERISTIC_UUID,
        },
    }

    services = getattr(client, "services", None) if client is not None else None
    if services is None:
        return data

    characteristics: list[dict[str, Any]] = []
    try:
        for service in services:
            for char in service.characteristics:
                characteristics.append(
                    {
                        "uuid": char.uuid,
                        "handle": _hex_int(getattr(char, "handle", None), 4),
                        "properties": list(getattr(char, "properties", [])),
                    }
                )
    except Exception:  # pragma: no cover - diagnostics must never break HA.
        data["services_error"] = "Unable to enumerate BLE services"
    else:
        data["characteristics"] = characteristics

    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    if coordinator is None:
        return async_redact_data(
            {
                "entry": {
                    "title": entry.title,
                    "data": dict(entry.data),
                    "options": dict(entry.options),
                },
                "coordinator": None,
            },
            TO_REDACT,
        )

    state_words = getattr(coordinator, "state_words", []) or []

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "available": getattr(coordinator, "available", None),
            "stopped": getattr(coordinator, "_stopped", None),
            "address": getattr(coordinator, "address", None),
            "raw_state_02bb": _hex_bytes(getattr(coordinator, "raw_state", None)),
            "state_word": _hex_int(getattr(coordinator, "state_word", None), 4),
            "state_words": [_hex_int(word, 4) for word in state_words],
            "decoded_state_bits": _state_bit_diagnostics(coordinator),
            "raw_telemetry_02aa": _hex_bytes(getattr(coordinator, "raw_battery_state", None)),
            "coach_voltage": getattr(coordinator, "coach_voltage", None),
            "levels": {
                "fresh_water_percent": getattr(coordinator, "fresh_water_level", None),
                "fresh_water_raw": _hex_int(getattr(coordinator, "raw_fresh_level", None)),
                "grey_water_percent": getattr(coordinator, "grey_water_level", None),
                "grey_water_raw": _hex_int(getattr(coordinator, "raw_grey_level", None)),
                "black_water_percent": getattr(coordinator, "black_water_level", None),
                "black_water_raw": _hex_int(getattr(coordinator, "raw_black_level", None)),
                "lp_gas_percent": getattr(coordinator, "lp_gas_level", None),
                "lp_gas_raw": _hex_int(getattr(coordinator, "raw_lp_level", None)),
            },
            "generator": {
                "running": getattr(coordinator, "generator_running", None),
                "status": getattr(coordinator, "generator_status", None),
                "status_key": getattr(coordinator, "generator_status_key", None),
                "runtime_hours": getattr(coordinator, "generator_runtime_hours", None),
                "raw_status": _hex_int(getattr(coordinator, "raw_generator_status", None)),
                "raw_status_word": _hex_int(getattr(coordinator, "raw_generator_status_word", None), 4),
                "raw_runtime_tenths": getattr(coordinator, "raw_generator_runtime_tenths", None),
            },
            "ble": _client_diagnostics(coordinator),
        },
    }

    return async_redact_data(diagnostics, TO_REDACT)
