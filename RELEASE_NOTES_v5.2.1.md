# Precision Plex v5.2.1 - Quadrature Motion Verification

v5.2.1 is a focused follow-up to v5.2.0. It keeps the quadrature slide telemetry architecture and adds motion verification for quadrature-enabled slides.

## Highlights

- Adds quadrature-only slide motion verification for Bedroom, Sofa, and Wardrobe slides.
- Stops the BLE hold stream when a commanded quadrature slide does not show encoder movement after approximately three seconds.
- Helps avoid repeated BLE hold commands when slides are locked out downstream, such as when the motorhome ignition interlock prevents slide motion.
- Keeps timing-only installations unchanged. Covers without quadrature telemetry continue to run using the existing time-based model.
- Adds diagnostic attributes for the last motion verification failure.

## New Diagnostic Attributes

When a quadrature-enabled slide command is aborted because no encoder movement was detected, the cover exposes diagnostics similar to:

```yaml
motion_verification_failed: true
motion_verification_reason: no_quadrature_movement
motion_verification_failed_age_seconds: 4.2
```

The diagnostic clears automatically after successful quadrature movement is detected later.

## Behavior

Quadrature-enabled slides now follow this command behavior:

1. Start the normal Precision Plex press-and-hold BLE command stream.
2. Read the current quadrature travel count.
3. Wait approximately three seconds.
4. If travel counts changed, continue normally.
5. If travel counts did not change, stop the hold stream and expose a diagnostic flag.

This is intended to catch conditions where the factory Precision Plex command path is reachable but the physical slide is prevented from moving by a downstream interlock or fault.

## Compatibility

No ESPHome telemetry is required. If quadrature telemetry is unavailable, the integration retains the existing timing-based slide behavior from previous releases.

## Included From v5.2.0

- Bedroom, Sofa, and Wardrobe quadrature slide positioning.
- Automatic quadrature telemetry discovery.
- Startup restoration directly into quadrature mode.
- Direction-independent quadrature position tracking.
- Timing fallback when telemetry is unavailable.
