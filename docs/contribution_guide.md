# Contribution Guide

## Goal

Help expand Precision Plex support across additional coaches and functions.

## Useful Contribution Types

- New command packet captures
- New state bit mappings
- Coach-specific function lists
- Travel-time values
- Bug reports
- Dashboard examples
- Documentation improvements

## Suggested Reverse-Engineering Workflow

1. Capture BLE traffic while using the Precision Circuits app.
2. Activate one function at a time.
3. Record the physical action performed.
4. Identify command writes to the control characteristic.
5. Identify matching state changes in `02BB` notifications.
6. Validate from Home Assistant.
7. Document the coach model, year, floorplan, and option package.

## Good Capture Notes

Example:

```text
Coach: 2022 Forest River Georgetown GT5 34M5
Function: Bed Slide
Action: Extend for 5 seconds, wait, retract for 5 seconds
Result:
- Out release: ...
- Out hold: ...
- In release: ...
- In hold: ...
- State word/bit: ...
```

## Future Targets

- Sofa Slide
- Wardrobe Slide
- Generator
- Tank Monitoring
- Additional Lighting Zones
- Additional Georgetown functions
- Other Forest River coaches
