# Precision Plex v2.6.4a — Coach Battery Sensor Sender Fix

This test build keeps the v2.6.4 coach battery voltage sensor and fixes notification sender handling so the integration can decode 0x002B telemetry whether Home Assistant/Bleak passes the sender as an integer handle or a characteristic object.

## Fix

- Normalizes BLE notification sender values before decoding telemetry.
- Ensures Handle 0x002B packets decode the first word as coach battery voltage in tenths of a volt.
- Adds a warning log when coach battery voltage is successfully decoded.

## Confirmed decoder

```text
00 7D = 125 = 12.5 V
00 88 = 136 = 13.6 V
coach_voltage = int.from_bytes(payload[0:2], "big") / 10
```
