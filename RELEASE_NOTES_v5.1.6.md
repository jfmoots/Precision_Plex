# Precision Plex v5.1.6

## Robust ESPHome Slide Telemetry Discovery

This release improves optional ESPHome Schwintek slide telemetry detection for installations where Home Assistant generates long area/device-prefixed entity IDs.

### Fixed

- Detects ESPHome telemetry entities even when Home Assistant creates long IDs such as:
  - `sensor.basement_lippert_sofa_slide_controller_sofa_slide_travel_pulses`
  - `sensor.basement_lippert_wardrobe_slide_controller_wardrobe_slide_travel_pulses`
- Matches telemetry by exact entity ID, friendly name, friendly-name suffix, entity-ID suffix, and slide-scoped fallback search.
- Prevents supported pulse telemetry from incorrectly showing `pulse_telemetry_available: false` when the ESPHome telemetry entities are present under long names.

### Notes

- Existing time-based slide positioning remains the fallback if telemetry is unavailable.
- Sofa slide retains all-channel averaged telemetry.
- Wardrobe slide support uses the wardrobe telemetry profile and measured full-travel pulse default.
- No change is required for users who do not have ESPHome slide telemetry modules.
