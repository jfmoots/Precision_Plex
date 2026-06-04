# Precision Plex v4.4.2 — HomeKit Naming Polish Merge

This release applies the HomeKit naming and presentation polish on top of the existing v4.4.1 codebase provided by the user, preserving the current runtime protections and telemetry behavior.

## Changes

- Uses exact friendly names for HomeKit-facing helper level sensors so Apple Home shows cleaner labels.
- Renames HomeKit helper levels:
  - Fresh Water
  - Grey Tank
  - Black Tank
  - Propane
- Renames clean native covers for friendlier HomeKit display:
  - Patio Awning
  - Bedroom Slide
- Uses exact friendly names for switch/light/generator button entities where appropriate, reducing device-name prefix clutter in Apple Home.
- Keeps existing unique IDs stable to avoid breaking automations and dashboards.

## Notes

Home Assistant may preserve old friendly names in the entity registry for entities that already existed. If a name does not change after installing this release, rename the entity manually in Home Assistant or remove/re-add the entity from the registry.
