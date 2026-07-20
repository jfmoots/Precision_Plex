# Precision Plex v5.5.4 — Command-Responsive PID32 Controls

This release makes Home Assistant controls respond immediately while retaining
authoritative LIN and Bluetooth confirmation.

## Immediate state feedback

- Awning Light, Water Pump, and Water Heater controls now share one
  confirmation-aware state layer.
- Patio Awning, Bedroom Slide, Wardrobe Slide, and Sofa Slide movement states
  update immediately for Home Assistant open, close, jog, and stop commands.
- Matching movement binary sensors receive the same immediate state, so cards
  no longer disagree with their cover entity while waiting for PID32.
- A stale PID32 frame cannot momentarily flip a newly commanded entity back to
  its previous state.

## Authoritative reconciliation

- PID32 and BLE 02BB remain authoritative telemetry sources.
- A matching telemetry value confirms and removes the provisional state without
  creating another visible transition.
- An unconfirmed command falls back to telemetry after 12 seconds, slightly
  longer than two measured PID32 broadcast cycles.
- Diagnostic attributes expose confirmed state, requested state, and whether
  confirmation is pending.

## Availability behavior

The independent 30-second freshness grace periods introduced in v5.5.3 remain
in place. They prevent rotating LIN sources from becoming unavailable between
broadcasts and do not delay real state changes.

All commands remain on Bluetooth. LIN remains the preferred telemetry source.
