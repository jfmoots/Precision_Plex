# Precision Plex v4.1.1 — Coach Profile Import Hotfix

This hotfix resolves a startup failure introduced in v4.1.0 during the coach profile refactor.

## Fixed

- Restored the `CONTROL_CHARACTERISTIC_UUID` compatibility export in `const.py`.
- Fixes Home Assistant setup failure: `cannot import name CONTROL_CHARACTERISTIC_UUID`.

## Notes

No entity behavior, BLE commands, telemetry decoding, or coach profile behavior changed from v4.1.0. This is a startup/import compatibility fix only.
