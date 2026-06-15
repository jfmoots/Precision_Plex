# Precision Plex v5.2.0 - Quadrature Slide Telemetry

v5.2.0 promotes Lippert slide telemetry from experimental pulse counting to true quadrature encoder-based position tracking.

## Highlights

- Added Bedroom Slide ESPHome quadrature telemetry support.
- Converted Sofa Slide telemetry from pulse-counter estimates to quadrature travel counts.
- Converted Wardrobe Slide telemetry from pulse-counter estimates to quadrature travel counts.
- Uses `Quadrature Travel` and `Quadrature Sync Error` ESPHome entities for slide position and diagnostics.
- Preserves automatic ESPHome entity discovery for differing Home Assistant entity names.
- Uses quadrature position immediately after Home Assistant restart when telemetry is valid.
- Fixes retract-direction position updates by treating quadrature travel as absolute travel, not as a cumulative pulse counter.
- Keeps timing-based slide position as the automatic fallback when telemetry is unavailable.
- Renames user-facing diagnostics from `pulse_*` to `quadrature_*`.

## Tested Full-Travel Counts

| Slide | Full Travel Count |
| --- | ---: |
| Bedroom Slide | 21,727 |
| Sofa Slide | 21,503 |
| Wardrobe Slide | 13,873 |

## Diagnostic Attributes

When telemetry is active, slide covers expose attributes such as:

```yaml
position_source: quadrature
quadrature_available: true
quadrature_travel_total: 21726
quadrature_full_travel: 21727
quadrature_sync_error: 36
```

When telemetry is unavailable, the integration falls back to the existing timing model:

```yaml
position_source: time
quadrature_available: false
```

## Validation Summary

Field testing confirmed:

- Bedroom full extension returns near 21,727 counts and returns near zero when retracted.
- Sofa full extension returns near 21,503 counts and returns near zero when retracted.
- Wardrobe full extension returns near 13,873 counts and returns near zero when retracted.
- Position updates correctly while extending and retracting.
- Position source restores to `quadrature` immediately after Home Assistant restart when valid telemetry is available.

## Notes

This release does not require ESPHome telemetry. Installations without telemetry nodes continue to use the existing time-based cover position model.
