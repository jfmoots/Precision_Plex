# Changelog

This file consolidates the former collection of individual release-note files.
Detailed historical descriptions remain attached to their GitHub releases.

## v5.5.3 - Stable LIN Telemetry and Quieter Diagnostics

- Added independent 30-second freshness grace periods for core telemetry,
  PID32 outputs, PIDEC power flags, and both PID37 HVAC zones.
- Kept the four-second whole-bridge timeout for genuine event transport loss.
- Prevented ignition, AC/converter, tank heater, HVAC, and other rotating LIN
  fields from cycling through unavailable between broadcasts.
- Disabled high-churn BLE forensic entities by default.
- Added a one-time config-entry migration that applies the quieter diagnostic
  defaults to existing installations.

## v5.5.2 - Two-Zone HVAC Freshness

- Added independent last-seen handling for alternating PID37 HVAC zones.
- Added regression coverage for zone availability and bridge-heartbeat loss.

## v5.5.1 - Change-Driven LIN Updates

- Made decoded LIN changes update Home Assistant immediately.
- Treated unchanged snapshots as freshness heartbeats without rewriting every
  Precision Plex entity.
- Added confirmation-aware feedback for awning-light, water-pump, and
  water-heater commands.

## v5.5.0 - Integration-Owned LIN Telemetry

- Added the versioned ESPHome LIN snapshot event transport.
- Moved decoded LIN entities, availability, and source selection into the Home
  Assistant integration.
- Added tank-heater, AC/converter, ignition, and two-zone HVAC telemetry.
- Retained field-level Bluetooth fallback and Bluetooth commands.

## v5.4.x - LIN-Preferred Telemetry and Motion Decodes

- Added LIN-preferred telemetry selection with Bluetooth fallback.
- Corrected Bedroom, Sofa, and Wardrobe slide movement direction decoding.
- Published LIN movement state for slides and the patio awning.
- Hardened BLE telemetry parsing while bringing the LIN transport online.

## v5.3.x - BLE Validation and Forensics

- Added conservative 02AA and 02BB packet validation.
- Added state-word and coach-voltage confirmation filters.
- Added bounded packet rejection diagnostics and comparison metadata.
- Improved reconnect behavior during long-running slide and awning commands.
- Fixed configuration-flow discovery and pairing behavior.

## v5.2.x - Quadrature Slide Telemetry

- Added optional quadrature position telemetry for Bedroom, Sofa, and Wardrobe
  slides.
- Preserved timing-based fallback when hardware telemetry is unavailable.

## v5.1.x - BLE Reliability and Optional Motion Telemetry

- Improved notification-first BLE startup and reconnect behavior.
- Added optional ESPHome motion telemetry and position-source diagnostics.

## v5.0.0 - Production Integration Baseline

- Consolidated native Home Assistant lights, switches, covers, buttons,
  numbers, binary sensors, and telemetry sensors.
- Preserved the tested Georgetown GT5 34M5 coach profile.

## Earlier milestones

- Introduced coach profiles and native cover entities.
- Added built-in BLE pairing and bonding.
- Added generator telemetry and guarded generator commands.
- Completed coach battery, tank, and propane telemetry decoding.
- Established persistent BLE communication and factory-control coexistence.
