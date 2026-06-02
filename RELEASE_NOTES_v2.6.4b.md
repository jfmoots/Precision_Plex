# Precision Plex v2.6.4b — Coach Battery 02AA Telemetry Fix

This test release fixes the coach battery voltage sensor by subscribing to the correct Wireless TP telemetry characteristic.

## Fixes

- Adds a dedicated read/notify path for `02aa6f62-6f74-7061-6a61-6d61732e6361` / value handle `0x002B`.
- Decodes the first 16-bit big-endian word as tenths of a volt.
- Keeps `02bb` state decoding separate so wall-panel state packets do not overwrite battery telemetry.

## Confirmed decode examples

```text
00 88 = 136 = 13.6 V
00 7D = 125 = 12.5 V
```

## Existing behavior retained

- v2.6.3 restart-safe enable/disable behavior
- Slide/awning position restore behavior
- Existing light, switch, cover, and number entities
