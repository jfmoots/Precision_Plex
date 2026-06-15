# Slide Position and Quadrature Telemetry

## Overview

v5.2.0 uses two position models for Precision Plex slide covers:

1. **Quadrature telemetry** when ESPHome Lippert slide telemetry nodes are available.
2. **Timing estimation** as the fallback when telemetry is unavailable.

The patio awning continues to use the timing model.

## Position Convention

- `0%` = fully retracted / closed
- `100%` = fully extended / open

## Quadrature Telemetry

Lippert 697096 slide controllers use Hall-effect motor feedback. The thin sensor wires in each 6-pin motor harness are separate from the heavy motor power wires.

| Wire | Function |
| --- | --- |
| Thin Red | 5V Hall sensor power |
| Thin Black | Hall sensor ground |
| Thin Green | Quadrature Channel A |
| Thin Yellow | Quadrature Channel B |

ESPHome `rotary_encoder` sensors decode each motor's Green/Yellow pair. The integration reads:

- Quadrature Travel
- Quadrature Sync Error

The cover position is calculated from:

```text
position = quadrature_travel_total / quadrature_full_travel * 100
```

The value is clamped to the Home Assistant cover range of 0-100%.

## Tested Full-Travel Counts

| Slide | Full Travel Count |
| --- | ---: |
| Bedroom Slide | 21,727 |
| Sofa Slide | 21,503 |
| Wardrobe Slide | 13,873 |

## Startup Behavior

When valid quadrature telemetry is present after a Home Assistant restart, the cover immediately uses `position_source: quadrature` and restores position from the ESPHome travel count. It does not wait for the first movement after restart.

## Timing Fallback

If quadrature telemetry is missing, unavailable, stale, or not installed, the cover uses the original timing model.

Travel-time settings are exposed as Home Assistant Number entities:

| Entity Purpose | Default |
| --- | ---: |
| Awning Open Seconds | 18 |
| Awning Close Seconds | 25 |
| Bed Slide Open Seconds | 28 |
| Bed Slide Close Seconds | 24 |
| Wardrobe Slide Open Seconds | 18 |
| Wardrobe Slide Close Seconds | 17 |
| Sofa Slide Open Seconds | 32 |
| Sofa Slide Close Seconds | 28 |

## Diagnostics

Active quadrature telemetry appears in cover attributes:

```yaml
position_source: quadrature
quadrature_available: true
quadrature_travel_total: 13875.5
quadrature_full_travel: 13873
quadrature_sync_error: 67
quadrature_last_delta: 0
```

Timing fallback appears as:

```yaml
position_source: time
quadrature_available: false
```
