# 2022 Forest River Georgetown GT5 34M5

This coach is the reference platform used for the current reverse-engineered Precision Plex integration.

## Official App Coach Profile

The official Precision Plex app diagnostic log identifies the coach as:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Observed application/platform details:

```text
Model: GT 34M5 with 2AC
STM Version: 4
App Version: 5.06.01
File Version: 3.989
RV Data: GT 34M5 with 2AC v5.06.01 f3.989
```

The official app reports:

```text
hvacSupportOnApp false
hvacSendsHeatPumpBits false
```

This confirms that HVAC support is not enabled by the official app for this coach profile.

## App Menus Observed

The official app main menu exposes:

- Lighting
- Levels
- Slides
- Awnings
- Generator
- Utilities

The utility menu exposes:

- Single User Mode
- Forget Paired RV / Pair Again

No HVAC, inverter, shore power, tank heater, water heater telemetry, native slide position telemetry, or native awning position telemetry pages were present in the app for this coach profile.

## Confirmed App-Visible Features Covered

### Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

### Telemetry / Status

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours
- Generator Status

Confirmed generator status values:

- Stopped
- Running
- Performing Generator AutoStart
- Performing Generator AutoStop
- Will Not Start

## Features Checked But Not Available in the Precision Plex App

The following items are not available in the Precision Plex mobile app for this tested coach, so they are not included as current integration targets:

- HVAC / thermostat controls
- Generator fault-code details beyond the decoded generator status field
- Shore power telemetry
- Inverter telemetry
- Tank heater controls
- Water heater telemetry
- Native slide position telemetry
- Native awning position telemetry

## Reference Travel Times

- Awning: 18 seconds open / 25 seconds close
- Bed Slide: 28 seconds open / 24 seconds close
- Wardrobe Slide: 18 seconds open / 17 seconds close
- Sofa Slide: 32 seconds open / 28 seconds close

## Pairing Notes

The official app performs bond verification before normal operation. The app log shows:

```text
Virgin first run - verifying connection
Attempt to connect
Connected to BLE Device
process_pairing()
*** Bond verified - Pairing Complete ***
```

The Precision Plex controller must be placed into mobile pairing mode before initial pairing.

## Notes

For this coach, the core app-visible Precision Plex feature set is considered decoded and validated as of v2.6.33.

Other Precision Plex installations may expose different app features, circuits, or telemetry. Those should be treated as coach-specific extensions until captured and validated.
