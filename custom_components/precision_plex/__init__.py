"""Precision Plex integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import PrecisionPlexStateCoordinator

_LOGGER = logging.getLogger(__name__)


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
