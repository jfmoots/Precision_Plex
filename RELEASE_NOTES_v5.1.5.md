# v5.1.5 – Wardrobe Slide Pulse Telemetry Support

This release expands the optional ESPHome/ESP32 Schwintek pulse telemetry support from the Sofa Slide to the Wardrobe Slide.

## New

- Added automatic Wardrobe Slide ESPHome pulse telemetry detection.
- Added Wardrobe Slide pulse-derived position tracking.
- Added Wardrobe Slide pulse sync error diagnostics.
- Added Wardrobe Slide travel pulse diagnostics.
- Added endpoint snapping for supported pulse-telemetry slides.
- Preserved automatic fallback to the existing time-based model when telemetry is unavailable.

## Notes

The Wardrobe Slide telemetry module uses the ESPHome `Wardrobe Slide Travel Pulses`, `Wardrobe Slide Sync Error`, and `Wardrobe Slide Moving` entities. The current default full-travel calibration is 3,773 pulses based on the first validated Wardrobe Slide test run.

The Sofa Slide telemetry behavior is preserved.
