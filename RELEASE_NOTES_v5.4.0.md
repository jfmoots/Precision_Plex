# Precision Plex v5.4.0 — LIN-preferred telemetry

- Automatically discovers the Precision Plex LIN Analyzer through its ESPHome entity registry entries.
- Prefers fresh LIN data for battery voltage, tank/LP levels, generator state, output states, and directional slide/awning motion.
- Falls back field-by-field to Bluetooth whenever LIN telemetry is stale, unavailable, or missing.
- Keeps all commands on Bluetooth for this release.
- Keeps generator cumulative runtime on Bluetooth because the current LIN decoder exposes only the runtime tenths digit.
- Adds a **Telemetry Transport** diagnostic sensor and LIN transport details to integration diagnostics.

This release expects LIN Analyzer firmware build 013.0 or newer for the separate coach/output freshness signals and directional motion entities.
