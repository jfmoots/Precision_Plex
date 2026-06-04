# Precision Plex v4.4.9 — Skip Pairing When Already Bonded

This release improves the setup/config flow for already-paired Precision Plex Bluetooth devices.

## Changes

- Checks BlueZ for an existing paired or bonded Precision Plex device after device selection.
- Skips the Pair with Mobile prompt when the selected device is already paired/bonded.
- Falls back to the existing pairing flow when no paired/bonded BlueZ device record is found.
- Keeps the v4.4.8 HomeKit-safe device grouping rollback behavior.

## Notes

This should make removing and re-adding the integration less annoying on systems where the Precision Plex BLE module is already bonded to Home Assistant.
