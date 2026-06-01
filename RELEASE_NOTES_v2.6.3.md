# Precision Plex v2.6.3 — Restore Cover Positions After Restart

## Summary

This maintenance release adds Home Assistant state restoration for Precision Plex cover entities.

Previously, estimated cover positions initialized to `0%` after a Home Assistant restart or integration reload. This made slides and the awning appear fully closed even when they were physically open.

v2.6.3 restores the last Home Assistant-known estimated position for:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

## New Behavior

After Home Assistant restarts or the integration reloads:

- Cover entities restore their last saved `current_position`
- Slides no longer default to `0%`
- Awning no longer defaults to `0%`
- Position estimation continues from the restored value

## Important Limitation

This restores the last Home Assistant-known estimate. It is not a physical position sensor.

If a slide or awning is moved while Home Assistant is offline, Home Assistant cannot know about that movement and may restore a stale position on the next startup.

## Retained v2.6.2 Improvements

This package preserves the improved integration lifecycle handling from v2.6.2.

The integration can still be disabled and re-enabled without requiring a Home Assistant restart because the coordinator now:

- Stops the persistent BLE coordinator cleanly
- Cancels and awaits the BLE monitor task
- Disconnects the BLE client
- Removes stale startup callbacks
- Clears stale listeners
- Unloads Home Assistant platforms cleanly

## Existing Supported Controls

- Awning Light
- Water Pump
- Water Heater
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Existing Motion Features

- Home Assistant control
- RV wall-panel tracking
- Position estimation
- Position restore after restart
- Automatic stop behavior
- Runtime safety limits
- User-configurable travel times
- Persistent BLE monitoring
- Clean disable/enable lifecycle

## Reference Calibrations

Validated on a Precision Plex system installed in a 2022 Forest River Georgetown GT5 34M5 Motorhome.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

These values are reference calibrations only. Travel times may vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear.

## Tested Coach and Scope

This project was reverse engineered from a Precision Plex system installed in a:

**2022 Forest River Georgetown GT5 34M5 Motorhome**

Other Precision Plex-equipped coaches may expose different combinations of slides, lights, tanks, relays, and telemetry.

## Known Limitations

- Position values are estimated rather than sensor-confirmed
- Travel times may require occasional recalibration
- Tank levels are not yet implemented
- Generator monitoring/control is not yet implemented
- If motion occurs while Home Assistant is offline, restored positions may be stale

## Next Planned Work

- Fresh water tank levels
- Gray tank levels
- Black tank levels
- Battery telemetry
- LP tank status
- Generator status and controls
