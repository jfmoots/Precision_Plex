# Precision Plex Home Assistant Integration v2.6.33

This is a GitHub-ready cleanup release built from the validated v2.6.31 generator work.

## Release Status

For the tested 2022 Forest River Georgetown GT5 34M5, this release is considered feature complete for the core Precision Plex functions visible in the Precision Plex mobile app.

## Confirmed Working Controls

- Awning Light
- Water Pump
- Water Heater
- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop
- Awning Cover
- Bed Slide Cover
- Wardrobe Slide Cover
- Sofa Slide Cover

## Confirmed Working Telemetry

- Coach Battery Voltage
- Fresh Water Tank Level
- Grey Water Tank Level
- Black Water Tank Level
- LP Gas Tank Level
- Generator Running Status
- Generator Runtime Hours
- Generator Status

## Confirmed Generator Status Values

- `0x0004` = Stopped
- `0x1004` = Running
- `0x00A0` = AutoStart accepted / transition begins
- `0x2004` = Will Not Start
- `0x6004` = Performing Generator AutoStart
- `0x7004` = Performing Generator AutoStop

## Documentation Updated

- README updated for v2.6.33 and app-visible feature-complete status.
- Protocol overview expanded with the final generator state map.
- State mapping expanded with tank, LP, generator runtime, and generator status fields.
- Command mapping updated with Generator AutoStart and AutoStop commands.
- Coach-specific documentation updated for the 2022 Forest River Georgetown GT5 34M5.
- Future work list cleaned up to remove features not exposed in the tested coach's Precision Plex app.

## Features Checked But Not Available in the Tested Coach App

The following are not current targets for this coach because they are not available in the Precision Plex mobile app:

- HVAC / thermostat controls
- Generator fault-code details beyond the decoded generator status field
- Shore power telemetry
- Inverter telemetry
- Tank heater controls
- Water heater telemetry
- Native slide position telemetry
- Native awning position telemetry

## Future Work

- Dashboard examples
- Improved entity naming/icons if desired
- Expanded protocol notes as new captures are discovered
- Additional coach-specific functions if other Precision Plex installations expose different app features
- Optional diagnostics for unknown packets/status codes
