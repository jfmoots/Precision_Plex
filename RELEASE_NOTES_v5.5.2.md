# Precision Plex v5.5.2 — Stable HVAC Telemetry and Quieter Diagnostics

This release keeps alternating PID37 HVAC broadcasts stable in Home Assistant
and reduces unnecessary recorder and Activity noise from deep BLE diagnostics.

## Stable two-zone HVAC telemetry

- Tracks freshness independently for the front and rear HVAC zones.
- Retains the last valid zone state for a 30-second grace period when PID37
  broadcasts alternate between zones.
- Prevents one zone from cycling to unavailable while the other zone is being
  reported.
- Preserves the four-second event-snapshot timeout, so a genuinely lost LIN
  bridge still becomes unavailable promptly.

## Quieter diagnostics

- High-churn BLE packet timestamps, counters, rejection details, and forensic
  logs are disabled by default when first registered.
- Operational telemetry, transport status, connection status, movement
  indicators, and controls remain enabled and update immediately.
- Existing installations retain their current entity enable/disable choices;
  noisy BLE diagnostic entities can be disabled from the Precision Plex device
  page without affecting telemetry or control.

All commands remain on Bluetooth. LIN remains the preferred telemetry source.
