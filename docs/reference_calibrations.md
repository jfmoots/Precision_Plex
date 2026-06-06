# Reference Calibrations

## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

Different Precision Plex equipped coaches may expose different numbers of slides, lights, tanks, relays, and sensors. The protocol documentation in `/docs` is intended to help other owners adapt the integration to their specific coach configuration.


## Reference Calibrations

These travel times were validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values are reference calibrations for this specific Georgetown GT5 34M5 installation and can be adjusted through the Home Assistant Number entities without modifying the integration.


## Home Assistant Number Entities

| Entity Purpose | Default |
|---|---:|
| Awning Open Seconds | 18 |
| Awning Close Seconds | 25 |
| Bed Slide Open Seconds | 28 |
| Bed Slide Close Seconds | 24 |
| Wardrobe Slide Open Seconds | 18 |
| Wardrobe Slide Close Seconds | 17 |
| Sofa Slide Open Seconds | 32 |
| Sofa Slide Close Seconds | 28 |

These values are user-adjustable in Home Assistant and do not require editing Python files.
