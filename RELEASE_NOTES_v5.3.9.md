# Precision Plex v5.3.9 — BLE Packet Comparison Diagnostics

This release expands the BLE packet forensics introduced in v5.3.8 while keeping the diagnostic footprint bounded for long field runs.

## Added

- Changed-byte comparison for rejected packets against the last accepted packet of the same type.
- Per-packet changed byte indexes.
- Expected and actual byte values for changed bytes.
- Seconds since the last accepted packet of the same type.
- Seconds since BLE connect.
- Changed-byte pattern counts to identify recurring packet variants.

## Preserved

- Rejected packet buffer remains capped at 100 entries.
- Rejected packet details are kept in diagnostics/entity attributes, not spammed into the Home Assistant log.
- v5.3.7/v5.3.8 packet validation remains in place to prevent malformed 02AA telemetry from causing false battery or switch-state history.

## Purpose

The goal is to distinguish random BLE corruption from repeatable Precision Plex 02AA packet variants by showing exactly which bytes differ and when those packets occur.
