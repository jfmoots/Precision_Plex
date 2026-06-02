# Precision Plex v2.6.4 — Coach Battery Voltage Sensor Test

## Test Build

This build adds the first Level Monitor telemetry sensor to Home Assistant while preserving the v2.6.3 slide, awning, and restart-safe coordinator behavior.

## New Sensor

- Added `sensor.precision_plex_coach_battery`
- Reports coach battery voltage in volts
- Uses Home Assistant voltage device class and measurement state class

## Protocol Mapping

Coach battery voltage is decoded from the Precision Plex monitor notification on handle `0x002B`.

Observed mapping:

```text
00 88 = 136 = 13.6V
00 7D = 125 = 12.5V
```

Decoder:

```python
coach_voltage = int.from_bytes(payload[0:2], "big") / 10
```

## Existing Features Retained

- Improved `__init__.py` unload behavior for enable/disable without requiring a Home Assistant restart
- Improved coordinator stop/disconnect handling
- Awning, bed slide, wardrobe slide, and sofa slide support
- Restored cover position persistence across Home Assistant restarts
- Configurable travel-time number entities
- Wall-panel tracking
