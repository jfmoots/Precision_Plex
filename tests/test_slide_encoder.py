"""Regression tests for signed quadrature through an encoder zero crossing."""

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock

from custom_components.precision_plex.cover import PrecisionPlexTimedCover
from custom_components.precision_plex.slide_encoder import (
    SlideEncoderCalibration,
    parse_motor_counts,
)


class TestSlideEncoder(TestCase):
    def test_sofa_counts_increase_monotonically_through_zero(self):
        retracted = (-8213.0, 8225.0)
        extended = (13485.0, -13484.0)
        calibration = SlideEncoderCalibration(retracted, extended)
        self.assertTrue(calibration.valid)
        self.assertEqual(calibration.full_travel, 21703.5)
        points = [retracted, (-4000, 4000), (0, 0), (4500, -4500), extended]
        travel = [sum(calibration.travel(point)) / 2 for point in points]
        self.assertEqual(travel[0], 0)
        self.assertEqual(travel[-1], calibration.full_travel)
        self.assertTrue(all(a < b for a, b in zip(travel, travel[1:])))
        self.assertAlmostEqual(travel[2] / calibration.full_travel * 100, 37.8695, places=2)

    def test_same_direction_and_reversed_motor_wiring(self):
        for start, end, midpoint in [
            ((-100, -200), (100, 200), (0, 0)),
            ((100, -200), (-100, 200), (0, 0)),
            ((100, 200), (-100, -200), (0, 0)),
        ]:
            calibration = SlideEncoderCalibration(start, end)
            self.assertTrue(calibration.valid)
            self.assertEqual(calibration.travel(midpoint), (100, 200))

    def test_invalid_and_incomplete_count_pairs(self):
        self.assertEqual(parse_motor_counts(["-25.5", "25.0"]), (-25.5, 25.0))
        for invalid in (None, [1], [1, None], ["unavailable", 0], [0, float("nan")]):
            self.assertIsNone(parse_motor_counts(invalid))
        self.assertFalse(SlideEncoderCalibration((0, 0), (0, 50)).valid)

    def make_cover(self, key="sofa_slide"):
        cover = object.__new__(PrecisionPlexTimedCover)
        cover._plex_description = SimpleNamespace(key=key)
        cover._signed_retracted_counts = None
        cover._signed_extended_counts = None
        cover._motor_entity_ids = {}
        cover._quadrature_retracted_total = 8220.0
        cover._quadrature_extended_total = 13485.0
        cover._last_quadrature_total = None
        cover._read_float_state = Mock(return_value=8221.0)
        return cover

    def test_cover_switches_to_signed_only_with_two_confirmed_endpoints(self):
        for key in ("bed_slide", "sofa_slide", "wardrobe_slide"):
            with self.subTest(slide=key):
                cover = self.make_cover(key)
                cover._read_signed_motor_counts = Mock(return_value=(0.0, 0.0))
                self.assertTrue(cover._learn_signed_endpoint(0, (-8213, 8225)))
                self.assertEqual(cover._read_quadrature_travel_total(), 8221)
                self.assertTrue(cover._learn_signed_endpoint(100, (13485, -13484)))
                self.assertTrue(cover._update_position_from_quadrature())
                self.assertAlmostEqual(cover._estimated_position, 37.8695, places=2)
                self.assertEqual(cover._read_quadrature_sync_error(), 12.0)
                self.assertFalse(cover._learn_signed_endpoint(100, (-8213, 8225)))
                self.assertEqual(cover._signed_extended_counts, (13485, -13484))

    def test_signed_calibration_does_not_mix_in_legacy_unsigned_when_sensor_is_lost(self):
        cover = self.make_cover()
        cover._signed_retracted_counts = (-8213, 8225)
        cover._signed_extended_counts = (13485, -13484)
        cover._read_signed_motor_counts = Mock(return_value=None)
        self.assertIsNone(cover._read_quadrature_travel_total())
        self.assertFalse(cover._update_position_from_quadrature())
        cover._read_float_state.assert_not_called()

    def test_finds_raw_entities_without_selecting_absolute_diagnostics(self):
        cover = self.make_cover()
        del cover._read_float_state
        states = {}
        for index, raw in ((1, -8213), (2, 8225)):
            prefix = f"sensor.test_sofa_slide_motor_{index}_quadrature"
            for suffix, name_suffix, value in (("_absolute", " Absolute", abs(raw)), ("", "", raw)):
                eid = prefix + suffix
                states[eid] = SimpleNamespace(
                    entity_id=eid,
                    state=str(value),
                    attributes={"friendly_name": f"Sofa Slide Motor {index} Quadrature{name_suffix}"},
                )
        cover.hass = SimpleNamespace(
            states=SimpleNamespace(get=states.get, async_all=lambda _domain: list(states.values()))
        )
        self.assertEqual(cover._read_signed_motor_counts(), (-8213, 8225))
        states["sensor.test_sofa_slide_motor_1_quadrature"].state = "unavailable"
        self.assertIsNone(cover._read_signed_motor_counts())


class TestSlideEncoderRestore(IsolatedAsyncioTestCase):
    """Exercise the state attributes used to restore signed calibration."""

    async def test_calibration_is_restored_from_cover_state(self):
        cover = object.__new__(PrecisionPlexTimedCover)
        cover._plex_description = SimpleNamespace(key="sofa_slide")
        cover.async_get_last_state = AsyncMock(
            return_value=SimpleNamespace(
                state="closed",
                attributes={
                    "current_position": 0,
                    "quadrature_retracted_total": 8219.0,
                    "quadrature_extended_total": 13486.5,
                    "quadrature_signed_retracted_counts": [-8213, 8225],
                    "quadrature_signed_extended_counts": [13485, -13484],
                },
            )
        )
        await cover._async_restore_last_position()
        self.assertEqual(cover._signed_calibration().full_travel, 21703.5)
        self.assertEqual(cover._quadrature_retracted_total, 8219.0)
        self.assertEqual(cover._estimated_position, 0)
