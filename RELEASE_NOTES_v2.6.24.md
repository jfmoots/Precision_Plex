# Precision Plex v2.6.24

Tank monitor decoder update.

## Changes

- Adds Black Water Tank sensor.
- Keeps Fresh Water Tank decoder as byte 2 low nibble.
- Keeps Grey Water Tank decoder as byte 3 high nibble.
- Adds Black Water Tank decoder as byte 4 high nibble.
- Uses the confirmed tank nibble scale: `0x0 = 0%`, `0x3 = 33%`, `0x6 = 67%`, `0xA = 100%`.

## 0x002B / 02AA tank layout used in this build

- Fresh: `payload[2] & 0x0F`
- Grey: `(payload[3] & 0xF0) >> 4`
- Black: `(payload[4] & 0xF0) >> 4`
