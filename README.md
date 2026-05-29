# Precision Plex Home Assistant Integration

## Stable BLE Baseline

This build keeps the verified reliable behavior.

### Awning Light
- Home Assistant ON/OFF control
- State read from the Precision Plex `02bb` state characteristic
- Short 5-second notification window after Home Assistant commands
- Periodic polling retained
- Reduced BLE hold time to avoid Precision Plex wireless module lockups

### Water Pump
- Home Assistant ON/OFF control
- State-aware toggle behavior
- Reads current pump state before sending a command
- Reads and verifies pump state after command execution
- Uses short-lived BLE sessions
- No water pump notification window in this stable baseline

## Notes

The Precision Plex wireless module appears sensitive to long-lived BLE sessions. This build avoids the previous 30-second notification window and uses a 5-second window for the awning light only.
