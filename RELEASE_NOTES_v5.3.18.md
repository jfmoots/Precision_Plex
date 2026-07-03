# Precision Plex v5.3.18 — Recorder-Safe BLE Packet Diagnostics

This maintenance release keeps the BLE packet forensic tools from v5.3.x while preventing Home Assistant Recorder attribute bloat.

## Fixed

- Reduced the `BLE Rejected Packet Log` sensor attributes so Home Assistant Recorder no longer attempts to store the full rolling forensic packet buffer.
- Replaced the full packet-log attribute with compact summaries of the newest entries.
- Kept the full internal 100-entry forensic buffer available through Home Assistant diagnostics/config-entry dumps.
- Trimmed large diagnostic count dictionaries exposed on entities to recorder-safe top-N summaries.

## Unchanged

- Packet validation behavior is unchanged.
- 02AA/02BB reject counters are unchanged.
- Last rejected packet details remain available.
- Command stream ownership guard behavior from v5.3.17 is retained.
