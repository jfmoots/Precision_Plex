# Precision Plex v2.6.23

## Changes

- Updates Fresh Water decoding to use the low nibble of byte 2 in the 0x002B / 02AA levels packet.
- Adds Grey Water Tank sensor decoded from the high nibble of byte 3 in the same 0x002B / 02AA levels packet.
- Uses the shared tank nibble mapping: 0x0=0%, 0x3=33%, 0x6=67%, 0xA=100%.

## Test Focus

- Verify Fresh still follows Empty / 1/3 / 2/3 / Full.
- Verify Grey Empty = 0%.
- Verify Grey 1/3 = 33%.
