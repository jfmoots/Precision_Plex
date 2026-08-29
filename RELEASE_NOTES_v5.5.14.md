# Precision Plex v5.5.14 — Automatic Slide Endpoint Learning

This release fixes a second slide-position persistence path exposed by a full
power-cycle test.

After a normal full Bedroom, Wardrobe, or Sofa extend/retract command, the
integration previously snapped the displayed position to 100%/0% only in
memory. The next quadrature update recalculated from the earlier calibration
and could immediately show an intermediate value. The Sofa Slide reproduced
this as 61% while physically fully retracted.

## Changes

- Successful full extend commands automatically learn and persist the current
  quadrature count as the extended endpoint.
- Successful full retract commands automatically learn and persist the current
  quadrature count as the retracted endpoint.
- Jog commands, intermediate-position moves, and manually stopped commands do
  not alter endpoint calibration.
- Manual Reset Fully Retracted and Reset Fully Extended controls remain
  available for initial calibration and recovery.
- Patio Awning behavior is unchanged.

## Immediate recovery for an already retracted slide

While the slide is physically fully retracted, press Reset Fully Retracted
once. After v5.5.14 is installed, subsequent successful full endpoint commands
will refresh the appropriate calibration automatically.
