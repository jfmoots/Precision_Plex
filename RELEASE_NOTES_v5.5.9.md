# Precision Plex v5.5.9 — Stable Awning Position After Restart

This release prevents the Patio Awning position estimate from drifting upward
when Home Assistant restarts while the controller briefly reports a stale
motion bit.

## Awning startup behavior

- Ignores startup awning motion until the controller has provided
  authoritative idle telemetry.
- Starts tracking normally after that idle state, including movement initiated
  from the wall panel.
- Keeps Home Assistant open, close, and jog commands immediately responsive.

## Smart open endpoint

The current-sense Carefree Flip sequence is unchanged. After arm-lock
detection, the configured overrun, and the fabric-tightening retract, the
awning continues to report a synthetic 100% open position instead of the
roughly 90% physical fabric extension.
