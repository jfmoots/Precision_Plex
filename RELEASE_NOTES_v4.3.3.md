# Precision Plex v4.3.3 - HomeKit Cleanup and Generator Runtime Guard

## Fixes

- Adds a guard for generator runtime telemetry so occasional malformed lower values do not overwrite the last known good runtime.
- Prevents Home Assistant recorder warnings caused by `total_increasing` generator runtime dropping temporarily.
- Preserves the existing generator runtime decoder and diagnostics while filtering non-monotonic samples.

## HomeKit

- Keeps the v4.3.x HomeKit-friendly helper sensors and exposure cleanup work.
