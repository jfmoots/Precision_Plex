# Precision Plex Home Assistant Integration v1.4.0

A custom Home Assistant integration for controlling a Precision Plex BLE controller.

## Features

- Stable awning light ON/OFF control
- Bluetooth auto-discovery with friendly device naming
- Pairing guidance for unbonded devices during setup
- Clean logging during normal operation
- Immediate BLE disconnect after commands so iPhone/mobile apps can connect freely

## Known Limitations

- First command can take several seconds because the BLE session is opened on demand.
- Wall-panel state changes are not currently reflected in Home Assistant.
- Home Assistant remains the authoritative state source for the awning light entity.
- Only the awning light is currently implemented.

## Notes

This release intentionally avoids persistent BLE keepalive so the Precision Plex mobile app can connect when needed.
