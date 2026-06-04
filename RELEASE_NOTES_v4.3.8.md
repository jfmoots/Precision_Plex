# Precision Plex v4.3.8

## Generator Runtime Masked Decode Test

This diagnostic build keeps the v4.3.5 runtime safety guard and adds a conservative masked/stabilized runtime decode path.

### Changes

- Detects runtime frames where the raw bytes 7-8 value is implausible but the current low byte can be safely combined with the previously accepted high byte.
- Uses the stabilized value only when it is monotonic and within the live jump threshold.
- Logs masked decode decisions so the 0x0004 vs 0x0060 runtime-field behavior can be verified from Home Assistant logs.
- Keeps existing HomeKit cleanup and helper sensor behavior from v4.3.x.

### Expected result

Generator runtime should remain at the correct real value even when status/flag bits contaminate the apparent high byte.
