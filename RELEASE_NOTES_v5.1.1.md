# v5.1.1 - Sofa Slide Pulse Telemetry Final-Stop Reconciliation

This maintenance release refines the optional Sofa Slide ESPHome pulse telemetry support introduced in v5.1.0.

## Fixes

- Keeps applying Sofa Slide pulse deltas briefly after the Precision Plex motion bit drops so ESPHome's final sensor update is not missed.
- Improves `pulse_telemetry_available` so it reflects the current ESPHome telemetry entity state instead of a stale internal flag.
- Preserves existing time-based slide position fallback when pulse telemetry is unavailable.
- Preserves existing manual position reset buttons and uses them to re-baseline pulse tracking.

## Notes

The ESPHome pulse counters are cumulative since ESP boot and may reset after ESP reboot or reflash. The Precision Plex reset buttons remain the calibration mechanism for known fully extended or fully retracted positions.
