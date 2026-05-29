# Precision Plex Home Assistant Integration v1.6.0

A custom Home Assistant integration for controlling a Precision Plex BLE controller.

## Features

- Stable awning light ON/OFF control
- Bluetooth auto-discovery with friendly device naming
- Pairing guidance for unbonded devices during setup
- Opportunistic wall-switch synchronization using BLE notifications
- Periodic awning light state polling using the `02bb` read characteristic
- No permanent BLE connection, preserving Precision Plex mobile app compatibility
- Polling starts only after Home Assistant startup completes

## State Sync Behavior

The awning light state is read from:

`02bb6f62-6f74-7061-6a61-6d61732e6361`

Observed values:

- `10 00 ... 4d` = awning light OFF
- `11 00 ... 4c` = awning light ON

## Polling

Production defaults:

- Poll start delay: 120 seconds after Home Assistant startup
- Poll interval: 300 seconds

## Known Limitations

- Only the awning light is currently implemented.
- State changes from the wall switch may take up to one polling interval to appear in Home Assistant when no active BLE notification window is open.
- First command may take several seconds because the BLE session is opened on demand.
