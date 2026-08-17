# Precision Plex v5.5.10 — Stable Carefree Flip Endpoint

This release keeps the Patio Awning's synthetic 100% position intact after the
smart current-sense Carefree Flip sequence.

## Endpoint handling

- Latches the 100% current-sense endpoint while trailing Flip retract telemetry
  is still active.
- Waits for authoritative controller-idle telemetry before releasing that
  endpoint hold.
- Prevents the time estimator from replacing 100% with the roughly 91% physical
  fabric-extension estimate.
- Clears the hold normally when a genuine open, close, or jog command begins.

The v5.5.9 restart motion guard and current-sense closed endpoint remain
unchanged.
