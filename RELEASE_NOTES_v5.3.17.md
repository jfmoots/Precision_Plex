# Precision Plex v5.3.17 – BLE Command Stream Ownership Guard

This diagnostic/stabilization release focuses on cover movement reliability during long-running slide and awning command streams.

## Changes

- Added BLE command stream ownership tracking for long-running hold streams.
- Defers monitor reconnect behavior while a cover command stream is active.
- Avoids bouncing cover entities unavailable during active movement if BLE disconnects transiently.
- Adds logging for command stream ownership start/end and deferred monitor reconnects.
- Keeps the v5.3.16 smart awning threshold and safety tuning.
- Keeps the v5.3.12 event-latch behavior and v5.3.15 smart-open state machine fixes.

## Test Focus

- Verify one slide still extends/stops/retracts normally.
- Test awning open and close while watching for any mid-motion unavailable transitions.
- If a cover stops early, download the Home Assistant log immediately so write/reconnect timing can be reviewed.
