# Precision Plex v5.3.15 – Smart Awning Open State Machine Fix

This maintenance build fixes a Smart Current Sense Awning Control regression in the open sequence.

## Fixes

- Removed an erroneous close-path diagnostic reference from the smart-open path.
- Prevents `NameError: detected_retract_seat is not defined` after arm-lock detection.
- Adds an explicit extend release before the Carefree-style fabric-tighten retract.
- Preserves v5.3.12 event-latching behavior for short arm-lock pulses.
- Keeps diagnostic logging around the smart awning open/close state machine.

## Test Focus

- HA Open should detect arm lock, complete overrun, stop extend, perform the Carefree Flip, and stop cleanly.
- HA Close should still detect retract-seat current and stop cleanly.
