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

## 02BB State Frame

The 02BB notification stream carries state words used by the app-visible switches, covers, lights, and movement flags. Cover entities expose raw 02BB bytes and state words as diagnostic attributes.

## Quadrature Slide Telemetry

v5.2.0 adds optional ESPHome quadrature slide telemetry for Bedroom, Sofa, and Wardrobe slides.

The integration validates telemetry availability before using it as the cover position source. If quadrature entities are missing or unavailable, the cover falls back to the existing timing model.

Quadrature diagnostics include:

- `quadrature_available`
- `quadrature_travel_total`
- `quadrature_full_travel`
- `quadrature_sync_error`
- `quadrature_last_delta`

Tested full-travel values:

| Slide | Full Travel Count | Observed Sync Error at Full Extension |
| --- | ---: | ---: |
| Bedroom | 21,727 | ~36-39 counts |
| Sofa | 21,503 | ~24 counts |
| Wardrobe | 13,873 | ~64-67 counts |

The sync error value is a diagnostic difference between the two decoded motor positions. It is not currently used to block movement.

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

The integration rejects non-clean LP samples and retains the last known good propane value.

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
