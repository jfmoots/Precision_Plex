# Precision Plex v2.6.22 - Fresh Tank 02AA Decoder Test

## Added
- Adds a Fresh Water Tank sensor.
- Decodes Fresh Water level from the confirmed 02AA / handle 0x002B levels packet.

## Confirmed Fresh Water mapping
- `0x00` -> `0%`
- `0x03` -> `33%`
- `0x06` -> `67%`
- `0x0A` -> `100%`

## Notes
- Keeps the working coach battery voltage decoder from the same 02AA packet.
- Removes reliance on the earlier experimental 0x0033/channel/probe logic for Fresh Water.
- Keeps the improved unload/reload behavior so the integration can be enabled/disabled without a full Home Assistant restart.
