# Precision Plex v4.0.1

## Fixes

- Fixed generator command buttons appearing unavailable when the generator telemetry intermittently reports status `0x80`.
- Generator status decoding now keeps the raw status byte for diagnostics while using the lower status bits for command eligibility.
- A stopped generator reporting `0x80` is treated as stopped, so Generator Start and Generator AutoStart remain available.
