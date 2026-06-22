# Historical README and Release Notes Collection

This file consolidates the older project README/release-note artifacts that were previously stored as many separate top-level Markdown files. Going forward, the repository should keep the current README at the root and roll older release/documentation snapshots into this historical collection.


---

## Historical Integration README Snapshot

<!-- Source: custom_components/precision_plex/README.md -->


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


---

## Previous Release Notes


---

<!-- Source: RELEASE_NOTES_v2.4.2.md -->


# Precision Plex v2.4.2 — Documentation & Protocol Reference Update

## Summary

This release focuses on documentation, protocol reference material, GitHub/HACS packaging improvements, and long-term maintainability.

The integration code remains functionally based on the known-good v2.4.1 baseline. The main changes are documentation, repository metadata, and packaging improvements.

## Highlights

- Added `/docs` protocol documentation
- Added BLE architecture documentation
- Added persistent BLE / Wireless TP replacement rationale
- Added state mapping reference
- Added command packet reference
- Added position estimation documentation
- Added Georgetown GT5 34M5 test environment notes
- Added contribution guide
- Added release history documentation
- Added HACS metadata file
- Corrected GitHub documentation and issue tracker URLs
- Updated README to clarify current recommended release and coach-specific support

## Primary Development Platform

2022 Forest River Georgetown GT5 34M5

## Current Stable Features

- Awning Light
- Water Pump
- Water Heater
- Awning Cover
- Bed Slide Cover
- Position Estimation
- Wall Panel Tracking
- Configurable Travel Times
- Bidirectional BLE Synchronization

## Known Limitations

- Position values are estimated rather than sensor-confirmed
- Travel times may require occasional calibration
- The Wireless TP monitor appears to allow only one active BLE connection
- Sofa Slide and Wardrobe Slide support are not yet implemented

## Next Planned Work

- Sofa Slide support
- Wardrobe Slide support
- Additional Wireless TP functions
- Expanded coach-specific protocol documentation


---

<!-- Source: RELEASE_NOTES_v2.5.0.md -->


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


---

<!-- Source: RELEASE_NOTES_v2.6.2.md -->


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


---

<!-- Source: RELEASE_NOTES_v2.6.3.md -->


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


---

<!-- Source: RELEASE_NOTES_v2.6.4.md -->


# Precision Plex v2.6.4 — Coach Battery Voltage Sensor Test

## Test Build

This build adds the first Level Monitor telemetry sensor to Home Assistant while preserving the v2.6.3 slide, awning, and restart-safe coordinator behavior.

## New Sensor

- Added `sensor.precision_plex_coach_battery`
- Reports coach battery voltage in volts
- Uses Home Assistant voltage device class and measurement state class

## Protocol Mapping

Coach battery voltage is decoded from the Precision Plex monitor notification on handle `0x002B`.

Observed mapping:

```text
00 88 = 136 = 13.6V
00 7D = 125 = 12.5V
```

Decoder:

```python
coach_voltage = int.from_bytes(payload[0:2], "big") / 10
```

## Existing Features Retained

- Improved `__init__.py` unload behavior for enable/disable without requiring a Home Assistant restart
- Improved coordinator stop/disconnect handling
- Awning, bed slide, wardrobe slide, and sofa slide support
- Restored cover position persistence across Home Assistant restarts
- Configurable travel-time number entities
- Wall-panel tracking


---

<!-- Source: RELEASE_NOTES_v2.6.4a.md -->


# Precision Plex v2.6.4a — Coach Battery Sensor Sender Fix

This test build keeps the v2.6.4 coach battery voltage sensor and fixes notification sender handling so the integration can decode 0x002B telemetry whether Home Assistant/Bleak passes the sender as an integer handle or a characteristic object.

## Fix

- Normalizes BLE notification sender values before decoding telemetry.
- Ensures Handle 0x002B packets decode the first word as coach battery voltage in tenths of a volt.
- Adds a warning log when coach battery voltage is successfully decoded.

## Confirmed decoder

```text
00 7D = 125 = 12.5 V
00 88 = 136 = 13.6 V
coach_voltage = int.from_bytes(payload[0:2], "big") / 10
```


---

<!-- Source: RELEASE_NOTES_v2.6.4b.md -->


# Precision Plex v2.6.4b — Coach Battery 02AA Telemetry Fix

This test release fixes the coach battery voltage sensor by subscribing to the correct Wireless TP telemetry characteristic.

## Fixes

- Adds a dedicated read/notify path for `02aa6f62-6f74-7061-6a61-6d61732e6361` / value handle `0x002B`.
- Decodes the first 16-bit big-endian word as tenths of a volt.
- Keeps `02bb` state decoding separate so wall-panel state packets do not overwrite battery telemetry.

## Confirmed decode examples

```text
00 88 = 136 = 13.6 V
00 7D = 125 = 12.5 V
```

## Existing behavior retained

- v2.6.3 restart-safe enable/disable behavior
- Slide/awning position restore behavior
- Existing light, switch, cover, and number entities


---

<!-- Source: RELEASE_NOTES_v2.6.22.md -->


# Precision Plex v2.6.22 - Fresh Tank 02AA Decoder Test

## Added
- Adds a Fresh Water Tank sensor.
- Decodes Fresh Water level from the confirmed 02AA / handle 0x002B levels packet.

## Confirmed Fresh Water mapping
- `0x00` -> `0%`
- `0x03` -> `33%`
- `0x06` -> `67%`
- `0x0A` -> `100%`

## Notes
- Keeps the working coach battery voltage decoder from the same 02AA packet.
- Removes reliance on the earlier experimental 0x0033/channel/probe logic for Fresh Water.
- Keeps the improved unload/reload behavior so the integration can be enabled/disabled without a full Home Assistant restart.


---

<!-- Source: RELEASE_NOTES_v2.6.23.md -->


# Precision Plex v2.6.23

## Changes

- Updates Fresh Water decoding to use the low nibble of byte 2 in the 0x002B / 02AA levels packet.
- Adds Grey Water Tank sensor decoded from the high nibble of byte 3 in the same 0x002B / 02AA levels packet.
- Uses the shared tank nibble mapping: 0x0=0%, 0x3=33%, 0x6=67%, 0xA=100%.

## Test Focus

- Verify Fresh still follows Empty / 1/3 / 2/3 / Full.
- Verify Grey Empty = 0%.
- Verify Grey 1/3 = 33%.


---

<!-- Source: RELEASE_NOTES_v2.6.24.md -->


# Precision Plex v2.6.24

Tank monitor decoder update.

## Changes

- Adds Black Water Tank sensor.
- Keeps Fresh Water Tank decoder as byte 2 low nibble.
- Keeps Grey Water Tank decoder as byte 3 high nibble.
- Adds Black Water Tank decoder as byte 4 high nibble.
- Uses the confirmed tank nibble scale: `0x0 = 0%`, `0x3 = 33%`, `0x6 = 67%`, `0xA = 100%`.

## 0x002B / 02AA tank layout used in this build

- Fresh: `payload[2] & 0x0F`
- Grey: `(payload[3] & 0xF0) >> 4`
- Black: `(payload[4] & 0xF0) >> 4`


---

