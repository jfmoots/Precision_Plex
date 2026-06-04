# Precision Plex v4.2.1 — Clean Native Covers

This hotfix completes the native cover rollout started in v4.2.0.

## What changed

- Added clean native cover entities for Awning, Bed Slide, Wardrobe Slide, and Sofa Slide.
- Preserved the original cover entities and unique IDs for backward compatibility.
- Preserved existing jog, calibration, and timing controls.
- Created new unique IDs for the clean cover entities so Home Assistant and HomeKit can discover them as new accessories.
- Kept the awning classified as a native awning cover.

## Why this release exists

v4.2.0 mainly updated the awning classification. The slide covers already existed in the older platform, so users did not see the intended new clean native entities. v4.2.1 adds those clean entities alongside the existing ones instead of replacing anything.

## Upgrade notes

No re-pairing or integration reconfiguration is required. After restart, you should see new clean cover entities in addition to the existing cover entities. Use the new clean entities for dashboards and HomeKit exposure.
