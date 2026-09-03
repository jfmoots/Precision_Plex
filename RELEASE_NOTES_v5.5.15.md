# Precision Plex v5.5.15 — Restart-Safe LIN Synchronization

This release prevents a retained LIN command from being treated as new after
Home Assistant restarts.

- Rejects command intents older than five seconds from v0.6.5 firmware.
- Suppresses the initial retained command from older bridge firmware.
- Works with bridge firmware v0.6.5 periodic complete snapshots so HVAC,
  ignition, and AC-present readings recover without waiting for a value change.
