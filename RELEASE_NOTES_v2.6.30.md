# Precision Plex v2.6.30 - Generator AutoStart / AutoStop Test

This test release adds managed generator AutoStart and AutoStop support based on Precision Plex app PacketLogger captures.

## Added

- Generator AutoStart button
- Generator AutoStop button
- Generator Status sensor

## Generator Managed Commands

- AutoStart: `55 1D 10 0B 00 3E 0A 00 00 00 00 00 00 00 00 2B`
- AutoStop: `55 1D 10 0B 00 3E 0B 00 00 00 00 00 00 00 00 2A`
- Release: `55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34`

## Generator Status Decode

Observed status/transition values in the 0x002B / 02AA status packet:

- `0004` = Stopped
- `1004` = Running
- `00A0` = AutoStart Accepted / transition begins
- `6004` = Performing Generator AutoStart
- `7004` = Performing Generator AutoStop

## Safety Interlocks

- Start and AutoStart are only available when Generator Status is Stopped.
- Stop and AutoStop are only available when Generator Status is Running.
- All generator command buttons are blocked when generator status is unknown or transitional.

Existing Fresh, Grey, Black, LP, Coach Battery, slide, awning, pump, water heater, and generator runtime telemetry remain unchanged.
