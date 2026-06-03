# Precision Plex Home Assistant Integration v2.6.31

This test release adds decoding for the failed generator AutoStart condition captured during controlled testing.

## New

- Generator Status now reports `Will Not Start`.
- Decoded status: `0x2004` / status byte `0x20`.
- Unknown generator status codes are logged with the raw 0x002B payload for future decoding.

## Retained from v2.6.30

- Generator Start button
- Generator Stop button
- Generator AutoStart button
- Generator AutoStop button
- Generator Running binary sensor
- Generator Runtime sensor
- Generator Status sensor
- Start/Stop and AutoStart/AutoStop safety interlocks

## Confirmed Generator Status Mapping

- `0x0004` = Stopped
- `0x1004` = Running
- `0x00A0` = AutoStart Accepted
- `0x2004` = Will Not Start
- `0x6004` = Performing Generator AutoStart
- `0x7004` = Performing Generator AutoStop

## Notes

A matching `Will Not Stop` state likely exists, but it has not been safely captured yet. This build does not guess that value. Any unknown future status code will be shown and logged for later analysis.
