# Telemetry Validation

Precision Plex BLE telemetry is mostly stable, but field testing showed that the wireless telemetry stream can occasionally emit transient invalid or malformed values. The official Precision Plex mobile app has also been observed to briefly show impossible tank readings, which supports treating the BLE stream as a source that needs validation before publishing user-facing Home Assistant states.

## 02AA Telemetry Frame

The 02AA notification stream carries the major read-only telemetry values:

- Coach battery voltage
- Fresh water level
- Grey water level
- Black water level
- Propane level
- Generator status
- Generator runtime

The integration performs frame-shape checks before decoding 02AA telemetry. Frames that appear shifted or malformed are rejected before any entity state is updated.

## Propane Validation

Controlled monitor traces confirmed the clean propane display encodings:

| Raw LP byte | Displayed level |
| --- | ---: |
| `0x00` | 0% |
| `0x20` | 25% |
| `0x50` | 50% |
| `0x70` | 75% |
| `0xA0` | 100% |

Long-duration diagnostics also observed transient LP bytes such as `0x05`, `0x0A`, `0x14`, and `0x28`. These do not match the clean display encoding and can cause false propane readings if published directly.

The integration now rejects non-clean LP samples and retains the last known good propane value.

## Tank Validation

Fresh, grey, and black water tanks use discrete level encodings:

| Raw nibble | Displayed level |
| --- | ---: |
| `0x0` | 0% |
| `0x3` | 33% |
| `0x6` | 67% |
| `0xA` | 100% |

Invalid tank nibbles are ignored rather than published.

## Generator Status

Generator status uses a base status byte with flag variants. Known flag variants are collapsed into clean user-facing states while the raw byte remains available for diagnostics.

Examples:

| Raw status | User-facing state |
| --- | --- |
| `0x00`, `0x40`, `0x80`, `0xC0` | Stopped |
| `0x10`, `0x90` | Running |

Other mapped generator states include AutoStart Accepted, Stop Accepted, AutoStart in progress, AutoStop in progress, and Will Not Start.

## Generator Runtime

Generator runtime is protected by sanity checks. Runtime candidates are rejected if they move backwards, jump implausibly, or come from malformed telemetry. The last known good runtime is retained when an invalid candidate is rejected.

## v4.5.1 Follow-Up: 02AA Frame Shape and LP Confirmation

Additional review after v4.5.0 showed that malformed or misleading 02AA samples can sometimes look valid at an individual field level. v4.5.1 adds stricter frame-shape validation before decoding telemetry.

For the tested coach, accepted 02AA telemetry frames are expected to be 20 bytes long and preserve the known tank framing nibbles around the fresh, grey, and black tank fields. Frames that do not match this shape are discarded before entity states are updated.

LP telemetry also now requires confirmation before publishing a changed clean value after startup. The first valid LP value initializes immediately. After that, a different LP percentage must appear in consecutive accepted frames before it replaces the last known good value. This prevents brief one-sample propane blips while still allowing real LP changes to propagate quickly.


## v4.5.2 Follow-Up: Production Logging Cleanup

v4.5.2 removes the remaining generator runtime source diagnostic message from normal logging while keeping the runtime recovery and sanity logic in place. 02AA and 02BB subscription confirmations are retained as informational startup events.
