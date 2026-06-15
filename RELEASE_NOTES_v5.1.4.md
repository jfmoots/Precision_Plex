# Precision Plex v5.1.4 — Guided Pairing and Re-pair Maintenance

This release improves the Bluetooth pairing and recovery experience for Precision Plex controllers in Home Assistant.

## What's New

### Improved Pairing Instructions

The pairing confirmation step now includes clearer wall-panel instructions:

- Open the Precision Plex wall panel.
- Navigate to **Setup → Wireless → Pair with Mobile**.
- Press **Pair with Mobile**.
- The button turns green briefly while pairing mode is active.
- The pairing window only stays active for a few seconds.
- While Home Assistant is trying to pair, keep pressing **Pair with Mobile** whenever the button returns to its normal color.
- Pairing may take several attempts.

This better matches the real-world behavior observed on the tested coach.

### New Re-pair Maintenance Flow

Existing Precision Plex installations now have an options flow that can re-pair the controller without deleting and recreating the integration.

Use **Re-pair Precision Plex** if you:

- Restored Home Assistant from backup.
- Changed SD cards.
- Moved to new hardware.
- Cleared Bluetooth data.
- Reinstalled Home Assistant OS.
- See Precision Plex entities unavailable after a Bluetooth change.

The re-pair flow will:

- Stop the current Precision Plex config entry.
- Clear the existing BlueZ Bluetooth device record for the controller.
- Prompt for Pair with Mobile mode.
- Pair/bond with the controller again.
- Mark the controller trusted in BlueZ when possible.
- Reload the Precision Plex integration.

### Pairing Flow Safety Improvement

Pairing now focuses on creating the BlueZ bond/trust relationship. It no longer depends on an immediate app-init GATT write during pairing. Runtime telemetry is populated by the notification-first startup path introduced in v5.1.3.

## Included From v5.1.3

This release includes the v5.1.3 notification-first BLE startup fix:

- Startup no longer performs initial 02AA/02BB reads.
- The integration subscribes to Precision Plex notifications first.
- Live notification streams populate tank, battery, generator, slide, and awning state.
- This avoids GATT "Unlikely Error" and timeout failures seen on fresh HAOS/BlueZ installs.

## Upgrade Notes

Existing installations can upgrade directly to v5.1.4 with no dashboard or entity changes required.

If your system is already working, no re-pair is required. The new Re-pair option is intended as a maintenance/recovery tool.
