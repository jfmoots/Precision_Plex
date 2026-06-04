# Precision Plex v4.4.14

## Startup Availability Tuning

This release keeps the v4.4.13 startup fix and tunes the BLE connection retry behavior so Precision Plex entities should become available faster after Home Assistant startup or after adding the integration.

### Changes

- Reduced the BLE connection timeout used by the monitor.
- Disabled long nested Bleak retry batches during startup.
- Let the Precision Plex coordinator retry quickly in its own connection loop instead.
- Kept the BLE connection loop as a background task so Home Assistant startup remains fast.

### Notes

No configuration changes are required.
