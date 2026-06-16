# Precision Plex Home Assistant Integration

A custom Home Assistant integration for Precision Circuits Precision Plex systems.

## Current Recommended Release

**v5.2.1** is the current GitHub-ready release.

This release builds on v5.2.0 by adding quadrature-only slide motion verification and retains real Lippert slide position telemetry for the Bedroom, Sofa, and Wardrobe slides using ESPHome quadrature decoding of the Lippert 697096 motor Hall sensor channels. Timing-based slide position remains in place as the automatic fallback whenever ESPHome telemetry is missing, unavailable, stale, or not installed.

## v5.2.1 Highlights

### Quadrature-based slide position

v5.2.0 replaces the earlier experimental pulse-counter slide model with true quadrature position tracking for the three Lippert/Schwintek slide rooms on the tested coach.

The thin motor harness sensor wires are treated as quadrature channels:

| Wire | Function |
| --- | --- |
| Thin Red | 5V Hall sensor power |
| Thin Black | Hall sensor ground |
| Thin Green | Quadrature Channel A |
| Thin Yellow | Quadrature Channel B |

ESPHome `rotary_encoder` sensors decode the green/yellow channel pair for each motor. Precision Plex then reads the ESPHome quadrature travel and sync-error entities and uses those counts as the primary cover position source.

### Tested full-travel counts

The following full-travel defaults were validated on the tested 2022 Georgetown GT5 34M5:

| Slide | Full Travel Count |
| --- | ---: |
| Bedroom Slide | 21,727 |
| Sofa Slide | 21,503 |
| Wardrobe Slide | 13,873 |

These values are used as defaults for encoder-based position calculation. The existing time-based travel settings remain available and continue to act as a fallback.

### Startup restoration

Quadrature telemetry is used immediately after a Home Assistant restart when valid ESPHome telemetry is available. The integration no longer waits for the first movement after restart before selecting the encoder-based position source.

### Direction-independent position tracking

Quadrature travel counts are treated as absolute travel position. Position updates correctly while extending and while retracting.


### Quadrature motion verification

v5.2.1 adds a protective command-stream abort for quadrature-enabled slides. When a Bedroom, Sofa, or Wardrobe slide is commanded to move and valid quadrature telemetry is available, the integration verifies that encoder travel actually changes shortly after the command begins.

If no quadrature movement is detected after approximately three seconds, the BLE hold stream is stopped and a diagnostic flag is exposed. This helps avoid repeated BLE hold commands when a downstream interlock, such as ignition-on slide lockout, accepts the command path but prevents the slide from moving.

This verification only runs when quadrature telemetry is available. Timing-only installations continue to behave exactly as before.

### Diagnostics

Slide cover attributes now expose quadrature diagnostics, including:

```yaml
position_source: quadrature
quadrature_available: true
quadrature_travel_total: 13875.5
quadrature_full_travel: 13873
quadrature_sync_error: 67
quadrature_last_delta: 0
motion_verification_failed: false
motion_verification_reason: null
```

When telemetry is unavailable, the cover falls back to timing:

```yaml
position_source: time
quadrature_available: false
```

## Optional ESPHome Quadrature Telemetry

The ESPHome telemetry nodes are optional. Without them, the integration behaves like previous releases and uses the configured open/close seconds for slide position estimation.

Normal GPIO mapping used by the tested ESP32 telemetry nodes:

| Signal | ESP32 GPIO |
| --- | ---: |
| Motor 1 Green | GPIO18 |
| Motor 1 Yellow | GPIO19 |
| Motor 2 Green | GPIO21 |
| Motor 2 Yellow | GPIO22 |

The integration auto-discovers expected ESPHome entity names for Bedroom, Sofa, and Wardrobe slide telemetry, including Home Assistant-generated names that include the ESPHome device name.

## Timing Fallback

The original timing model remains available for all native cover entities. If quadrature telemetry is not available, the cover continues to use the configured full-open and full-close seconds.

This preserves compatibility for installations that do not have ESPHome telemetry nodes and provides a safe fallback if an ESPHome device is offline.

## Tested Coach and Scope

This integration was reverse engineered from a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

The current implementation should be considered feature complete for the app-visible Precision Plex functions available on this tested coach. Other Precision Plex-equipped coaches may expose different circuits, slides, tanks, generator options, or app configuration profiles.

Observed application profile:

```text
Model_Georgetown_GT_34M5_w_2AC
```

## Features

- Local BLE communication with the Precision Plex Wireless TP module
- Notification-first BLE startup handling
- Guided pairing and re-pair support
- Native Home Assistant cover entities for the patio awning and slide rooms
- Encoder-aware Bedroom, Sofa, and Wardrobe slide position telemetry when ESPHome quadrature nodes are available
- Quadrature-only motion verification that aborts slide hold streams when no encoder movement is detected
- Time-based slide and awning position fallback
- Jog controls and endpoint reset/calibration buttons
- Generator status, runtime, start/stop, AutoStart, and AutoStop support
- Coach battery telemetry
- Fresh, grey, and black tank telemetry
- LP/propane telemetry validation
- Water pump and water heater controls
- Light controls for app-visible Precision Plex lighting circuits
- HomeKit-friendly sensor exposure cleanup
- Diagnostic attributes for raw state words, BLE frames, and slide telemetry source

## Installation

Copy the `custom_components/precision_plex` folder into your Home Assistant `custom_components` directory, restart Home Assistant, then add the Precision Plex integration from Settings → Devices & services.

For HACS custom repository use, upload the repository contents to GitHub and add it as a custom integration repository.

## Package Contents

- `custom_components/precision_plex/` - Home Assistant integration
- `docs/` - protocol notes, reference calibrations, slide telemetry documentation, and release history
- `dashboard/` - example Mooterhome mobile dashboard YAML
- `RELEASE_NOTES_v5.2.1.md` - release notes for this version

## Safety Notes

Slide and awning controls move large mechanical equipment. Keep the physical wall controls available and maintain line-of-sight when testing. Quadrature telemetry improves position feedback but does not replace the Lippert controller's built-in safety and synchronization logic.
