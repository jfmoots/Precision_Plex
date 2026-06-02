# Precision Plex Home Assistant Integration

A custom Home Assistant integration for Precision Circuits Precision Plex systems.

## Current Recommended Release

**v2.6.26** is the current recommended release.

This release is the cleaned GitHub-ready build that incorporates the tested work from v2.6.3 through v2.6.25, including the complete Level Monitor decoder.

## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

Different Precision Plex-equipped coaches may expose different numbers of slides, lights, tanks, relays, and sensors. The protocol documentation in `/docs` is intended to help other owners adapt the integration to their specific coach configuration.

## Project Vision

This project began as a Home Assistant integration for monitoring Precision Plex state.

The current direction is a native Home Assistant replacement for the Precision Circuits Wireless TP mobile application:

```text
Precision Plex Controller
        ⇅
Wireless TP BLE Module
        ⇅
Home Assistant
```

The integration provides:

- Persistent local BLE connectivity
- Real-time Precision Plex status monitoring
- Bidirectional control for supported circuits
- Native Home Assistant lights, switches, covers, sensors, binary sensors, and number entities
- Awning and slide position estimation
- Complete Level Monitor telemetry for the tested coach

## Important Bluetooth Architecture Note

The Precision Plex Wireless TP module appears to allow only one active BLE connection at a time.

The integration intentionally maintains a persistent Bluetooth connection while Home Assistant is running. When Home Assistant is connected, the Precision Circuits iOS app may be unable to connect at the same time. This is expected behavior for the Wireless TP module.

## Current Stable Feature Set

Tested and working as of **v2.6.26**:

### Controls

- `light.awning_light`
- `switch.water_pump`
- `switch.water_heater`
- `cover.awning`
- `cover.bed_slide`
- `cover.wardrobe_slide`
- `cover.sofa_slide`

### Level Monitor Sensors

Decoded from handle `0x002B` / characteristic `02AA`:

- `sensor.coach_battery`
- `sensor.fresh_water_tank`
- `sensor.grey_water_tank`
- `sensor.black_water_tank`
- `sensor.lp_gas_tank`

### Status / Movement Sensors

- Awning light state
- Water pump state
- Water heater state
- Awning extending/retracting
- Bed slide extending/retracting
- Wardrobe slide extending/retracting
- Sofa slide extending/retracting

### Configurable Travel-Time Settings

Travel times are exposed as Home Assistant Number entities:

- `number.awning_open_seconds`
- `number.awning_close_seconds`
- `number.bed_slide_open_seconds`
- `number.bed_slide_close_seconds`
- `number.wardrobe_slide_open_seconds`
- `number.wardrobe_slide_close_seconds`
- `number.sofa_slide_open_seconds`
- `number.sofa_slide_close_seconds`

These values are editable from Home Assistant and persist across restarts.

## Level Monitor Decoder

The Level Monitor page is decoded from the `02AA` telemetry packet, observed at handle `0x002B`.

Example payload:

```text
00 83 06 3F 3F 50 ...
```

Known fields:

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |

## Installation

### HACS Custom Repository

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository.
3. Select repository type: **Integration**.
4. Install **Precision Plex**.
5. Restart Home Assistant.
6. Add the Precision Plex integration from **Settings → Devices & Services**.

### Manual Installation

Copy this folder into Home Assistant:

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

- Confirm the awning path is clear.
- Confirm slide rooms have clearance.
- Keep visual contact with moving equipment.
- Use Stop immediately if motion is unexpected.
- Verify travel-time settings before relying on full-open or full-close automation.

The integration includes timed safety limits for covers, but it does not replace operator awareness.

## Reference Calibrations

These travel times were validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values can be adjusted through the Home Assistant Number entities without modifying the integration.

## Restore Cover Positions After Restart

Cover entities restore their last Home Assistant-known estimated position after Home Assistant restarts or the integration reloads.

The restored value is still an estimate. If the awning or slides are moved while Home Assistant is offline, the restored position may be stale until recalibrated or moved again through Home Assistant while connected.

## Clean Disable / Enable Lifecycle

The integration can be disabled and re-enabled from Home Assistant without requiring a full Home Assistant restart.

During unload, the integration stops the persistent BLE coordinator, cancels and awaits the BLE monitor task, disconnects the BLE client, removes stale startup callbacks, clears listeners, and unloads platforms cleanly.

## Planned / Future Work

Likely next targets:

- Generator status / generator hours
- Additional lighting circuits
- Additional coach-specific Precision Plex functions
- Dashboard examples
- Expanded protocol documentation
