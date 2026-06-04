# Precision Plex v4.3.2 — HomeKit Exposure Cleanup

This release tightens the HomeKit experience introduced in v4.3.x by reducing noisy/internal entities that Apple Home was rendering as confusing categories such as occupancy/person, generic switches, or miscellaneous tiles.

## Changed

- Marks decoded Precision Plex state-bit binary sensors as diagnostic entities.
- Marks the generator running binary status as diagnostic.
- Marks generator runtime and generator status telemetry as diagnostic.
- Marks slide/awning jog and position reset utility buttons as configuration entities.
- Marks travel-time tuning number entities as configuration entities.

## Unchanged

- Keeps the v4.3.1 HomeKit-friendly humidity percentage helper sensors for Fresh Water, Grey Water, Black Water, and Propane.
- Keeps core controls unchanged: covers, awning light, water pump, water heater, and generator command buttons.
- Does not change BLE command payloads, pairing behavior, cover timing logic, or telemetry decoding.

## Notes

After installing, restart Home Assistant and review the HomeKit Bridge include/exclude list. Existing entities already added to Apple Home may need to be removed from the Home app or re-synced after Home Assistant updates their entity categories.
