# Protocol Overview

## Communication Model

The Precision Plex Wireless TP module exposes BLE characteristics used by the mobile app.

The integration uses the same communication path:

1. Subscribe to state and level notifications.
2. Decode state words and level-monitor bytes from notification payloads.
3. Send command packets to the control characteristic for supported controls.
4. Update Home Assistant entities from BLE notifications and command results.

## Conceptual Path

```text
RV Wall Panel
    ⇅
Precision Plex Controller
    ⇅
Wireless TP Module
    ⇅ BLE
Home Assistant
```

## Important Characteristics

| Purpose | Characteristic | Observed Handle | Notes |
|---|---|---:|---|
| Control writes | `03726f62-6f74-7061-6a61-6d61732e6361` | `0x0037` in app traces | Used for button/control commands |
| State/status | `02bb6f62-6f74-7061-6a61-6d61732e6361` | observed `0x002F` / related notify stream | Wall-panel and circuit status words |
| Level monitor / generator telemetry | `02aa6f62-6f74-7061-6a61-6d61732e6361` | `0x002B` | Coach battery, tanks, LP, generator running, generator runtime |

## Command Packet Pattern

Several command families follow this general structure:

```text
55 1D 10 0B [function id] [action] 00 00 00 00 00 00 [checksum]
```

For momentary/toggle devices, the app sends a short button-action sequence.

For movement devices such as awnings and slides, the mobile app sends:

1. A release/neutral packet.
2. A repeated hold packet approximately every 300 ms.
3. A release/neutral packet when movement stops.

Home Assistant mirrors this behavior.

## Level Monitor and Generator Telemetry Packet

The Level Monitor page and generator telemetry are decoded from `02AA`, observed at handle `0x002B`.

Example:

```text
00 83 06 3F 3F 50 10 04 B5 ...
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

## Generator Telemetry Captures

Generator telemetry was confirmed in the same `02AA` / handle `0x002B` status packet.

```text
Stopped: 0083 000F 0F50 0004 B400 0001 ...
Running: 0088 000F 0F50 1004 B400 0001 ...
```

Decoded fields:

- Generator running flag: byte 6 bit `0x10`
- Generator runtime: bytes 7-8 as big-endian tenths of hours
- Example: `0x04B4` = 1204 tenths = 120.4 hours

## Generator Control Captures

Generator Start and Stop are written to the control characteristic, observed at handle `0x0037`.

```text
Start press: 55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
Stop press:  55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
Release:     55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

The Home Assistant integration sends the press command followed by the release command and uses live generator-running telemetry as a safety interlock.

## Coach Variability

The protocol appears largely shared across Precision Plex installations, but function IDs, state bits, and available features may vary by coach.

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.
