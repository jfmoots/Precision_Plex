# Precision Plex v2.4.1 GitHub Draft Notes

## Summary

v2.4.1 represents the first strong GitHub-ready baseline for the Precision Plex Home Assistant integration.

The project has evolved from a monitoring-only experiment into a native Home Assistant replacement for the Precision Circuits Wireless TP mobile application.

## Major Direction Change Since v1.7.1

Earlier versions focused on observing Precision Plex state.

Since then, the project direction changed to:

- Maintain a constant BLE connection
- Subscribe to live Wireless TP notifications
- Decode state changes initiated by the RV wall panel
- Send Precision-compatible BLE command packets from Home Assistant
- Represent RV functions as native Home Assistant entities
- Replace core Wireless TP app functionality with Home Assistant controls

The constant Bluetooth connection is intentional and important. It enables:

- Bidirectional updates
- Fast response
- Near real-time wall-panel synchronization
- Accurate cover/slide position estimation
- Reduced command latency

The Wireless TP module appears to support only one active BLE connection, so the Precision Circuits app may not connect while Home Assistant is connected.

## Changes Since v1.7.1

### Monitoring Improvements

- Added continuous BLE notification monitoring
- Improved state decoding from `02BB`
- Added support for multiple 16-bit state words
- Added state tracking for:
  - Awning light
  - Water pump
  - Water heater
  - Awning movement
  - Bed slide movement

### Command Support

Added verified BLE command support for:

- Awning Light
- Water Pump
- Water Heater
- Awning Extend / Retract / Stop
- Bed Slide Extend / Retract / Stop

### Home Assistant Entity Support

Added:

- `light.awning_light`
- `switch.water_pump`
- `switch.water_heater`
- `cover.awning`
- `cover.bed_slide`
- Movement binary sensors
- Travel-time number entities

### Cover / Slide Position Estimation

Added timed position estimation for:

- Awning
- Bed Slide

Position estimation tracks:

- Home Assistant initiated movement
- RV wall-panel initiated movement

### Configurable Travel Times

Added editable Number entities:

- Awning Open Seconds
- Awning Close Seconds
- Bed Slide Open Seconds
- Bed Slide Close Seconds

These replace hard-coded travel times and allow future calibration from the Home Assistant UI.

### Stability Fixes

Addressed issues discovered during live RV testing:

- BLE cleanup failures
- Websocket service-call exceptions
- Duplicate BlueZ notification subscription errors
- Idle Stop behavior
- Cover entity setup crashes
- Number entity setup crashes
- Multi-word state decoding
- Reconnect/disconnect callback handling

## Known Stable Defaults

- Awning open: 18 seconds
- Awning close: 25 seconds
- Bed slide open: 28 seconds
- Bed slide close: 23 seconds

## Known Limitations

- Position is estimated, not sensor-confirmed
- Travel-time values may need tuning over time
- The Wireless TP module appears to allow only one active BLE connection
- Precision Circuits app coexistence may be limited while HA is connected
- Sofa Slide and Wardrobe Slide are not yet implemented

## Suggested GitHub Release Title

Precision Plex v2.4.1 — Wireless TP Replacement Baseline

## Suggested Release Description

This release establishes the first stable baseline for using Home Assistant as a native Precision Plex Wireless TP replacement.

Highlights:

- Persistent BLE connection for fast bidirectional state updates
- Awning Light, Water Pump, and Water Heater control
- Awning cover control with position estimation
- Bed Slide cover control with position estimation
- Wall-panel movement tracking
- Configurable travel-time values from Home Assistant
- Improved BLE stability and recovery behavior

This release should be considered the current rollback point before adding additional slide-room support.
