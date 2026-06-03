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
