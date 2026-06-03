# Precision Plex v2.6.29 - Generator Control & Complete Coach Monitoring

This is the current GitHub-ready release.

v2.6.29 consolidates the tested work from v2.6.3 through v2.6.28 and adds confirmed generator telemetry plus guarded generator Start/Stop control.

## Confirmed Working Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Confirmed Working Telemetry

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours

## Configuration Entities

- Awning Open Seconds
- Awning Close Seconds
- Bed Slide Open Seconds
- Bed Slide Close Seconds
- Wardrobe Slide Open Seconds
- Wardrobe Slide Close Seconds
- Sofa Slide Open Seconds
- Sofa Slide Close Seconds

## Generator Support

Added and validated:

- `binary_sensor.generator_running`
- `sensor.generator_runtime`
- `button.generator_start`
- `button.generator_stop`

Safety interlocks:

- Generator Start is only available when generator telemetry says the generator is not running.
- Generator Stop is only available when generator telemetry says the generator is running.
- Both commands are blocked when generator state is unknown or unavailable.

## Decoded Precision Plex Telemetry

Level Monitor / Generator telemetry packet:

```text
Handle: 0x002B
Characteristic: 02AA
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

## Generator Command Mapping

Written to control handle `0x0037` in PacketLogger captures:

```text
Start press: 55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
Stop press:  55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
Release:     55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

## Validation

All telemetry and control functions were validated against a live Precision Plex installation using:

- Precision Plex wall panel displays
- Precision Plex mobile application behavior
- Bluetooth PacketLogger captures
- Home Assistant integration testing

Generator validation confirmed:

- Generator Running changed correctly from Not Running to Running.
- Generator Runtime displayed 120.4 hours, then updated live to 120.5 hours in Home Assistant at the same time as the Precision Plex display.
- Generator Start successfully started the generator from Home Assistant.
- Generator Stop successfully stopped the generator from Home Assistant.
- Start/Stop safety interlocks behaved correctly in all tested states.

## Tested Platform

- 2022 Forest River Georgetown GT5 34M5
- Precision Circuits Precision Plex Control System
- Precision Circuits Wireless TP module
- Home Assistant

## Project Status

The core Precision Plex integration is now stable and feature complete for the major coach functions available on the tested platform.

## Future Work

- Generator fault decoding
- Generator maintenance information
- Native slide position telemetry
- Native awning position telemetry
- Additional coach-specific functions
- Dashboard examples
- Expanded protocol documentation
