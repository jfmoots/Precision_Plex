# Precision Plex v4.0.3 — Cleanup & Diagnostics

This release cleans up the GitHub-ready package and adds Home Assistant diagnostics support for easier troubleshooting and future development.

## Added

- Home Assistant diagnostics download support.
- Diagnostics include redacted config-entry data, BLE availability, expected GATT UUIDs, discovered characteristics when connected, raw 02BB state, decoded 02BB state bits, raw 02AA telemetry, decoded tank/LP levels, coach voltage, and generator status/runtime fields.

## Changed

- Updated manifest version to `4.0.3`.
- Updated README version references to `v4.0.3`.

## Cleanup

- Removed generated `__pycache__` and `.pyc` files from the release ZIP.

## Notes

Diagnostics redact the Bluetooth address and config-entry unique identifiers before export.