<!-- Source: RELEASE_NOTES_v2.6.25.md -->


# Precision Plex v2.6.25

Test release adding LP Gas tank level decoding from the confirmed 0x002B / 02AA levels packet.

## Changes

- Keeps confirmed Fresh / Grey / Black tank decoders.
- Adds LP Gas Tank sensor.
- LP Gas is decoded from byte 5 high nibble of handle 0x002B / characteristic 02AA.

## LP Mapping

- 0x0 = 0%
- 0x2 = 25%
- 0x5 = 50%
- 0x7 = 75%
- 0xA = 100%


---

<!-- Source: RELEASE_NOTES_v2.6.26.md -->


# Precision Plex v2.6.26 - Level Monitor Complete / GitHub Ready

This is the cleaned GitHub-ready release that consolidates the tested work from v2.6.3 through v2.6.25.

## Confirmed Working Feature Set

### Controls

- Awning Light
- Water Pump
- Water Heater
- Awning cover
- Bed Slide cover
- Wardrobe Slide cover
- Sofa Slide cover

### Level Monitor

Decoded from `02AA` / handle `0x002B`:

- Coach Battery
- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank

## Confirmed Level Decoder

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |

## Notes

- This release does not change the tested Fresh/Grey/Black tank decoder behavior from v2.6.24/v2.6.25.
- LP Gas was added as the next confirmed nibble in the same Level Monitor packet.
- Documentation has been updated to make this repository ready for GitHub publishing.


---

<!-- Source: RELEASE_NOTES_v2.6.27.md -->


# Precision Plex v2.6.27 - Generator Telemetry Test

This release adds generator telemetry to the confirmed `0x002B` / `02AA` status packet decoder.

## Added

- `binary_sensor.generator_running`
- `sensor.generator_runtime`

## Generator Decode

```text
Stopped: 0083 000F 0F50 0004 B400 0001 ...
Running: 0088 000F 0F50 1004 B400 0001 ...
```

- Generator Running: byte 6 bit `0x10`
- Generator Runtime: bytes 7-8, big-endian tenths of hours
- Example: `0x04B4` = 1204 tenths = 120.4 hours

## Unchanged

- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank
- Coach Battery Voltage
- Existing controls and cover travel-time calibration


---

<!-- Source: RELEASE_NOTES_v2.6.28.md -->


# Precision Plex v2.6.28 - Generator Control Test

Adds guarded generator control buttons using the command packets captured from the Precision Plex iOS app.

## Added

- Generator Start button
- Generator Stop button
- State-aware safety interlocks based on live Generator Running telemetry

## Generator Commands

- Start press: `55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33`
- Stop press: `55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32`
- Release: `55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34`

## Safety Behavior

- Generator Start is available only when Generator Running is false.
- Generator Stop is available only when Generator Running is true.
- Both buttons are unavailable when generator telemetry is unknown or unavailable.
- The command handler also re-checks generator state immediately before writing.

## Unchanged

- Fresh, Grey, Black, LP, Coach Battery, and Generator Runtime telemetry remain unchanged from v2.6.27.


---

<!-- Source: RELEASE_NOTES_v2.6.29.md -->


# Precision Plex v2.6.29 - Generator Control & Complete Coach Monitoring

This is the current GitHub-ready release.

v2.6.29 consolidates the tested work from v2.6.3 through v2.6.28 and adds confirmed generator telemetry plus guarded generator Start/Stop control.

## Confirmed Working Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Confirmed Working Telemetry

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours

## Configuration Entities

- Awning Open Seconds
- Awning Close Seconds
- Bed Slide Open Seconds
- Bed Slide Close Seconds
- Wardrobe Slide Open Seconds
- Wardrobe Slide Close Seconds
- Sofa Slide Open Seconds
- Sofa Slide Close Seconds

## Generator Support

Added and validated:

- `binary_sensor.generator_running`
- `sensor.generator_runtime`
- `button.generator_start`
- `button.generator_stop`

Safety interlocks:

- Generator Start is only available when generator telemetry says the generator is not running.
- Generator Stop is only available when generator telemetry says the generator is running.
- Both commands are blocked when generator state is unknown or unavailable.

## Decoded Precision Plex Telemetry

Level Monitor / Generator telemetry packet:

```text
Handle: 0x002B
Characteristic: 02AA
```

Known fields:

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |
| Generator Running | byte 6 bit `0x10` | `0x00=stopped`, `0x10=running` |
| Generator Runtime | bytes 7-8, big-endian tenths of hours | `0x04B5` = 120.5 hours |

## Generator Command Mapping

Written to control handle `0x0037` in PacketLogger captures:

