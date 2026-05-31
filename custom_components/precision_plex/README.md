# Precision Plex Home Assistant Integration

A custom Home Assistant integration for Precision Circuits Precision Plex systems.

## Project Vision

This project began as a Home Assistant integration for monitoring Precision Plex state.

Beginning around the v1.7.x series, the project direction changed from simple monitoring to a more ambitious goal:

> Replace the Precision Circuits Wireless TP mobile application with native Home Assistant entities.

The current integration is designed to provide:

- Real-time state monitoring
- Bidirectional RV control
- Home Assistant native lights, switches, covers, binary sensors, and number entities
- Awning and slide position estimation
- Wall-panel synchronization
- Continuous Bluetooth Low Energy connectivity
- Reduced dependency on the Precision Circuits Wireless TP mobile application

## Important Bluetooth Architecture Note

The Precision Plex Wireless TP module appears to allow only one active BLE connection at a time.

Because of this, the integration intentionally maintains a persistent Bluetooth connection while Home Assistant is running.

This is required for:

- Near real-time state notifications
- Immediate wall-panel updates in Home Assistant
- Reliable bidirectional synchronization
- Fast command response
- Cover and slide position estimation
- Avoiding repeated BLE connection setup latency

When Home Assistant is connected, the Precision Circuits iOS application may be unable to connect at the same time. This is expected behavior and is part of the Wireless TP module limitation.

## Architecture Change Since v1.7.x

### Earlier Direction

Earlier builds focused on monitoring state from Precision Plex.

That approach could expose basic status in Home Assistant, but it was limited by:

- Delayed state updates
- Missed wall-panel transitions
- No reliable command path
- No position estimation
- No true replacement for the Wireless TP application

### Current Direction

The current v2.x direction uses Home Assistant as the primary BLE client and controller.

The integration keeps the BLE connection open and subscribes to live notifications from the Wireless TP module. This lets Home Assistant stay synchronized with both:

- Commands sent from Home Assistant
- Actions performed on the RV wall panel

Conceptually:

```text
RV Wall Panel
    ⇅
Precision Plex Wireless TP Monitor
    ⇅
Home Assistant
```

This persistent connection is the foundation for bidirectional updates and responsive performance.

## Current Stable Feature Set

Tested and working as of v2.4.1:

### Controls

- `light.awning_light`
- `switch.water_pump`
- `switch.water_heater`
- `cover.awning`
- `cover.bed_slide`

### Status / Movement Sensors

- Awning light state
- Water pump state
- Water heater state
- Awning extending
- Awning retracting
- Bed slide extending
- Bed slide retracting

### Configurable Travel-Time Settings

Travel times are exposed as Home Assistant Number entities:

- `number.awning_open_seconds`
- `number.awning_close_seconds`
- `number.bed_slide_open_seconds`
- `number.bed_slide_close_seconds`

These values are editable from Home Assistant and persist across restarts.

They control:

- Automatic runtime safety limits
- Position estimation speed
- Set-position movement timing

Current defaults:

| Entity | Default |
|---|---:|
| Awning Open Seconds | 18 seconds |
| Awning Close Seconds | 25 seconds |
| Bed Slide Open Seconds | 28 seconds |
| Bed Slide Close Seconds | 23 seconds |

## Cover Behavior

The awning and bed slide use a press-and-hold BLE command model matching the Precision Circuits app behavior.

For each cover:

- Open sends a release/neutral frame, then repeated hold frames
- Close sends a release/neutral frame, then repeated hold frames
- Stop sends release/neutral frames
- Position is estimated from elapsed movement time
- Movement initiated from the wall panel is tracked from live BLE state bits
- Travel-time Number entities determine full-open and full-close timing

## Position Estimation

The system does not currently have physical position sensors for the awning or bed slide. Position is estimated by timing movement.

Position convention:

- `0%` = fully closed / retracted
- `100%` = fully open / extended

Position can stay synchronized when using either:

- Home Assistant controls
- RV wall panel controls

because the integration receives live BLE movement notifications.

The estimate may drift over time due to motor speed changes, battery voltage, friction, or mechanical wear. The configurable travel-time Number entities allow recalibration without editing code.

## Current BLE State Mapping

The `02BB` notification payload is decoded as a sequence of 16-bit words.

### Word 0

| Function | Bit |
|---|---:|
| Awning Light | `0x0100` |
| Awning In Active | `0x0002` |
| Awning Out Active | `0x0004` |
| Water Heater | `0x1000` |
| Water Pump | `0x8000` |

### Word 1

| Function | Bit |
|---|---:|
| Bed Slide Out Active | `0x1000` |
| Bed Slide In Active | `0x0800` |

## Known Command Packets

All command writes go to the Precision Plex control characteristic:

```text
03726f62-6f74-7061-6a61-6d61732e6361
```

Known command packets:

### Awning Light

Tap / toggle:

```text
55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

### Water Pump

Tap / toggle:

```text
55 1D 10 0B 00 07 00 00 00 00 00 00 00 00 00 6C
```

### Water Heater

Tap / toggle:

```text
55 1D 10 0B 00 04 00 00 00 00 00 00 00 00 00 6F
```

### Awning Out

Release / neutral:

```text
55 1D 10 0B 00 0A 00 00 00 00 00 00 00 00 00 69
```

Hold:

```text
55 1D 10 0B 00 0A 00 01 00 00 00 00 00 00 00 68
```

### Awning In

Release / neutral:

```text
55 1D 10 0B 00 09 00 00 00 00 00 00 00 00 00 6A
```

Hold:

```text
55 1D 10 0B 00 09 00 01 00 00 00 00 00 00 00 69
```

### Bed Slide Out

Release / neutral:

```text
55 1D 10 0B 00 14 00 00 00 00 00 00 00 00 00 5F
```

Hold:

```text
55 1D 10 0B 00 14 00 01 00 00 00 00 00 00 00 5E
```

### Bed Slide In

Release / neutral:

```text
55 1D 10 0B 00 13 00 00 00 00 00 00 00 00 00 60
```

Hold:

```text
55 1D 10 0B 00 13 00 01 00 00 00 00 00 00 00 5F
```

## Installation

Copy the integration folder into Home Assistant:

```text
config/custom_components/precision_plex
```

Then restart Home Assistant.

After restart, add or configure the Precision Plex integration from:

```text
Settings → Devices & Services
```

## Safety Notes

This integration can control physical RV equipment.

Use care when testing:

- Confirm the awning path is clear
- Confirm slide rooms have clearance
- Keep visual contact with moving equipment
- Use Stop immediately if motion is unexpected
- Verify travel-time settings before relying on full-open or full-close automation

The integration includes timed safety limits for covers, but it does not replace operator awareness.

## Current Status

v2.4.1 is a known-good working baseline with:

- Bidirectional BLE state synchronization
- Persistent BLE notification monitoring
- Awning control
- Bed slide control
- Water pump control
- Water heater control
- Awning light control
- Position estimation
- Configurable travel times
- Wall-panel movement tracking

## Planned / Future Work

Likely next targets:

- Sofa Slide
- Wardrobe Slide
- Additional Wireless TP functions
- Dashboard examples
- Better diagnostics
- Optional HACS packaging
- Expanded protocol documentation

The long-term goal is a complete native Home Assistant replacement for the Precision Circuits Wireless TP app.
