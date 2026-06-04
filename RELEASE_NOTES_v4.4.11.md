# Precision Plex v4.4.11

## Fixes

- Fixes a config-entry startup issue after adding the integration from the UI.
- If Home Assistant is already running when the config entry is created, the BLE coordinator now starts immediately instead of waiting for a startup event that has already passed.
- This should prevent entities from remaining unavailable until a full Home Assistant restart after adding the integration.

## Also included

- Existing BlueZ paired/bonded detection from v4.4.10 remains in place.
- Existing HomeKit/entity cleanup and generator runtime protections remain unchanged.
