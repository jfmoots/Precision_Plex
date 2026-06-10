# Precision Plex v5.1.0 – Optional Sofa Slide Pulse Telemetry

This release adds optional pulse-based Sofa Slide position tracking for installations with an ESPHome Lippert slide telemetry node.

## New

- Adds optional Sofa Slide ESPHome telemetry support.
- Uses measured slide motor travel pulses when available.
- Keeps the existing time-based position estimator as the automatic fallback.
- Adds Sofa Slide cover attributes for:
  - `position_source`
  - `pulse_telemetry_available`
  - `pulse_travel_total`
  - `pulse_last_delta`
  - `pulse_full_travel`
  - `pulse_sync_error`
- Re-baselines pulse tracking when the existing fully-extended or fully-retracted reset buttons are used.
- Handles ESPHome pulse counter reset/reflash by re-baselining instead of applying a bad negative movement delta.

## Expected ESPHome Entities

The integration looks for these friendly names by default:

- `Sofa Slide Travel Pulses`
- `Sofa Slide Sync Error`
- `Sofa Slide Moving`

It also checks common entity IDs such as:

- `sensor.sofa_slide_travel_pulses`
- `sensor.lippert_sofa_slide_controller_sofa_slide_travel_pulses`
- `sensor.lippert_sofa_slide_telemetry_sofa_slide_travel_pulses`

## Tested Prototype Notes

The tested Georgetown sofa slide produced approximately 5,400–5,450 pulses per full travel, with Motor 1 and Motor 2 remaining closely synchronized. The default full-travel pulse value is 5,450 pulses.

## Compatibility

No existing Precision Plex users are required to add ESPHome hardware. If pulse telemetry is not present, slide position behavior remains time-based just like v5.0.0.