```text
Start press: 55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
Stop press:  55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
Release:     55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

## Validation

All telemetry and control functions were validated against a live Precision Plex installation using:

- Precision Plex wall panel displays
- Precision Plex mobile application behavior
- Bluetooth PacketLogger captures
- Home Assistant integration testing

Generator validation confirmed:

- Generator Running changed correctly from Not Running to Running.
- Generator Runtime displayed 120.4 hours, then updated live to 120.5 hours in Home Assistant at the same time as the Precision Plex display.
- Generator Start successfully started the generator from Home Assistant.
- Generator Stop successfully stopped the generator from Home Assistant.
- Start/Stop safety interlocks behaved correctly in all tested states.

## Tested Platform

- 2022 Forest River Georgetown GT5 34M5
- Precision Circuits Precision Plex Control System
- Precision Circuits Wireless TP module
- Home Assistant

## Project Status

The core Precision Plex integration is now stable and feature complete for the major coach functions available on the tested platform.

## Future Work

- Generator fault decoding
- Generator maintenance information
- Native slide position telemetry
- Native awning position telemetry
- Additional coach-specific functions
- Dashboard examples
- Expanded protocol documentation


---

<!-- Source: RELEASE_NOTES_v2.6.30.md -->


# Precision Plex v2.6.30 - Generator AutoStart / AutoStop Test

This test release adds managed generator AutoStart and AutoStop support based on Precision Plex app PacketLogger captures.

## Added

- Generator AutoStart button
- Generator AutoStop button
- Generator Status sensor

## Generator Managed Commands

- AutoStart: `55 1D 10 0B 00 3E 0A 00 00 00 00 00 00 00 00 2B`
- AutoStop: `55 1D 10 0B 00 3E 0B 00 00 00 00 00 00 00 00 2A`
- Release: `55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34`

## Generator Status Decode

Observed status/transition values in the 0x002B / 02AA status packet:

- `0004` = Stopped
- `1004` = Running
- `00A0` = AutoStart Accepted / transition begins
- `6004` = Performing Generator AutoStart
- `7004` = Performing Generator AutoStop

## Safety Interlocks

- Start and AutoStart are only available when Generator Status is Stopped.
- Stop and AutoStop are only available when Generator Status is Running.
- All generator command buttons are blocked when generator status is unknown or transitional.

Existing Fresh, Grey, Black, LP, Coach Battery, slide, awning, pump, water heater, and generator runtime telemetry remain unchanged.


---

<!-- Source: RELEASE_NOTES_v2.6.31.md -->


# Precision Plex Home Assistant Integration v2.6.31

This test release adds decoding for the failed generator AutoStart condition captured during controlled testing.

## New

- Generator Status now reports `Will Not Start`.
- Decoded status: `0x2004` / status byte `0x20`.
- Unknown generator status codes are logged with the raw 0x002B payload for future decoding.

## Retained from v2.6.30

- Generator Start button
- Generator Stop button
- Generator AutoStart button
- Generator AutoStop button
- Generator Running binary sensor
- Generator Runtime sensor
- Generator Status sensor
- Start/Stop and AutoStart/AutoStop safety interlocks

## Confirmed Generator Status Mapping

- `0x0004` = Stopped
- `0x1004` = Running
- `0x00A0` = AutoStart Accepted
- `0x2004` = Will Not Start
- `0x6004` = Performing Generator AutoStart
- `0x7004` = Performing Generator AutoStop

## Notes

A matching `Will Not Stop` state likely exists, but it has not been safely captured yet. This build does not guess that value. Any unknown future status code will be shown and logged for later analysis.


---

<!-- Source: RELEASE_NOTES_v2.6.32.md -->


# Precision Plex Home Assistant Integration v2.6.33

This is a GitHub-ready cleanup release built from the validated v2.6.31 generator work.

## Release Status

For the tested 2022 Forest River Georgetown GT5 34M5, this release is considered feature complete for the core Precision Plex functions visible in the Precision Plex mobile app.

## Confirmed Working Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Confirmed Working Telemetry

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours
- Generator Status

## Confirmed Generator Status Values

- `0x0004` = Stopped
- `0x1004` = Running
- `0x00A0` = AutoStart accepted / transition begins
- `0x2004` = Will Not Start
- `0x6004` = Performing Generator AutoStart
- `0x7004` = Performing Generator AutoStop

## Documentation Updated

- README updated for v2.6.33 and app-visible feature-complete status.
- Protocol overview expanded with the final generator state map.
- State mapping expanded with tank, LP, generator runtime, and generator status fields.
- Command mapping updated with Generator AutoStart and AutoStop commands.
- Coach-specific documentation updated for the 2022 Forest River Georgetown GT5 34M5.
- Future work list cleaned up to remove features not exposed in the tested coach's Precision Plex app.

## Features Checked But Not Available in the Tested Coach App

The following are not current targets for this coach because they are not available in the Precision Plex mobile app:

- HVAC / thermostat controls
- Generator fault-code details beyond the decoded generator status field
- Shore power telemetry
- Inverter telemetry
- Tank heater controls
- Water heater telemetry
- Native slide position telemetry
- Native awning position telemetry

## Future Work

- Dashboard examples
- Improved entity naming/icons if desired
- Expanded protocol notes as new captures are discovered
- Additional coach-specific functions if other Precision Plex installations expose different app features
- Optional diagnostics for unknown packets/status codes


---

<!-- Source: RELEASE_NOTES_v2.6.33.md -->


# Precision Plex Home Assistant Integration v2.6.33

## Feature Complete Release with Protocol Documentation

This release represents the completion of all major Precision Plex functionality exposed through the official Precision Plex mobile application for the tested coach platform.

Version 2.6.33 consolidates all functionality developed throughout the reverse-engineering effort, including lighting control, utilities, tank monitoring, slide and awning control, generator control, generator telemetry, protocol documentation, and coach-specific application analysis.

All functionality has been validated against a live Precision Plex installation using Home Assistant, Bluetooth PacketLogger captures, Precision Plex controller displays, Precision Plex wireless touch panel operation, and the official Precision Plex mobile application.

## Supported Controls

### Lighting

- Awning Light

### Utilities

- Water Pump
- Water Heater

### Slides

- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

### Awnings

- Awning Cover

### Generator

- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop

## Supported Telemetry

### Electrical

- Coach Battery Voltage

### Tank Monitoring

- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank

### Generator

- Generator Running Status
- Generator Runtime Hours
- Generator Status

Supported Generator States:

- Stopped
- Running
- Auto Starting
- Auto Stopping
- Will Not Start

## Generator Safety Features

- Prevent Start while already running
- Prevent Stop while already stopped
- Prevent AutoStart while already running
- Prevent AutoStop while already stopped
- Unknown-state protection
- Unknown status code logging

## Precision Plex Telemetry Decoding

### Coach Battery

Example:

`0x0083 = 13.1V`

### Fresh Water Tank

- `0x0 = Empty`
- `0x3 = 1/3`
- `0x6 = 2/3`
- `0xA = Full`

### Grey Water Tank

- `0x0 = Empty`
- `0x3 = 1/3`
- `0x6 = 2/3`
- `0xA = Full`

### Black Water Tank

- `0x0 = Empty`
- `0x3 = 1/3`
- `0x6 = 2/3`
- `0xA = Full`

### LP Gas Tank

- `0x0 = Empty`
- `0x2 = 25%`
- `0x5 = 50%`
- `0x7 = 75%`
- `0xA = Full`

### Generator Status

- `0x0004 = Stopped`
- `0x1004 = Running`
- `0x6004 = Auto Starting`
- `0x7004 = Auto Stopping`
- `0x2004 = Will Not Start`

### Generator Runtime

Example:

`0x04B4 = 120.4 Hours`

## Precision Plex Command Decoding

### Generator Start

`551D100B003E02000000000000000033`

### Generator Stop

`551D100B003E03000000000000000032`

### Generator AutoStart

`551D100B003E0A00000000000000002B`

### Generator AutoStop

`551D100B003E0B00000000000000002A`

### Generator Release

`551D100B003F00000000000000000034`

## Coach Profile

Validated against:

- Forest River Georgetown GT5 34M5
- Precision Plex Control System
- Precision Plex Wireless Touch Panel

Application Information:

- Model: GT 34M5 with 2AC
- Coach Profile: `Model_Georgetown_GT_34M5_w_2AC`
- App Version: 5.06.01
- File Version: 3.989
- STM Version: 4

## Precision Plex Application Characteristics

ANDROID1_CHAR_UUID

`02AA6F62-6F74-7061-6A61-6D61732E6361`

ANDROID2_CHAR_UUID

`02BB6F62-6F74-7061-6A61-6D61732E6361`

ANDROID3_CHAR_UUID

`02BB6F62-6374-7061-6A61-6D61332E6361`

BLE_TX_CHAR_UUID

`BBC94B12-7BBC-42CE-BB6F-757DA304199F`

Observed Custom Service:

`00726F62-6F74-7061-6A61-6D61732E6361`

## Features Not Present in the Official Application

The following features are not exposed by the official Precision Plex application for the tested coach profile:

- HVAC Controls
- Thermostat Telemetry
- Generator Fault Codes
- Shore Power Monitoring
- Inverter Monitoring
- Tank Heater Controls
- Water Heater Telemetry
- Slide Position Telemetry
- Awning Position Telemetry

Application diagnostics indicate:

- `hvacSupportOnApp = false`
- `hvacSendsHeatPumpBits = false`

## Project Status

This release is considered feature complete for all major functions exposed through the official Precision Plex mobile application for the tested coach platform.

## Acknowledgements

This project was developed through extensive reverse engineering of Precision Plex Bluetooth Low Energy communications, including PacketLogger analysis, protocol decoding, telemetry mapping, command discovery, and real-world validation against a live Precision Plex installation.

The result is a Home Assistant integration providing feature parity with the official Precision Plex mobile application while exposing the data and controls natively within Home Assistant.


---

<!-- Source: RELEASE_NOTES_v3.0.0.md -->


# Precision Plex Home Assistant Integration v3.0.0

## Major Release: Built-In BLE Pairing / Bonding

This release promotes the working Precision Plex BLE pairing workflow into the integration setup flow.

Version 3.0.0 is a major release because setup behavior has changed significantly: Home Assistant can now perform the Precision Plex BLE bonding step during integration setup instead of requiring the system to already be paired manually.

## Highlights

- Adds a Home Assistant config-flow pairing step.
- Registers a temporary BlueZ `NoInputNoOutput` pairing agent during setup.
- Supports the Precision Plex app-style BLE security flow observed in PacketLogger traces.
- Confirms the working BLE control endpoint is the Precision advertiser, for example `80:4B:50:D2:44:B4`, rather than the separate `BLE#0x...` advertiser.
- Preserves the existing v2.6.33 runtime behavior and supported entities.

