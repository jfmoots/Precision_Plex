# Precision Plex v5.5.1 — Change-Driven LIN Updates

This release makes the LIN telemetry path change-driven and removes redundant
one-second Home Assistant entity rewrites.

## Improved

- Meaningful LIN telemetry changes update integration entities immediately.
- Unchanged event snapshots refresh transport freshness without rewriting every
  Precision Plex entity or generating unnecessary recorder/websocket traffic.
- Snapshot sequence and reason are available as Telemetry Transport diagnostics.
- Pairs with ESPHome Precision Plex LIN v0.6.1, which sends an immediate event
  when PID32, PIDBA, PIDEC, or PID37 decoded values change and uses a two-second
  heartbeat only for freshness.

## Command feedback

- Awning-light, water-pump, and water-heater commands show their requested state
  immediately while awaiting confirmed telemetry.
- Pending state clears when LIN confirms the requested value or immediately if
  the BLE write fails.
- If confirmation never arrives, the entity returns to confirmed telemetry
  after ten seconds.

All normal commands remain on Bluetooth. LIN remains the preferred telemetry
source, with field-by-field Bluetooth fallback.
