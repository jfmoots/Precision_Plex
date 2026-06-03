# 2022 Forest River Georgetown GT5 34M5

## Status

Primary development and validation platform.

## System

- Precision Circuits Precision Plex
- Precision Circuits Wireless TP Monitor

## Verified Entities

### Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

### Telemetry

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours

## Verified Travel Times

| Function | Direction | Time |
|---|---|---:|
| Awning | Open / Out | 18 seconds |
| Awning | Close / In | 25 seconds |
| Bed Slide | Open / Out | 28 seconds |
| Bed Slide | Close / In | 24 seconds |
| Wardrobe Slide | Open / Out | 18 seconds |
| Wardrobe Slide | Close / In | 17 seconds |
| Sofa Slide | Open / Out | 32 seconds |
| Sofa Slide | Close / In | 28 seconds |

## Notes

This coach should be treated as the reference implementation for current command and state mappings.

Other coaches may require additional function IDs, state mappings, and feature-specific captures.