## Pairing Behavior

During setup, select the discovered Precision Plex device, put the Precision Plex console into **Pair with Mobile** mode, and continue the config flow. The integration registers a temporary BlueZ pairing agent, requests BLE pairing/bonding, writes the existing app/session initialization payload, and then creates the Home Assistant config entry.

Successful pairing has been validated with BlueZ showing:

```text
Paired: yes
Bonded: yes
Trusted: yes
LE.Paired: yes
LE.Bonded: yes
```

## Technical Notes

PacketLogger analysis showed the official app receives `Insufficient Authentication` from a protected GATT operation, then proceeds through a normal BLE SMP pairing/security exchange. The final working Home Assistant implementation therefore uses BlueZ bonding with a temporary pairing agent rather than treating the `06` payload as the pairing mechanism itself.

The `06` payload remains an application/session initialization write after the BLE bond is established.

## Upgrade Notes

Existing paired installations should continue to work. New installations, or systems where Home Assistant has been unpaired from the Precision Plex console, should use the config-flow pairing step.

If pairing fails, remove the failed device/bond from BlueZ and the Precision Plex console, restart Home Assistant, then retry setup with the console in **Pair with Mobile** mode.


---

<!-- Source: RELEASE_NOTES_v4.0.0.md -->


# Precision Plex v4.0.0 Release Notes

## Highlights

Precision Plex v4.0.0 adds manual jog and position reset controls for the awning and all slide covers while preserving the proven press-and-hold cover movement engine from v3.0.0.

## Added

- Cover jog buttons for every slide and awning direction:
  - Awning Jog Extend / Jog Retract
  - Bed Slide Jog Extend / Jog Retract
  - Wardrobe Slide Jog Extend / Jog Retract
  - Sofa Slide Jog Extend / Jog Retract
- Position reset buttons for every cover:
  - Reset Fully Extended
  - Reset Fully Retracted
- Configurable jog duration number entities:
  - Awning Jog Seconds defaults to 2 seconds
  - Bed Slide Jog Seconds defaults to 5 seconds
  - Wardrobe Slide Jog Seconds defaults to 5 seconds
  - Sofa Slide Jog Seconds defaults to 5 seconds

## Behavior

- Jog buttons are manual overrides and intentionally run even when the estimated position already says the cover is fully extended or fully retracted.
- Estimated position is still updated from elapsed jog time and clamped between 0% and 100%.
- Reset buttons do not move hardware. They only correct Home Assistant's estimated position.
- Normal cover open, close, stop, and set-position behavior remains unchanged.

## Notes

The jog buttons reuse the same app-like hold stream and release/stop packets as the cover entity, so they should behave like short timed button holds while keeping the cover position model synchronized.


---

<!-- Source: RELEASE_NOTES_v4.0.1.md -->


# Precision Plex v4.0.1

## Fixes

- Fixed generator command buttons appearing unavailable when the generator telemetry intermittently reports status `0x80`.
- Generator status decoding now keeps the raw status byte for diagnostics while using the lower status bits for command eligibility.
- A stopped generator reporting `0x80` is treated as stopped, so Generator Start and Generator AutoStart remain available.


---

<!-- Source: RELEASE_NOTES_v4.0.2.md -->


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


---

<!-- Source: RELEASE_NOTES_v4.0.3.md -->


# Precision Plex v4.0.3 — Cleanup & Diagnostics

This release cleans up the GitHub-ready package and adds Home Assistant diagnostics support for easier troubleshooting and future development.

## Added

- Home Assistant diagnostics download support.
- Diagnostics include redacted config-entry data, BLE availability, expected GATT UUIDs, discovered characteristics when connected, raw 02BB state, decoded 02BB state bits, raw 02AA telemetry, decoded tank/LP levels, coach voltage, and generator status/runtime fields.

## Changed

- Updated manifest version to `4.0.3`.
- Updated README version references to `v4.0.3`.

## Cleanup

- Removed generated `__pycache__` and `.pyc` files from the release ZIP.

## Notes

Diagnostics redact the Bluetooth address and config-entry unique identifiers before export.


---

<!-- Source: RELEASE_NOTES_v4.1.0.md -->


# Precision Plex v4.1.0 — Coach Profile Foundation

v4.1.0 introduces the first coach profile architecture for the Precision Plex Home Assistant integration.

## What Changed

- Added a `profiles/` package for coach-specific mappings.
- Moved the Georgetown GT5 34M5 command and state-bit mappings into `profiles/georgetown_gt5_34m5.py`.
- Kept the Georgetown GT5 34M5 profile as the default active profile.
- Preserved the existing v4.0.3 entity names, unique IDs, commands, state bits, and timing behavior.
- Added active coach profile information to Home Assistant diagnostics.
- Bumped the integration version to `4.1.0`.

## Compatibility

This is intended to be a low-risk refactor release. It should behave the same as v4.0.3 on the tested Georgetown GT5 34M5 coach.

## Why This Matters

Coach profiles make it possible to support additional Precision Plex RV floorplans in the future without mixing all command mappings and telemetry definitions into the core integration code.


---

<!-- Source: RELEASE_NOTES_v4.1.1.md -->


# Precision Plex v4.1.1 — Coach Profile Import Hotfix

This hotfix resolves a startup failure introduced in v4.1.0 during the coach profile refactor.

## Fixed

- Restored the `CONTROL_CHARACTERISTIC_UUID` compatibility export in `const.py`.
- Fixes Home Assistant setup failure: `cannot import name CONTROL_CHARACTERISTIC_UUID`.

## Notes

No entity behavior, BLE commands, telemetry decoding, or coach profile behavior changed from v4.1.0. This is a startup/import compatibility fix only.


---

<!-- Source: RELEASE_NOTES_v4.2.0.md -->


# Precision Plex v4.2.0 — Native Cover Entities

This release focuses on making the awning and slide controls behave like first-class Home Assistant cover entities while preserving the tested legacy jog and calibration controls.

## What changed

