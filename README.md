# Precision Plex Home Assistant Integration v1.7.0

## Features

### Awning Light
- ON/OFF control from Home Assistant
- State synchronization using Precision Plex state characteristic (02bb)
- Notification-based updates after Home Assistant commands
- Periodic state polling for recovery and resynchronization
- Wall-switch changes eventually synchronize with Home Assistant
- Startup-safe polling architecture

### Water Pump
- ON/OFF control from Home Assistant
- State-aware operation using Precision Plex state characteristic (02bb)
- Reads current pump state before sending commands
- Only sends a toggle when a state change is required
- Reads and verifies state after command execution
- Automatic BLE reconnect handling

### General Features
- Bluetooth auto-discovery
- Guided pairing workflow
- Precision Plex mobile app compatibility
- Local Bluetooth operation

## Supported Devices
- Awning Light
- Water Pump

## Release Notes

### v1.7.0
- Added Water Pump switch entity
- Added state-aware water pump control
- Added automatic BLE reconnect handling
- Added pre-command state verification
- Added post-command state verification
