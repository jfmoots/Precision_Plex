# Precision Plex v5.5.16 — Immediate Toggle Feedback

This release removes the visible delay and state bounce from awning-light and
other latched-output commands.

- Publishes the requested state to Home Assistant and HomeKit immediately.
- Recognizes the bridge's fast PID5E command event as the echo of that local
  request instead of treating it as another toggle.
- Waits up to 45 seconds for authoritative PID32 output confirmation, covering
  the observed roughly 30-second PID32 rotation.
- Retains PID32 as the final source of truth and reverts safely if confirmation
  never arrives.
