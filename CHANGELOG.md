# Changelog

This file consolidates the former collection of individual release-note files.
Detailed historical descriptions remain attached to their GitHub releases.

## v5.5.11 - Authoritative Carefree Flip Completion

- Keeps the synthetic 100% awning endpoint after the configured Fabric Tighten
  duration completes.
- Ignores provisional idle state while delayed PID32/02BB telemetry still
  reports retract motion.
- Releases endpoint protection only after authoritative controller telemetry
  confirms both awning directions idle.

## v5.5.10 - Stable Carefree Flip Endpoint

- Holds the smart awning's synthetic 100% endpoint through trailing Carefree
  Flip retract telemetry.
- Releases the endpoint hold only after authoritative controller-idle telemetry.
- Clears the hold normally when a genuine open, close, or jog begins.

## v5.5.9 - Stable Awning Position After Restart

- Prevents stale startup motion bits from advancing the patio awning's
  time-based position estimate after a Home Assistant restart.
- Waits for authoritative idle telemetry before accepting unsolicited awning
  motion, while keeping Home Assistant commands immediately responsive.
- Preserves the smart current-sense Carefree Flip sequence and its synthetic
  100% open endpoint.

## v5.5.8 - Recorder-Friendly Telemetry

- Accepts compact v0.6.4 firmware heartbeats while preserving the last full
  telemetry snapshot and the existing four-second bridge timeout.
- Removes raw BLE packets, decoder mappings, high-frequency awning current,
  packet counters, and snapshot counters from ordinary entity attributes.
- Retains raw forensic data and the last complete LIN snapshot in Download
  diagnostics; awning current remains available as its dedicated ESPHome
  sensor.
- Documents excluding the internal LIN snapshot event from Recorder history.
- Pairs with ESPHome Precision Plex LIN v0.6.4.

## v5.5.7 - Thread-Safe LIN Updates

- Marshaled the complete LIN coordinator update path onto Home Assistant's
  event loop when a transport listener fires from another thread.
- Kept same-loop LIN updates immediate while protecting snapshot expiry,
  per-source expiry, discovery, state-change, and snapshot listener paths.
- Captured each snapshot, command intent, and bridge identity at the listener
  boundary so queued cross-thread updates retain the event that triggered them.

## v5.5.6 - Fast PID1F/PID5E Command Intent

- Added one normalized command-intent consumer for PID1F and PID5E events.
- Made wall-panel, Wireless TP, and Home Assistant toggle/motion requests appear
  immediately while PID32 remains authoritative confirmation.
- Deduplicated request/active motion phases, repeated holds, idle frames, and
  injected PID5E echoes in the firmware/integration event contract.
- Retained local optimistic feedback only as a compatibility fallback for
  bridges older than v0.6.3.
- Paired with ESPHome Precision Plex LIN v0.6.3.

## v5.5.5 - LIN Generator Runtime and Responsive Generator Commands

- Prefers the complete validated PIDBA LIN generator runtime and retains BLE
  as a field-level fallback.
- Adds immediate Start Requested, Stop Requested, AutoStart Requested, and
  AutoStop Requested generator-status feedback while waiting for telemetry.
- Keeps Generator Running authoritative rather than optimistically changing it.
- Keeps generator command buttons available with the BLE command path instead
  of cycling availability with each status, preventing false button activity.
- Removes the unsupported fixed five-second PID32 schedule claim.
- Pairs with firmware v0.6.2 and its corrected PID32 generator-running bit.

## v5.5.4 - Command-Responsive PID32 Controls

- Added one shared provisional-state layer for every stateful Home Assistant
  control backed by the slower PID32 output bitmap.
- Made awning-light, water-pump, and water-heater controls update their control
  entities and matching binary sensors immediately.
- Made Bedroom, Wardrobe, and Sofa slide plus Patio Awning movement state react
  immediately to Home Assistant open, close, jog, and stop commands.
- Prevented stale PID32 frames from bouncing controls back to their previous
  state while the next scheduled PID32 broadcast is pending.
- Reconciled provisional values automatically when PID32 or BLE 02BB confirms
  the command, with a safe 12-second fallback when confirmation never arrives.
- Retained the independent 30-second LIN source freshness grace periods; those
  prevent unavailable flicker and are separate from command responsiveness.

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
