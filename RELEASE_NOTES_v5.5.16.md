# Precision Plex v5.5.16 — Immediate Toggle Feedback

This release removes the visible delay and state bounce from awning-light and
other latched-output commands.

- Publishes the requested state to Home Assistant and HomeKit immediately.
- Recognizes the bridge's fast PID5E command event as the echo of that local
  request instead of treating it as another toggle.
- Waits up to 45 seconds for authoritative PID32 output confirmation. Flight
  recordings show that PID32 packets can be frequent while their output bit
  remains stale beyond the old 12-second timeout.
- Retains PID32 as the final source of truth and reverts safely if confirmation
  never arrives.
