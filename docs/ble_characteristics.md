# BLE Characteristics

## Control Characteristic

UUID:

```text
03726f62-6f74-7061-6a61-6d61732e6361
```

Purpose:

Send control commands to the Precision Plex Wireless TP monitor.

Known commands include:

- Awning Light
- Water Pump
- Water Heater
- Awning In / Out
- Bed Slide In / Out

## State Notification Characteristic

Known in captures as the `02BB` notification stream.

Purpose:

Report current state and movement activity.

The payload is decoded as a sequence of big-endian 16-bit words.

Known decoded words:

- Word 0: awning, pump, heater, awning light
- Word 1: bed slide movement

## Notes

The integration maintains an active subscription to the state notification characteristic so Home Assistant can receive live updates from both Home Assistant commands and RV wall-panel actions.