- Bumped integration version to `4.2.0`.
- Clarified the cover platform as the native Home Assistant cover interface for the awning and slides.
- Added native cover diagnostic attributes so support logs clearly identify these entities as the primary cover interface.
- Added the Home Assistant awning device class to the awning entity for better UI/HomeKit presentation.
- Preserved existing cover unique IDs, jog buttons, reset/calibration buttons, runtime timing numbers, BLE commands, and coach profile behavior.

## Native cover behavior

The following devices continue to expose native Home Assistant cover controls:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Supported services include:

- `cover.open_cover`
- `cover.close_cover`
- `cover.stop_cover`
- `cover.set_cover_position`

## Compatibility

This release is designed to be upgrade-safe from v4.1.1. No remove/re-add, re-pairing, or configuration migration should be required.

Legacy jog and calibration buttons remain available so existing dashboards and workflows continue to work.


---

<!-- Source: RELEASE_NOTES_v4.2.1.md -->


# Precision Plex v4.2.1 — Clean Native Covers

This hotfix completes the native cover rollout started in v4.2.0.

## What changed

- Added clean native cover entities for Awning, Bed Slide, Wardrobe Slide, and Sofa Slide.
- Preserved the original cover entities and unique IDs for backward compatibility.
- Preserved existing jog, calibration, and timing controls.
- Created new unique IDs for the clean cover entities so Home Assistant and HomeKit can discover them as new accessories.
- Kept the awning classified as a native awning cover.

## Why this release exists

v4.2.0 mainly updated the awning classification. The slide covers already existed in the older platform, so users did not see the intended new clean native entities. v4.2.1 adds those clean entities alongside the existing ones instead of replacing anything.

## Upgrade notes

No re-pairing or integration reconfiguration is required. After restart, you should see new clean cover entities in addition to the existing cover entities. Use the new clean entities for dashboards and HomeKit exposure.


---

<!-- Source: RELEASE_NOTES_v4.2.2.md -->


# Precision Plex v4.2.2 — Native Cover Startup Hotfix

This is a hotfix release for v4.2.1.

## Fixed

- Fixed a startup failure caused by shared native cover helper methods being attached only to the new clean cover subclass instead of the preserved legacy cover class.
- Restored availability for existing awning, bed slide, wardrobe slide, and sofa slide cover entities.
- Preserved the new clean native cover entities introduced for HomeKit/dashboard testing.

## Upgrade Notes

Install over v4.2.1 and restart Home Assistant. Do not remove or re-add the integration.

## Testing Focus

After restart, confirm:

- Precision Plex loads without cover platform errors.
- Existing cover entities are available again.
- New clean native cover entities are present.
- Sensors, switches, generator controls, jog buttons, and calibration buttons remain available.


---

<!-- Source: RELEASE_NOTES_v4.2.3.md -->


# Precision Plex v4.2.3 — Native Cover Cleanup

## Overview

This release cleans up the v4.2 native cover transition. v4.2.2 correctly restored availability and created both legacy and clean native cover entities. v4.2.3 makes that transition clearer in Home Assistant by labeling the old preserved entities as legacy and making the clean native cover entities the primary entities for new installs and HomeKit exposure.

## What Changed

- Legacy cover entities are now labeled with `Legacy` in their default name.
- Legacy cover entities are disabled by default for new installations. Existing installations will keep already-enabled entities until the user disables or hides them.
- Clean native cover entities remain enabled by default.
- Slide native cover entities are left as generic covers instead of being forced into a misleading window-style presentation.
- Awning remains marked as a native awning cover.
- Existing unique IDs are preserved so dashboards and automations are not forcibly broken.

## Recommended HomeKit Setup

Expose the clean native cover entities to HomeKit:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Remove or exclude the legacy cover entities from HomeKit Bridge.

## Upgrade Notes

No re-pairing is required. No Precision Plex configuration changes are required. Restart Home Assistant after installing the release.


---

<!-- Source: RELEASE_NOTES_v4.2.4.md -->


# Precision Plex v4.2.4 — Native Cover Cleanup

This release completes the v4.2 native cover transition by stopping creation of the preserved legacy cover entities.

## Changed

- New clean native cover entities are now the only cover entities created by the integration.
- Legacy cover entities are no longer created during platform setup.
- Jog buttons, calibration buttons, travel timing numbers, and jog timing numbers remain available.
- Awning remains classified as an awning cover.
- RV slide covers remain generic covers to avoid the misleading window device class/icon.

## Existing Home Assistant Entity Registry Note

Home Assistant may keep old legacy entity registry entries from previous v4.2.x installs. If those stale entries still appear after upgrade, remove the old legacy/unavailable cover entities from Settings → Devices & Services → Entities.

## Expected Result

After cleanup, the active cover set should be:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Each should expose standard Home Assistant cover controls while the existing jog and calibration controls remain available on the Precision Plex device.


---

<!-- Source: RELEASE_NOTES_v4.3.1.md -->


# Precision Plex v4.3.1 — HomeKit Level Sensor Cleanup

This maintenance release refines the Enhanced HomeKit experience introduced in v4.3.0.

## Improvements

- Keeps the new HomeKit-friendly Fresh Water, Grey Water, Black Water, and Propane percentage helpers as humidity-style sensors for clean Apple Home display.
- Marks the original native tank/propane telemetry sensors as diagnostic entities so they are less likely to be auto-exposed to HomeKit as generic/air-quality-style sensors.
- Cleans up helper display names so Apple Home can show simple names like Fresh Water, Grey Water, Black Water, and Propane.

## Notes

If an older native tank or propane entity was already exposed through the HomeKit Bridge, remove that accessory from the bridge or exclude the original entity. The preferred Apple Home entities are the new HomeKit helper sensors.


---

<!-- Source: RELEASE_NOTES_v4.3.2.md -->


# Precision Plex v4.3.2 — HomeKit Exposure Cleanup

This release tightens the HomeKit experience introduced in v4.3.x by reducing noisy/internal entities that Apple Home was rendering as confusing categories such as occupancy/person, generic switches, or miscellaneous tiles.

## Changed

- Marks decoded Precision Plex state-bit binary sensors as diagnostic entities.
- Marks the generator running binary status as diagnostic.
- Marks generator runtime and generator status telemetry as diagnostic.
- Marks slide/awning jog and position reset utility buttons as configuration entities.
- Marks travel-time tuning number entities as configuration entities.

## Unchanged

- Keeps the v4.3.1 HomeKit-friendly humidity percentage helper sensors for Fresh Water, Grey Water, Black Water, and Propane.
- Keeps core controls unchanged: covers, awning light, water pump, water heater, and generator command buttons.
- Does not change BLE command payloads, pairing behavior, cover timing logic, or telemetry decoding.

## Notes

After installing, restart Home Assistant and review the HomeKit Bridge include/exclude list. Existing entities already added to Apple Home may need to be removed from the Home app or re-synced after Home Assistant updates their entity categories.


---

<!-- Source: RELEASE_NOTES_v4.3.3.md -->


# Precision Plex v4.3.3 - HomeKit Cleanup and Generator Runtime Guard

## Fixes

- Adds a guard for generator runtime telemetry so occasional malformed lower values do not overwrite the last known good runtime.
- Prevents Home Assistant recorder warnings caused by `total_increasing` generator runtime dropping temporarily.
- Preserves the existing generator runtime decoder and diagnostics while filtering non-monotonic samples.

