# Precision Plex v4.4.16 — Telemetry Confidence Cleanup + Overnight Diagnostics

Temporary investigation build for validating Precision Plex telemetry decoding.

## Changes

- Adds propane/LP field validation for 02AA telemetry.
- Accepts only known-clean LP byte encodings with a zero low nibble: `0x00`, `0x20`, `0x50`, `0x70`, `0xA0`.
- Rejects suspicious LP bytes with non-zero low nibbles, such as `0x28`, `0x0A`, and `0x05`, while retaining the last known good LP value.
- Collapses generator flag variants into clean visible states:
  - `0x00`, `0x40`, `0x80`, `0xC0` show as `Stopped`.
  - `0x10`, `0x90` show as `Running`.
- Preserves raw generator status bytes and raw LP diagnostics as attributes for troubleshooting.
- Keeps the v4.4.15 02AA frame diagnostics enabled so overnight logs can be correlated against Home Assistant state history.

## Important

This is intentionally noisy and is not intended as the final GitHub production release. A later build should keep the telemetry cleanup and remove or downgrade the frame diagnostics.
