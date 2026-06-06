# Precision Plex Home Assistant Integration v4.5.3

## Logging Level Cleanup

This maintenance release removes the remaining successful subscription startup messages that were still appearing in the Home Assistant warning log.

### Changes

- Removed normal-success startup logging for 02AA telemetry notification subscription.
- Removed normal-success startup logging for 02BB state notification subscription.
- Retained all telemetry validation and runtime protection behavior from v4.5.x.

### No Functional Changes

This release contains no changes to BLE communication behavior, entity behavior, telemetry decoding, propane validation, generator runtime validation, tank monitoring, cover controls, or HomeKit support.

### Summary

v4.5.3 is a small production-polish release focused only on keeping the Home Assistant warning log clean during normal startup.
