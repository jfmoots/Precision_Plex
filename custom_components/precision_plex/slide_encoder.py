"""Calibrate slide travel from two signed motor encoders."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

MIN_ENCODER_TRAVEL = 25.0
MotorCounts = tuple[float, float]


def parse_motor_counts(value: object) -> MotorCounts | None:
    """Read two finite counts from a Home Assistant state attribute."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        first, second = float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None
    return (first, second) if isfinite(first) and isfinite(second) else None


@dataclass(frozen=True)
class SlideEncoderCalibration:
    """The signed counts measured with a slide fully closed and fully open."""

    retracted: MotorCounts
    extended: MotorCounts

    @property
    def valid(self) -> bool:
        """Require a measurable travel span from each motor."""
        return all(
            abs(end - start) >= MIN_ENCODER_TRAVEL
            for start, end in zip(self.retracted, self.extended)
        )

    @property
    def full_travel(self) -> float:
        """Return average travel in counts over the full stroke."""
        return sum(abs(end - start) for start, end in zip(self.retracted, self.extended)) / 2

    def travel(self, counts: MotorCounts) -> MotorCounts:
        """Measure both motors from closed, positive in the extension direction."""
        first, second = (
            (count - start) if end > start else (start - count)
            for count, start, end in zip(counts, self.retracted, self.extended)
        )
        return first, second
