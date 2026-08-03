# Precision Plex v5.5.7 — Thread-Safe LIN Updates

This maintenance release makes LIN-driven entity updates compliant with Home
Assistant's event-loop threading requirements.

## Thread-safe LIN callback boundary

- Moves the complete LIN coordinator update onto Home Assistant's event loop
  whenever a transport listener originates in another thread.
- Keeps listener calls already running on Home Assistant's loop immediate.
- Covers snapshots, snapshot expiry, per-source expiry, entity discovery, and
  ESPHome state-change notifications through one shared callback boundary.

## Reliable command intent processing

- Captures the snapshot, normalized command intent, and bridge identity before
  queuing cross-thread work.
- Preserves existing command-sequence deduplication and PID32/02BB authoritative
  confirmation behavior.

No firmware update is required; this release remains compatible with ESPHome
Precision Plex LIN firmware v0.6.3.
