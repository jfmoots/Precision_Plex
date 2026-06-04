# Precision Plex v4.4.0 — Generator Runtime Source Diagnostics

This diagnostic release keeps the stable HomeKit cleanup and generator runtime protections from the v4.3.x series, then adds focused logging to identify which generator telemetry packet variant is the true runtime source.

## What changed

- Keeps the v4.3.9 runtime outlier and flag-bit protection.
- Adds focused generator runtime source diagnostics.
- Logs same-shaped generator telemetry variants when the low runtime byte changes away from the previously accepted value.
- Includes nearby bytes 6–12, raw status, raw word, generator state, current/previous low bytes, and decode decision.
- Does not intentionally change control behavior or HomeKit entity cleanup.

## Testing goal

Run this build long enough to capture the repeating byte-8 variant family, especially values such as `0x0B`, `0x16`, `0x2D`, `0x5B`, and `0xB6`. The goal is to identify which variant should be allowed to update the persistent generator runtime sensor.
