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

AWNING_CURRENT_RUNNING_THRESHOLD_AMPS = 2.0
AWNING_CURRENT_ZERO_THRESHOLD_AMPS = 1.0
AWNING_CURRENT_ZERO_CONFIRM_SECONDS = 0.5
AWNING_SMART_EXTRA_TIMEOUT_SECONDS = 5.0

SLIDE_ENDPOINT_SNAP_PERCENT = 2.0

# Quadrature-only motion verification: if a supported slide is commanded
# but encoder travel does not change shortly after the hold stream begins,
# abort the stream. This prevents spamming BLE commands when a downstream
# interlock, such as ignition lockout, accepts commands but prevents motion.
MOTION_VERIFICATION_SECONDS = 3.0
MOTION_VERIFICATION_MIN_DELTA_COUNTS = 25.0

SLIDE_PULSE_TELEMETRY: dict[str, dict[str, Any]] = {
    "bed_slide": {
        "default_full_travel_pulses": 21727.0,
        "full_travel_setting_key": "bed_slide_full_travel_pulses",
        "friendly_names": {
            "travel_pulses": "Bed Slide Quadrature Travel",
            "sync_error": "Bed Slide Quadrature Sync Error",
            "moving": "Bed Slide Moving",
        },
        "entity_candidates": {
            "travel_pulses": (
                "sensor.bed_slide_quadrature_travel",
                "sensor.lippert_bed_slide_controller_bed_slide_quadrature_travel",
            ),
            "sync_error": (
                "sensor.bed_slide_quadrature_sync_error",
                "sensor.lippert_bed_slide_controller_bed_slide_quadrature_sync_error",
            ),
            "moving": ("binary_sensor.bed_slide_moving",),
        },
    },
    "sofa_slide": {
        "default_full_travel_pulses": 21503.0,
        "full_travel_setting_key": "sofa_slide_full_travel_pulses",
        "friendly_names": {
            "travel_pulses": "Sofa Slide Quadrature Travel",
            "sync_error": "Sofa Slide Quadrature Sync Error",
            "moving": "Sofa Slide Moving",
        },
        "entity_candidates": {
            "travel_pulses": (
                "sensor.sofa_slide_quadrature_travel",
                "sensor.lippert_sofa_slide_controller_sofa_slide_quadrature_travel",
            ),
            "sync_error": (
                "sensor.sofa_slide_quadrature_sync_error",
                "sensor.lippert_sofa_slide_controller_sofa_slide_quadrature_sync_error",
            ),
            "moving": ("binary_sensor.sofa_slide_moving",),
        },
    },
    "wardrobe_slide": {
        "default_full_travel_pulses": 13873.0,
        "full_travel_setting_key": "wardrobe_slide_full_travel_pulses",
        "friendly_names": {
            "travel_pulses": "Wardrobe Slide Quadrature Travel",
            "sync_error": "Wardrobe Slide Quadrature Sync Error",
            "moving": "Wardrobe Slide Moving",
        },
        "entity_candidates": {
            "travel_pulses": (
                "sensor.wardrobe_slide_quadrature_travel",
                "sensor.lippert_wardrobe_slide_controller_wardrobe_slide_quadrature_travel",
            ),
            "sync_error": (
                "sensor.wardrobe_slide_quadrature_sync_error",
                "sensor.lippert_wardrobe_slide_controller_wardrobe_slide_quadrature_sync_error",
            ),
            "moving": ("binary_sensor.wardrobe_slide_moving",),
        },
    },
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
        self._last_quadrature_total: float | None = None
        self._last_quadrature_delta: float | None = None
        self._last_quadrature_sync_error: float | None = None
        self._quadrature_available = False
        # When the controller state bit drops, the ESPHome sensor update can lag
        # by a second or two. Keep applying pulse deltas briefly after motion
        # stops so the final encoder pulses are not missed.
        self._pulse_settle_direction: str | None = None
        self._pulse_settle_until: float | None = None
        self._motion_direction: str | None = None
        self._motion_started_at: float | None = None
        self._last_position_update_at: float | None = None
        self._motion_verification_failed = False
        self._motion_verification_reason: str | None = None
        self._motion_verification_failed_at: float | None = None

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
        out_desc = STATE_BITS[self._plex_description.out_state_key]
        in_desc = STATE_BITS[self._plex_description.in_state_key]
        return (
            self.coordinator.available
            and self.coordinator.is_bit_on(out_desc["bit"], out_desc.get("word_index", 0)) is not None
            and self.coordinator.is_bit_on(in_desc["bit"], in_desc.get("word_index", 0)) is not None
        )

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
            "telemetry_source": self.coordinator.telemetry_source_for(
                self._plex_description.out_state_key
            ),
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
            "motion_verification_failed": self._motion_verification_failed,
            "motion_verification_reason": self._motion_verification_reason,
            "motion_verification_failed_age_seconds": (
                round(time.time() - self._motion_verification_failed_at, 1)
                if self._motion_verification_failed_at is not None
                else None
            ),
            "native_cover_entity": False,
            "legacy_cover_entity": True,
            "replacement_entity": f"{self._plex_description.name}",
            "legacy_jog_buttons_available": True,
            "legacy_calibration_buttons_available": True,
        }
        if self._is_awning():
            attrs.update(
                {
                    "awning_smart_available": self._smart_awning_available(),
                    "awning_control_method": (
                        "Smart Current Sense" if self._smart_awning_available() else "Timed"
                    ),
                    "awning_motor_current": self._read_awning_current(),
                }
            )
        if self._supports_pulse_telemetry():
            quadrature_travel_total = self._read_quadrature_travel_total()
            quadrature_sync_error = self._read_quadrature_sync_error()
            attrs.update(
                {
                    "quadrature_available": quadrature_travel_total is not None,
                    "quadrature_travel_total": quadrature_travel_total,
                    "quadrature_last_delta": (
                        round(self._last_quadrature_delta, 1)
                        if self._last_quadrature_delta is not None
                        else None
                    ),
                    "quadrature_full_travel": self._quadrature_full_travel(),
                    "quadrature_sync_error": quadrature_sync_error,
                }
            )
        return attrs

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Extend/open until stopped or safety limit expires."""
        if self._is_awning() and self._smart_awning_available():
            await self._async_start_smart_awning_open()
            return

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
        if self._is_awning() and self._smart_awning_available():
            await self._async_start_smart_awning_close()
            return

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

        # Some Home Assistant UI surfaces and HomeKit bridges send full open/close
        # requests as SET_POSITION 100/0 instead of native open_cover/close_cover.
        # Route those full-travel awning requests through the same smart current-
        # sense handlers so the Carefree-style flip and retract-seat detection are
        # used consistently everywhere.  Intermediate positions intentionally keep
        # the existing time-based behavior because current sensing only identifies
        # the physical endpoints, not an arbitrary percentage along the travel.
        if self._is_awning() and self._smart_awning_available():
            if target_position >= 99.0:
                await self._async_start_smart_awning_open()
                return
            if target_position <= 1.0:
                await self._async_start_smart_awning_close()
                return

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
            self._last_quadrature_total = self._read_quadrature_travel_total()
            self._last_quadrature_delta = None
            self._position_source = "quadrature" if self._last_quadrature_total is not None else "time"
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
                self._set_provisional_motion(None)
                self._motion_direction = None
                self._motion_started_at = None
                self._last_position_update_at = None
                self._active_direction = None
                self.async_write_ha_state()
                return

            await self._async_stop_hold_task()
            self._set_provisional_motion(None)

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


    async def _async_start_smart_awning_open(self) -> None:
        """Start smart awning extend with current-sensed arm lock and fabric flip."""
        async with self._command_lock:
            _LOGGER.info(
                "Precision Plex smart awning open requested; current=%.2fA position=%.1f%%",
                self._read_awning_current() or 0.0,
                self._estimated_position,
            )
            await self._async_stop_hold_task()

            self._update_estimated_position()
            self._start_tracking_motion("out")
            self._set_provisional_motion("out")

            self._stop_event = asyncio.Event()
            self._active_direction = "out"
            self._hold_task = asyncio.create_task(
                self._async_smart_awning_open_runner(self._stop_event)
            )
            self.async_write_ha_state()

    async def _async_start_smart_awning_close(self) -> None:
        """Start smart awning retract and mark closed when factory cutout drops current."""
        async with self._command_lock:
            _LOGGER.info(
                "Precision Plex smart awning close requested; current=%.2fA position=%.1f%%",
                self._read_awning_current() or 0.0,
                self._estimated_position,
            )
            await self._async_stop_hold_task()

            self._update_estimated_position()
            self._start_tracking_motion("in")
            self._set_provisional_motion("in")

            self._stop_event = asyncio.Event()
            self._active_direction = "in"
            self._hold_task = asyncio.create_task(
                self._async_smart_awning_close_runner(self._stop_event)
            )
            self.async_write_ha_state()

    async def _async_smart_awning_open_runner(self, stop_event: asyncio.Event) -> None:
        """Run smart awning open sequence.

        Sequence:
        extend -> detect arm-lock current -> overrun briefly -> stop ->
        retract briefly to tighten fabric -> stop.
        """
        detected_arm_lock = False
        stream_task: asyncio.Task | None = None
        try:
            max_duration = self._out_full_seconds() + AWNING_SMART_EXTRA_TIMEOUT_SECONDS
            stream_task = asyncio.create_task(
                self.coordinator.async_write_hold_stream(
                    release_payload=self._plex_description.out_release_payload,
                    hold_payload=self._plex_description.out_hold_payload,
                    stop_event=stop_event,
                    interval_seconds=HOLD_INTERVAL_SECONDS,
                    max_duration_seconds=max_duration,
                )
            )

            ignore_seconds = self._runtime_setting("awning_current_ignore_seconds", 2.0)
            threshold = self._runtime_setting("awning_arm_lock_threshold", 6.0)
            confirm_seconds = self._runtime_setting("awning_current_confirm_milliseconds", 300.0) / 1000.0
            overrun_seconds = self._runtime_setting("awning_extend_overrun_milliseconds", 100.0) / 1000.0
            flip_seconds = self._runtime_setting("awning_fabric_tighten_milliseconds", 4000.0) / 1000.0

            _LOGGER.info(
                "Precision Plex smart awning open runner started; threshold=%.2fA ignore=%.2fs confirm=%.2fs safety_max=%.2fs overrun=%.2fs flip=%.2fs current=%.2fA",
                threshold,
                ignore_seconds,
                confirm_seconds,
                max_duration,
                overrun_seconds,
                flip_seconds,
                self._read_awning_current() or 0.0,
            )

            detected_arm_lock = await self._async_wait_for_awning_current_above(
                threshold=threshold,
                confirm_seconds=confirm_seconds,
                ignore_seconds=ignore_seconds,
                stop_event=stop_event,
                max_wait_seconds=max_duration,
            )

            if detected_arm_lock and not stop_event.is_set():
                _LOGGER.info(
                    "Precision Plex smart awning arm lock detected at %.2fA; overrun %.2fs then flip %.2fs",
                    self._read_awning_current() or 0.0,
                    overrun_seconds,
                    flip_seconds,
                )
                if overrun_seconds > 0:
                    _LOGGER.info("Precision Plex smart awning open overrun started for %.2fs", overrun_seconds)
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=overrun_seconds)
                    except asyncio.TimeoutError:
                        pass
                    _LOGGER.info("Precision Plex smart awning open overrun complete; stopping extend stream")


            stop_event.set()

            if stream_task is not None:
                await stream_task
                _LOGGER.info("Precision Plex smart awning extend stream stopped; detected_arm_lock=%s current=%.2fA", detected_arm_lock, self._read_awning_current() or 0.0)

            # Send one explicit extend release after the hold stream exits. This
            # mirrors the manual Stop behavior and makes sure the Precision Plex
            # controller is not left latched before the fabric-tighten retract.
            try:
                await self.coordinator.async_write_command(self._plex_description.out_release_payload)
            except Exception as err:
                _LOGGER.debug("Precision Plex smart awning open extra extend release failed safely: %r", err)

            if detected_arm_lock and flip_seconds > 0 and not self._stop_event_cancelled_externally():
                _LOGGER.info("Precision Plex smart awning Carefree flip started for %.2fs", flip_seconds)
                self._active_direction = "in"
                self._start_tracking_motion("in")
                self._set_provisional_motion("in")
                flip_stop_event = asyncio.Event()
                try:
                    await self.coordinator.async_write_hold_stream(
                        release_payload=self._plex_description.in_release_payload,
                        hold_payload=self._plex_description.in_hold_payload,
                        stop_event=flip_stop_event,
                        interval_seconds=HOLD_INTERVAL_SECONDS,
                        max_duration_seconds=flip_seconds,
                    )
                finally:
                    flip_stop_event.set()
                _LOGGER.info("Precision Plex smart awning Carefree flip complete; current=%.2fA", self._read_awning_current() or 0.0)

            if detected_arm_lock:
                self._estimated_position = 100.0
                self._position_source = "current_sense"
                _LOGGER.info("Precision Plex smart awning open complete; position forced to 100%%")
            else:
                _LOGGER.warning("Precision Plex smart awning open ended without arm-lock detection; current=%.2fA", self._read_awning_current() or 0.0)
        except Exception as err:
            _LOGGER.warning(
                "Precision Plex smart awning open ended safely after error: %r",
                err,
            )
        finally:
            if stream_task is not None and not stream_task.done():
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    _LOGGER.debug("Precision Plex smart awning stream cleanup failed safely: %r", err)

            self._motion_direction = None
            self._set_provisional_motion(None)
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self._hold_task = None
            self._stop_event = None
            self.async_write_ha_state()

    async def _async_smart_awning_close_runner(self, stop_event: asyncio.Event) -> None:
        """Run smart awning close sequence using high-current seat detection.

        The Solera/Precision Plex retract path does not reliably drop current to
        zero while the retract command is still being streamed.  In testing, the
        ESPHome Retract End Event stayed ON until the user released the button.
        Therefore the reliable closed signal is the sustained high-current seat
        event, not drop-to-zero.
        """
        stream_task: asyncio.Task | None = None
        detected_retract_seat = False
        saw_running_current = False
        try:
            # In smart mode this is only a safety guardrail.  Normal stopping is
            # driven by current, not by the old timed close estimate.
            max_duration = max(self._in_full_seconds() + AWNING_SMART_EXTRA_TIMEOUT_SECONDS, 60.0)
            stream_task = asyncio.create_task(
                self.coordinator.async_write_hold_stream(
                    release_payload=self._plex_description.in_release_payload,
                    hold_payload=self._plex_description.in_hold_payload,
                    stop_event=stop_event,
                    interval_seconds=HOLD_INTERVAL_SECONDS,
                    max_duration_seconds=max_duration,
                )
            )

            ignore_seconds = self._runtime_setting("awning_current_ignore_seconds", 2.0)
            threshold = self._runtime_setting("awning_retract_end_threshold", 11.0)
            confirm_seconds = self._runtime_setting("awning_current_confirm_milliseconds", 300.0) / 1000.0
            start_time = time.monotonic()
            above_since: float | None = None
            _LOGGER.info(
                "Precision Plex smart awning close runner started; threshold=%.2fA ignore=%.2fs confirm=%.2fs max=%.2fs current=%.2fA",
                threshold,
                ignore_seconds,
                confirm_seconds,
                max_duration,
                self._read_awning_current() or 0.0,
            )

            while not stop_event.is_set():
                elapsed = time.monotonic() - start_time
                if elapsed >= max_duration:
                    break

                current = self._read_awning_current()
                if current is not None and elapsed >= ignore_seconds:
                    if current >= AWNING_CURRENT_RUNNING_THRESHOLD_AMPS:
                        saw_running_current = True

                    if current >= threshold:
                        if above_since is None:
                            above_since = time.monotonic()
                        elif (time.monotonic() - above_since) >= confirm_seconds:
                            detected_retract_seat = True
                            _LOGGER.info(
                                "Precision Plex smart awning close detected retract seat at %.2fA",
                                current,
                            )
                            break
                    else:
                        above_since = None

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass

            if not detected_retract_seat:
                _LOGGER.warning(
                    "Precision Plex smart awning close reached safety timeout before retract seat current; stopping stream and setting closed as a safety fallback"
                )

            stop_event.set()

            if stream_task is not None:
                await stream_task

            # Always send one additional release after the stream exits.  This is
            # intentionally redundant and mirrors the manual Stop action that
            # clears the Precision Plex active/moving bit if the stream exit
            # release was missed or the controller stayed latched.
            try:
                await self.coordinator.async_write_command(self._plex_description.in_release_payload)
            except Exception as err:
                _LOGGER.debug("Precision Plex smart awning close extra release failed safely: %r", err)

            if detected_retract_seat or saw_running_current:
                self._estimated_position = 0.0
                self._position_source = "current_sense" if detected_retract_seat else "current_sense_timeout"
        except Exception as err:
            _LOGGER.warning(
                "Precision Plex smart awning close ended safely after error: %r",
                err,
            )
        finally:
            if stream_task is not None and not stream_task.done():
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    _LOGGER.debug("Precision Plex smart awning close stream cleanup failed safely: %r", err)

            self._motion_direction = None
            self._set_provisional_motion(None)
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self._hold_task = None
            self._stop_event = None
            self.async_write_ha_state()

    def _stop_event_cancelled_externally(self) -> bool:
        """Return whether the current stop event was set by a user stop.

        The smart runner sets its own stop event after detection. This helper is
        intentionally conservative for now; the explicit Stop button still works
        because _async_stop_hold_task cancels/waits the runner task.
        """
        return False

    async def _async_wait_for_awning_current_above(
        self,
        threshold: float,
        confirm_seconds: float,
        ignore_seconds: float,
        stop_event: asyncio.Event,
        max_wait_seconds: float,
    ) -> bool:
        """Wait for awning arm-lock current.

        The ACS758 arm-lock signature can be very short.  Polling the current
        sensor is not always enough because Home Assistant may publish a brief
        current spike or ESPHome extend-event pulse between polling intervals.
        Listen for state_changed events too, and latch the first qualifying
        sample/event after the ignore window.
        """
        start_time = time.monotonic()
        latched = asyncio.Event()
        current_state = self._find_awning_current_state()
        current_entity_id = current_state.entity_id if current_state is not None else None
        _LOGGER.info(
            "Precision Plex smart awning waiting for arm-lock current; threshold=%.2fA ignore=%.2fs confirm=%.2fs current_entity=%s current=%.2fA",
            threshold,
            ignore_seconds,
            confirm_seconds,
            current_entity_id,
            self._read_awning_current() or 0.0,
        )

        @callback
        def _state_changed(event) -> None:
            if latched.is_set() or stop_event.is_set():
                return
            if (time.monotonic() - start_time) < ignore_seconds:
                return

            entity_id = str(event.data.get("entity_id", ""))
            new_state = event.data.get("new_state")
            if new_state is None:
                return

            # ESPHome template binary sensor: this is the cleanest arm-lock
            # pulse when it is available.  It may be too brief for polling, so
            # latch it from the event bus.
            if entity_id.endswith("_awning_extend_event") and new_state.state == "on":
                _LOGGER.info("Precision Plex smart awning latched extend event from %s", entity_id)
                latched.set()
                return

            # Also latch directly from the raw current sensor update.  This
            # protects us if the binary event is renamed/disabled but current
            # still crosses the configured threshold.
            if (
                entity_id == current_entity_id
                or entity_id.endswith("_awning_motor_current")
                or entity_id.endswith(".awning_motor_current")
            ):
                try:
                    current = float(new_state.state)
                except (TypeError, ValueError):
                    return
                if current >= threshold:
                    _LOGGER.info(
                        "Precision Plex smart awning latched current %.2fA from %s",
                        current,
                        entity_id,
                    )
                    latched.set()

        unsubscribe = self.hass.bus.async_listen("state_changed", _state_changed)
        try:
            while not stop_event.is_set():
                elapsed = time.monotonic() - start_time
                if elapsed >= max_wait_seconds:
                    return False

                if latched.is_set():
                    return True

                current = self._read_awning_current()
                if elapsed >= ignore_seconds and current is not None and current >= threshold:
                    _LOGGER.info("Precision Plex smart awning latched polled current %.2fA", current)
                    return True

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.05)
                except asyncio.TimeoutError:
                    pass

            return False
        finally:
            unsubscribe()


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
            self._set_provisional_motion(direction)

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
        verification_task: asyncio.Task | None = None
        try:
            verification_task = asyncio.create_task(
                self._async_verify_quadrature_motion(
                    stop_event=stop_event,
                    max_duration_seconds=max_duration_seconds,
                )
            )

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
            if verification_task is not None and not verification_task.done():
                verification_task.cancel()
                try:
                    await verification_task
                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    _LOGGER.debug(
                        "Precision Plex %s motion verification task ended safely: %r",
                        self._plex_description.key,
                        err,
                    )

            self._update_estimated_position()

            # If the task ended because its timer expired, snap to the expected
            # endpoint only when the command was a full open/full close.
            if completed_by_timeout:
                if direction == "out" and max_duration_seconds >= self._remaining_open_seconds() - 0.25:
                    self._estimated_position = 100.0
                elif direction == "in" and max_duration_seconds >= self._remaining_close_seconds() - 0.25:
                    self._estimated_position = 0.0

            self._motion_direction = None
            self._set_provisional_motion(None)
            self._motion_started_at = None
            self._last_position_update_at = None
            self._active_direction = None
            self._hold_task = None
            self._stop_event = None
            self.async_write_ha_state()

    async def _async_verify_quadrature_motion(
        self,
        stop_event: asyncio.Event,
        max_duration_seconds: float,
    ) -> None:
        """Abort quadrature slide commands when no encoder movement is detected.

        This is intentionally quadrature-only. Timing-only covers do not have a
        reliable movement feedback signal, so they retain the legacy behavior of
        running the hold stream for the configured duration.
        """
        if not self._supports_pulse_telemetry():
            return

        if max_duration_seconds < MOTION_VERIFICATION_SECONDS:
            return

        start_total = self._read_quadrature_travel_total()
        if start_total is None:
            return

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=MOTION_VERIFICATION_SECONDS,
            )
            return
        except asyncio.TimeoutError:
            pass

        if stop_event.is_set():
            return

        current_total = self._read_quadrature_travel_total()
        if current_total is None:
            return

        delta = abs(current_total - start_total)
        if delta >= MOTION_VERIFICATION_MIN_DELTA_COUNTS:
            self._motion_verification_failed = False
            self._motion_verification_reason = None
            self._motion_verification_failed_at = None
            self.async_write_ha_state()
            return

        self._motion_verification_failed = True
        self._motion_verification_reason = "no_quadrature_movement"
        self._motion_verification_failed_at = time.time()

        _LOGGER.info(
            "Precision Plex %s command aborted: no quadrature movement detected "
            "after %.1f seconds (start=%.1f current=%.1f delta=%.1f)",
            self._plex_description.key,
            MOTION_VERIFICATION_SECONDS,
            start_total,
            current_total,
            delta,
        )

        stop_event.set()
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


    def _set_provisional_motion(self, direction: str | None) -> None:
        """Expose an HA command immediately while slow PID32 catches up."""
        self.coordinator.set_provisional_states(
            {
                self._plex_description.out_state_key: direction == "out",
                self._plex_description.in_state_key: direction == "in",
            }
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
            if self._motion_direction is not None and self._supports_pulse_telemetry():
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
        self._last_quadrature_total = self._read_quadrature_travel_total()
        self._last_quadrature_delta = None

    def _update_estimated_position(self) -> None:
        """Update estimated position using quadrature telemetry when available.

        The original time-based estimator remains the fallback. For supported
        slides, an optional ESPHome telemetry node publishes absolute
        Schwintek/SlimRack quadrature travel counts. When that telemetry is
        present, use the absolute travel count directly so startup, opening, and
        closing all report the same position source and position math.
        """
        now = time.monotonic()

        # Quadrature travel is an absolute position count. If it is available,
        # use it immediately, even when the slide is not currently moving. This
        # lets HA restarts restore the live encoder position without waiting for
        # the first motion event.
        if self._update_position_from_quadrature():
            self._clamp_position()
            return

        if self._motion_direction is None:
            self._pulse_settle_direction = None
            self._pulse_settle_until = None
            return

        if self._last_position_update_at is None:
            return

        elapsed = max(0.0, now - self._last_position_update_at)
        self._last_position_update_at = now

        if elapsed <= 0:
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

    def _update_position_from_quadrature(self) -> bool:
        """Update position from optional ESPHome quadrature telemetry."""
        if not self._supports_pulse_telemetry():
            self._quadrature_available = False
            return False

        current_total = self._read_quadrature_travel_total()
        if current_total is None:
            self._quadrature_available = False
            return False

        full_travel = self._quadrature_full_travel()
        if full_travel <= 0:
            self._quadrature_available = False
            return False

        self._quadrature_available = True
        self._last_quadrature_sync_error = self._read_quadrature_sync_error()

        if self._last_quadrature_total is not None:
            self._last_quadrature_delta = current_total - self._last_quadrature_total
            if abs(self._last_quadrature_delta) >= MOTION_VERIFICATION_MIN_DELTA_COUNTS:
                self._motion_verification_failed = False
                self._motion_verification_reason = None
                self._motion_verification_failed_at = None
        else:
            self._last_quadrature_delta = None

        self._last_quadrature_total = current_total
        self._estimated_position = max(
            0.0,
            min(100.0, (current_total / full_travel) * 100.0),
        )
        self._position_source = "quadrature"
        return True


    def _is_awning(self) -> bool:
        """Return whether this cover is the patio awning."""
        return self._plex_description.key == "awning"

    def _runtime_setting(self, key: str, default: float) -> float:
        """Return a numeric runtime setting."""
        try:
            return float(getattr(self.coordinator, "runtime_settings", {}).get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _smart_awning_available(self) -> bool:
        """Return whether the awning current telemetry sensor is available."""
        return self._read_awning_current() is not None

    def _read_awning_current(self) -> float | None:
        """Read absolute awning current from ESPHome if present."""
        state = self._find_awning_current_state()
        if state is None:
            return None
        try:
            value = abs(float(state.state))
        except (TypeError, ValueError):
            return None
        return value

    def _read_awning_motor_running(self) -> bool | None:
        """Read ESPHome awning motor-running binary sensor if present."""
        if self.hass is None:
            return None

        invalid_states = ("unknown", "unavailable")
        candidates = (
            "binary_sensor.lippert_awning_telemetry_awning_motor_running",
            "binary_sensor.awning_motor_running",
        )
        for entity_id in candidates:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in invalid_states:
                return state.state == "on"

        for state in self.hass.states.async_all():
            if state.state in invalid_states:
                continue
            entity_id = state.entity_id.lower()
            friendly = str(state.attributes.get("friendly_name", "")).lower()
            if (
                entity_id.endswith("_awning_motor_running")
                or friendly == "awning motor running"
                or friendly.endswith(" awning motor running")
            ):
                return state.state == "on"

        return None

    def _find_awning_current_state(self) -> State | None:
        """Find the ESPHome awning motor current sensor."""
        if self.hass is None:
            return None

        invalid_states = ("unknown", "unavailable")

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


    def _supports_pulse_telemetry(self) -> bool:
        """Return whether this cover has optional ESPHome pulse telemetry support."""
        return self._plex_description.key in SLIDE_PULSE_TELEMETRY

    def _telemetry_config(self) -> dict[str, Any] | None:
        """Return optional telemetry configuration for this cover."""
        return SLIDE_PULSE_TELEMETRY.get(self._plex_description.key)

    def _read_quadrature_travel_total(self) -> float | None:
        """Return cumulative slide travel pulses from ESPHome, if present."""
        if not self._supports_pulse_telemetry():
            return None
        return self._read_float_state("travel_pulses")

    def _read_quadrature_sync_error(self) -> float | None:
        """Return slide motor sync error from ESPHome, if present."""
        if not self._supports_pulse_telemetry():
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
        """Find an optional ESPHome telemetry entity for this cover.

        ESPHome entity IDs are affected by the device name, area, and HA's entity
        registry naming rules. The telemetry boxes therefore commonly create IDs
        such as:

            sensor.basement_lippert_wardrobe_slide_controller_wardrobe_slide_travel_pulses

        instead of the shorter candidate IDs. Prefer exact candidates first, then
        fall back to friendly-name and entity-id suffix matching.
        """
        if self.hass is None:
            return None

        config = self._telemetry_config()
        if config is None:
            return None

        invalid_states = ("unknown", "unavailable")

        entity_candidates = config.get("entity_candidates", {})
        for entity_id in entity_candidates.get(telemetry_key, ()):
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in invalid_states:
                return state

        friendly_names = config.get("friendly_names", {})
        friendly_name = friendly_names.get(telemetry_key)
        if friendly_name is None:
            return None

        # Friendly-name match, including HA/ESPHome generated prefixes like
        # "Lippert Wardrobe Slide Controller Wardrobe Slide Travel Pulses".
        for state in self.hass.states.async_all():
            if state.state in invalid_states:
                continue
            current_friendly_name = str(state.attributes.get("friendly_name", ""))
            if (
                current_friendly_name == friendly_name
                or current_friendly_name.endswith(friendly_name)
            ):
                return state

        # Entity-id suffix match. This handles area/device-prefixed ESPHome IDs.
        suffix = friendly_name.lower().replace(" ", "_")
        for state in self.hass.states.async_all():
            if state.state in invalid_states:
                continue
            if state.entity_id.endswith(suffix):
                return state

        # Last-resort contains match scoped to the slide key and telemetry key.
        slide_key = self._plex_description.key
        key_suffix = telemetry_key.lower()
        for state in self.hass.states.async_all():
            if state.state in invalid_states:
                continue
            entity_id = state.entity_id.lower()
            if slide_key in entity_id and key_suffix in entity_id:
                return state

        return None

    def _quadrature_full_travel(self) -> float:
        """Return configured full-travel pulse count for this slide."""
        config = self._telemetry_config() or {}
        setting_key = config.get("full_travel_setting_key")
        default_full_travel = float(config.get("default_full_travel_pulses", 1.0))
        if setting_key is None:
            return default_full_travel
        return float(
            getattr(self.coordinator, "runtime_settings", {}).get(
                setting_key,
                default_full_travel,
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
        # of a percent short of the learned end stop. Snap supported pulse slides
        # to visible endpoints so Home Assistant shows fully closed/open when the
        # pulse-derived position lands within the calibrated tolerance.
        if self._supports_pulse_telemetry() and self._position_source == "quadrature":
            if self._estimated_position <= SLIDE_ENDPOINT_SNAP_PERCENT:
                self._estimated_position = 0.0
            elif self._estimated_position >= (100.0 - SLIDE_ENDPOINT_SNAP_PERCENT):
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