## HomeKit

- Keeps the v4.3.x HomeKit-friendly helper sensors and exposure cleanup work.


---

<!-- Source: RELEASE_NOTES_v4.3.4.md -->


# Precision Plex v4.3.4 - Quiet Generator Runtime Guard

This maintenance release keeps the v4.3.3 generator runtime protection but prevents normal bad telemetry samples from spamming the Home Assistant log.

## Fixed

- Demotes ignored decreasing generator runtime samples from warning/error-level logging to debug logging.
- Changes the generator runtime sensor state class from `total_increasing` to `measurement` so Home Assistant Recorder does not complain when the Precision Plex telemetry occasionally reports a bogus lower runtime value.
- Keeps the runtime guard in place so the displayed runtime is not overwritten by obvious decreasing samples during a running session.

## Retained

- v4.3.2 HomeKit exposure cleanup.
- v4.3.x HomeKit-friendly humidity percentage helper sensors for Fresh Water, Grey Water, Black Water, and Propane.

## Packaging

- Built without `__pycache__` directories or `.pyc` files.


---

<!-- Source: RELEASE_NOTES_v4.3.5.md -->


# Precision Plex v4.3.5

## Generator Runtime Outlier Protection

This release improves the generator runtime guard added in the v4.3.x HomeKit cleanup series.

### Fixed

- Prevents implausibly high generator runtime samples, such as thousands of hours, from being accepted as the stored runtime.
- Prevents a bad high sample from causing later legitimate runtime samples to look like decreases.
- Keeps the existing decreasing-sample protection.
- Adds protection against implausible jumps between accepted live telemetry samples.

### Diagnostics

The Generator Runtime sensor now includes diagnostic attributes for the last ignored runtime sample and the reason it was ignored.

### Packaging

- Source-only GitHub/HACS-ready package.
- Excludes `__pycache__`, `.pyc`, and temporary build artifacts.


---

<!-- Source: RELEASE_NOTES_v4.3.6.md -->


# Precision Plex v4.3.6

Generator runtime diagnostic build.

This release keeps the v4.3.5 runtime protection and adds targeted warning-level diagnostic logging for packets that reach the generator runtime decoder.

## Added

- Logs the generator runtime decode decision for each runtime candidate:
  - accepted
  - decreasing
  - implausibly_high
  - implausible_jump
- Logs nearby 16-bit candidate byte windows so we can determine whether the runtime is being decoded from the wrong packet or wrong offset.
- Includes raw packet length, status byte, status word, decoded candidate, previous accepted runtime, and full raw packet hex.

## Notes

This is intentionally a short-term diagnostic build. It may produce repeated warning-level log lines while installed. Once the bad packet pattern is identified, the diagnostic trace should be removed or demoted back to debug level.


---

<!-- Source: RELEASE_NOTES_v4.3.7.md -->


# Precision Plex v4.3.7 - Generator Runtime Field Diagnostics

This diagnostic build keeps the v4.3.5/v4.3.6 generator runtime protections and adds more focused tracing around the suspected runtime field-width issue.

## What changed

- Adds byte-level diagnostics for generator runtime packets.
- Logs bytes 6-9 and multiple candidate interpretations.
- Adds masked 12-bit and 14-bit candidates for the suspected runtime field.
- Adds a candidate that combines the previously accepted high byte with the current low byte.
- Emits warning-level diagnostics only for rejected or non-standard runtime frames; normal accepted `0x0004` frames are debug-level.

## Purpose

This is intended to prove whether packets such as `0x0060` are non-runtime/status frames being misread as runtime, or whether the generator runtime field uses a narrower byte/nibble layout than originally assumed.


---

<!-- Source: RELEASE_NOTES_v4.3.8.md -->


# Precision Plex v4.3.8

## Generator Runtime Masked Decode Test

This diagnostic build keeps the v4.3.5 runtime safety guard and adds a conservative masked/stabilized runtime decode path.

### Changes

- Detects runtime frames where the raw bytes 7-8 value is implausible but the current low byte can be safely combined with the previously accepted high byte.
- Uses the stabilized value only when it is monotonic and within the live jump threshold.
- Logs masked decode decisions so the 0x0004 vs 0x0060 runtime-field behavior can be verified from Home Assistant logs.
- Keeps existing HomeKit cleanup and helper sensor behavior from v4.3.x.

### Expected result

Generator runtime should remain at the correct real value even when status/flag bits contaminate the apparent high byte.


---

<!-- Source: RELEASE_NOTES_v4.3.9.md -->


# Precision Plex v4.3.9

Frame alignment protection diagnostics build.

## Changes

- Adds a pre-decode guard for shifted 02AA telemetry frames.
- Rejects one-byte-misaligned frames before they can update tank, propane, generator, pump, or other fixed-position entities.
- Keeps the v4.3.8 generator runtime protection and masked decode behavior.
- Logs rejected misaligned frames with the raw packet so the frame-boundary issue can be confirmed from Home Assistant logs.

## Why

Runtime diagnostics showed packets like the normal frame:

```text
00 87 00 0f 0f 50 00 04 b6 ... ae
```

and a shifted version:

```text
87 00 0f 0f 50 00 04 b6 ... ae 55
```

The shifted frame caused fixed byte offsets to decode the wrong fields, which could affect more than generator runtime. This build rejects that frame pattern before any entity state is updated.


---

<!-- Source: RELEASE_NOTES_v4.4.0.md -->


# Precision Plex v4.4.0 — Generator Runtime Source Diagnostics

This diagnostic release keeps the stable HomeKit cleanup and generator runtime protections from the v4.3.x series, then adds focused logging to identify which generator telemetry packet variant is the true runtime source.

## What changed

- Keeps the v4.3.9 runtime outlier and flag-bit protection.
- Adds focused generator runtime source diagnostics.
- Logs same-shaped generator telemetry variants when the low runtime byte changes away from the previously accepted value.
- Includes nearby bytes 6–12, raw status, raw word, generator state, current/previous low bytes, and decode decision.
- Does not intentionally change control behavior or HomeKit entity cleanup.

## Testing goal

Run this build long enough to capture the repeating byte-8 variant family, especially values such as `0x0B`, `0x16`, `0x2D`, `0x5B`, and `0xB6`. The goal is to identify which variant should be allowed to update the persistent generator runtime sensor.


---

<!-- Source: RELEASE_NOTES_v4.4.2.md -->


# Precision Plex v4.4.2 — HomeKit Naming Polish Merge

This release applies the HomeKit naming and presentation polish on top of the existing v4.4.1 codebase provided by the user, preserving the current runtime protections and telemetry behavior.

## Changes

- Uses exact friendly names for HomeKit-facing helper level sensors so Apple Home shows cleaner labels.
- Renames HomeKit helper levels:
  - Fresh Water
  - Grey Tank
  - Black Tank
  - Propane
- Renames clean native covers for friendlier HomeKit display:
  - Patio Awning
  - Bedroom Slide
- Uses exact friendly names for switch/light/generator button entities where appropriate, reducing device-name prefix clutter in Apple Home.
- Keeps existing unique IDs stable to avoid breaking automations and dashboards.

## Notes

