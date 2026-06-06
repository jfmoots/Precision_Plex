# Precision Plex v5.0.0 – Full RV Integration & Mobile Dashboard Release

This release marks the first complete Precision Plex Home Assistant ecosystem release.

What began as a reverse-engineering effort focused on controlling a single awning light has evolved into a comprehensive Home Assistant integration for Precision Plex-equipped coaches, complete with mobile dashboard examples, documentation, HomeKit support, generator controls, tank monitoring, slide controls, and more.

## Highlights

### Precision Plex Integration

- Fresh Water Tank monitoring
- Grey Tank monitoring
- Black Tank monitoring
- Propane monitoring
- Water Pump control
- Water Heater control
- Generator monitoring
- Generator Start control
- Generator Stop control
- Generator AutoStart control
- Generator AutoStop control
- Patio Awning control
- Bedroom Slide control
- Wardrobe Slide control
- Sofa Slide control

### Enhanced Cover Controls

- Position-aware slide entities
- Position-aware awning entity
- Manual jog controls
- Configurable jog durations
- Fully Extended reset controls
- Fully Retracted reset controls
- Configurable travel timing

### Home Assistant Improvements

- Bluetooth discovery support
- Improved startup behavior
- Entity cleanup and organization
- Improved HomeKit compatibility
- Mobile-friendly entity naming
- Enhanced diagnostics

### Mobile Dashboard Package

This release includes a complete mobile dashboard example optimized for iPhone and Android devices.

Dashboard sections include:

- Home
- Lights
- Slides
- Generator
- Resources
- Environment
- Service

The dashboard demonstrates a practical real-world RV Home Assistant deployment and provides a foundation that users can customize for their own coaches.

### Documentation Improvements

- Dashboard example YAML included
- Mobile dashboard screenshots included
- Dashboard data-source notes included
- Consolidated historical documentation retained
- README cleanup and expansion
- Project history preserved in docs/historical_readmes_and_release_notes.md

## Dashboard Data Sources

The included dashboard demonstrates how Precision Plex can be integrated into a broader Home Assistant ecosystem.

### Precision Plex

- Water Pump
- Water Heater
- Fresh Water Tank
- Grey Tank
- Black Tank
- Propane Tank
- Generator Status
- Generator Runtime
- Generator Controls
- Patio Awning
- Slide Controls
- House Battery Voltage
- Precision Plex Awning Light

### Shelly Integration Examples

The example dashboard also contains entities provided by separate Home Assistant integrations:

- Interior lighting circuits controlled through Shelly relays
- Coach/chassis battery monitoring through Shelly UNI
- Environmental monitoring through Shelly temperature and humidity sensors

These entities are included as examples and are not required for Precision Plex operation.

## Tested Coach

This integration was developed and validated using a:

**2022 Forest River Georgetown GT5 34M5**

Precision Plex profile observed in the official application:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Other Precision Plex-equipped coaches may expose different circuits, tanks, slides, awnings, generators, and control options.

## Looking Ahead

This release establishes a stable foundation for future development.

Planned future exploration includes:

- Direct Precision Plex bus communications
- Additional subsystem integration
- Enhanced telemetry
- ESP32 encoder-based slide and awning position tracking
- Advanced diagnostics and maintenance features

## Thank You

Thank you to everyone following the reverse-engineering effort, testing releases, reviewing logs, and helping expand support for Precision Plex-equipped coaches.

This release represents the most complete and polished version of the project to date.
