# Precision Plex v5.3.4 — Smart Awning Retract Close Fix

This test build improves the smart awning close path.

## Changes

- Smart retract now watches the ESPHome `Awning Motor Running` binary sensor when available.
- Smart retract still supports current drop-to-zero detection as a fallback.
- The retract stream is stopped when the motor-running sensor turns off after the factory awning cutout.
- Smart close sets the awning position to 0% after confirmed close detection.
- Safety-timeout handling is more conservative and avoids leaving the cover stuck in a moving state.
- Manifest updated to 5.3.4.

## Test Focus

- Verify HA Close retracts fully.
- Verify HA no longer leaves the awning in a Moving state after the factory cutout.
- Verify HA reports 0% after smart close.
- Reconfirm Smart Open still performs the tuned Carefree Flip.