Home Assistant may preserve old friendly names in the entity registry for entities that already existed. If a name does not change after installing this release, rename the entity manually in Home Assistant or remove/re-add the entity from the registry.


---

<!-- Source: RELEASE_NOTES_v4.4.3.md -->


# Precision Plex v4.4.3 - HomeKit Accessory Name Cleanup

This release continues the Enhanced HomeKit Experience work.

## Changes

- Shortens the Precision Plex device name reported through Home Assistant device metadata.
- Keeps clean entity names such as Bedroom Slide, Patio Awning, Fresh Water, Grey Tank, Black Tank, and Propane.
- Reduces the chance that Apple Home builds long accessory names containing the Bluetooth MAC address.
- Preserves existing unique IDs and runtime protections from the current baseline.

## Testing Focus

After updating and restarting Home Assistant, remove/re-add the affected HomeKit Bridge entities if Apple Home keeps cached names, then verify the imported accessory names are shorter and cleaner.


---

<!-- Source: RELEASE_NOTES_v4.4.8.md -->


# Precision Plex v4.4.8 - Restore HomeKit-Safe Device Grouping

This release rolls back the experimental entity-registry naming migration from v4.4.7.

## Why

v4.4.7 proved that HomeKit was using Home Assistant registry names, but it also exposed a HomeKit grouping behavior: when Precision Plex entities remain associated with the same Home Assistant device, HomeKit may group them under a single accessory name. Setting one entity registry name, such as Bedroom Slide, can cause the grouped HomeKit accessory to prefix other services with that same name.

## Changes

- Restores the safer v4.4.5 device association behavior.
- Removes the automatic entity-registry naming migration.
- Keeps entities grouped correctly under the Precision Plex device in Home Assistant.
- Keeps the previous HomeKit exposure cleanup and generator runtime protections from the 4.4.x baseline.

## Notes

If v4.4.7 was installed and Home Assistant/HomeKit cached names, remove and re-add the Precision Plex integration and refresh/re-add the HomeKit Bridge accessories as needed.


---

<!-- Source: RELEASE_NOTES_v4.4.9.md -->


# Precision Plex v4.4.9 — Skip Pairing When Already Bonded

This release improves the setup/config flow for already-paired Precision Plex Bluetooth devices.

## Changes

- Checks BlueZ for an existing paired or bonded Precision Plex device after device selection.
- Skips the Pair with Mobile prompt when the selected device is already paired/bonded.
- Falls back to the existing pairing flow when no paired/bonded BlueZ device record is found.
- Keeps the v4.4.8 HomeKit-safe device grouping rollback behavior.

## Notes

This should make removing and re-adding the integration less annoying on systems where the Precision Plex BLE module is already bonded to Home Assistant.


---

<!-- Source: RELEASE_NOTS_v4.4.10.md -->


# Precision Plex v4.4.10

## Fixes

- Improves config flow detection of existing BlueZ pair/bond state.
- Skips the Pair with Mobile step when the selected Precision Plex BLE device is already paired or bonded in BlueZ.
- Adds visible setup log lines showing the selected address and BlueZ paired/bonded/trusted state.


---

<!-- Source: RELEASE_NOTES_v4.4.11.md -->


# Precision Plex v4.4.11

## Fixes

- Fixes a config-entry startup issue after adding the integration from the UI.
- If Home Assistant is already running when the config entry is created, the BLE coordinator now starts immediately instead of waiting for a startup event that has already passed.
- This should prevent entities from remaining unavailable until a full Home Assistant restart after adding the integration.

## Also included

- Existing BlueZ paired/bonded detection from v4.4.10 remains in place.
- Existing HomeKit/entity cleanup and generator runtime protections remain unchanged.


---

<!-- Source: RELEASE_NOTES_v4.4.12.md -->


# Precision Plex v4.4.12

## Home Assistant entity naming compliance

- Updates Precision Plex entity classes to use Home Assistant modern entity-name semantics consistently.
- Intended to test whether Home Assistant voice-assistant/HomeKit exposed names stop prepending the Precision Plex device name to entity names.
- Keeps v4.4.11 config-flow pairing skip and startup behavior fixes.


---

<!-- Source: RELEASE_NOTES_v4.4.13.md -->


# Precision Plex v4.4.13

## Fixes

- Fixed a Home Assistant startup timeout where the Precision Plex BLE connection loop could be tracked as a startup task.
- The BLE monitor now runs as a background task for the lifetime of the config entry instead of blocking bootstrap.
- No HomeKit naming behavior changes in this build.

## Testing focus

- Restart Home Assistant and confirm it no longer remains stuck on "Wrapping up startup" waiting for `PrecisionPlexStateCoordinator._connection_loop()`.
- Confirm Precision Plex entities still become available normally after startup.


---

<!-- Source: RELEASE_NOTES_v4.4.14.md -->


# Precision Plex v4.4.14

## Startup Availability Tuning

This release keeps the v4.4.13 startup fix and tunes the BLE connection retry behavior so Precision Plex entities should become available faster after Home Assistant startup or after adding the integration.

### Changes

- Reduced the BLE connection timeout used by the monitor.
- Disabled long nested Bleak retry batches during startup.
- Let the Precision Plex coordinator retry quickly in its own connection loop instead.
- Kept the BLE connection loop as a background task so Home Assistant startup remains fast.

### Notes

No configuration changes are required.


---

<!-- Source: RELEASE_NOTES_v4.4.16.md -->


# Precision Plex v4.4.16 — Telemetry Confidence Cleanup + Overnight Diagnostics

Temporary investigation build for validating Precision Plex telemetry decoding.

## Changes

- Adds propane/LP field validation for 02AA telemetry.
- Accepts only known-clean LP byte encodings with a zero low nibble: `0x00`, `0x20`, `0x50`, `0x70`, `0xA0`.
- Rejects suspicious LP bytes with non-zero low nibbles, such as `0x28`, `0x0A`, and `0x05`, while retaining the last known good LP value.
- Collapses generator flag variants into clean visible states:
  - `0x00`, `0x40`, `0x80`, `0xC0` show as `Stopped`.
  - `0x10`, `0x90` show as `Running`.
- Preserves raw generator status bytes and raw LP diagnostics as attributes for troubleshooting.
- Keeps the v4.4.15 02AA frame diagnostics enabled so overnight logs can be correlated against Home Assistant state history.

## Important

This is intentionally noisy and is not intended as the final GitHub production release. A later build should keep the telemetry cleanup and remove or downgrade the frame diagnostics.


---

<!-- Source: RELEASE_NOTES_v4.5.0.md -->


# Precision Plex Home Assistant Integration v4.5.0

## Telemetry Validation & Stability Release

This release establishes a new stable baseline for the Precision Plex Home Assistant integration.

Over the course of extensive reverse engineering, live telemetry monitoring, and overnight diagnostic testing, the integration has been refined to better handle real-world Precision Plex BLE telemetry behavior.

The result is a more reliable and resilient integration that remains responsive while filtering out invalid or malformed telemetry that can occasionally appear on the Precision Plex wireless interface.

---

## What Was Learned

Long-duration telemetry diagnostics revealed that the Precision Plex BLE telemetry stream can occasionally produce transient invalid values.

