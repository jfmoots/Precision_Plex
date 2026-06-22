# State Mapping

## Level Monitor and Generator Telemetry

The Level Monitor page and generator telemetry are decoded from the `02AA` status packet, observed at handle `0x002B`.

Representative payloads:

```text
Stopped:      00 83 00 0F 0F 50 00 04 B4 00 00 01 ...
Running:      00 88 00 0F 0F 50 10 04 B4 00 00 01 ...
WillNotStart: 00 8F 00 0F 0F 50 20 04 B6 00 00 01 ...
```

## Known Fields

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |
| Generator status word | bytes 6-7, big-endian | see generator status table |
| Generator Runtime | established decoder path uses adjacent bytes as big-endian tenths of hours | `0x04B4` = 120.4 hours |

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

Generator telemetry was confirmed in the same `02AA` / handle `0x002B` packet.

| Status Word | Home Assistant Status | Notes |
|---:|---|---|
| `0x0004` | `Stopped` | Generator off |
| `0x1004` | `Running` | Generator running |
| `0x00A0` | AutoStart accepted / transitional | Brief transition seen after AutoStart command |
| `0x2004` | `Will Not Start` | Confirmed after four failed AutoStart attempts |
| `0x6004` | `Performing Generator AutoStart` | Managed start sequence in progress |
| `0x7004` | `Performing Generator AutoStop` | Managed stop sequence in progress |

Other confirmed generator fields:

- Generator running binary sensor: derived from the confirmed running status/flag.
- Generator runtime: decoded as tenths of hours; `0x04B4` = 120.4 hours.
- Runtime was observed updating live from 120.4 to 120.5 hours in Home Assistant at the same time as the Precision Plex display.

## Notes

The tank and LP values are interpreted states from the Precision Plex controller, not raw probe continuity states. The controller handles probe interpretation and transmits the resulting status over BLE.

A matching `Will Not Stop` generator status likely exists, but it has not been safely captured. Unknown future generator status codes are exposed/logged as raw values for later decoding.
