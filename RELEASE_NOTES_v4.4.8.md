# Precision Plex v4.4.8 - Restore HomeKit-Safe Device Grouping

This release rolls back the experimental entity-registry naming migration from v4.4.7.

## Why

v4.4.7 proved that HomeKit was using Home Assistant registry names, but it also exposed a HomeKit grouping behavior: when Precision Plex entities remain associated with the same Home Assistant device, HomeKit may group them under a single accessory name. Setting one entity registry name, such as Bedroom Slide, can cause the grouped HomeKit accessory to prefix other services with that same name.

## Changes

- Restores the safer v4.4.5 device association behavior.
- Removes the automatic entity-registry naming migration.
- Keeps entities grouped correctly under the Precision Plex device in Home Assistant.
- Keeps the previous HomeKit exposure cleanup and generator runtime protections from the 4.4.x baseline.

## Notes

If v4.4.7 was installed and Home Assistant/HomeKit cached names, remove and re-add the Precision Plex integration and refresh/re-add the HomeKit Bridge accessories as needed.
