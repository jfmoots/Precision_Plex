# Precision Plex v5.5.8 — Recorder-Friendly Telemetry

This release preserves fast, local LIN telemetry and failover while removing
the reverse-engineering data that was creating excessive Home Assistant
Recorder traffic.

## Quieter entity state

- Removes raw 02AA/02BB packets, decoder mappings, rejection counters, and
  source-byte details from ordinary entity attributes.
- Removes high-frequency awning motor current from the Patio Awning cover
  attributes; the dedicated ESPHome current sensor remains available.
- Removes heartbeat sequence, packet counters, packet rate, and last PID from
  the Telemetry Transport entity.
- Keeps stable operational attributes such as telemetry source, bridge health,
  firmware version, command status, and cover calibration.
- Retains raw BLE data and the last complete LIN snapshot in Home Assistant
  Download diagnostics and keeps the ESPHome flight-recorder tools.

## Compact heartbeat support

- Merges ESPHome Precision Plex LIN v0.6.4 compact heartbeats into the last
  complete change snapshot.
- Preserves the two-second heartbeat and four-second bridge-loss timeout used
  for prompt Bluetooth fallback.
- Remains compatible with full heartbeat snapshots from firmware v0.6.3.

## Recorder configuration

The `esphome.precision_plex_lin_snapshot` event is live integration transport,
not useful historical data. Exclude that event type from Recorder to avoid
storing heartbeat events while leaving live telemetry unchanged.

Pair with ESPHome Precision Plex LIN v0.6.4.
