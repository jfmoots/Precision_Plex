# Reference Calibrations

## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

Different Precision Plex equipped coaches may expose different numbers of slides, lights, tanks, relays, and sensors. The protocol documentation in `/docs` is intended to help other owners adapt the integration to their specific coach configuration.

## Quadrature Full-Travel Counts

v5.2.0 uses ESPHome quadrature telemetry as the primary position source for the tested Bedroom, Sofa, and Wardrobe slide covers when telemetry is available.

| Slide | Full Travel Count |
| --- | ---: |
| Bedroom Slide | 21,727 |
| Sofa Slide | 21,503 |
| Wardrobe Slide | 13,873 |

These values were measured from full-retract to full-extension using ESPHome `rotary_encoder` decoding of the Lippert motor Hall sensor channels.

## Timing Fallback Calibrations

Timing remains available as a fallback and for the patio awning.

| Device | Open / Out | Close / In |
| --- | ---: | ---: |
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values are reference calibrations for this specific Georgetown GT5 34M5 installation and can be adjusted through the Home Assistant Number entities without modifying the integration.
