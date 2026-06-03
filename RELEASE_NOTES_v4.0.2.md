# Precision Plex for Home Assistant v4.0.2

This maintenance release fixes button availability refresh behavior introduced with the new V4 jog/reset controls.

## Fixes

- Fixed generator buttons remaining greyed out after the BLE coordinator connects.
- Fixed cover jog buttons remaining greyed out after startup.
- Added coordinator update subscriptions to button entities so availability refreshes when Precision Plex telemetry arrives.
- Added generator idle/resting status `0x40` as a stopped state.
- Preserved previously added stopped idle flag handling for `0x80`.
- Treated combined stopped idle flags `0xC0` as stopped for diagnostics and command eligibility.
- Kept generator raw status values visible for troubleshooting.

## Notes

The V4 jog/reset feature set remains unchanged:

- Slide jogs default to 5 seconds.
- Awning jogs default to 2 seconds.
- Jog durations remain configurable.
- Jog controls intentionally bypass estimated end-stop limits.
- Reset buttons correct Home Assistant's estimated position only and do not move hardware.
