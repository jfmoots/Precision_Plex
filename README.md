# Precision Plex Home Assistant Integration

Bring Precision Circuits Precision Plex controls and telemetry into Home Assistant.

This custom integration provides local control and monitoring of supported Precision Plex-equipped motorhomes. It prefers a discovered ESPHome Precision Plex LIN bridge for telemetry and automatically falls back to the Precision Plex Wireless TP BLE module. Commands remain on BLE in v5.5.0.

---

## Current Stable Release

**v5.5.1**

v5.5.1 makes LIN updates change-driven end to end. Unchanged bridge heartbeats
refresh availability without rewriting every Precision Plex entity, while
meaningful decoded changes update immediately. It also adds confirmation-aware
feedback for BLE-controlled toggle entities.

v5.5.0 pairs with ESPHome Precision Plex LIN v0.6.0. The bridge emits one
compact event snapshot while this integration owns decoded entities,
availability, diagnostics, and transport selection. It adds LIN-only tank
heater, AC/converter, ignition, and two-zone HVAC telemetry while retaining
field-by-field BLE fallback for shared fields.

---

## Supported Features

- Precision Plex Wireless TP BLE communication
- Automatic ESPHome LIN event ingestion and LIN-preferred telemetry
- LIN-only tank-heater, coach-power, ignition, and two-zone HVAC telemetry
- Field-by-field Bluetooth telemetry fallback
- Guided setup and pairing support
- Native Home Assistant light, cover, switch, button, binary sensor, and sensor entities
- Patio awning control
- Slide room control
- Generator start, stop, AutoStart, AutoStop, runtime, and status telemetry
- Fresh, grey, and black tank telemetry
- LP/propane telemetry
- Coach battery telemetry
- Water pump and water heater controls
- HomeKit-friendly entity exposure
- Diagnostic attributes for raw Precision Plex telemetry
- Custom integration branding/icons

Generator cumulative runtime remains on Bluetooth because the current LIN
decoder exposes only the tenths digit. All commands remain on Bluetooth while
the LIN command path is investigated.

---

## v5.3.7 Highlights

### BLE Packet Validation

The integration now performs additional validation before publishing Precision Plex BLE telemetry to Home Assistant. This helps prevent rare malformed, shifted, stale, or one-frame BLE samples from briefly creating false state history.

### 02BB State Confirmation

App-visible state bits from the 02BB stream are now confirmed before publishing changed state words. This is designed to suppress one-sample ghosts such as a water heater briefly appearing to turn off and back on when the physical system did not change.

### 02AA Voltage Hardening

Coach battery voltage from the 02AA telemetry stream is now range-checked and sudden large one-sample jumps are held until confirmed. This keeps implausible battery spikes/drops out of Home Assistant history while preserving normal charging transitions.

### BLE Hold-Stream Recovery

Long-running commands such as slide and awning motion now attempt a short reconnect/retry if an individual BLE write fails during the hold stream. This improves resilience when the Wireless TP or Bluetooth stack hiccups during movement.

### Diagnostics

Packet health counters and recent rejection details are exposed through diagnostics and selected entity attributes, including rejected 02AA/02BB counts, pending state confirmations, suppressed 02BB glitches, and hold-stream recovery counts.

---

## Coach Systems

### Lighting

Precision Plex lighting circuits are exposed as native Home Assistant light entities where available in the tested coach profile.

### Slides

Supported slide rooms are exposed as native cover entities with open, close, stop, jog, and calibration support.

Optional ESPHome-based quadrature telemetry can provide real slide position feedback from Lippert motor Hall sensor channels. When telemetry is available, the integration uses it for position tracking and motion verification. When telemetry is unavailable, timing-based fallback remains available.

### Patio Awning

The patio awning is exposed as a native cover entity. The tested coach also supports an optional ESP32 current-sensing enhancement for smarter awning behavior and improved end-of-travel detection.

### Generator

Generator support includes running status, status text, runtime hours, start/stop controls, and AutoStart/AutoStop controls where available.

### Tanks and Propane

Fresh, grey, black, and LP/propane levels are decoded from Precision Plex telemetry and exposed as native Home Assistant sensors.

### Water Systems

Water pump and water heater states are exposed as native switch entities using the Precision Plex state stream and app-style tap commands.

---

## Installation

### HACS

Add this repository to HACS as a custom integration repository, install the integration, restart Home Assistant, and add Precision Plex from Settings → Devices & services.

### Manual

Copy:

```text
custom_components/precision_plex
```

into your Home Assistant `custom_components` directory, restart Home Assistant, then add the Precision Plex integration from Settings → Devices & services.

---

## Optional Hardware Enhancements

The integration works without additional hardware. Optional enhancements developed for the tested coach include:

- ESPHome slide quadrature telemetry
- ESP32 awning current monitoring
- Custom Mooterhome dashboards

These enhancements are coach-specific and should be treated as advanced projects.

---

## Tested Coach

This integration was reverse engineered and tested on a:

**2022 Forest River Georgetown GT5 34M5**

Observed Precision Plex app profile:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Other Precision Plex-equipped coaches may expose different circuits, slides, tanks, generators, or profile layouts.

---

## Architecture

The current production transport is Precision Plex Wireless TP BLE.

The long-term goal is a single Precision Plex integration with a shared telemetry model and multiple possible transports. The BLE transport remains the current stable path, while future wired-bus research may add another way to feed the same decoder and entities.

---

## Safety Notice

Slides, awnings, generators, water heaters, and other RV systems control real physical equipment. Maintain line-of-sight when testing movement commands and keep factory controls available.

This integration supplements the factory Precision Plex system. It does not replace manufacturer safety systems, interlocks, or required operating procedures.

## BLE Packet Forensics

v5.3.8 adds a rolling rejected-packet forensic buffer. The integration stores the most recent rejected BLE packets as diagnostic data, including timestamp, packet type, reject reason, length, sender handle, and raw hex payload.

v5.3.10 expands the packet forensics added in v5.3.8 with bounded comparison diagnostics. Rejected packets are now compared against the last accepted packet of the same type, recording changed byte indexes, expected/actual byte values, seconds since the last good packet, and seconds since BLE connect. The forensic buffer remains capped at 100 entries and continues to avoid log spam.


This is intended for field troubleshooting in RF-noisy environments such as campgrounds, where malformed or misaligned BLE notifications may occur intermittently.
