# Precision Plex Home Assistant Integration v1.3.0

A custom Home Assistant integration for controlling a Precision Plex BLE controller.

## Features

- Stable awning light ON/OFF control
- Bluetooth auto-discovery with friendly device naming
- Pairing guidance for unbonded devices during setup
- Clean logging during normal operation
- Startup BLE warm-up to reduce delay on first light command

## Known Limitations

- Wall-panel state changes are not currently reflected in Home Assistant.
- Home Assistant remains the authoritative state source for the awning light entity.
- Only the awning light is currently implemented.

## Notes

This integration requires the Precision Plex controller to be paired, bonded, and trusted by the Home Assistant host.
