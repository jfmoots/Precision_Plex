# 2022 Forest River Georgetown GT5 34M5

This coach is the reference platform used for the current reverse-engineered Precision Plex integration.

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

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

## Notes

For this coach, the core app-visible Precision Plex feature set is considered decoded and validated as of v2.6.32.

Other Precision Plex installations may expose different app features, circuits, or telemetry. Those should be treated as coach-specific extensions until captured and validated.
