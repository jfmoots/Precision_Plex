# Precision Plex Home Assistant Integration v1.5.0

A custom Home Assistant integration for controlling a Precision Plex BLE controller.

## Features

- Stable awning light ON/OFF control
- Bluetooth auto-discovery with friendly device naming
- Pairing guidance for unbonded devices during setup
- Clean logging during normal operation
- Immediate BLE disconnect after the notification window so iPhone/mobile apps can connect freely
- Opportunistic wall-switch synchronization using the Precision Plex `02bb` notification characteristic

## Wall-Switch Sync Behavior

Home Assistant listens for awning light state notifications for a short window after it controls the light.

Observed state values on `02bb6f62-6f74-7061-6a61-6d61732e6361`:

- `10 00 ... 4d` = awning light OFF
- `11 00 ... 4c` = awning light ON

This allows the HA UI to update when the Precision Plex wall switch is used while the BLE session is active.

## Known Limitations

- Wall-switch changes are only detected while Home Assistant is connected during the notification window.
- First command can take several seconds because the BLE session is opened on demand.
- Home Assistant remains the authoritative state source outside the notification window.
- Only the awning light is currently implemented.

## Notes

This release intentionally avoids a persistent BLE connection so the Precision Plex mobile app can connect when needed.
