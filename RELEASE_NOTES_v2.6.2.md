# Precision Plex v2.6.2 — Motion Control Complete

## Summary

This release completes the motion-control phase of the Precision Plex reverse-engineering project for the **2022 Forest River Georgetown GT5 34M5 Motorhome**.

The integration now supports awning and slide control with bidirectional wall-panel tracking, position estimation, persistent Bluetooth monitoring, configurable travel-time calibration, and clean Home Assistant disable/enable lifecycle handling.

## New Since v2.4.1

- Added Wardrobe Slide support
- Added Sofa Slide support
- Fixed Sofa Slide Home Assistant command mapping
- Added Sofa Slide wall-panel tracking
- Added Sofa Slide position estimation
- Added Sofa Slide configurable travel-time numbers
- Updated Bed Slide calibrated close time
- Updated Wardrobe Slide calibrated travel times
- Updated Sofa Slide calibrated travel times
- Added clean integration disable/enable lifecycle support
- Added reference calibration documentation for the tested coach
- Expanded protocol documentation for future adaptation

## Current Supported Controls

- Awning Light
- Water Pump
- Water Heater
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Current Motion Features

- Home Assistant control
- RV wall-panel tracking
- Position estimation
- Automatic stop behavior
- Runtime safety limits
- User-configurable travel times

## Reference Calibrations

Validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values are reference calibrations and can be adjusted through Home Assistant Number entities without modifying the integration.

## Tested Coach and Scope

This project was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

Different Precision Plex equipped coaches may expose different numbers of slides, lights, tanks, relays, and sensors. The protocol documentation included under `/docs` is intended to help other owners adapt the integration to their specific coach configuration.

## Known Limitations

- Position values are estimated rather than sensor-confirmed
- Travel times may require occasional recalibration
- The Wireless TP monitor appears to allow only one active BLE connection
- Tank levels are not yet implemented
- Generator status/control is not yet implemented

## Next Planned Work

- Tank level decoding
- Battery voltage/status decoding
- LP level/status decoding
- Generator status discovery
- Generator control discovery, with additional safety review


## Clean Integration Disable / Enable Lifecycle

This release preserves the coordinator unload/reload fix validated during live testing.

When the integration is disabled, Home Assistant now:

- Stops the persistent BLE coordinator
- Cancels and awaits the BLE monitor task
- Disconnects the BLE client cleanly
- Removes stale startup callbacks
- Clears stale listeners
- Unloads Home Assistant platforms cleanly

This allows the Precision Plex integration to be disabled and re-enabled without requiring a full Home Assistant restart.
