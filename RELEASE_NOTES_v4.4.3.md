# Precision Plex v4.4.3 - HomeKit Accessory Name Cleanup

This release continues the Enhanced HomeKit Experience work.

## Changes

- Shortens the Precision Plex device name reported through Home Assistant device metadata.
- Keeps clean entity names such as Bedroom Slide, Patio Awning, Fresh Water, Grey Tank, Black Tank, and Propane.
- Reduces the chance that Apple Home builds long accessory names containing the Bluetooth MAC address.
- Preserves existing unique IDs and runtime protections from the current baseline.

## Testing Focus

After updating and restarting Home Assistant, remove/re-add the affected HomeKit Bridge entities if Apple Home keeps cached names, then verify the imported accessory names are shorter and cleaner.
