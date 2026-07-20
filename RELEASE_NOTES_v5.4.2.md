# Precision Plex v5.4.2 — Corrected LIN Movement Telemetry

- Pairs with LIN Analyzer Build 013.1 for corrected PID32 movement telemetry.
- Corrects LIN-reported bedroom slide extend and retract movement through the
  updated analyzer firmware.
- Corrects LIN-reported sofa extend movement through the updated analyzer
  firmware.
- Retains the already-correct LIN mappings for sofa retract, both wardrobe
  directions, and both patio-awning directions.
- Keeps LIN-preferred telemetry with field-by-field BLE fallback.
- Leaves all commands on Bluetooth while safe LIN stop/release behavior remains
  under investigation.

The movement decoder is implemented in the separate LIN Analyzer firmware.
Install LIN Analyzer Build 013.1 alongside this integration release to receive
the corrected movement states.
