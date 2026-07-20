# Precision Plex v5.5.0 — Integration-Owned LIN Telemetry

This release pairs with ESPHome Precision Plex LIN v0.6.0 and moves decoded
LIN telemetry ownership into the Home Assistant integration.

## Added

- Versioned `esphome.precision_plex_lin_snapshot` event ingestion with a
  one-second heartbeat and automatic stale-data expiry.
- Integration-owned LIN-only entities for tank-heater state, AC/converter
  presence, ignition, and both HVAC zones.
- HVAC room temperature, setpoint, mode, request phase, operating state, fan,
  compressor lockout, and lockout time.
- LIN firmware, bus activity, packet rate, counters, CRC errors, and last PID
  as compact attributes on Telemetry Transport.

## Compatibility and behavior

- LIN remains preferred independently for core telemetry, output state,
  coach-power flags, and each HVAC zone.
- Shared fields still fall back to BLE when their LIN source is stale.
- The v0.5.x ESPHome entity-based telemetry path remains supported during the
  upgrade, but the v0.6.0 event path is preferred.
- Generator cumulative runtime remains on BLE; only the LIN tenths digit is
  decoded so far.
- All commands remain on BLE while LIN stop/release behavior is investigated.
