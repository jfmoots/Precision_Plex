# Precision Plex v2.6.27 - Generator Telemetry Test

This release adds generator telemetry to the confirmed `0x002B` / `02AA` status packet decoder.

## Added

- `binary_sensor.generator_running`
- `sensor.generator_runtime`

## Generator Decode

```text
Stopped: 0083 000F 0F50 0004 B400 0001 ...
Running: 0088 000F 0F50 1004 B400 0001 ...
```

- Generator Running: byte 6 bit `0x10`
- Generator Runtime: bytes 7-8, big-endian tenths of hours
- Example: `0x04B4` = 1204 tenths = 120.4 hours

## Unchanged

- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank
- Coach Battery Voltage
- Existing controls and cover travel-time calibration
