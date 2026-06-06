# BLE Characteristics

## Official App Characteristic Names

The official Precision Plex app diagnostic log reports these BLE characteristic identifiers:

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

## Control Characteristic

UUID used by the integration:

```text
03726f62-6f74-7061-6a61-6d61732e6361
```

Observed handle in PacketLogger app traces:

```text
0x0037
```

Purpose:

Send control commands to the Precision Plex Wireless TP module.

Known commands include:

- Awning Light
- Water Pump
- Water Heater
- Awning In / Out
- Bed Slide In / Out
- Wardrobe Slide In / Out
- Sofa Slide In / Out
- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop

## 02AA Notification Characteristic

Official app name:

```text
ANDROID1_CHAR_UUID
```

UUID:

```text
02AA6F62-6F74-7061-6A61-6D61732E6361
```

Observed handle in app traces:

```text
0x002B
```

Purpose:

Primary Level Monitor and generator telemetry packet.

Known decoded values:

- Coach battery voltage
- Fresh tank level
- Grey tank level
- Black tank level
- LP gas level
- Generator running/stopped status
- Generator runtime hours
- Generator managed AutoStart/AutoStop status
- Generator Will Not Start failure state

## 02BB Notification Characteristics

Official app names:

```text
ANDROID2_CHAR_UUID
ANDROID3_CHAR_UUID
```

UUIDs:

```text
02BB6F62-6F74-7061-6A61-6D61732E6361
02BB6F62-6374-7061-6A61-6D61332E6361
```

Purpose:

State/status notifications used by the official app. These streams carry wall-panel/circuit status words and other display/status data.

## Additional Status/Text Notifications

PacketLogger captures also showed notifications on related handles such as:

```text
0x0033
0x003A
```

`0x003A` has been observed carrying ASCII coach/model text such as `GT 34M5 with 2AC`. These streams are documented for reference but are not required for the current feature-complete Home Assistant decoder.

## Notes

The integration maintains an active BLE subscription so Home Assistant can receive live updates from both Home Assistant commands and RV wall-panel/app actions.

The Precision Plex Wireless TP module appears to allow only one active BLE client at a time. When Home Assistant is connected, the official mobile app may not be able to connect simultaneously.
