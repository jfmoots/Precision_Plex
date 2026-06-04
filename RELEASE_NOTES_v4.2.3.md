# Precision Plex v4.2.3 — Native Cover Cleanup

## Overview

This release cleans up the v4.2 native cover transition. v4.2.2 correctly restored availability and created both legacy and clean native cover entities. v4.2.3 makes that transition clearer in Home Assistant by labeling the old preserved entities as legacy and making the clean native cover entities the primary entities for new installs and HomeKit exposure.

## What Changed

- Legacy cover entities are now labeled with `Legacy` in their default name.
- Legacy cover entities are disabled by default for new installations. Existing installations will keep already-enabled entities until the user disables or hides them.
- Clean native cover entities remain enabled by default.
- Slide native cover entities are left as generic covers instead of being forced into a misleading window-style presentation.
- Awning remains marked as a native awning cover.
- Existing unique IDs are preserved so dashboards and automations are not forcibly broken.

## Recommended HomeKit Setup

Expose the clean native cover entities to HomeKit:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Remove or exclude the legacy cover entities from HomeKit Bridge.

## Upgrade Notes

No re-pairing is required. No Precision Plex configuration changes are required. Restart Home Assistant after installing the release.
