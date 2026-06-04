# Release History

## v4.1.0 — Coach Profile Foundation

- Added the first coach profile architecture.
- Moved Georgetown GT5 34M5 state-bit and command mappings into `custom_components/precision_plex/profiles/georgetown_gt5_34m5.py`.
- Kept the Georgetown GT5 34M5 profile as the default active profile to preserve v4.0.3 behavior.
- Added active profile information to diagnostics.


## v4.0.3 — Cleanup & Diagnostics

- Added Home Assistant diagnostics support for redacted config, BLE connection details, raw 02BB/02AA frames, decoded state bits, tank/LP percentages, coach voltage, and generator status/runtime.
- Updated package version and README references to v4.0.3.
- Removed generated Python cache files from the GitHub-ready ZIP.

## v2.6.33 - Feature Complete Release with Official App Protocol Documentation

- Promotes v2.6.32 into an expanded GitHub-ready release.
- Adds official Precision Plex app diagnostic details to the documentation.
- Documents the tested coach profile: `Model_Georgetown_GT_34M5_w_2AC`.
- Documents app/version details: App Version `5.06.01`, File Version `3.989`, STM Version `4`.
- Documents official app BLE characteristic names: `ANDROID1_CHAR_UUID`, `ANDROID2_CHAR_UUID`, `ANDROID3_CHAR_UUID`, and `BLE_TX_CHAR_UUID`.
- Documents the official app pairing/bond-verification sequence.
- Documents that HVAC is disabled in the official app for this coach profile with `hvacSupportOnApp false` and `hvacSendsHeatPumpBits false`.
- Clarifies implemented app-visible features and features not present in the official app on the tested coach.

## v2.6.33 - GitHub Ready App-Visible Feature Complete Release

- Promoted validated v2.6.31 generator work into a GitHub-ready release.
- Updated README and docs to reflect that the tested coach's core app-visible Precision Plex feature set is complete.
- Expanded protocol documentation for Level Monitor, LP, generator runtime, generator status, AutoStart, AutoStop, and Will Not Start.
- Removed unavailable app features from the future-work target list for the tested coach.

## v2.6.31 - Generator Will Not Start Status Test

- Added Generator Status decoding for failed AutoStart state.
- Maps 0x2004 / status byte 0x20 to `Will Not Start`.
- Preserves v2.6.30 Generator AutoStart / AutoStop buttons and interlocks.
- Unknown future generator status codes are exposed as unknown states and logged with raw 0x002B payloads.

## v2.6.30 - Generator AutoStart / AutoStop Test

- Added Generator AutoStart button.
- Added Generator AutoStop button.
- Added Generator Status sensor.
- Added status-aware safety interlocks for all generator command buttons.
- Decoded managed generator transition values observed in 0x002B / 02AA telemetry.

## v2.6.29 - Generator Control & Complete Coach Monitoring

- Current GitHub-ready release.
- Consolidates tested work from v2.6.3 through v2.6.28.
- Adds confirmed Generator Start and Generator Stop buttons.
- Adds generator command safety interlocks using live generator running telemetry.
- Confirms generator running status and runtime hours from the `0x002B` / `02AA` status packet.
- Confirms runtime updates live with the Precision Plex display.
- Keeps Fresh, Grey, Black, LP Gas, Coach Battery, water pump, water heater, awning, and slide functionality unchanged.

## v2.6.28 - Generator Control Test

- Added guarded Generator Start and Generator Stop buttons.
- Added safety interlocks using live generator running telemetry.
- Start is blocked while running.
- Stop is blocked while stopped.
- Both commands are blocked if generator state is unknown.

## v2.6.27 - Generator Telemetry Test

- Adds Generator Running binary sensor from the confirmed `0x002B` / `02AA` status packet.
- Adds Generator Runtime sensor decoded from bytes 7-8 as big-endian tenths of hours.
- Confirmed example: `0x04B4` = 120.4 hours.
- Keeps the existing Fresh, Grey, Black, LP Gas, and Coach Battery decoders unchanged.

## v2.6.26 - Level Monitor Complete / GitHub Ready

- Cleaned and consolidated the tested releases from v2.6.3 through v2.6.25.
- Includes confirmed Level Monitor telemetry:
  - Coach Battery
  - Fresh Water Tank
  - Grey Water Tank
  - Black Water Tank
  - LP Gas Tank
- Documents the confirmed `02AA` / handle `0x002B` nibble model.
- Keeps the tested control stack for awning light, water pump, water heater, awning, bed slide, wardrobe slide, and sofa slide.

## v2.6.25 - LP Gas Level Test

- Added LP Gas Tank sensor from the confirmed `0x002B` / `02AA` levels packet.
- LP Gas mapping: `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%`.

## v2.6.24 - Tank Model Complete Test

- Added Black Water Tank sensor from the `0x002B` / `02AA` levels packet.
- Completed Fresh/Grey/Black tank nibble model.

## v2.6.23 - Fresh Nibble + Grey Tank Test

- Corrected Fresh Water to low-nibble decoding.
- Added Grey Water Tank sensor.

## v2.6.22 - Fresh Tank 02AA Decoder Test

- Added Fresh Water Tank sensor decoded from `02AA` / handle `0x002B`.
- Confirmed Fresh mapping: `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- Retained coach battery voltage decoder.

## v2.6.3 - Stable Control Baseline

- Stable persistent BLE coordinator baseline.
- Clean disable / enable lifecycle.
- Working awning light, water pump, water heater, awning, bed slide, wardrobe slide, sofa slide, binary sensors, and travel-time settings.

## v2.4.2

- Documentation and protocol reference expansion.
- Added structured documentation under `/docs`, HACS metadata, repository URLs, and Georgetown GT5 34M5 reference platform notes.

## v2.4.1

- Wireless TP replacement baseline.
- Major shift to persistent BLE connection, bidirectional synchronization, covers, position estimation, wall-panel tracking, and configurable travel times.

## v1.7.1

- Stable BLE baseline using short-lived BLE sessions.
- Final strong version of the original coexistence approach.

## v1.7.0

- Added water pump support.

## v1.5.0

- Added early wall-switch synchronization support.

## v1.0.0

- Initial working awning light control.

## v3.0.0 - Built-In BLE Pairing / Bonding

- Added config-flow BLE pairing support using a temporary BlueZ `NoInputNoOutput` pairing agent.
- Promoted the successful Precision Plex pairing workflow validated against the `Precision - D244B4` BLE endpoint.
- Confirmed pairing occurs through standard BLE SMP bonding/security, followed by the existing app/session initialization payload.

