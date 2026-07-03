# Precision Plex v5.3.10 — BLE Variant Diagnostics

This release expands the bounded BLE packet forensic diagnostics added in v5.3.8/v5.3.9. It does not relax packet validation or publish rejected packets; it only improves the evidence collected while the integration runs normally.

## New Diagnostics

- Adds rejected-packet variant classification.
- Adds variant count summaries for recurring 02AA packet shapes.
- Adds changed-byte value count summaries, such as `4:0x3F->0x03`.
- Fixes `seconds_since_last_good` for 02AA packet rejects by correctly tracking accepted 02AA packet timestamps.
- Keeps the rejected packet forensic buffer capped at 100 entries.
- Keeps diagnostic counters bounded to avoid long-run attribute/log growth.

## Behavior

- No intentionally rejected packet is decoded into Home Assistant state.
- No rejected packets are logged as warnings during normal operation.
- Existing 5.3.8 validation behavior is preserved.

## Purpose

The goal is to determine whether the recurring rejected 02AA samples are malformed BLE data, legitimate 02AA packet variants, or a Wireless TP telemetry artifact. This release provides better pattern grouping while keeping the integration safe for extended field testing.
