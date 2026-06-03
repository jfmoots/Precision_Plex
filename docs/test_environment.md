# Test Environment

## Primary Development Platform

```text
2022 Forest River Georgetown GT5 34M5
```

System:

```text
Precision Circuits Precision Plex
Precision Circuits Wireless TP Monitor
```

## Validated Functions

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Generator Running telemetry
- Generator Runtime telemetry
- Coach Battery telemetry
- Fresh Water Tank telemetry
- Grey Water Tank telemetry
- Black Water Tank telemetry
- LP Gas telemetry
- Awning Extend
- Awning Retract
- Bed Slide Extend
- Bed Slide Retract
- Wardrobe Slide Extend
- Wardrobe Slide Retract
- Sofa Slide Extend
- Sofa Slide Retract
- Position estimation
- Wall-panel tracking
- Bidirectional synchronization

## Validation Methods

The project used:

- Precision Plex wall panel observation
- Precision Plex iOS app observation
- Bluetooth PacketLogger captures
- Controlled tank probe jumper testing
- Home Assistant log validation
- Live Home Assistant entity testing

## Coach-Specific Notes

Precision Plex installations vary by manufacturer, model, year, and option package.

Different coaches may expose different:

- Slide rooms
- Lighting zones
- HVAC controls
- Generator controls
- Water system controls
- Tank monitoring functions
- Specialty accessories

Current support should be considered verified for the Georgetown GT5 34M5 reference coach.

Other coaches may require additional state mapping and command decoding.