These anomalies are not unique to this integration. Similar behavior has been observed in the official Precision Plex mobile application, which can occasionally display impossible tank readings or brief telemetry glitches.

Examples observed during testing included:

- Invalid propane telemetry bytes
- Corrupted generator runtime candidates
- Generator status flag variants
- Rare malformed 02AA telemetry frames

Importantly, these events were isolated to specific telemetry fields and did not indicate a failure of the overall BLE connection or the core telemetry mapping.

---

## Telemetry Validation Improvements

### Propane Sensor Validation

Propane telemetry is now validated before being published.

Testing confirmed that valid propane display values are transmitted using known-clean byte encodings:

- `0x00` = 0%
- `0x20` = 25%
- `0x50` = 50%
- `0x70` = 75%
- `0xA0` = 100%

Live field testing also showed transient LP bytes such as:

- `0x05`
- `0x0A`
- `0x14`
- `0x28`

Those bytes follow a structured pattern, but they do not match the known-clean display encoding. They are now treated as invalid LP samples.

When invalid propane telemetry is encountered:

- The invalid sample is discarded
- The last known good propane value is retained
- Spurious 0%, 25%, and other false readings are prevented
- Diagnostic details are retained at debug level instead of spamming normal logs

---

### 02AA Frame Shape Validation

The integration now performs additional sanity checks before decoding 02AA telemetry frames.

This protects against rare malformed or shifted frames that can otherwise place plausible-looking values at the wrong offsets.

Malformed 02AA frames are now rejected before they can update:

- Coach battery voltage
- Fresh water level
- Grey water level
- Black water level
- Propane level
- Generator status
- Generator runtime

---

### Generator Runtime Protection

Generator runtime telemetry now includes additional sanity validation.

The integration rejects:

- Runtime values that move backwards
- Implausible runtime jumps
- Corrupted runtime samples from malformed telemetry

This prevents brief telemetry corruption from producing unrealistic runtime values while preserving valid runtime accumulation.

---

### Generator State Cleanup

Generator state reporting has been simplified.

Multiple observed generator flag variants now correctly map to their corresponding user-facing state.

Examples include:

- Stopped
- Running
- AutoStart Accepted
- AutoStart In Progress
- AutoStop In Progress
- Stop Accepted
- Will Not Start

Internal flag variations are preserved through raw diagnostic attributes, but they no longer create unnecessary visible state changes in Home Assistant.

---

## Diagnostic Logging Cleanup

The temporary overnight telemetry investigation logging has been removed or downgraded.

Normal operation now produces significantly cleaner logs while retaining useful startup and connection information.

Kept at normal log level:

- BLE connection lifecycle messages
- 02AA notification subscription confirmation
- 02BB notification subscription confirmation
- Important connection or decoding warnings

Moved to debug level:

- Raw 02AA frame dumps
- Rejected LP byte details
- Generator runtime candidate diagnostics
- Repeated telemetry investigation output

---

## Existing Features

### Lighting Control

- Awning Light control
- Native Home Assistant light entity support

### Generator Integration

- Generator status monitoring
- Generator runtime monitoring
- Generator start and stop controls
- AutoStart support
- AutoStop support

### Tank Monitoring

- Fresh water tank
- Grey water tank
- Black water tank
- Propane level monitoring

### Battery Monitoring

- Coach battery voltage
- House battery voltage

### Cover Integration

- Main slide
- Bed slide
- Sofa slide
- Wardrobe slide
- Awning

Cover features include:

- Open
- Close
- Stop
- Configurable jog controls
- Position reset controls

### HomeKit Support

- Improved HomeKit naming
- HomeKit-friendly entity presentation
- Better cover behavior and exposure

---

## Tested Platform

This integration was reverse engineered and validated using:

**2022 Forest River Georgetown GT5 34M5**

Precision Plex profile:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Other Precision Plex-equipped coaches may expose different circuits, tank configurations, slides, awnings, generators, or feature sets.

---

## Summary

v4.5.0 focuses on reliability rather than new features.

By validating telemetry, rejecting malformed data, and preserving known-good values, this release provides the most stable Precision Plex Home Assistant experience to date while maintaining compatibility with the complete feature set already available within the integration.


---

<!-- Source: RELEASE_NOTES_v4.5.1.md -->


# Precision Plex Home Assistant Integration v4.5.1

## Telemetry Sanity Guard Follow-Up

v4.5.1 is a focused stability follow-up to v4.5.0.

After the v4.5.0 telemetry validation release, additional startup-history review showed that a small number of short-lived propane changes could still appear when the Wireless TP stream emitted clean-looking but incorrect LP samples. This release tightens the telemetry guardrails without reintroducing noisy diagnostic logging.

## Changes

### Stronger 02AA Frame Shape Validation

The 02AA telemetry decoder now rejects frames that do not match the known fixed-position frame shape for the tested coach.

Additional whole-frame checks include:

- Enforcing the expected 20-byte 02AA telemetry frame length
- Rejecting known shifted frames with trailing `0x55`
- Rejecting frames with an invalid fresh-tank framing nibble
- Retaining existing grey/black framing nibble checks
- Retaining voltage plausibility checks

Malformed frames are discarded before any telemetry entities are updated.

### LP / Propane Stability Improvement

LP telemetry validation now includes confirmation for changed clean LP values.

The first valid LP value still populates immediately at startup. After that, a changed clean LP value must be observed in consecutive accepted frames before it is published.

This prevents brief one-sample `0%` or `25%` propane blips from appearing when the Wireless TP stream emits transient but clean-looking LP samples.

Existing LP validation remains in place:

- Known-good LP encodings are accepted
- Dirty LP bytes with non-zero low nibbles are rejected
- Last-known-good propane value is retained when LP telemetry is invalid

### Logging Cleanup

Startup subscription messages for the 02AA and 02BB notification streams remain informational and are no longer treated as warnings.

Noisy overnight diagnostic frame logging remains removed from production builds.

## Summary

v4.5.1 keeps the telemetry validation foundation introduced in v4.5.0 and adds another layer of protection against brief malformed or misleading Wireless TP telemetry samples.


---

<!-- Source: RELEASE_NOTES_v4.5.2.md -->


# Precision Plex Home Assistant Integration v4.5.2

## Production Log Cleanup Follow-Up

v4.5.2 is a small cleanup release following the v4.5.0 telemetry validation release and the v4.5.1 02AA sanity guard follow-up.

This release keeps the telemetry protection work intact while removing the remaining reverse-engineering diagnostic log chatter from normal Home Assistant startup.

## Changes

- Removed the generator runtime source diagnostic message from normal logging.
- Kept the generator runtime recovery and sanity logic in production behavior.
- Kept 02AA and 02BB subscription confirmations as normal startup information.
- Preserved propane telemetry validation and last-known-good retention.
- Preserved 02AA frame-shape sanity checks and LP change confirmation.
- Preserved generator flag cleanup and runtime protection.
- Kept logs quiet unless something actually needs attention.

## Notes

The generator runtime recovery logic remains part of the production decoder. What was removed is only the diagnostic message explaining which runtime candidate was selected.

This release should produce a cleaner Home Assistant restart log while retaining the telemetry stability improvements from v4.5.0 and v4.5.1.
