# Precision Plex Home Assistant Integration

Custom Home Assistant integration for controlling a Precision Plex BLE RV controller.

## Version 1.1.0

### Features

- Bluetooth config flow for Home Assistant UI setup
- Bluetooth discovery of Precision Plex devices
- Friendly device naming, for example `Precision - D244B4 (80:4B:50:D2:44:B4)`
- Stable awning light ON/OFF control
- Uses the discovered or selected Bluetooth address from the config entry
- Minimal normal-operation logging

### Known limitations

- Wall-panel state changes are not currently reflected in Home Assistant.
- The Home Assistant UI state reflects commands sent from Home Assistant.
- The Precision Plex controller must already be paired, bonded, and trusted with the Home Assistant host.

## Installation

Copy the integration folder into Home Assistant:

```text
/config/custom_components/precision_plex/
```

Restart Home Assistant.

Then add the integration from:

```text
Settings → Devices & services → Add integration → Precision Plex
```

Select the discovered Precision Plex Bluetooth device.

## Required Bluetooth pairing

Before setup, the Precision Plex controller must be paired and trusted from the Home Assistant host.

A working pairing sequence used during development was:

```bash
(
sleep 1
echo agent on
sleep 1
echo default-agent
sleep 1
echo power on
sleep 1
echo scan on
sleep 2
echo pair 80:4B:50:D2:44:B4
sleep 8
echo trust 80:4B:50:D2:44:B4
sleep 1
echo connect 80:4B:50:D2:44:B4
sleep 5
echo info 80:4B:50:D2:44:B4
sleep 1
echo quit
) | bluetoothctl
```

Run this immediately after pressing **Pair with Mobile** on the Precision Plex controller.

Verify that Bluetooth shows:

```text
Paired: yes
Bonded: yes
Trusted: yes
```

## Behavior

Home Assistant ON sends an OFF command followed by an ON command in one bonded BLE session. This matches the working behavior discovered during reverse engineering.

Home Assistant OFF sends the OFF command.

## Repository layout

```text
custom_components/
└── precision_plex/
    ├── __init__.py
    ├── config_flow.py
    ├── const.py
    ├── light.py
    └── manifest.json
```
