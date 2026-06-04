# Precision Plex v4.2.0 — Native Cover Entities

This release focuses on making the awning and slide controls behave like first-class Home Assistant cover entities while preserving the tested legacy jog and calibration controls.

## What changed

- Bumped integration version to `4.2.0`.
- Clarified the cover platform as the native Home Assistant cover interface for the awning and slides.
- Added native cover diagnostic attributes so support logs clearly identify these entities as the primary cover interface.
- Added the Home Assistant awning device class to the awning entity for better UI/HomeKit presentation.
- Preserved existing cover unique IDs, jog buttons, reset/calibration buttons, runtime timing numbers, BLE commands, and coach profile behavior.

## Native cover behavior

The following devices continue to expose native Home Assistant cover controls:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Supported services include:

- `cover.open_cover`
- `cover.close_cover`
- `cover.stop_cover`
- `cover.set_cover_position`

## Compatibility

This release is designed to be upgrade-safe from v4.1.1. No remove/re-add, re-pairing, or configuration migration should be required.

Legacy jog and calibration buttons remain available so existing dashboards and workflows continue to work.
