# Precision Plex v4.3.9

Frame alignment protection diagnostics build.

## Changes

- Adds a pre-decode guard for shifted 02AA telemetry frames.
- Rejects one-byte-misaligned frames before they can update tank, propane, generator, pump, or other fixed-position entities.
- Keeps the v4.3.8 generator runtime protection and masked decode behavior.
- Logs rejected misaligned frames with the raw packet so the frame-boundary issue can be confirmed from Home Assistant logs.

## Why

Runtime diagnostics showed packets like the normal frame:

```text
00 87 00 0f 0f 50 00 04 b6 ... ae
```

and a shifted version:

```text
87 00 0f 0f 50 00 04 b6 ... ae 55
```

The shifted frame caused fixed byte offsets to decode the wrong fields, which could affect more than generator runtime. This build rejects that frame pattern before any entity state is updated.
