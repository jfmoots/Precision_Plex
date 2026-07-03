# Precision Plex v5.3.12 – Smart Awning Event Latch Fix

This maintenance release fixes a Smart Current Sense awning regression where the ESPHome arm-lock pulse could occur too quickly for the smart-open polling loop to reliably catch it.

## Fixes

- Smart awning open now listens to Home Assistant state change events for the awning extend event.
- Smart awning open also latches raw current sensor spikes above the configured arm-lock threshold.
- This prevents the awning from blowing past arm lock when the ESPHome event pulse is very brief.
- Maintains the corrected v5.3.11 units for awning configuration entities.

## Expected Behavior

When Smart Current Sense is available, HA Open should again perform:

Extend → arm lock detected → overrun → Carefree Flip → stop.
