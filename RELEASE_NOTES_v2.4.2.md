# Precision Plex v2.4.2 — Documentation & Protocol Reference Update

## Summary

This release focuses on documentation, protocol reference material, GitHub/HACS packaging improvements, and long-term maintainability.

The integration code remains functionally based on the known-good v2.4.1 baseline. The main changes are documentation, repository metadata, and packaging improvements.

## Highlights

- Added `/docs` protocol documentation
- Added BLE architecture documentation
- Added persistent BLE / Wireless TP replacement rationale
- Added state mapping reference
- Added command packet reference
- Added position estimation documentation
- Added Georgetown GT5 34M5 test environment notes
- Added contribution guide
- Added release history documentation
- Added HACS metadata file
- Corrected GitHub documentation and issue tracker URLs
- Updated README to clarify current recommended release and coach-specific support

## Primary Development Platform

2022 Forest River Georgetown GT5 34M5

## Current Stable Features

- Awning Light
- Water Pump
- Water Heater
- Awning Cover
- Bed Slide Cover
- Position Estimation
- Wall Panel Tracking
- Configurable Travel Times
- Bidirectional BLE Synchronization

## Known Limitations

- Position values are estimated rather than sensor-confirmed
- Travel times may require occasional calibration
- The Wireless TP monitor appears to allow only one active BLE connection
- Sofa Slide and Wardrobe Slide support are not yet implemented

## Next Planned Work

- Sofa Slide support
- Wardrobe Slide support
- Additional Wireless TP functions
- Expanded coach-specific protocol documentation
