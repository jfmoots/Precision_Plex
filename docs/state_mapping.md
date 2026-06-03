# State Mapping

## Level Monitor and Generator Telemetry

The Level Monitor page and generator telemetry are decoded from the `02AA` status packet, observed at handle `0x002B`.

Example payload:

```text
00 83 06 3F 3F 50 10 04 B5 ...
```

## Known Fields

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |
| Generator Running | byte 6 bit `0x10` | `0x00=stopped`, `0x10=running` |
| Generator Runtime | bytes 7-8, big-endian tenths of hours | `0x04B5` = 120.5 hours |

## Tank Level Encoding

Fresh, Grey, and Black use a four-state tank encoding:

```text
0x0 = Empty / 0%
0x3 = 1/3 / 33%
0x6 = 2/3 / 67%
0xA = Full / 100%
```

## LP Level Encoding

LP uses a five-state encoding:

```text
0x0 = Empty / 0%
0x2 = 1/4 / 25%
0x5 = 1/2 / 50%
0x7 = 3/4 / 75%
0xA = Full / 100%
```

## Generator Telemetry

Generator telemetry was confirmed in the same packet:

```text
Stopped: 0083 000F 0F50 0004 B400 0001 ...
Running: 0088 000F 0F50 1004 B400 0001 ...
```

- Generator running flag: byte 6 bit `0x10`
- Generator runtime: bytes 7-8 as big-endian tenths of hours
- Example: `0x04B4` = 1204 tenths = 120.4 hours

The runtime value was observed updating live from 120.4 to 120.5 hours in Home Assistant at the same time as the Precision Plex display.

## Notes

The tank and LP values are interpreted states from the Precision Plex controller, not raw probe continuity states. The controller handles probe interpretation and transmits the resulting status over BLE.
