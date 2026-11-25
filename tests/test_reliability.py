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


class TestLinCommandPathAlert(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = 100.0
        self.services = SimpleNamespace(has_service=Mock(return_value=True))
        self.hass = SimpleNamespace(services=self.services, loop=asyncio.get_running_loop())
        entry = SimpleNamespace(
            data={"address": "00:00:00:00:00:01"},
            options={coordinator.CONF_LIN_BRIDGE_ID: "coach-a"},
        )
        self.plex = coordinator.PrecisionPlexStateCoordinator(self.hass, entry)
        self.lin = self.plex.lin
        self.alert_timer = Mock(side_effect=lambda *_: Mock())
        for patched in (
            patch.object(lin_transport, "time", SimpleNamespace(monotonic=lambda: self.now)),
            patch.object(lin_transport, "async_call_later", return_value=Mock()),
            patch.object(coordinator, "async_call_later", self.alert_timer),
        ):
            patched.start()
            self.addCleanup(patched.stop)
        self.send_snapshot()
        self.assertEqual(self.plex.lin_command_problems, {"bridge": (), "generator": (), "outputs": ()})

    def send_snapshot(self, *, reason="periodic_full", **values):
        defaults = {
            "outputs_active": True,
            "output_control_capable": True,
            "generator_command_capable": True,
            **{f"{key}_motion_capable": True for key in lin_transport.LIN_MOTION_KEYS},
            **values,
        }
        self.lin._handle_snapshot(
            snapshot("coach-a", reason=reason, uptime=int(self.now * 1000), **defaults)
        )

    def fire_alert_timer(self, index=0):
        hass, delay, confirm = self.alert_timer.call_args_list[index].args
        self.assertIs(hass, self.hass)
        self.assertEqual(delay, coordinator.LIN_FEEDBACK_ALERT_DELAY_SECONDS)
        confirm(None)

    async def test_transient_generator_gap_does_not_flag_bridge_or_slide_path(self):
        self.now += 2
        self.send_snapshot(reason="heartbeat", telemetry_active=False)
        self.assertEqual(self.lin.command_path_problems["generator"], ("PIDBA generator feedback stale",))
        self.assertIsNone(self.lin.generator_action)
        self.assertIsNotNone(self.lin.motion_action("wardrobe_slide"))
        self.assertFalse(self.plex._refresh_lin_command_health())
        self.assertEqual(self.plex.lin_command_problems, {"bridge": (), "generator": (), "outputs": ()})

        cancel = self.plex._lin_command_alert_unsubs["generator"]
        self.now += 2
        self.send_snapshot(reason="heartbeat")
        self.alert_timer.assert_called_once()
        cancel.assert_called_once()
        self.assertTrue(self.plex._refresh_lin_command_health())
        self.assertEqual(self.plex.lin_command_problems, {"bridge": (), "generator": (), "outputs": ()})

    async def test_transient_output_gap_does_not_raise_alert_or_enable_motion(self):
        self.now += 2
        self.send_snapshot(reason="heartbeat", outputs_active=False)
        self.assertTrue(self.lin.snapshot_fresh)
        self.assertEqual(self.lin.command_path_problems["outputs"], ("PID32 output feedback stale",))
        self.assertIsNotNone(self.lin.generator_action)
        self.assertIsNone(self.lin.motion_action("wardrobe_slide"))
        self.assertEqual(self.plex.lin_command_problems["outputs"], ())
        cancel = self.plex._lin_command_alert_unsubs["outputs"]
        self.now += 2
        self.send_snapshot(reason="heartbeat", outputs_active=False)
        self.alert_timer.assert_called_once()

        self.now += 2
        self.send_snapshot(reason="heartbeat")
        cancel.assert_called_once()
        self.assertEqual(self.plex.lin_command_problems["outputs"], ())

    async def test_bridge_heartbeat_expiry_alerts_without_extra_feedback_delay(self):
        self.now += lin_transport.SNAPSHOT_MAX_AGE_SECONDS + 0.1
        self.lin._handle_snapshot_expired(None)
        self.assertEqual(self.plex.lin_command_problems, {
            "bridge": ("LIN bridge heartbeat",), "generator": None, "outputs": None,
        })
        self.alert_timer.assert_not_called()

        self.send_snapshot(reason="heartbeat")
        self.assertEqual(self.plex.lin_command_problems, {"bridge": (), "generator": (), "outputs": ()})

    async def test_expected_bridge_has_one_heartbeat_window_at_startup(self):
        startup = coordinator.PrecisionPlexStateCoordinator(self.hass, self.plex.entry)
        startup.lin_commands_expected = True
        self.assertFalse(startup._refresh_lin_command_health())
        self.assertIsNone(startup.lin_command_problems["bridge"])
        self.alert_timer.assert_called_once()
        hass, delay, confirm = self.alert_timer.call_args.args
        self.assertIs(hass, self.hass)
        self.assertEqual(delay, lin_transport.SNAPSHOT_MAX_AGE_SECONDS)
        self.now += delay
        confirm(None)
        self.assertEqual(startup.lin_command_problems["bridge"], ("LIN bridge heartbeat",))

    async def test_inactive_bus_is_distinct_from_missing_heartbeat(self):
        self.now += 2
        self.send_snapshot(reason="heartbeat", telemetry_active=False)
        cancel = self.plex._lin_command_alert_unsubs["generator"]
        self.now += 2
        self.send_snapshot(reason="heartbeat", bus_active=False)
        self.assertTrue(self.lin.snapshot_fresh)
        self.assertEqual(self.plex.lin_command_problems, {
            "bridge": ("LIN bus traffic",), "generator": None, "outputs": None,
        })
        cancel.assert_called_once()
        self.alert_timer.assert_called_once()

    async def test_feedback_alerts_have_independent_confirmation_windows(self):
        self.now += 2
        self.send_snapshot(reason="heartbeat", telemetry_active=False)
        self.now += 2
        self.send_snapshot(reason="heartbeat", telemetry_active=False, outputs_active=False)
        for _ in range(2):
            self.now += 2
            self.send_snapshot(reason="heartbeat", telemetry_active=False, outputs_active=False)
        self.fire_alert_timer()
        self.assertEqual(self.plex.lin_command_problems, {
            "bridge": (), "generator": ("PIDBA generator feedback stale",), "outputs": (),
        })

        self.now += 2
        self.send_snapshot(reason="heartbeat", outputs_active=False)
        self.fire_alert_timer(index=1)
        self.assertEqual(self.plex.lin_command_problems, {
            "bridge": (), "generator": (), "outputs": ("PID32 output feedback stale",),
        })

    async def test_unchanged_heartbeats_track_missing_and_restored_actions(self):
        self.services.has_service.side_effect = (
            lambda _domain, name: not name.endswith("_wardrobe_slide_motion")
        )
        self.now += 2
        self.send_snapshot(reason="heartbeat")
        self.assertEqual(self.lin.command_path_problems["outputs"], ("wardrobe_slide",))
        self.assertEqual(self.plex.lin_command_problems["outputs"], ())
        for _ in range(3):
            self.now += 2
            self.send_snapshot(reason="heartbeat")
        self.fire_alert_timer()
        self.assertEqual(self.plex.lin_command_problems, {
            "bridge": (), "generator": (), "outputs": ("wardrobe_slide",),
        })

        self.services.has_service.side_effect = None
        self.now += 2
        self.send_snapshot(reason="heartbeat")
        self.assertEqual(self.plex.lin_command_problems, {"bridge": (), "generator": (), "outputs": ()})


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
