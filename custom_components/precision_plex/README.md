# Precision Plex Home Assistant Integration

A custom Home Assistant integration for Precision Circuits Precision Plex systems.

## Current Recommended Release

**v4.5.0** is the current GitHub-ready stable baseline release.

This release focuses on telemetry validation and long-term stability. It keeps the complete feature set from the prior Precision Plex integration releases while adding production-grade validation for noisy or malformed BLE telemetry. The integration now rejects invalid propane samples, protects generator runtime from corrupted candidates, collapses generator flag variants into clean user-facing states, and removes the temporary overnight diagnostic log chatter used during protocol analysis.

## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

The current implementation should be considered **feature complete for the app-visible Precision Plex functions available on this tested coach**. Other Precision Plex-equipped coaches may expose different features, circuits, slides, tanks, generator options, or app configuration profiles.

### Coach Profile Observed in Official App Diagnostics

The official Precision Plex application identifies this coach profile as:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Observed application/platform details:

```text
Model: GT 34M5 with 2AC
STM Version: 4
App Version: 5.06.01
File Version: 3.989
RV Data: GT 34M5 with 2AC v5.06.01 f3.989
```

The app diagnostic log also reports:

```text
hvacSupportOnApp false
hvacSendsHeatPumpBits false
```

This confirms that HVAC support is disabled by the official app for this coach profile.

## Coach Profile Architecture

v4.1.1 introduces a coach profile foundation. The Georgetown GT5 34M5 mappings that were previously hardcoded in the integration now live in:

```text
custom_components/precision_plex/profiles/georgetown_gt5_34m5.py
```

This release intentionally keeps the default profile locked to the tested Georgetown GT5 34M5 behavior. Entity names, unique IDs, BLE commands, decoded state bits, and timing defaults are preserved from v4.0.3. The profile structure is a compatibility-safe foundation for adding other Precision Plex coach layouts later.

## Implemented Precision Plex Features

The following features are present in the official Precision Plex app for the tested coach and are implemented in this integration.

### Lighting

- Awning Light

### Levels

- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank
- Coach Battery Voltage

### Slides

- Bed Slide
- Wardrobe Slide
- Sofa Slide

### Awnings

- Awning Cover
- Configurable jog controls for all slides and awning
- Estimated position reset buttons for all slides and awning

### Generator

- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop
- Generator Running Status
- Generator Runtime Hours
- Generator Status
- Generator Failure Detection: Will Not Start

### Utilities

- Water Pump
- Water Heater

## Features Not Present in the Official App on the Tested Coach

The following items were checked and are **not available in the Precision Plex app on the tested coach**, so they are not current integration targets:

- HVAC / thermostat controls
- Generator fault-code details beyond the decoded generator status field
- Shore power telemetry
- Inverter telemetry
- Tank heater controls
- Water heater telemetry
- Native slide position telemetry
- Native awning position telemetry

## Project Vision

This project began as a Home Assistant integration for monitoring Precision Plex state.

The current direction is a native Home Assistant replacement for the Precision Circuits Wireless TP mobile application for the tested coach:

```text
Precision Plex Controller
        ⇅
Wireless TP BLE Module
        ⇅ BLE
Home Assistant
```

The integration provides:

- Persistent local BLE connectivity
- Real-time Precision Plex status monitoring
- Bidirectional control for supported circuits
- Native Home Assistant light, switch, cover, sensor, binary sensor, button, and number entities
- Awning and slide position estimation
- Complete Level Monitor telemetry for the tested coach
- Complete generator control/status coverage for the tested app-visible generator functions

## Important Bluetooth Architecture Note

The Precision Plex Wireless TP module appears to allow only one active BLE connection at a time.

The integration intentionally maintains a persistent Bluetooth connection while Home Assistant is running. When Home Assistant is connected, the Precision Circuits iOS app may be unable to connect at the same time. This is expected behavior for the Wireless TP module.

## Precision Plex Pairing Notes

The official Precision Plex app performs a BLE bonding verification process before normal operation.

Observed official app sequence:

```text
Virgin first run - verifying connection
doConnect()
Attempt to connect
centralManager didConnect()
Connected to BLE Device. Now discovering services
peripheral didDiscoverServices()
process_pairing()
*** Bond verified - Pairing Complete ***
rvRead()
+++++++ RV READ++++++
```

The Precision Plex controller must be placed into mobile pairing mode before initial pairing.

## Official App BLE Characteristics

The official app diagnostic log reports these subscription/write characteristic identifiers:

```text
ANDROID1_CHAR_UUID: 02AA6F62-6F74-7061-6A61-6D61732E6361
ANDROID2_CHAR_UUID: 02BB6F62-6F74-7061-6A61-6D61732E6361
ANDROID3_CHAR_UUID: 02BB6F62-6374-7061-6A61-6D61332E6361
BLE_TX_CHAR_UUID:   BBC94B12-7BBC-42CE-BB6F-757DA304199F
```

