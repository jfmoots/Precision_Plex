# Precision Plex v4.3.1 — HomeKit Level Sensor Cleanup

This maintenance release refines the Enhanced HomeKit experience introduced in v4.3.0.

## Improvements

- Keeps the new HomeKit-friendly Fresh Water, Grey Water, Black Water, and Propane percentage helpers as humidity-style sensors for clean Apple Home display.
- Marks the original native tank/propane telemetry sensors as diagnostic entities so they are less likely to be auto-exposed to HomeKit as generic/air-quality-style sensors.
- Cleans up helper display names so Apple Home can show simple names like Fresh Water, Grey Water, Black Water, and Propane.

## Notes

If an older native tank or propane entity was already exposed through the HomeKit Bridge, remove that accessory from the bridge or exclude the original entity. The preferred Apple Home entities are the new HomeKit helper sensors.
