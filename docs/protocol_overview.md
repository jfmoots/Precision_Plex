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


## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

Different Precision Plex equipped coaches may expose different numbers of slides, lights, tanks, relays, and sensors. The protocol documentation in `/docs` is intended to help other owners adapt the integration to their specific coach configuration.


## Reference Calibrations

These travel times were validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values are reference calibrations for this specific Georgetown GT5 34M5 installation and can be adjusted through the Home Assistant Number entities without modifying the integration.
