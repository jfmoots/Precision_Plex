"""Outcomes shared by the LIN and Bluetooth cover command paths."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MotionEnd(str, Enum):
    """Describe how a cover motion request ended."""

    NOT_SENT = "not_sent"
    CANCELED = "canceled"
    STOPPED = "stopped"
    DURATION_COMPLETE = "duration_complete"
    MOTION_ENDED = "motion_ended"


@dataclass(frozen=True)
class MotionResult:
    """A completed motion request and its transport, if it was dispatched."""

    end: MotionEnd
    transport: str | None = None
