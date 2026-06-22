Precision Plex Home Assistant Integration

Bring Precision Circuits Precision Plex controls and telemetry into Home Assistant.

This integration provides local control and monitoring of supported Precision Plex-equipped motorhomes using the Precision Plex Wireless TP module. It exposes coach systems as native Home Assistant entities and enables automation, dashboarding, HomeKit integration, and remote monitoring.

⸻

Current Stable Release

v5.3.6

The current stable release includes:

* Native Home Assistant cover entities
* Generator telemetry and control
* Tank telemetry
* Propane telemetry
* Coach battery telemetry
* Water pump and water heater controls
* Lighting controls
* BLE bonding and recovery improvements
* Optional slide encoder telemetry
* Optional awning current-sensing enhancements
* HomeKit-friendly entity exposure
* Custom integration branding and icons

⸻

Supported Features

Lighting

Control Precision Plex lighting circuits from Home Assistant.

Features:

* Native light entities
* HomeKit compatible
* Dashboard friendly
* Automation support

Slides

Native cover entities are provided for supported slide rooms.

Features:

* Open
* Close
* Stop
* Position tracking
* Calibration controls
* Jog controls

Optional Encoder Telemetry

Supported Lippert slide systems can be upgraded with ESPHome-based encoder telemetry.

Benefits:

* Real slide position feedback
* Improved accuracy
* Position persistence across restarts
* Motion verification
* Automatic fallback to timing when telemetry is unavailable

Patio Awning

Native awning cover entity.

Features:

* Open
* Close
* Stop
* Position tracking
* Jog controls

Optional Current-Sensing Upgrade

The tested coach includes an ESP32-based awning monitoring system using Hall-effect current sensing.

Benefits:

* Improved end-of-travel detection
* Awning tightening behavior after retract
* Enhanced position confidence

Generator

Monitor and control the onboard generator.

Features:

* Start
* Stop
* Runtime telemetry
* Running status
* AutoStart support
* AutoStop support

Tank Monitoring

Monitor:

* Fresh Water
* Grey Tank
* Black Tank

Values are exposed as native Home Assistant sensors.

Propane Monitoring

LP tank level telemetry is exposed as a native sensor.

Additional validation logic filters known invalid values observed on the tested coach.

Battery Monitoring

Monitor coach battery voltage directly from Precision Plex telemetry.

Water Systems

Control:

* Water Pump
* Water Heater

using native Home Assistant switch entities.

⸻

Home Assistant Integration

The integration creates native Home Assistant entities including:

* Lights
* Covers
* Switches
* Sensors
* Buttons
* Diagnostic entities

All entities support:

* Dashboards
* Automations
* Scripts
* Scenes
* HomeKit

⸻

Optional Hardware Enhancements

The integration functions without any additional hardware.

Optional upgrades developed during this project include:

Slide Encoder Telemetry

ESP32 + ESPHome telemetry using Lippert motor Hall sensors.

Provides:

* Real position feedback
* Motion verification
* Improved reliability

Awning Current Monitoring

ESP32 + Hall-effect current sensor.

Provides:

* End-of-travel detection
* Improved retract behavior
* Additional diagnostics

⸻

Installation

Manual Installation

Copy:

custom_components/precision_plex

into your Home Assistant custom_components directory.

Restart Home Assistant.

Add the integration from:

Settings → Devices & Services

HACS Installation

Add the GitHub repository as a custom HACS integration repository.

Install through HACS and restart Home Assistant.

⸻

Tested Coach

This integration was developed and tested on:

2022 Forest River Georgetown GT5 34M5

Observed Precision Plex profile:

Model_Georgetown_GT_34M5_w_2AC

Other Precision Plex-equipped coaches may expose different circuits, slides, tanks, generators, or configuration profiles.

⸻

Architecture

Current transport:

* Precision Plex Wireless TP BLE

Future development is focused on expanding the integration to support additional Precision Plex transport methods while preserving the same entities and telemetry model.

The long-term goal is a single Precision Plex integration capable of using the best available transport while maintaining a consistent Home Assistant experience.

⸻

Safety Notice

Slides, awnings, generators, and water systems control physical equipment.

Always maintain line-of-sight when testing automated controls and retain access to factory controls.

This integration supplements the factory control system and does not replace manufacturer safety systems.

⸻

Acknowledgements

This project was reverse engineered through extensive analysis of Precision Plex BLE communications and real-world testing on a Georgetown GT5 motorhome.

Special thanks to the Home Assistant, ESPHome, and RV automation communities whose tools made this project possible.
