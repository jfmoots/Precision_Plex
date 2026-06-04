# Current Project Status

The Precision Plex Home Assistant Integration has evolved from an initial reverse-engineering effort into a practical Home Assistant replacement for the Precision Circuits Wireless TP mobile application on the tested coach profile.

The integration was developed and validated against a Precision Plex system installed in a 2022 Forest River Georgetown GT5 34M5 Motorhome and currently provides coverage for essentially all major Precision Plex functions exposed by the official mobile application for that coach.

## Current Recommended Release

v4.4.14 is the current GitHub-ready release.

Recent development has focused on:

- Coach profile architecture
- Persistent Bluetooth connectivity
- Automatic Bluetooth discovery
- Home Assistant cover improvements
- Apple Home / HomeKit optimization
- Generator control reliability
- Generator telemetry decoding
- Startup and reconnect performance
- Integration lifecycle cleanup and stability

The integration is now stable for daily operation and is capable of maintaining long-term connectivity to the Precision Plex Wireless TP module without requiring use of the official mobile application.

## Implemented and Validated Features

### Lighting

- Awning Light

### Utilities

- Water Pump
- Water Heater

### Tank and Level Monitoring

- Fresh Water Tank
- Grey Water Tank
- Black Water Tank
- LP Gas Tank
- Coach Battery Voltage

### Slide Controls

- Bed Slide
- Wardrobe Slide
- Sofa Slide

### Awning Controls

- Main Awning

### Generator Controls

- Generator Start
- Generator Stop
- Generator AutoStart
- Generator AutoStop

### Generator Telemetry

- Running Status
- Generator Status
- Runtime Hours
- Failure Detection

Known generator states currently decoded include:

- Stopped
- Running
- Performing Generator AutoStart
- Performing Generator AutoStop
- Will Not Start

### Home Assistant Platform Support

The integration currently exposes native:

- Light entities
- Switch entities
- Cover entities
- Sensor entities
- Binary sensor entities
- Button entities
- Number entities

All entities participate fully in:

- Device Registry
- Entity Registry
- Restore State
- Diagnostics
- HomeKit Export

## Cover System

The cover implementation has matured significantly beyond the original mobile application.

Features include:

- Native Home Assistant Cover entities
- Open / Close controls
- Estimated position tracking
- Position restoration after restart
- Movement state detection
- Configurable travel times
- Manual jog controls
- Position reset buttons
- HomeKit-compatible cover presentation

Supported covers:

- Awning
- Bed Slide
- Wardrobe Slide
- Sofa Slide

Travel times are user-configurable through Home Assistant Number entities and persist across restarts.

## Apple Home / HomeKit Integration

The integration has been optimized for export through the Home Assistant HomeKit Bridge.

Validated HomeKit support exists for:

- Awning Light
- Water Pump
- Water Heater
- Generator Controls
- Generator Status Sensors
- Tank Level Sensors
- Battery Telemetry
- Slide Covers
- Awning Cover

Recent releases improved:

- Entity naming
- HomeKit categorization
- Cover presentation
- Sensor presentation
- Device organization

Some Apple Home naming behavior remains controlled by Home Assistant and Apple Home and cannot be fully overridden by the integration.

## Bluetooth Architecture

The integration maintains a persistent Bluetooth Low Energy connection to the Precision Plex Wireless TP module.

Implemented features include:

- Automatic Bluetooth discovery
- Config Flow device selection
- Persistent BLE coordinator
- Automatic reconnect handling
- Startup recovery
- Connection health monitoring
- Clean unload and reload support
- Graceful shutdown handling

The Wireless TP module appears to support only a single active BLE connection.

When Home Assistant is connected, the official Precision Plex mobile application may be unable to connect simultaneously. This behavior is expected.

## Coach Profile Architecture

The integration now supports coach-specific profile definitions.

Current validated profile:

custom_components/precision_plex/profiles/georgetown_gt5_34m5.py

The profile system separates coach-specific mappings from the core protocol implementation and provides a foundation for supporting additional Precision Plex-equipped coaches in the future.

The Georgetown GT5 34M5 profile remains the reference implementation and is currently the only fully validated profile.

## Generator Runtime Investigation

Generator runtime decoding remains the primary active reverse-engineering effort.

The integration currently decodes runtime as tenths of hours and has identified multiple candidate runtime packet formats.

Observed valid runtime values include:

- 69.4 hours
- 103.5 hours
- 104.6 hours
- 106.9 hours
- 111.5 hours
- 120.6 hours

Additional packet variants have been observed that produce unrealistic values.

Recent releases include protections against these runtime outliers while protocol analysis continues to determine the authoritative runtime source.

Current runtime protection successfully prevents previously observed erroneous values such as:

- 2475.8 hours
- 4933.4 hours

from appearing in Home Assistant.

## Reliability Improvements

Recent releases resolved:

- Startup delays
- BLE reconnect issues
- Duplicate cover entities
- Generator command availability issues
- Integration reload issues
- HomeKit export inconsistencies
- Entity restoration issues

The integration can now be disabled and re-enabled without requiring a Home Assistant restart.

## Project Vision

The original goal of this project was to monitor Precision Plex telemetry from Home Assistant.

The project has since evolved into a complete Home Assistant-native replacement for the Precision Circuits Wireless TP mobile application for the tested coach profile.

Current architecture:

Precision Plex Controller
        ⇅
Wireless TP BLE Module
        ⇅ BLE
Home Assistant
        ⇅
Apple Home / HomeKit

The integration now provides:

- Persistent local Bluetooth connectivity
- Real-time Precision Plex monitoring
- Bidirectional equipment control
- Native Home Assistant entities
- HomeKit integration
- Enhanced cover functionality beyond the official application
- Local operation without cloud dependencies

## Active Development Areas

The major app-visible feature set for the tested coach is now complete and operational.

Current development efforts are focused on:

- Final generator runtime packet identification
- Generator telemetry cleanup
- Additional protocol documentation
- Discovery of undocumented Precision Plex telemetry
- Support for additional coach profiles
- Expanded diagnostics for unknown packet types

## Overall Status

For the tested 2022 Forest River Georgetown GT5 34M5 motorhome, the Precision Plex Home Assistant Integration has reached a mature state and now serves as a practical day-to-day replacement for the official Precision Circuits mobile application.

All major app-visible functions currently available on the tested coach have been implemented, validated, and integrated into Home Assistant and Apple Home.
