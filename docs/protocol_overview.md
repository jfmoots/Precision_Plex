# Protocol Overview

## Communication Model

The Precision Plex Wireless TP module exposes BLE services and characteristics used by the official mobile app. This integration uses the same communication path:

1. Subscribe to state, status, level, and generator telemetry notifications.
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

## Official App Diagnostic Information

The official Precision Plex app reports the tested coach profile as:

```text
Model_Georgetown_GT_34M5_w_2AC
Model: GT 34M5 with 2AC
STM Version: 4
App Version: 5.06.01
File Version: 3.989
RV Data: GT 34M5 with 2AC v5.06.01 f3.989
```

The app also reports:

```text
hvacSupportOnApp false
hvacSendsHeatPumpBits false
```

This confirms that HVAC support is disabled in the official app for the tested coach profile.

## Official App BLE Characteristics

Observed directly in the official Precision Plex app diagnostic log:

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

Known Home Assistant integration usage:

- Control writes use the control characteristic observed at handle `0x0037` in app traces.
- Level Monitor and generator telemetry are decoded from `02AA`, observed at handle `0x002B`.
- State/status notifications are received from `02BB`-family streams.
- Additional status/text notifications were observed on handles `0x0033` and `0x003A`, but they are not required for the current feature-complete decoder.

## Pairing / Bond Verification

The official app performs a BLE bonding verification sequence before normal operation.

Observed app sequence:

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

After bonding is verified, the app subscribes to the telemetry characteristics and begins normal RV reads.

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

- Coach Battery: bytes 0-1, big-endian tenths of volts. Example: `0x0083 = 13.1 V`.
- Fresh Water: byte 2 low nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- Grey Water: byte 3 high nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- Black Water: byte 4 high nibble. `0=0%`, `3=33%`, `6=67%`, `A=100%`.
- LP Gas: byte 5 high nibble. `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%`.
- Generator Status Word: bytes 6-7, big-endian.
- Generator Runtime: established decoder path uses adjacent bytes as big-endian tenths of hours. Example: `0x04B4 = 120.4 hours`, `0x04B5 = 120.5 hours`.

## Generator Status Word

Confirmed on the tested coach:

- `0x0004 = Stopped`
- `0x1004 = Running`
- `0x00A0 = AutoStart command accepted / transition begins`
- `0x2004 = Will Not Start`
- `0x6004 = Performing Generator AutoStart`
- `0x7004 = Performing Generator AutoStop`

A matching `Will Not Stop` state likely exists, but it has not been safely captured. Unknown status codes are exposed/logged as raw values rather than guessed.

## Level Monitor Encoding

Fresh, Grey, and Black use the same 4-state encoding:

```text
0x0 = Empty / 0%
0x3 = 1/3 / 33%
0x6 = 2/3 / 67%
0xA = Full / 100%
```

The controller interprets the physical tank probes and transmits the resulting status. The BLE packet does not expose individual raw probe continuity states.

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

The protocol appears largely shared across Precision Plex installations, but function IDs, state bits, model files, and available features may vary by coach.

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**. For this coach, the app-visible Precision Plex feature set is now covered by the integration.
