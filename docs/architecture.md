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
    ⇅
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

The Wireless TP module appears to support only one active BLE connection at a time. Because of this, the Precision Circuits mobile app may not connect while Home Assistant is connected.

This is an intentional tradeoff. The project goal is now to replace the Wireless TP app with Home Assistant-native controls.

## Design Goals

- Keep Home Assistant synchronized with wall-panel activity
- Represent RV systems as native HA entities
- Support safe physical motion control
- Keep travel-time calibration user-editable
- Document the reverse-engineered protocol for future coaches
