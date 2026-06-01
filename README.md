# Precision Plex Home Assistant Integration

A custom Home Assistant integration for Precision Circuits Precision Plex systems.

## Current Recommended Release

**v2.4.2** is the current recommended release.

Earlier releases are retained for historical and development reference. The v1.x releases document the original monitoring/coexistence architecture. The v2.x releases document the transition toward a native Home Assistant replacement for the Precision Circuits Wireless TP application.

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

## Test Environment

This integration has been developed and validated on:

```text
Precision Circuits Precision Plex
Precision Circuits Wireless TP Monitor

Primary Development Platform:
2022 Forest River Georgetown GT5 34M5
```

The decoded functions, state bits, and command packets currently implemented correspond to equipment installed on that coach.

Precision Plex installations vary by manufacturer, model, year, and option package. Different coaches may expose different slide rooms, lighting zones, HVAC controls, generator controls, water systems, tank monitoring functions, and coach-specific accessories.

The protocol appears to be largely shared across Precision Plex installations, but command mappings and available functions may vary by coach.

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

## Current Stable Feature Set

Tested and working as of v2.4.2:

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

They control automatic runtime safety limits, position estimation speed, and set-position movement timing.

Current defaults:

| Entity | Default |
|---|---:|
| Awning Open Seconds | 18 seconds |
| Awning Close Seconds | 25 seconds |
| Bed Slide Open Seconds | 28 seconds |
| Bed Slide Close Seconds | 23 seconds |

## Installation

### HACS Custom Repository

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository.
3. Select repository type: **Integration**.
4. Install **Precision Plex**.
5. Restart Home Assistant.
6. Add the Precision Plex integration from **Settings → Devices & Services**.

### Manual Installation

Copy the integration folder into Home Assistant:

```text
config/custom_components/precision_plex
```

Then restart Home Assistant.

## Documentation

Protocol and reverse-engineering documentation is maintained under `/docs`.

Useful starting points:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/protocol_overview.md`](docs/protocol_overview.md)
- [`docs/ble_characteristics.md`](docs/ble_characteristics.md)
- [`docs/state_mapping.md`](docs/state_mapping.md)
- [`docs/command_mapping.md`](docs/command_mapping.md)
- [`docs/position_estimation.md`](docs/position_estimation.md)
- [`docs/test_environment.md`](docs/test_environment.md)
- [`docs/contribution_guide.md`](docs/contribution_guide.md)
- [`docs/coaches/georgetown_gt5_34m5.md`](docs/coaches/georgetown_gt5_34m5.md)

## Safety Notes

This integration can control physical RV equipment.

Use care when testing:

- Confirm the awning path is clear
- Confirm slide rooms have clearance
- Keep visual contact with moving equipment
- Use Stop immediately if motion is unexpected
- Verify travel-time settings before relying on full-open or full-close automation

The integration includes timed safety limits for covers, but it does not replace operator awareness.

## Planned / Future Work

Likely next targets:

- Sofa Slide
- Wardrobe Slide
- Additional Wireless TP functions
- Dashboard examples
- Better diagnostics
- Expanded protocol documentation

The long-term goal is a complete native Home Assistant replacement for the Precision Circuits Wireless TP app.
