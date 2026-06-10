"""Cover platform for Precision Plex awning and slide controls."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    AWNING_IN_HOLD,
    AWNING_IN_RELEASE,
    AWNING_OUT_HOLD,
    AWNING_OUT_RELEASE,
    BED_SLIDE_IN_HOLD,
    BED_SLIDE_IN_RELEASE,
    BED_SLIDE_OUT_HOLD,
    BED_SLIDE_OUT_RELEASE,
    WARDROBE_SLIDE_IN_HOLD,
    WARDROBE_SLIDE_IN_RELEASE,
    WARDROBE_SLIDE_OUT_HOLD,
    WARDROBE_SLIDE_OUT_RELEASE,
    SOFA_SLIDE_IN_HOLD,
    SOFA_SLIDE_IN_RELEASE,
    SOFA_SLIDE_OUT_HOLD,
    SOFA_SLIDE_OUT_RELEASE,
    DOMAIN,
    STATE_BITS,
)
from .coordinator import PrecisionPlexStateCoordinator


_LOGGER = logging.getLogger(__name__)

HOLD_INTERVAL_SECONDS = 0.30

SOFA_SLIDE_DEFAULT_FULL_TRAVEL_PULSES = 5450.0
SOFA_SLIDE_ENDPOINT_SNAP_PERCENT = 2.0
SOFA_SLIDE_TELEMETRY_FRIENDLY_NAMES = {
    "travel_pulses": "Sofa Slide Travel Pulses",
    "sync_error": "Sofa Slide Sync Error",
    "moving": "Sofa Slide Moving",
}
SOFA_SLIDE_TELEMETRY_ENTITY_CANDIDATES = {
    "travel_pulses": (
        "sensor.sofa_slide_travel_pulses",
        "sensor.lippert_sofa_slide_controller_sofa_slide_travel_pulses",
        "sensor.lippert_sofa_slide_telemetry_sofa_slide_travel_pulses",
    ),
    "sync_error": (
        "sensor.sofa_slide_sync_error",
        "sensor.lippert_sofa_slide_controller_sofa_slide_sync_error",
        "sensor.lippert_sofa_slide_telemetry_sofa_slide_sync_error",
    ),
    "moving": (
        "binary_sensor.sofa_slide_moving",
        "binary_sensor.lippert_sofa_slide_controller_sofa_slide_moving",
        "binary_sensor.lippert_sofa_slide_telemetry_sofa_slide_moving",
    ),
}


@dataclass(frozen=True)
class PrecisionPlexCoverDescription:
    """Description for a Precision Plex press-and-hold cover."""

    key: str
    name: str
    out_state_key: str
    in_state_key: str
    out_release_payload: bytes
    out_hold_payload: bytes
    in_release_payload: bytes
    in_hold_payload: bytes
    out_full_seconds: float
    in_full_seconds: float
    out_seconds_setting_key: str
    in_seconds_setting_key: str
    jog_seconds_setting_key: str


COVERS: tuple[PrecisionPlexCoverDescription, ...] = (
    PrecisionPlexCoverDescription(
        key="awning",
        name="Patio Awning",
        out_state_key="awning_out",
        in_state_key="awning_in",
        out_release_payload=AWNING_OUT_RELEASE,
        out_hold_payload=AWNING_OUT_HOLD,
        in_release_payload=AWNING_IN_RELEASE,
        in_hold_payload=AWNING_IN_HOLD,
        out_full_seconds=18.0,
        in_full_seconds=25.0,
        out_seconds_setting_key="awning_open_seconds",
        in_seconds_setting_key="awning_close_seconds",
        jog_seconds_setting_key="awning_jog_seconds",
    ),
    PrecisionPlexCoverDescription(
        key="bed_slide",
        name="Bedroom Slide",
        out_state_key="bed_slide_out",
        in_state_key="bed_slide_in",
        out_release_payload=BED_SLIDE_OUT_RELEASE,
        out_hold_payload=BED_SLIDE_OUT_HOLD,
        in_release_payload=BED_SLIDE_IN_RELEASE,
        in_hold_payload=BED_SLIDE_IN_HOLD,
        out_full_seconds=28.0,
        in_full_seconds=24.0,
        out_seconds_setting_key="bed_slide_open_seconds",
        in_seconds_setting_key="bed_slide_close_seconds",
        jog_seconds_setting_key="bed_slide_jog_seconds",
    ),
    PrecisionPlexCoverDescription(
        key="wardrobe_slide",
        name="Wardrobe Slide",
        out_state_key="wardrobe_slide_out",
        in_state_key="wardrobe_slide_in",
        out_release_payload=WARDROBE_SLIDE_OUT_RELEASE,
        out_hold_payload=WARDROBE_SLIDE_OUT_HOLD,
        in_release_payload=WARDROBE_SLIDE_IN_RELEASE,
        in_hold_payload=WARDROBE_SLIDE_IN_HOLD,
        out_full_seconds=18.0,
        in_full_seconds=17.0,
        out_seconds_setting_key="wardrobe_slide_open_seconds",
        in_seconds_setting_key="wardrobe_slide_close_seconds",
        jog_seconds_setting_key="wardrobe_slide_jog_seconds",
    ),
    PrecisionPlexCoverDescription(
        key="sofa_slide",
        name="Sofa Slide",
        out_state_key="sofa_slide_out",
        in_state_key="sofa_slide_in",
        out_release_payload=SOFA_SLIDE_OUT_RELEASE,
        out_hold_payload=SOFA_SLIDE_OUT_HOLD,
        in_release_payload=SOFA_SLIDE_IN_RELEASE,
        in_hold_payload=SOFA_SLIDE_IN_HOLD,
        out_full_seconds=32.0,
        in_full_seconds=28.0,
        out_seconds_setting_key="sofa_slide_open_seconds",
        in_seconds_setting_key="sofa_slide_close_seconds",
        jog_seconds_setting_key="sofa_slide_jog_seconds",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Precision Plex cover entities."""
    coordinator: PrecisionPlexStateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for description in COVERS:
        # v4.2.4 stops creating the preserved legacy cover entities.
        # The jog/calibration/timing controls remain available, and the clean
        # native covers are now the only cover entities created by the platform.
        entities.append(PrecisionPlexCleanNativeCover(coordinator, entry, description))

    async_add_entities(entities)


