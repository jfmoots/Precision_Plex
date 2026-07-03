# Precision Plex v5.3.16 – Smart Awning Threshold & Safety Timeout Tuning

This release tunes Smart Current Sense Awning Control for warmer-weather arm-lock behavior and reduces the smart-open safety window so the awning cannot continue extending far past the expected full-travel window if arm-lock current is not detected.

## Changes

- Lowered the default awning arm-lock threshold from 8.0A to 6.0A.
- Reduced the smart-awning extra open safety timeout from 45 seconds to 5 seconds beyond the configured full-open travel time.
- Kept event-latched arm-lock detection from v5.3.12.
- Kept smart-open state machine fixes from v5.3.15.

## Notes

Existing installations may retain the previous restored threshold value. If upgrading from an earlier v5.3.x build, verify the Home Assistant number entity:

- Awning Arm Lock Threshold: 6.0A

