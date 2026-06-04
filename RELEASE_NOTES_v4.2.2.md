# Precision Plex v4.2.2 — Native Cover Startup Hotfix

This is a hotfix release for v4.2.1.

## Fixed

- Fixed a startup failure caused by shared native cover helper methods being attached only to the new clean cover subclass instead of the preserved legacy cover class.
- Restored availability for existing awning, bed slide, wardrobe slide, and sofa slide cover entities.
- Preserved the new clean native cover entities introduced for HomeKit/dashboard testing.

## Upgrade Notes

Install over v4.2.1 and restart Home Assistant. Do not remove or re-add the integration.

## Testing Focus

After restart, confirm:

- Precision Plex loads without cover platform errors.
- Existing cover entities are available again.
- New clean native cover entities are present.
- Sensors, switches, generator controls, jog buttons, and calibration buttons remain available.
