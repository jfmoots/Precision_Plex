# Precision Plex v2.5.0 — Wardrobe Slide Support

## Summary

This release adds Wardrobe Slide support to the Precision Plex Home Assistant integration.

Wardrobe Slide uses the same press-and-hold cover architecture already validated for the awning and bed slide, including wall-panel tracking, position estimation, configurable travel times, and runtime safety limits.

## New Features

- Added `cover.wardrobe_slide`
- Added Wardrobe Slide Out Active binary sensor
- Added Wardrobe Slide In Active binary sensor
- Added `number.wardrobe_slide_open_seconds`
- Added `number.wardrobe_slide_close_seconds`
- Added Wardrobe Slide position estimation
- Added Wardrobe Slide wall-panel movement tracking
- Added Wardrobe Slide command mappings to documentation
- Added Wardrobe Slide state mappings to documentation

## Wardrobe Slide Calibration

Default travel times:

| Direction | Time |
|---|---:|
| Full Out / Open | 15 seconds |
| Full In / Close | 13 seconds |

These values are configurable from Home Assistant.

## Verified Command Packets

### Wardrobe Out

Release:

```text
55 1D 10 0B 00 12 00 00 00 00 00 00 00 00 00 61
```

Hold:

```text
55 1D 10 0B 00 12 00 01 00 00 00 00 00 00 00 60
```

### Wardrobe In

Release:

```text
55 1D 10 0B 00 11 00 00 00 00 00 00 00 00 00 62
```

Hold:

```text
55 1D 10 0B 00 11 00 01 00 00 00 00 00 00 00 61
```

## Verified State Bits

State notification word 1:

| Bit | Function |
|---:|---|
| `0x0400` | Wardrobe Slide Out Active |
| `0x0200` | Wardrobe Slide In Active |

## Current Stable Feature Set

- Awning Light
- Water Pump
- Water Heater
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Position Estimation
- Wall Panel Tracking
- Configurable Travel Times
- Bidirectional BLE Synchronization

## Known Limitations

- Position values are estimated rather than sensor-confirmed
- Travel times may require calibration over time
- The Wireless TP monitor appears to allow only one active BLE connection
- Sofa Slide support is not yet implemented
