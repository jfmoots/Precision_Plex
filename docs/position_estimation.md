# Position Estimation

## Overview

The awning and bed slide do not currently expose absolute position sensors through the decoded Precision Plex state.

Position is estimated using movement time.

## Position Convention

- `0%` = fully retracted / closed
- `100%` = fully extended / open

## Configurable Travel Times

Travel-time settings are exposed as Home Assistant Number entities:

| Entity | Default |
|---|---:|
| `number.awning_open_seconds` | 18 seconds |
| `number.awning_close_seconds` | 25 seconds |
| `number.bed_slide_open_seconds` | 28 seconds |
| `number.bed_slide_close_seconds` | 23 seconds |

These values control:

- Maximum safety runtime
- Position estimation speed
- Slider/set-position timing

## Wall-Panel Tracking

Because the integration keeps a persistent BLE connection, it can observe movement initiated from the RV wall panel.

When a movement bit turns on, position tracking begins. When the bit clears, the estimated position freezes.

## Limitations

Position is estimated, not physically measured.

Accuracy can drift due to:

- Motor wear
- Battery voltage
- Mechanical friction
- Slide or awning loading
- Weather or temperature
- Partial manual movement while Home Assistant is offline

Use the configurable travel-time values to recalibrate.
