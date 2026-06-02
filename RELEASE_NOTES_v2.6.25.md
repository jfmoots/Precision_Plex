# Precision Plex v2.6.25

Test release adding LP Gas tank level decoding from the confirmed 0x002B / 02AA levels packet.

## Changes

- Keeps confirmed Fresh / Grey / Black tank decoders.
- Adds LP Gas Tank sensor.
- LP Gas is decoded from byte 5 high nibble of handle 0x002B / characteristic 02AA.

## LP Mapping

- 0x0 = 0%
- 0x2 = 25%
- 0x5 = 50%
- 0x7 = 75%
- 0xA = 100%
