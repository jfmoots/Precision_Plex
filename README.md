# Precision Plex Home Assistant Integration

Version 1.0 custom Home Assistant integration for controlling a Precision Plex BLE RV awning light.

## Version 1.0 status

Working:

- Home Assistant ON turns the physical awning light ON.
- Home Assistant OFF turns the physical awning light OFF.
- Uses a bonded/trusted BLE connection.
- Uses the required OFF → ON sequence for ON commands.
- Normal routine BLE logs are at debug level to avoid log spam.

Known limitation:

- Changes made from the physical Precision Plex wall panel do not update Home Assistant state yet.

## Installation

Copy this folder into Home Assistant as:

```text
/config/custom_components/precision_plex/
```

Then restart Home Assistant.

## Bluetooth pairing requirement

The Precision Plex device must be paired, bonded, and trusted with the Home Assistant host.

Check with:

```bash
bluetoothctl info 80:4B:50:D2:44:B4
```

Expected:

```text
Paired: yes
Bonded: yes
Trusted: yes
```

If pairing is difficult because the Precision Plex pairing window is short, this delayed `bluetoothctl` script was used successfully:

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

## Notes

The ON command intentionally sends OFF first, waits 0.5 seconds, then sends ON. This matches the behavior needed for the physical light to respond reliably.
