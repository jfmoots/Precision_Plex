# Precision Plex v5.3.1 — Smart Awning Control Test 2

This test build wires smart awning current sensing into the actual awning cover command path.

## Changes

- Smart awning open now uses ACS758 current telemetry when available.
- Open sequence:
  - extend
  - ignore startup current
  - detect arm-lock current
  - overrun briefly
  - stop
  - retract briefly for fabric tightening
  - stop
- Smart awning close now uses current-drop-to-zero after the factory retract cutout.
- Slides remain on the existing timed/quadrature code paths.
- Automatic fallback to timed mode remains in place when awning current telemetry is unavailable.
- Adds/keeps tuning numbers for thresholds and timing.
- Adds Awning Control Method diagnostic sensor.

## Defaults

- Arm Lock Threshold: 8.0 A
- Current Confirm: 300 ms
- Current Ignore: 2.0 s
- Extend Overrun: 500 ms
- Fabric Tighten: 1000 ms
- Retract End Threshold: 11.0 A

