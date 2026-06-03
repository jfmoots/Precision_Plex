# Precision Plex v4.0.0 Release Notes

## Highlights

Precision Plex v4.0.0 adds manual jog and position reset controls for the awning and all slide covers while preserving the proven press-and-hold cover movement engine from v3.0.0.

## Added

- Cover jog buttons for every slide and awning direction:
  - Awning Jog Extend / Jog Retract
  - Bed Slide Jog Extend / Jog Retract
  - Wardrobe Slide Jog Extend / Jog Retract
  - Sofa Slide Jog Extend / Jog Retract
- Position reset buttons for every cover:
  - Reset Fully Extended
  - Reset Fully Retracted
- Configurable jog duration number entities:
  - Awning Jog Seconds defaults to 2 seconds
  - Bed Slide Jog Seconds defaults to 5 seconds
  - Wardrobe Slide Jog Seconds defaults to 5 seconds
  - Sofa Slide Jog Seconds defaults to 5 seconds

## Behavior

- Jog buttons are manual overrides and intentionally run even when the estimated position already says the cover is fully extended or fully retracted.
- Estimated position is still updated from elapsed jog time and clamped between 0% and 100%.
- Reset buttons do not move hardware. They only correct Home Assistant's estimated position.
- Normal cover open, close, stop, and set-position behavior remains unchanged.

## Notes

The jog buttons reuse the same app-like hold stream and release/stop packets as the cover entity, so they should behave like short timed button holds while keeping the cover position model synchronized.
