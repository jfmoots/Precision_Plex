# Protocol Overview

## Communication Model

The Precision Plex Wireless TP module exposes BLE characteristics used by the mobile app. This integration uses the same communication path:

1. Subscribe to state, status, and level notifications.
2. Decode circuit state words, Level Monitor bytes, and generator status/runtime fields from notification payloads.
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
| Level monitor / generator telemetry | `02aa6f62-6f74-7061-6a61-6d61732e6361` | `0x002B` | Coach battery, tanks, LP, generator status, generator runtime |
| Additional status/text stream | observed on related app captures | `0x0033`, `0x003A` | Used by the app for other display/status data; not required for the current feature-complete decoder |

## Command Packet Pattern

Several command families follow this general structure:

```text
55 1D 10 0B [function/action bytes] 00 00 00 00 00 00 [checksum]
```

For momentary/toggle devices, the app sends a short button-action sequence.

For movement devices such as awnings and slides, the mobile app sends:

1. A release/neutral packet.
2. A repeated hold packet approximately every 300 ms.
3. A release/neutral packet when movement stops.

Home Assistant mirrors this behavior for cover entities.

## 02AA / Handle 0x002B Packet

The Level Monitor page and generator telemetry are decoded from `02AA`, observed at handle `0x002B`.

Representative payloads:

```text
Stopped:      00 83 00 0F 0F 50 00 04 B4 00 00 01 ...
Running:      00 88 00 0F 0F 50 10 04 B4 00 00 01 ...
WillNotStart: 00 8F 00 0F 0F 50 20 04 B6 00 00 01 ...
```

Known fields:

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |
| Generator status word | bytes 6-7, big-endian | see status table |
| Generator Runtime | established decoder path uses adjacent bytes as big-endian tenths of hours | `0x04B4` = 120.4 hours, `0x04B5` = 120.5 hours |

### Generator Status Word

| Status Word | Meaning | Validation |
|---:|---|---|
| `0x0004` | Stopped | Captured with generator off |
| `0x1004` | Running | Captured with generator running |
| `0x00A0` | AutoStart command accepted / transition begins | Observed during AutoStart process |
| `0x2004` | Will Not Start | Captured after four failed AutoStart attempts |
| `0x6004` | Performing Generator AutoStart | Captured during managed AutoStart sequence |
| `0x7004` | Performing Generator AutoStop | Captured during managed AutoStop sequence |

A matching `Will Not Stop` state likely exists, but it has not been safely captured. Unknown status codes are exposed/logged as raw values rather than guessed.

## Level Monitor Encoding

### Fresh / Grey / Black Tanks

Fresh, Grey, and Black use the same 4-state encoding:

```text
0x0 = Empty / 0%
0x3 = 1/3 / 33%
0x6 = 2/3 / 67%
0xA = Full / 100%
```

The controller interprets the physical tank probes and transmits the resulting status. The BLE packet does not expose individual raw probe continuity states.

### LP Gas

LP uses a 5-state encoding:

```text
0x0 = Empty / 0%
0x2 = 1/4 / 25%
0x5 = 1/2 / 50%
0x7 = 3/4 / 75%
0xA = Full / 100%
```

## Control Commands / Handle 0x0037

Generator and coach control commands are written to the control characteristic, observed at handle `0x0037`.

Generator commands:

```text
Start press:     55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
Stop press:      55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
AutoStart press: 55 1D 10 0B 00 3E 0A 00 00 00 00 00 00 00 00 2B
AutoStop press:  55 1D 10 0B 00 3E 0B 00 00 00 00 00 00 00 00 2A
Release:         55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

See `docs/command_mapping.md` for the full control map.

## Coach Variability

The protocol appears largely shared across Precision Plex installations, but function IDs, state bits, and available features may vary by coach.

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**. For this coach, the app-visible Precision Plex feature set is now covered by the integration.
