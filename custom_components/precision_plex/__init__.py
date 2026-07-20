"""Precision Plex integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

from .const import DOMAIN, PLATFORMS
from .coordinator import PrecisionPlexStateCoordinator

_LOGGER = logging.getLogger(__name__)

_NOISY_BLE_UNIQUE_ID_SUFFIXES = (
    "_ble_last_valid_packet",
    "_ble_last_packet_age",
    "_ble_reconnect_count",
    "_ble_disconnect_count",
    "_ble_packets_accepted",
    "_ble_packets_rejected",
    "_ble_02aa_rejected",
    "_ble_02bb_rejected",
    "_ble_last_reject_reason",
    "_ble_last_rejected_packet",
    "_ble_last_rejected_packet_length",
    "_ble_packet_rejection_percent",
    "_ble_rejected_packet_log",
    "_ble_command_stream_recoveries",
    "_ble_command_stream_interruptions",
    "_ble_command_stream_last_error",
)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate existing entries to quieter BLE diagnostic defaults."""
    if entry.version > 3:
        return False

    if entry.version < 3 or entry.minor_version < 2:
        registry = er.async_get(hass)
        disabled_count = 0
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            if (
                registry_entry.disabled_by is None
                and registry_entry.unique_id.endswith(
                    _NOISY_BLE_UNIQUE_ID_SUFFIXES
                )
            ):
                registry.async_update_entity(
                    registry_entry.entity_id,
                    disabled_by=RegistryEntryDisabler.INTEGRATION,
                )
                disabled_count += 1

        hass.config_entries.async_update_entry(
            entry,
            version=3,
            minor_version=2,
        )
        _LOGGER.info(
            "Precision Plex migration disabled %s high-churn BLE diagnostic entities",
            disabled_count,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Precision Plex from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PrecisionPlexStateCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_start()

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        _LOGGER.exception("Failed to set up Precision Plex platforms")
        await coordinator.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if DOMAIN in hass.data and not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
        raise

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Precision Plex cleanly."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    if coordinator is not None:
        await coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