Observed custom service:

```text
00726F62-6F74-7061-6A61-6D61732E6361
```

These match the characteristic families used by the Home Assistant integration for telemetry and control.

## Confirmed Working Feature Set

Tested and working as of **v4.2.4**.

### Controls

- `light.awning_light`
- `switch.water_pump`
- `switch.water_heater`
- `button.generator_start`
- `button.generator_stop`
- `button.generator_auto_start`
- `button.generator_auto_stop`
- `cover.awning`
- `cover.bed_slide`
- `cover.wardrobe_slide`
- `cover.sofa_slide`

### Telemetry and Status

Decoded from BLE notifications, primarily handle `0x002B` / characteristic `02AA`:

- `sensor.coach_battery`
- `sensor.fresh_water_tank`
- `sensor.grey_water_tank`
- `sensor.black_water_tank`
- `sensor.lp_gas_tank`
- `binary_sensor.generator_running`
- `sensor.generator_runtime`
- `sensor.generator_status`

Confirmed generator status values:

- `Stopped`
- `Running`
- `Performing Generator AutoStart`
- `Performing Generator AutoStop`
- `Will Not Start`

### Status / Movement Helpers

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

## Level Monitor and Generator Decoder

The Level Monitor and generator telemetry are decoded from the `02AA` telemetry packet, observed at handle `0x002B`.

Example payload:

```text
00 83 06 3F 3F 50 10 04 B5 ...
```

Known fields:

- Coach Battery: bytes 0-1, big-endian tenths of volts. Example: `0x0083 = 13.1 V`.
- Fresh Water: byte 2 low nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- Grey Water: byte 3 high nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- Black Water: byte 4 high nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- LP Gas: byte 5 high nibble. `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%`.
- Generator Status Word: bytes 6-7, big-endian.
- Generator Runtime: established decoder path uses adjacent bytes as big-endian tenths of hours. Example: `0x04B5 = 120.5 hours`.

Confirmed generator status values:

- `0x0004 = Stopped`
- `0x1004 = Running`
- `0x00A0 = AutoStart command accepted / transition begins`
- `0x2004 = Will Not Start`
- `0x6004 = Performing Generator AutoStart`
- `0x7004 = Performing Generator AutoStop`

Unknown generator status codes are exposed/logged as raw values for future decoding.

## Generator Control

Generator controls are implemented as guarded momentary button entities.

The integration blocks unsafe or redundant commands:

- Start is only allowed when live telemetry says the generator is not running.
- Stop is only allowed when live telemetry says the generator is running.
- AutoStart is only allowed when live telemetry says the generator is not running.
- AutoStop is only allowed when live telemetry says the generator is running.
- All generator commands are blocked when generator state is unknown or unavailable.

Confirmed command packets are written to the control characteristic / handle `0x0037` in app captures:

```text
Start press:     55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
Stop press:      55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
AutoStart press: 55 1D 10 0B 00 3E 0A 00 00 00 00 00 00 00 00 2B
AutoStop press:  55 1D 10 0B 00 3E 0B 00 00 00 00 00 00 00 00 2A
Release:         55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

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
- Confirm generator operating conditions are safe before starting or stopping it.
- Keep visual contact with moving equipment.
- Use Stop immediately if motion is unexpected.
- Verify travel-time settings before relying on full-open or full-close automation.

The integration includes timed safety limits for covers and generator command interlocks, but it does not replace operator awareness.

## Reference Calibrations

These travel times were validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

- Awning: 18 seconds open / 25 seconds close
- Bed Slide: 28 seconds open / 24 seconds close
- Wardrobe Slide: 18 seconds open / 17 seconds close
- Sofa Slide: 32 seconds open / 28 seconds close

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values can be adjusted through the Home Assistant Number entities without modifying the integration.

## Restore Cover Positions After Restart

Cover entities restore their last Home Assistant-known estimated position after Home Assistant restarts or the integration reloads.

The restored value is still an estimate. If the awning or slides are moved while Home Assistant is offline, the restored position may be stale until recalibrated or moved again through Home Assistant while connected.

## Clean Disable / Enable Lifecycle

The integration can be disabled and re-enabled from Home Assistant without requiring a full Home Assistant restart.

During unload, the integration stops the persistent BLE coordinator, cancels and awaits the BLE monitor task, disconnects the BLE client, removes stale startup callbacks, clears listeners, and unloads platforms cleanly.

## Current Project Status

For the tested 2022 Forest River Georgetown GT5 34M5, the core Precision Plex mobile-app-visible feature set has been decoded and validated.

Future work is limited to:

- Dashboard examples
- Improved entity naming/icons if desired
- Expanded protocol notes as new captures are discovered
- Additional coach-specific functions if other Precision Plex installations expose different app features
- Optional diagnostics for unknown packets/status codes
