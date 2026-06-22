"""Coach profile support for Precision Plex."""

from __future__ import annotations

from typing import Any

from .georgetown_gt5_34m5 import PROFILE as GEORGETOWN_GT5_34M5_PROFILE

DEFAULT_PROFILE_ID = "georgetown_gt5_34m5"

PROFILES: dict[str, dict[str, Any]] = {
    DEFAULT_PROFILE_ID: GEORGETOWN_GT5_34M5_PROFILE,
}


def get_profile(profile_id: str | None = None) -> dict[str, Any]:
    """Return a coach profile by id, falling back to the default profile."""
    if profile_id in PROFILES:
        return PROFILES[profile_id]  # type: ignore[index]
    return PROFILES[DEFAULT_PROFILE_ID]


DEFAULT_PROFILE = get_profile(DEFAULT_PROFILE_ID)
