# Protocol Overview

## Communication Model

The Precision Plex Wireless TP module exposes BLE characteristics used by the mobile app.

The integration uses the same communication path:

1. Subscribe to state notifications.
2. Decode state words from the notification payload.
3. Send command packets to the control characteristic.
4. Update Home Assistant entities from notifications and command results.

## Conceptual Path

```text
RV Wall Panel
    ⇅
Precision Plex Controller
    ⇅
Wireless TP Module
    ⇅ BLE
Home Assistant
```

## Packet Pattern

Several command families follow this general structure:

```text
55 1D 10 0B [function id] [action] 00 00 00 00 00 00 [checksum]
```

For momentary/toggle devices, a single command packet is sent.

For movement devices such as awnings and slides, the mobile app sends:

1. A release/neutral packet.
2. A repeated hold packet approximately every 300 ms.
3. A release/neutral packet when movement stops.

Home Assistant mirrors this behavior.

## Coach Variability

The protocol appears largely shared across Precision Plex installations, but function IDs, state bits, and available features may vary by coach.
