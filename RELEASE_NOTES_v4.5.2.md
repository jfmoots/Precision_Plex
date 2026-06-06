# Precision Plex Home Assistant Integration v4.5.2

## Production Log Cleanup Follow-Up

v4.5.2 is a small cleanup release following the v4.5.0 telemetry validation release and the v4.5.1 02AA sanity guard follow-up.

This release keeps the telemetry protection work intact while removing the remaining reverse-engineering diagnostic log chatter from normal Home Assistant startup.

## Changes

- Removed the generator runtime source diagnostic message from normal logging.
- Kept the generator runtime recovery and sanity logic in production behavior.
- Kept 02AA and 02BB subscription confirmations as normal startup information.
- Preserved propane telemetry validation and last-known-good retention.
- Preserved 02AA frame-shape sanity checks and LP change confirmation.
- Preserved generator flag cleanup and runtime protection.
- Kept logs quiet unless something actually needs attention.

## Notes

The generator runtime recovery logic remains part of the production decoder. What was removed is only the diagnostic message explaining which runtime candidate was selected.

This release should produce a cleaner Home Assistant restart log while retaining the telemetry stability improvements from v4.5.0 and v4.5.1.
