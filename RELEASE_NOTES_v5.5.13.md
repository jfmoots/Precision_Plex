# Precision Plex v5.5.13 — Persistent Slide Quadrature Calibration

This release fixes quadrature endpoint calibration for the Bedroom, Wardrobe,
and Sofa slides. Patio Awning behavior is unchanged.

## Root cause

The Reset Fully Extended/Retracted buttons changed only the cover's estimated
percentage. The next ESPHome quadrature update immediately recalculated that
percentage using a fixed default full-travel count, erasing the reset. On the
Sofa Slide, a live fully extended count of 13,413.5 was being divided by the
old 21,503 default and reported as 62.4%.

A complete coach power cycle made the mismatch visible because Home Assistant
rebuilt the cover position from the restored raw count and fixed default.

## Fix

- Reset Fully Retracted records the current quadrature count as the slide's
  learned zero endpoint.
- Reset Fully Extended records the current quadrature count as the learned
  extended endpoint.
- Position is calculated between those two learned endpoints.
- Both endpoint counts are persisted in the cover state and restored after a
  Home Assistant restart.
- New diagnostic attributes show calibration status and both learned counts.

The same implementation applies to Bedroom, Wardrobe, and Sofa slides. If a
slide's ESPHome quadrature telemetry is unavailable, its endpoint cannot be
learned until that telemetry returns.
