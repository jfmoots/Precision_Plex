# Precision Plex v4.2.4 — Native Cover Cleanup

This release completes the v4.2 native cover transition by stopping creation of the preserved legacy cover entities.

## Changed

- New clean native cover entities are now the only cover entities created by the integration.
- Legacy cover entities are no longer created during platform setup.
- Jog buttons, calibration buttons, travel timing numbers, and jog timing numbers remain available.
- Awning remains classified as an awning cover.
- RV slide covers remain generic covers to avoid the misleading window device class/icon.

## Existing Home Assistant Entity Registry Note

Home Assistant may keep old legacy entity registry entries from previous v4.2.x installs. If those stale entries still appear after upgrade, remove the old legacy/unavailable cover entities from Settings → Devices & Services → Entities.

## Expected Result

After cleanup, the active cover set should be:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Each should expose standard Home Assistant cover controls while the existing jog and calibration controls remain available on the Precision Plex device.
