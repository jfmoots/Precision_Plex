"""Regression tests for LIN recovery, bridge selection, and cover fallback."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.exceptions import HomeAssistantError

from custom_components.precision_plex import coordinator, cover, lin_transport
from custom_components.precision_plex.motion import MotionEnd, MotionResult


def snapshot(bridge_id, *, uptime=20_000, reason="periodic_full", **values):
    return SimpleNamespace(
        data={
            "bridge_id": bridge_id,
            "payload": {
                "schema": 1,
                "uptime_ms": uptime,
                "snapshot_reason": reason,
                "bus_active": True,
                "telemetry_active": True,
                **values,
            },
        },
    )


class TestLinRecovery(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.listener = Mock()
        self.services = SimpleNamespace(has_service=Mock(return_value=True))
        self.hass = SimpleNamespace(services=self.services)
        clock = patch.object(lin_transport, "time", SimpleNamespace(monotonic=lambda: self.now))
        timers = patch.object(lin_transport, "async_call_later", return_value=Mock())
        clock.start()
        timers.start()
        self.addCleanup(clock.stop)
        self.addCleanup(timers.stop)

    def test_identical_heartbeat_notifies_after_expiry(self):
        lin = lin_transport.PrecisionPlexLinTelemetry(self.hass, self.listener)
        lin._handle_snapshot(snapshot("coach-a", coach_voltage=13.2))
        self.now += 2
        lin._handle_snapshot(snapshot("coach-a", reason="heartbeat", uptime=22_000))
        self.assertEqual(self.listener.call_count, 1)
        self.now += 5
        lin._handle_snapshot_expired(None)
        self.assertIsNone(lin.value("coach_voltage"))
        lin._handle_snapshot(snapshot("coach-a", reason="heartbeat", uptime=27_000))
        self.assertEqual(lin.value("coach_voltage"), 13.2)
        self.assertEqual(self.listener.call_count, 3)

    def test_configured_bridge_owns_telemetry_and_commands(self):
        lin = lin_transport.PrecisionPlexLinTelemetry(
            self.hass, self.listener, selected_bridge_id="coach-a"
        )
        lin._handle_snapshot(snapshot("coach-b", coach_voltage=12.0))
        self.assertFalse(lin.snapshot_fresh)
        lin._handle_snapshot(snapshot(
            "coach-a", coach_voltage=13.2, output_control_capable=True, outputs_active=True
        ))
        lin._handle_snapshot(snapshot("coach-b", coach_voltage=12.0))
        self.assertEqual(lin.value("coach_voltage"), 13.2)
        self.assertTrue(lin.output_control_available)
        self.services.has_service.assert_called_once_with(
            "esphome", "coach_a_precision_plex_set_output"
        )
        self.now += 5
        lin._handle_snapshot(snapshot("coach-b", coach_voltage=12.0))
        self.assertFalse(lin.snapshot_fresh)

    def test_automatic_binding_fails_closed_on_second_bridge(self):
        lin = lin_transport.PrecisionPlexLinTelemetry(self.hass, self.listener)
        lin._handle_snapshot(snapshot("coach-a", coach_voltage=13.2))
        lin._handle_snapshot(snapshot("coach-b", coach_voltage=12.0))
        self.assertEqual(lin.bridge_id, "coach-a")
        self.assertIsNone(lin.value("coach_voltage"))
        lin._handle_snapshot(snapshot("coach-a", coach_voltage=13.2))
        self.assertFalse(lin.snapshot_fresh)
        self.assertEqual(self.listener.call_count, 2)

    def test_multiple_coach_entries_require_explicit_binding(self):
        lin = lin_transport.PrecisionPlexLinTelemetry(
            self.hass, self.listener, allow_auto_binding=lambda: False
        )
        lin._handle_snapshot(snapshot("coach-a", coach_voltage=13.2))
        self.listener.assert_not_called()
        self.assertFalse(lin.snapshot_fresh)


class TestMotionCompletion(unittest.IsolatedAsyncioTestCase):
    def make_coordinator(self):
        plex = object.__new__(coordinator.PrecisionPlexStateCoordinator)
        plex.__dict__.update(
            _stopped=False,
            _write_lock=asyncio.Lock(),
            _lin_motion_lock=asyncio.Lock(),
            _client=None,
            _begin_command_stream=Mock(),
            _end_command_stream=Mock(),
            _async_disconnect=AsyncMock(),
            hold_stream_recoveries=0,
            hold_stream_interruption_count=0,
            lin=SimpleNamespace(motion_action=Mock(return_value=None)),
        )
        return plex

    def make_cover(self, plex, counts):
        entity = object.__new__(cover.PrecisionPlexTimedCover)
        entity.__dict__.update(
            coordinator=plex,
            _plex_description=SimpleNamespace(key="sofa_slide"),
            _lin_motion_key=lambda: "sofa_slide",
            _read_quadrature_travel_total=Mock(side_effect=counts),
            _async_verify_quadrature_motion=AsyncMock(),
            _update_estimated_position=Mock(),
            _calibrate_quadrature_endpoint=Mock(return_value=True),
            _set_provisional_motion=Mock(),
            async_write_ha_state=Mock(),
            _estimated_position=42.0,
            _signed_retracted_counts=None,
            _signed_extended_counts=None,
        )
        return entity

    async def run_cover(self, entity):
        await entity._async_hold_runner("out", b"release", b"hold", asyncio.Event(), 25, 100.0)

    async def test_failed_ble_fallback_preserves_endpoint(self):
        plex = self.make_coordinator()
        plex._connect_and_subscribe = AsyncMock(side_effect=coordinator.BleakError("offline"))
        entity = self.make_cover(plex, [4200])
        with patch.object(coordinator.asyncio, "sleep", new_callable=AsyncMock):
            await self.run_cover(entity)
        self.assertEqual(plex.hold_stream_interruption_count, 1)
        entity._calibrate_quadrature_endpoint.assert_not_called()
        self.assertEqual(entity._estimated_position, 42.0)

    async def test_successful_run_learns_moving_encoder(self):
        plex = SimpleNamespace(async_write_hold_stream=AsyncMock(
            return_value=MotionResult(MotionEnd.DURATION_COMPLETE, "lin")
        ))
        entity = self.make_cover(plex, [4200, 10000])
        await self.run_cover(entity)
        entity._calibrate_quadrature_endpoint.assert_called_once_with(100.0, 10000)
        self.assertEqual(entity._estimated_position, 100.0)

    async def test_finished_stream_with_stationary_encoder_does_not_learn(self):
        plex = SimpleNamespace(async_write_hold_stream=AsyncMock(
            return_value=MotionResult(MotionEnd.DURATION_COMPLETE, "bluetooth")
        ))
        entity = self.make_cover(plex, [4200, 4200])
        await self.run_cover(entity)
        entity._calibrate_quadrature_endpoint.assert_not_called()
        self.assertEqual(entity._estimated_position, 42.0)

    async def test_lin_uncertainty_never_falls_back_to_ble(self):
        plex = self.make_coordinator()
        plex.lin.motion_action.return_value = "motion"
        plex.lin.async_motion_hold = AsyncMock(side_effect=HomeAssistantError("unknown outcome"))
        plex._async_write_hold_stream_locked = AsyncMock()
        with self.assertRaises(HomeAssistantError):
            await plex.async_write_hold_stream(
                b"release", b"hold", asyncio.Event(), lin_direction="out"
            )
        plex._async_write_hold_stream_locked.assert_not_awaited()

    async def test_explicit_lin_not_sent_permits_ble_fallback(self):
        plex = self.make_coordinator()
        plex.lin.motion_action.return_value = "motion"
        plex.lin.async_motion_hold = AsyncMock(return_value=MotionEnd.NOT_SENT)
        completed = MotionResult(MotionEnd.DURATION_COMPLETE, "bluetooth")
        plex._async_write_hold_stream_locked = AsyncMock(return_value=completed)
        self.assertEqual(
            await plex.async_write_hold_stream(b"release", b"hold", asyncio.Event(), lin_direction="out"),
            completed,
        )
        plex._async_write_hold_stream_locked.assert_awaited_once()
