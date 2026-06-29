# Precision Plex v5.3.7 — BLE Hardening and Packet Validation

## Summary

v5.3.7 hardens the Precision Plex BLE integration against rare malformed, stale, shifted, or one-sample telemetry glitches. It also improves cover hold-stream reliability by retrying after transient BLE write failures.

## Changes

- Added packet health diagnostics for rejected 02AA and 02BB frames.
- Added conservative 02BB state-change confirmation to suppress one-frame switch/status ghosts.
- Added coach battery voltage range checking and jump confirmation for 02AA telemetry.
- Added diagnostics for pending/rejected voltage samples.
- Added BLE hold-stream reconnect/retry behavior for long-running slide and awning commands.
- Added hold-stream recovery diagnostics.
- Preserved existing v5.3.6 features and branding/icons.

## Why

Field history showed brief false samples in Precision Plex BLE telemetry, such as implausible battery voltage spikes and one-frame water heater state changes. Separate slide and awning hiccups also suggested occasional BLE command-stream interruptions. This release addresses those symptoms at the transport/packet layer rather than patching each entity independently.

## Diagnostic visibility

This build also exposes BLE health diagnostics on the Precision Plex device page:

- BLE Connected
- BLE Last Valid Packet
- BLE Last Packet Age
- BLE Reconnect Count
- BLE Disconnect Count
- BLE Packets Accepted
- BLE Packets Rejected
- BLE 02AA Rejected
- BLE 02BB Rejected
- BLE Last Reject Reason
- BLE Command Stream Recoveries
- BLE Command Stream Interruptions
- BLE Command Stream Last Error

The package keeps branding assets only under `custom_components/precision_plex/brand/` and removes the duplicate top-level `brand/` folder.
