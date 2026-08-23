# Precision Plex v5.5.12 — Persistent Awning Endpoints

This release keeps the Patio Awning's synthetic closed and extended positions
stable across Home Assistant restarts and external wall-panel movement.

## Restart behavior

- A time-based estimate within 10% of fully retracted is restored as the
  synthetic 0% seated endpoint.
- A time-based estimate within 10% of fully extended is restored as the
  synthetic 100% Carefree Flip endpoint.
- Intermediate positions remain unchanged.

## Endpoint telemetry

- ESPHome Awning Retract End events immediately persist 0%.
- ESPHome Awning Extend events immediately persist 100%.
- Both endpoints remain protected through trailing motion bits until
  authoritative controller-idle telemetry arrives.

This corrects the observed case where a physically closed awning restored as
7% after Home Assistant restarted, and applies the same protection to the
synthetic 100% extended endpoint.
