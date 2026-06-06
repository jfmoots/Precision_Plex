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
