# v5.1.3 - Notification-First BLE Startup Recovery

This maintenance release hardens Precision Plex BLE startup after Home Assistant OS reinstall/restore, Bluetooth re-pairing, or BlueZ/Bleak service-cache changes.

## Fixes

- Removes the startup dependency on the old bonded-session prime write.
- Removes the startup dependency on initial 02BB and 02AA GATT reads.
- Subscribes directly to the live 02BB wall-panel/control-state notification stream.
- Subscribes directly to the live 02AA battery/tank/generator telemetry notification stream.
- Avoids the GATT `Unlikely Error` / `TimeoutError` retry loop observed after a clean HAOS restore and BLE re-pair.

## Notes

Precision Plex publishes the needed state continuously through notifications, so startup reads are not required for normal operation. The integration still uses the same decoded notification data for coach battery, tanks, propane, generator status/runtime, lights, switches, slides, awning, and optional Sofa Slide pulse telemetry.

After restoring Home Assistant to new hardware or a new SD card, the Precision Plex BLE module may still need to be re-paired from the coach panel so BlueZ shows `Paired: yes`, `Bonded: yes`, and `Trusted: yes`.
