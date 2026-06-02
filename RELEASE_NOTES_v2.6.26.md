# Precision Plex v2.6.26 - Level Monitor Complete / GitHub Ready

This is the cleaned GitHub-ready release that consolidates the tested work from v2.6.3 through v2.6.25.

## Confirmed Working Feature Set

### Controls

- Awning Light
- Water Pump
- Water Heater
- Awning cover
- Bed Slide cover
- Wardrobe Slide cover
- Sofa Slide cover

### Level Monitor

Decoded from `02AA` / handle `0x002B`:

- Coach Battery
- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank

## Confirmed Level Decoder

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |

## Notes

- This release does not change the tested Fresh/Grey/Black tank decoder behavior from v2.6.24/v2.6.25.
- LP Gas was added as the next confirmed nibble in the same Level Monitor packet.
- Documentation has been updated to make this repository ready for GitHub publishing.
