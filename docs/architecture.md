# Architecture

## Project Evolution

The Precision Plex integration began as a monitoring and control experiment for a single awning light circuit.

The early architecture attempted to preserve coexistence with the Precision Circuits Wireless TP mobile application by using short-lived BLE connections. Home Assistant connected, issued a command or read state, and disconnected.

That approach worked for limited control, but it introduced several limitations:

- Slow command startup
- Missed wall-panel state changes
- Limited real-time synchronization
- No reliable position tracking
- Incomplete replacement for the Wireless TP application

The v2.x architecture intentionally changed direction.

## Current Architecture

The integration now maintains a persistent Bluetooth Low Energy connection to the Precision Plex Wireless TP monitor.

This lets Home Assistant act as the primary BLE client and receive live state notifications while also issuing commands.

```text
RV Wall Panel
    ⇅
Precision Plex Controller
    ⇅ LIN
ESPHome Precision Plex LIN Bridge
    ⇅ Home Assistant event
Home Assistant

Precision Plex Controller
    ⇅ LIN
Precision Plex Wireless TP Monitor
    ⇅ BLE
Home Assistant
```

## Why Persistent BLE Is Required

Persistent BLE enables:

- Near real-time state updates
- Immediate wall-panel synchronization
- Fast command response
- Reliable bidirectional communication
- Cover and slide position estimation
- Reduced connection setup latency

The current integration uses a hybrid transport model. The ESPHome LIN bridge
is preferred for decoded telemetry, while Bluetooth remains the command path
and field-level telemetry fallback. A shared provisional-state layer provides
immediate HA control feedback while slower PID32 output confirmation is
pending.

The Wireless TP module appears to support only one active BLE connection at a time. Because of this, the Precision Circuits mobile app may not connect while Home Assistant is connected.

This is an intentional tradeoff. The project goal is now to replace the Wireless TP app with Home Assistant-native controls.

## Design Goals

- Keep Home Assistant synchronized with wall-panel activity
- Represent RV systems as native HA entities
- Support safe physical motion control
- Keep travel-time calibration user-editable
- Document the reverse-engineered protocol for future coaches

## v5.2.0 Slide Position Architecture

Slide covers now use a two-layer position model. When ESPHome quadrature telemetry is available, the cover calculates position from decoded Lippert motor Hall sensor travel counts. When telemetry is not available, the cover falls back to the existing time-based estimator.

This keeps the integration compatible with installations that do not have ESPHome telemetry nodes while allowing the tested Georgetown GT5 slide rooms to report actual encoder-derived position.
