# Precision Plex Home Assistant Integration v3.0.0

## Major Release: Built-In BLE Pairing / Bonding

This release promotes the working Precision Plex BLE pairing workflow into the integration setup flow.

Version 3.0.0 is a major release because setup behavior has changed significantly: Home Assistant can now perform the Precision Plex BLE bonding step during integration setup instead of requiring the system to already be paired manually.

## Highlights

- Adds a Home Assistant config-flow pairing step.
- Registers a temporary BlueZ `NoInputNoOutput` pairing agent during setup.
- Supports the Precision Plex app-style BLE security flow observed in PacketLogger traces.
- Confirms the working BLE control endpoint is the Precision advertiser, for example `80:4B:50:D2:44:B4`, rather than the separate `BLE#0x...` advertiser.
- Preserves the existing v2.6.33 runtime behavior and supported entities.

## Pairing Behavior

During setup, select the discovered Precision Plex device, put the Precision Plex console into **Pair with Mobile** mode, and continue the config flow. The integration registers a temporary BlueZ pairing agent, requests BLE pairing/bonding, writes the existing app/session initialization payload, and then creates the Home Assistant config entry.

Successful pairing has been validated with BlueZ showing:

```text
Paired: yes
Bonded: yes
Trusted: yes
LE.Paired: yes
LE.Bonded: yes
```

## Technical Notes

PacketLogger analysis showed the official app receives `Insufficient Authentication` from a protected GATT operation, then proceeds through a normal BLE SMP pairing/security exchange. The final working Home Assistant implementation therefore uses BlueZ bonding with a temporary pairing agent rather than treating the `06` payload as the pairing mechanism itself.

The `06` payload remains an application/session initialization write after the BLE bond is established.

## Upgrade Notes

Existing paired installations should continue to work. New installations, or systems where Home Assistant has been unpaired from the Precision Plex console, should use the config-flow pairing step.

If pairing fails, remove the failed device/bond from BlueZ and the Precision Plex console, restart Home Assistant, then retry setup with the console in **Pair with Mobile** mode.