class PrecisionPlexTimedCover(CoverEntity, RestoreEntity):
    """Native Home Assistant cover entity using app-like press-and-hold BLE packets.

    Legacy jog and calibration buttons remain available on the same device.
    """

    _attr_has_entity_name = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        description: PrecisionPlexCoverDescription,
    ) -> None:
        """Initialize the cover."""
        self.coordinator = coordinator
        self.entry = entry
        self._plex_description = description
        # Legacy cover entities are preserved for backward compatibility,
        # but new installs should use the clean native cover entities instead.
        self._attr_name = f"{description.name} Legacy"
        self._attr_unique_id = f"{coordinator.address}_{description.key}_cover"
        self._attr_entity_registry_enabled_default = False
        if description.key == "awning":
            self._attr_device_class = CoverDeviceClass.AWNING
        self._remove_listener = None
        self._command_lock = asyncio.Lock()
        self._hold_task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._active_direction: str | None = None

        self._estimated_position = 0.0
        self._position_source = "time"
        self._last_pulse_total: float | None = None
        self._last_pulse_delta: float | None = None
        self._last_pulse_sync_error: float | None = None
        self._pulse_telemetry_available = False
        # When the controller state bit drops, the ESPHome sensor update can lag
        # by a second or two. Keep applying pulse deltas briefly after motion
        # stops so the final encoder pulses are not missed.
        self._pulse_settle_direction: str | None = None
        self._pulse_settle_until: float | None = None
        self._motion_direction: str | None = None
        self._motion_started_at: float | None = None
        self._last_position_update_at: float | None = None

        if not hasattr(self.coordinator, "cover_entities"):
            self.coordinator.cover_entities = {}
        self.coordinator.cover_entities[description.key] = self

    async def async_added_to_hass(self) -> None:
        """Restore last estimated position and subscribe to coordinator updates."""
        await self._async_restore_last_position()

        self._remove_listener = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        self._sync_motion_from_state()

    async def _async_restore_last_position(self) -> None:
        """Restore the last Home Assistant estimated cover position."""
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        restored_position = last_state.attributes.get("current_position")

        if restored_position is None:
            # Fallback for older states or unusual recorder data.
            if last_state.state == "open":
                restored_position = 100
            elif last_state.state == "closed":
                restored_position = 0

        if restored_position is None:
            return

        try:
            self._estimated_position = float(max(0, min(100, float(restored_position))))
        except (TypeError, ValueError):
            _LOGGER.debug(
                "Precision Plex %s could not restore position from state=%s attributes=%s",
                self._plex_description.key,
                last_state.state,
                dict(last_state.attributes),
            )
            return

        _LOGGER.debug(
            "Precision Plex %s restored estimated position to %.1f%%",
            self._plex_description.key,
            self._estimated_position,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Stop stream and unsubscribe."""
        await self._async_stop_hold_task()
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated BLE state."""
        self._sync_motion_from_state()
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.available and self.coordinator.state_word is not None

    @property
    def is_opening(self) -> bool:
        """Return true if cover is moving out."""
        return self._controller_is_out()

    @property
    def is_closing(self) -> bool:
        """Return true if cover is moving in."""
        return self._controller_is_in()

    @property
    def is_closed(self) -> bool | None:
        """Return closed if estimated fully retracted."""
        return self._estimated_position <= 0.5

    @property
    def current_cover_position(self) -> int:
        """Return estimated cover position."""
        self._update_estimated_position()
        return round(self._estimated_position)

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
        self._update_estimated_position()
        attrs = {
            "state_word": (
                f"0x{self.coordinator.state_word:04X}"
                if self.coordinator.state_word is not None
                else None
            ),
            "state_words": [f"0x{word:04X}" for word in self.coordinator.state_words],
            "raw_02bb": (
                self.coordinator.raw_state.hex(" ")
                if self.coordinator.raw_state is not None
                else None
            ),
            "command_mode": "press_and_hold_stream",
            "active_ha_direction": self._active_direction,
            "tracked_motion_direction": self._motion_direction,
            "estimated_position": round(self._estimated_position, 1),
            "position_source": self._position_source,
            "open_full_seconds": self._out_full_seconds(),
            "close_full_seconds": self._in_full_seconds(),
            "hold_interval_seconds": HOLD_INTERVAL_SECONDS,
            "jog_seconds": self._jog_seconds(),
            "native_cover_entity": False,
            "legacy_cover_entity": True,
            "replacement_entity": f"{self._plex_description.name}",
            "legacy_jog_buttons_available": True,
            "legacy_calibration_buttons_available": True,
        }
        if self._plex_description.key == "sofa_slide":
            pulse_travel_total = self._read_pulse_travel_total()
            pulse_sync_error = self._read_pulse_sync_error()
            attrs.update(
                {
                    "pulse_telemetry_available": pulse_travel_total is not None,
                    "pulse_travel_total": pulse_travel_total,
                    "pulse_last_delta": (
                        round(self._last_pulse_delta, 1)
                        if self._last_pulse_delta is not None
                        else None
                    ),
                    "pulse_full_travel": self._pulse_full_travel(),
                    "pulse_sync_error": pulse_sync_error,
                }
            )
        return attrs

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Extend/open until stopped or safety limit expires."""
        remaining_seconds = self._remaining_open_seconds()
        if remaining_seconds <= 0:
            self._estimated_position = 100.0
            self.async_write_ha_state()
            return

        await self._async_start_hold(
            direction="out",
            release_payload=self._plex_description.out_release_payload,
            hold_payload=self._plex_description.out_hold_payload,
            max_duration_seconds=remaining_seconds,
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Retract/close until stopped or safety limit expires."""
        remaining_seconds = self._remaining_close_seconds()
        if remaining_seconds <= 0:
            self._estimated_position = 0.0
            self.async_write_ha_state()
            return

        await self._async_start_hold(
            direction="in",
            release_payload=self._plex_description.in_release_payload,
            hold_payload=self._plex_description.in_hold_payload,
            max_duration_seconds=remaining_seconds,
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move cover toward a requested estimated position."""
        target = kwargs.get("position")
        if target is None:
            return

        target_position = float(max(0, min(100, target)))
        self._update_estimated_position()
        delta = target_position - self._estimated_position

        if abs(delta) < 1.0:
            self._estimated_position = target_position
            self.async_write_ha_state()
            return

        if delta > 0:
            seconds = (delta / 100.0) * self._out_full_seconds()
            await self._async_start_hold(
                direction="out",
                release_payload=self._plex_description.out_release_payload,
                hold_payload=self._plex_description.out_hold_payload,
                max_duration_seconds=seconds,
            )
        else:
            seconds = (abs(delta) / 100.0) * self._in_full_seconds()
            await self._async_start_hold(
                direction="in",
                release_payload=self._plex_description.in_release_payload,
                hold_payload=self._plex_description.in_hold_payload,
                max_duration_seconds=seconds,
            )


    async def async_jog(self, direction: str) -> None:
        """Manually jog the cover for the configured duration, ignoring estimated limits."""
        duration = self._jog_seconds()
        if direction == "out":
            await self._async_start_hold(
                direction="out",
                release_payload=self._plex_description.out_release_payload,
                hold_payload=self._plex_description.out_hold_payload,
                max_duration_seconds=duration,
            )
        elif direction == "in":
            await self._async_start_hold(
                direction="in",
                release_payload=self._plex_description.in_release_payload,
                hold_payload=self._plex_description.in_hold_payload,
                max_duration_seconds=duration,
            )
        else:
            raise ValueError(f"Unsupported Precision Plex jog direction: {direction}")

    async def async_reset_estimated_position(self, position: float) -> None:
        """Reset the estimated position without moving hardware."""
        async with self._command_lock:
            await self._async_stop_hold_task()
            self._motion_direction = None
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self._pulse_settle_direction = None
            self._pulse_settle_until = None
            self._estimated_position = max(0.0, min(100.0, float(position)))
            self._last_pulse_total = self._read_pulse_travel_total()
            self._last_pulse_delta = None
            self._position_source = "pulse" if self._last_pulse_total is not None else "time"
            self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop cover movement."""
        async with self._command_lock:
            self._update_estimated_position()

            controller_idle = not self._controller_is_out() and not self._controller_is_in()
            no_ha_stream = self._hold_task is None or self._hold_task.done()

            # If the cover is already idle and HA has no active hold stream,
            # do not send BLE release packets. This avoids waking/reconnecting
            # the BLE command path just because the user presses Stop after the
            # cover has already stopped.
            if controller_idle and no_ha_stream:
                self._motion_direction = None
                self._motion_started_at = None
                self._last_position_update_at = None
                self._active_direction = None
                self.async_write_ha_state()
                return

            await self._async_stop_hold_task()

            # Send both releases for safety. These are best-effort so a stale
            # BlueZ/Bleak connection cannot make the entity unavailable from
            # an exception in the websocket service call.
            for payload in (
                self._plex_description.out_release_payload,
                self._plex_description.in_release_payload,
            ):
                try:
                    await self.coordinator.async_write_command(payload)
                except Exception as err:
                    _LOGGER.warning(
                        "Precision Plex %s stop release failed safely: %r",
                        self._plex_description.key,
                        err,
                    )

            self._motion_direction = None
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self.async_write_ha_state()

    async def _async_start_hold(
        self,
        direction: str,
        release_payload: bytes,
        hold_payload: bytes,
        max_duration_seconds: float,
    ) -> None:
        """Start app-like hold stream for a direction."""
        async with self._command_lock:
            await self._async_stop_hold_task()

            self._update_estimated_position()
            self._start_tracking_motion(direction)

            self._stop_event = asyncio.Event()
            self._active_direction = direction
            self._hold_task = asyncio.create_task(
                self._async_hold_runner(
                    direction=direction,
                    release_payload=release_payload,
                    hold_payload=hold_payload,
                    stop_event=self._stop_event,
                    max_duration_seconds=max_duration_seconds,
                )
            )
            self.async_write_ha_state()

    async def _async_hold_runner(
        self,
        direction: str,
        release_payload: bytes,
        hold_payload: bytes,
        stop_event: asyncio.Event,
        max_duration_seconds: float,
    ) -> None:
        """Run hold stream and clean up when complete."""
        completed_by_timeout = False
        try:
            await self.coordinator.async_write_hold_stream(
                release_payload=release_payload,
                hold_payload=hold_payload,
                stop_event=stop_event,
                interval_seconds=HOLD_INTERVAL_SECONDS,
                max_duration_seconds=max_duration_seconds,
            )
            completed_by_timeout = not stop_event.is_set()
        except Exception as err:
            # The coordinator should already suppress BLE failures, but keep this
            # guard so a background task never leaks an exception to HA.
            _LOGGER.warning(
                "Precision Plex %s hold task ended safely after error: %r",
                self._plex_description.key,
                err,
            )
        finally:
            self._update_estimated_position()

            # If the task ended because its timer expired, snap to the expected
            # endpoint only when the command was a full open/full close.
            if completed_by_timeout:
                if direction == "out" and max_duration_seconds >= self._remaining_open_seconds() - 0.25:
                    self._estimated_position = 100.0
                elif direction == "in" and max_duration_seconds >= self._remaining_close_seconds() - 0.25:
                    self._estimated_position = 0.0

            self._motion_direction = None
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self._hold_task = None
            self._stop_event = None
            self.async_write_ha_state()

    async def _async_stop_hold_task(self) -> None:
        """Signal any active hold stream to stop without letting it wedge HA."""
        task = self._hold_task
        event = self._stop_event

        if event is not None:
            event.set()

        if task is not None and not task.done():
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "Precision Plex %s hold task did not stop promptly; cancelling",
                    self._plex_description.key,
                )
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    _LOGGER.warning(
                        "Precision Plex %s cancelled hold task ended safely: %r",
                        self._plex_description.key,
                        err,
                    )
            except Exception as err:
                _LOGGER.warning(
                    "Precision Plex %s hold task ended safely during stop: %r",
                    self._plex_description.key,
                    err,
                )

        self._hold_task = None
        self._stop_event = None
        self._active_direction = None

    def _controller_is_out(self) -> bool:
        """Return whether controller reports cover moving out."""
        desc = STATE_BITS[self._plex_description.out_state_key]
        return bool(
            self.coordinator.is_bit_on(
                desc["bit"],
                desc.get("word_index", 0),
            )
        )


    def _controller_is_in(self) -> bool:
        """Return whether controller reports cover moving in."""
        desc = STATE_BITS[self._plex_description.in_state_key]
        return bool(
            self.coordinator.is_bit_on(
                desc["bit"],
                desc.get("word_index", 0),
            )
        )


    def _sync_motion_from_state(self) -> None:
        """Track position from live state bits, including wall-panel movement."""
        controller_direction: str | None = None
        if self._controller_is_out():
            controller_direction = "out"
        elif self._controller_is_in():
            controller_direction = "in"

        if controller_direction == self._motion_direction:
            self._update_estimated_position()
            return

        # Direction changed or motion stopped.
        self._update_estimated_position()

        if controller_direction is None:
            if self._motion_direction is not None and self._plex_description.key == "sofa_slide":
                self._pulse_settle_direction = self._motion_direction
                self._pulse_settle_until = time.monotonic() + 2.5
            self._motion_direction = None
            self._motion_started_at = None
            self._last_position_update_at = None
            self._clamp_position()
            return

        self._start_tracking_motion(controller_direction)

    def _start_tracking_motion(self, direction: str) -> None:
        """Begin position tracking for a movement direction."""
        now = time.monotonic()
        self._motion_direction = direction
        self._pulse_settle_direction = None
        self._pulse_settle_until = None
        self._motion_started_at = now
        self._last_position_update_at = now
        self._last_pulse_total = self._read_pulse_travel_total()
        self._last_pulse_delta = None

    def _update_estimated_position(self) -> None:
        """Update estimated position using pulse telemetry when available.

        The original time-based estimator remains the fallback. For the Sofa
        Slide, an optional ESPHome telemetry node can publish cumulative
        Schwintek/SlimRack motor pulse counts. When that telemetry is present,
        the Precision Plex direction tracker supplies direction and pulse deltas
        supply distance moved.
        """
        now = time.monotonic()

        if self._motion_direction is None:
            if (
                self._pulse_settle_direction is not None
                and self._pulse_settle_until is not None
                and now <= self._pulse_settle_until
            ):
                if self._update_position_from_pulses(self._pulse_settle_direction):
                    self._clamp_position()
                return
            self._pulse_settle_direction = None
            self._pulse_settle_until = None
            return

        if self._last_position_update_at is None:
            return

        elapsed = max(0.0, now - self._last_position_update_at)
        self._last_position_update_at = now

        if elapsed <= 0:
            return

        if self._update_position_from_pulses(self._motion_direction):
            self._clamp_position()
            return

        self._position_source = "time"
        if self._motion_direction == "out":
            self._estimated_position += (
                elapsed / self._out_full_seconds()
            ) * 100.0
        elif self._motion_direction == "in":
            self._estimated_position -= (
                elapsed / self._in_full_seconds()
            ) * 100.0

        self._clamp_position()

    def _update_position_from_pulses(self, direction: str | None = None) -> bool:
        """Update position from optional Sofa Slide ESPHome pulse telemetry."""
        if self._plex_description.key != "sofa_slide":
            self._pulse_telemetry_available = False
            return False

        current_total = self._read_pulse_travel_total()
        if current_total is None:
            self._pulse_telemetry_available = False
            return False

        self._pulse_telemetry_available = True
        self._last_pulse_sync_error = self._read_pulse_sync_error()

        if self._last_pulse_total is None:
            self._last_pulse_total = current_total
            self._position_source = "pulse"
            return True

        delta = current_total - self._last_pulse_total

        # ESPHome pulse counters reset to zero on ESP reboot/reflash. Re-baseline
        # and skip this update rather than applying a large negative jump.
        if delta < 0:
            _LOGGER.debug(
                "Precision Plex %s pulse counter reset detected: previous=%.1f current=%.1f",
                self._plex_description.key,
                self._last_pulse_total,
                current_total,
            )
            self._last_pulse_total = current_total
            self._last_pulse_delta = None
            self._position_source = "pulse"
            return True

        self._last_pulse_total = current_total
        self._last_pulse_delta = delta

        if delta <= 0:
            self._position_source = "pulse"
            return True

        percent_delta = (delta / self._pulse_full_travel()) * 100.0
        movement_direction = direction or self._motion_direction
        if movement_direction == "out":
            self._estimated_position += percent_delta
        elif movement_direction == "in":
            self._estimated_position -= percent_delta
        else:
            return False

        self._position_source = "pulse"
        return True

    def _read_pulse_travel_total(self) -> float | None:
        """Return cumulative Sofa Slide travel pulses from ESPHome, if present."""
        if self._plex_description.key != "sofa_slide":
            return None
        return self._read_float_state("travel_pulses")

    def _read_pulse_sync_error(self) -> float | None:
        """Return Sofa Slide motor sync error from ESPHome, if present."""
        if self._plex_description.key != "sofa_slide":
            return None
        return self._read_float_state("sync_error")

    def _read_float_state(self, telemetry_key: str) -> float | None:
        """Read a numeric Home Assistant state by candidate entity IDs or friendly name."""
        state = self._find_telemetry_state(telemetry_key)
        if state is None:
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _find_telemetry_state(self, telemetry_key: str) -> State | None:
        """Find an optional ESPHome telemetry entity for this cover."""
        if self.hass is None:
            return None

        for entity_id in SOFA_SLIDE_TELEMETRY_ENTITY_CANDIDATES.get(telemetry_key, ()):
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in ("unknown", "unavailable"):
                return state

        friendly_name = SOFA_SLIDE_TELEMETRY_FRIENDLY_NAMES.get(telemetry_key)
        if friendly_name is None:
            return None

        for state in self.hass.states.async_all():
            if (
                state.attributes.get("friendly_name") == friendly_name
                and state.state not in ("unknown", "unavailable")
            ):
                return state

        return None

    def _pulse_full_travel(self) -> float:
        """Return configured full-travel pulse count for the Sofa Slide."""
        return float(
            getattr(self.coordinator, "runtime_settings", {}).get(
                "sofa_slide_full_travel_pulses",
                SOFA_SLIDE_DEFAULT_FULL_TRAVEL_PULSES,
            )
        )


    def _out_full_seconds(self) -> float:
        """Return current configured full open/extend travel time."""
        return float(
            getattr(self.coordinator, "runtime_settings", {}).get(
                self._plex_description.out_seconds_setting_key,
                self._plex_description.out_full_seconds,
            )
        )

    def _in_full_seconds(self) -> float:
        """Return current configured full close/retract travel time."""
        return float(
            getattr(self.coordinator, "runtime_settings", {}).get(
                self._plex_description.in_seconds_setting_key,
                self._plex_description.in_full_seconds,
            )
        )

    def _jog_seconds(self) -> float:
        """Return current configured jog duration."""
        return float(
            getattr(self.coordinator, "runtime_settings", {}).get(
                self._plex_description.jog_seconds_setting_key,
                2.0 if self._plex_description.key == "awning" else 5.0,
            )
        )

    def _remaining_open_seconds(self) -> float:
        """Return remaining estimated seconds to fully open."""
        self._update_estimated_position()
        return max(
            0.0,
            ((100.0 - self._estimated_position) / 100.0)
            * self._out_full_seconds(),
        )

    def _remaining_close_seconds(self) -> float:
        """Return remaining estimated seconds to fully close."""
        self._update_estimated_position()
        return max(
            0.0,
            (self._estimated_position / 100.0)
            * self._in_full_seconds(),
        )

    def _clamp_position(self) -> None:
        """Clamp estimated position and snap pulse telemetry near endpoints."""
        self._estimated_position = max(0.0, min(100.0, self._estimated_position))

        # Pulse telemetry is precise, but real RV slides often settle a fraction
        # of a percent short of the learned end stop. Snap the Sofa Slide to the
        # visible endpoints so Home Assistant shows fully closed/open when the
        # pulse-derived position lands within the calibrated tolerance.
        if (
            self._plex_description.key == "sofa_slide"
            and self._position_source == "pulse"
        ):
            if self._estimated_position <= SOFA_SLIDE_ENDPOINT_SNAP_PERCENT:
                self._estimated_position = 0.0
            elif self._estimated_position >= (100.0 - SOFA_SLIDE_ENDPOINT_SNAP_PERCENT):
                self._estimated_position = 100.0




class PrecisionPlexCleanNativeCover(PrecisionPlexTimedCover):
    """Clean native cover entity exposed alongside the original legacy cover.

    The original cover unique IDs are intentionally preserved by
    PrecisionPlexTimedCover. This class creates new, cleanly named entities for
    Home Assistant dashboards and HomeKit without forcing a migration.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrecisionPlexStateCoordinator,
        entry: ConfigEntry,
        description: PrecisionPlexCoverDescription,
    ) -> None:
        """Initialize the clean native cover."""
        super().__init__(coordinator, entry, description)
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.address}_{description.key}_native_cover"
        self._attr_entity_registry_enabled_default = True
        self._attr_translation_key = None
        if description.key != "awning":
            # RV slides do not have a perfect Home Assistant device class.
            # Leaving them generic avoids the misleading window icon.
            self._attr_device_class = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "native_cover_entity": True,
                "clean_homekit_entity": True,
                "legacy_cover_entity_preserved": True,
            }
        )
        return attrs
