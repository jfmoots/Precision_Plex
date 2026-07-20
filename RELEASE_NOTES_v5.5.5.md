# Precision Plex v5.5.5 — LIN Generator Runtime and Responsive Generator Commands

This release completes LIN-preferred generator telemetry and makes generator
commands feel immediate without claiming the generator has changed state before
the coach confirms it.

## Complete LIN runtime

- Prefers the complete PIDBA generator runtime published by firmware v0.6.2.
- Retains the existing guarded Bluetooth decoder as a field-level fallback.
- Applies range and cross-transport jump checks while the BCD whole-hour
  rollover is being field-validated.
- The current `125.4` LIN decode exactly matches Bluetooth.

## Responsive generator commands

- Generator Status immediately reports Start Requested, Stop Requested,
  AutoStart Requested, or AutoStop Requested after a Home Assistant command.
- Authoritative LIN/Bluetooth state automatically replaces the requested state
  when the coach confirms the transition.
- Generator Running remains authoritative telemetry and is never changed merely
  because a command was sent.

## Quieter activity

- Generator command buttons no longer cycle available/unavailable with each
  generator state.
- Safety interlocks are still checked when a button is pressed.
- This prevents unrelated generator buttons from appearing as Pressed in the
  Home Assistant Activity view when telemetry refreshes.

Pair with ESPHome Precision Plex LIN firmware v0.6.2.
