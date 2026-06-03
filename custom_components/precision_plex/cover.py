"""Cover platform for Precision Plex awning and slide controls."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
        name="Awning",
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
        name="Bed Slide",
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
    async_add_entities(
        PrecisionPlexTimedCover(coordinator, entry, description)
        for description in COVERS
    )


class PrecisionPlexTimedCover(CoverEntity, RestoreEntity):
    """Precision Plex cover using app-like press-and-hold BLE packets."""

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
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.address}_{description.key}_cover"
        self._remove_listener = None
        self._command_lock = asyncio.Lock()
        self._hold_task: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None
        self._active_direction: str | None = None

        self._estimated_position = 0.0
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
            "name": self.entry.title,
            "manufacturer": "Precision Circuits",
            "model": "Precision Plex Wireless TP Monitor",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        self._update_estimated_position()
        return {
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
            "open_full_seconds": self._out_full_seconds(),
            "close_full_seconds": self._in_full_seconds(),
            "hold_interval_seconds": HOLD_INTERVAL_SECONDS,
            "jog_seconds": self._jog_seconds(),
        }

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
            self._estimated_position = max(0.0, min(100.0, float(position)))
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
        self._motion_started_at = now
        self._last_position_update_at = now

    def _update_estimated_position(self) -> None:
        """Update estimated position using elapsed motion time."""
        if self._motion_direction is None or self._last_position_update_at is None:
            return

        now = time.monotonic()
        elapsed = max(0.0, now - self._last_position_update_at)
        self._last_position_update_at = now

        if elapsed <= 0:
            return

        if self._motion_direction == "out":
            self._estimated_position += (
                elapsed / self._out_full_seconds()
            ) * 100.0
        elif self._motion_direction == "in":
            self._estimated_position -= (
                elapsed / self._in_full_seconds()
            ) * 100.0

        self._clamp_position()


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
        """Clamp estimated position."""
        self._estimated_position = max(0.0, min(100.0, self._estimated_position))
