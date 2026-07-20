# Precision Plex v5.4.1 — LIN Output Entity Registration Fix

- Fixes unavailable LIN-backed awning, slide, water-system, and generator-running entities caused by an invalid `telemetry_source` field in Home Assistant device registry data.
- Moves `telemetry_source` to normal entity state attributes where it belongs.
- Adds regression coverage for every literal `device_info` key returned by the integration.
- Confirms a LIN binary state of `off` remains a valid, available value.
- Leaves BLE packet validation and command behavior unchanged from v5.4.0.
- Continues to use LIN Analyzer Build 013.0 without firmware changes.
