# Precision Plex v5.3.6 – Smart Awning Cover Routing Fix

This maintenance release fixes a Smart Current Sense Awning routing issue where some Home Assistant or HomeKit cover controls could send full open/close requests as `set_cover_position` commands instead of native `open_cover` / `close_cover` service calls.

## Fixed

- Routes full awning position requests (`100%` and `0%`) through Smart Current Sense logic when awning telemetry is available.
- Ensures full open requests from cover cards, mobile controls, and HomeKit-style position controls trigger arm-lock detection and the Carefree-style fabric tighten sequence.
- Ensures full close requests from position controls trigger retract-seat current detection instead of falling back to old timed travel.
- Keeps intermediate position requests time-based because current sensing only identifies physical endpoint events, not arbitrary awning percentage.

## Unchanged

- Slide logic remains unchanged.
- Jog controls remain unchanged.
- Timed fallback remains available when awning current telemetry is unavailable.
