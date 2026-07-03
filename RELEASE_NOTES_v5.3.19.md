# Precision Plex v5.3.19 — Config Flow Discovery Fix

This release fixes a setup bug in the Precision Plex config flow.

## Fixes

- Removed the development fallback that inserted the original test coach Bluetooth address when no Precision Plex devices were discovered.
- Setup now correctly reports that no Precision Plex Wireless TP devices were found instead of offering a stale/hard-coded address.
- Added a clearer setup error message with basic discovery troubleshooting guidance.

## Notes

If setup reports no devices found, Home Assistant is not currently seeing a Precision Plex Wireless TP advertisement. Verify coach power, Bluetooth range, phone app connection state, and Pair with Mobile mode on the wall panel.
