# Precision Plex v2.6.28 - Generator Control Test

Adds guarded generator control buttons using the command packets captured from the Precision Plex iOS app.

## Added

- Generator Start button
- Generator Stop button
- State-aware safety interlocks based on live Generator Running telemetry

## Generator Commands

- Start press: `55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33`
- Stop press: `55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32`
- Release: `55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34`

## Safety Behavior

- Generator Start is available only when Generator Running is false.
- Generator Stop is available only when Generator Running is true.
- Both buttons are unavailable when generator telemetry is unknown or unavailable.
- The command handler also re-checks generator state immediately before writing.

## Unchanged

- Fresh, Grey, Black, LP, Coach Battery, and Generator Runtime telemetry remain unchanged from v2.6.27.
