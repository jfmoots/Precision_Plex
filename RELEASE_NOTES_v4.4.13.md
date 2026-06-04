# Precision Plex v4.4.13

## Fixes

- Fixed a Home Assistant startup timeout where the Precision Plex BLE connection loop could be tracked as a startup task.
- The BLE monitor now runs as a background task for the lifetime of the config entry instead of blocking bootstrap.
- No HomeKit naming behavior changes in this build.

## Testing focus

- Restart Home Assistant and confirm it no longer remains stuck on "Wrapping up startup" waiting for `PrecisionPlexStateCoordinator._connection_loop()`.
- Confirm Precision Plex entities still become available normally after startup.
