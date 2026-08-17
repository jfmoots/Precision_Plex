# Precision Plex Home Assistant Integration

Local monitoring and control for supported Precision Circuits Precision Plex
systems.

## Current release

**v5.5.9 - Stable Awning Position After Restart**

- Ignores stale awning motion bits during startup until authoritative idle
  telemetry is received.
- Preserves immediate command response, wall-panel tracking after startup, and
  the smart Carefree Flip sequence's synthetic 100% open endpoint.

- Prefers a discovered ESPHome Precision Plex LIN bridge for telemetry.
- Retains Bluetooth as field-level fallback and for all commands.
- Uses independent 30-second freshness grace periods for rotating LIN sources.
- Keeps a four-second whole-bridge timeout for genuine communication loss.
- Observes PID1F touchscreen and PID5E Wireless TP command intent immediately,
  then reconciles it against authoritative PID32/02BB state.
- Marshals every LIN telemetry/listener update onto Home Assistant's event loop
  before changing coordinator state or updating entities.
- Accepts compact firmware heartbeats without losing the last complete
  telemetry snapshot.
- Applies the same responsive state to covers, switches, lights, and their
  matching movement/status binary sensors.
- Disables high-churn BLE forensic entities by default and migrates existing
  entries to the same quieter defaults.
- Keeps raw packet bytes and transport counters out of ordinary entity
  attributes while retaining them in Download diagnostics; live motor current
  remains available from its dedicated ESPHome sensor.

## Supported systems

- Coach battery voltage
- Fresh, grey, black, and propane tank levels
- Generator status, runtime, start, stop, AutoStart, and AutoStop
- Awning light, water pump, and water heater
- Patio awning and Bedroom, Sofa, and Wardrobe slides
- Tank heater, AC/converter, and ignition telemetry from LIN
- Two-zone HVAC room temperature, setpoint, mode, phase, operating state, fan,
  and compressor-lockout telemetry from LIN
- Optional slide quadrature and awning current-sensing enhancements

Generator cumulative runtime now prefers validated LIN PIDBA telemetry with
Bluetooth fallback. All commands remain on Bluetooth while the LIN command path
is investigated.

## Transport behavior

The integration automatically discovers the co-located ESPHome LIN bridge and
prefers fresh LIN values field by field. If a LIN field is unavailable, the
integration falls back to Bluetooth where an equivalent value exists.

Rotating PIDBA, PID32, PIDEC, and PID37 broadcasts retain their last valid state
for 30 seconds while the bridge heartbeat remains healthy. If the event
heartbeat stops, LIN telemetry becomes unavailable after four seconds.

PID1F and PID5E are the fast command-intent channels. Firmware v0.6.3 folds
their request and accepted/active forms into one edge-driven event stream,
ignores repeated hold traffic, and publishes a release only for the motion
channel that was active. The integration uses that event to show toggles and
movement immediately, regardless of whether the action began in Home
Assistant, at the touchscreen, or through the Wireless TP path.

PID32 remains authoritative confirmation. If it does not confirm an intent
within 12 seconds, the temporary requested state expires back to telemetry.
With older firmware that lacks intent events, Home Assistant commands retain
the v5.5.5 local provisional-state fallback.

## Installation

### HACS

1. Add this repository to HACS as a custom integration repository.
2. Install **Precision Plex**.
3. Restart Home Assistant.
4. Add Precision Plex from **Settings > Devices & services**.

### Manual

Copy `custom_components/precision_plex` into the Home Assistant
`custom_components` directory, restart Home Assistant, and add the integration
from **Settings > Devices & services**.

## Tested coach

Development and validation are based on a **2022 Forest River Georgetown GT5
34M5** using the Precision Plex profile:

```text
Model_Georgetown_GT_34M5_w_2AC
```

Other coaches may use different circuits, commands, tanks, slides, or profiles.

## Diagnostics

Operational telemetry and connection status remain enabled. High-frequency BLE
packet timestamps, counters, rejection details, and forensic logs are disabled
by default to reduce Home Assistant Activity and recorder traffic. They can be
re-enabled temporarily from the entity registry for troubleshooting. Detailed
redacted information is also available through **Download diagnostics**.

The internal snapshot event is live transport rather than useful history. To
keep Recorder from storing it, add this event type to the existing Recorder
exclusions and restart Home Assistant:

```yaml
recorder:
  exclude:
    event_types:
      - esphome.precision_plex_lin_snapshot
```

## Release history

See [CHANGELOG.md](CHANGELOG.md) for consolidated milestones. Detailed release
descriptions remain available with the corresponding GitHub releases.

## Safety

Slides, awnings, generators, water heaters, and other RV equipment control real
physical systems. Maintain line-of-sight during movement, preserve factory
controls and interlocks, and follow the vehicle and equipment manufacturers'
safety instructions.
